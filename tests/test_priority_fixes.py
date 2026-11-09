# -*- coding: utf-8 -*-
"""高/中优先级修复的回归测试（SQLite 覆盖，不连生产库）。

覆盖点：
- 批量导入兼容重量缺失(0)的行，负重量行跳过（不再让整片 400 回滚）
- 覆盖导入写一条 REPLACE 汇总审计
- update_bill 无实际变更不写 UPDATE 审计；有变更时金额 JSON 归一为字符串
- BillCreate 域校验：status/currency/fee_type 非法值被拒绝
- 未改密用户后端强制 403（改密页接口放行）
- /bills 的 exclude_packaging 过滤
- 品种服务端分页 list_species_paginated
- 管理员注册的新用户 must_change_password=True
"""
import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
_DB_PATH = BACKEND_ROOT / "test_priority_fixes.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pydantic  # noqa: E402
import models  # noqa: E402
import schemas  # noqa: E402
import auth as auth_mod  # noqa: E402
from database import engine, SessionLocal  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from routers import auth as auth_router  # noqa: E402
from services.bill_service import (  # noqa: E402
    batch_create_bills,
    create_bill,
    list_bills,
    update_bill,
)
from services.species_service import list_species_paginated  # noqa: E402


class PriorityFixesTests(unittest.TestCase):
    def setUp(self):
        models.Base.metadata.drop_all(engine)
        models.Base.metadata.create_all(engine)
        self.db = SessionLocal()
        self.user = models.User(username="u", password_hash="x", role="admin")
        self.db.add(self.user)
        self.db.flush()
        self._mk_species("草鱼")

    def tearDown(self):
        self.db.close()

    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        if _DB_PATH.exists():
            _DB_PATH.unlink()

    def _mk_species(self, name, price=1):
        sp = models.Species(name_zh=name, default_unit="公斤", default_price=price)
        self.db.add(sp)
        self.db.flush()
        return sp

    def _bill(self, sp, d=None, w=1.0):
        if d is None:
            d = date.today()
        return create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=w, unit_price=1, fee_value=0,
                release_date=d, status="DRAFT",
            ),
            self.user,
            self.db,
            commit=True,
        )

    def _req(self, rows, replace=False, replace_dates=None):
        return schemas.BatchImportRequest(
            rows=[schemas.BatchImportRow(**r) for r in rows],
            replace=replace,
            replace_dates=replace_dates,
        )

    # ---- 批量导入：重量缺失(0)的行兼容导入，仅负重量行跳过 ----
    def test_batch_import_zero_weight_imported_negative_skipped(self):
        sp = self._mk_species("鲫鱼")
        result = batch_create_bills(
            self._req([
                {"name_zh": "草鱼", "weight": 0, "unit_price": 2, "fee_value": 0,
                 "release_date": date(2026, 11, 7)},
                {"name_zh": "鲫鱼", "weight": -1, "unit_price": 2, "fee_value": 0,
                 "release_date": date(2026, 11, 7)},
                {"name_zh": "鲫鱼", "weight": 2, "unit_price": 2, "fee_value": 0,
                 "release_date": date(2026, 11, 7)},
            ]),
            self.user,
            self.db,
        )
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.skip_count, 1)
        self.assertEqual(len(result.errors), 1)
        active = self.db.query(models.Bill).filter(models.Bill.is_deleted.is_(False)).all()
        self.assertEqual(len(active), 2)
        weights = sorted(float(b.weight) for b in active)
        self.assertEqual(weights, [0.0, 2.0])
        self.assertIn(sp.id, [b.species_id for b in active])

    # ---- 覆盖导入写 REPLACE 汇总审计 ----
    def test_batch_replace_writes_replace_audit(self):
        sp = self._mk_species("鲫鱼")
        self._bill(sp, d=date(2026, 11, 7))
        self.db.commit()

        batch_create_bills(
            self._req(
                [{"name_zh": "鲫鱼", "weight": 2, "unit_price": 2, "fee_value": 0,
                  "release_date": date(2026, 11, 7)}],
                replace=True,
            ),
            self.user,
            self.db,
        )
        logs = (
            self.db.query(models.AuditLog)
            .filter(models.AuditLog.action == "REPLACE")
            .all()
        )
        self.assertEqual(len(logs), 1)
        detail = json.loads(logs[0].old_data)
        self.assertIn("2026-11-07", detail["dates"])
        self.assertEqual(detail["deleted_bills"], 1)

    # ---- 无实际变更不写 UPDATE 审计 ----
    def test_update_bill_no_change_skips_audit(self):
        sp = self.db.query(models.Species).first()
        bill = self._bill(sp, d=date.today())
        self.db.query(models.AuditLog).delete()
        self.db.commit()

        update_bill(
            bill.id,
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=1, fee_value=0,
                release_date=date.today(), status="DRAFT",
            ),
            self.user,
            self.db,
        )
        updates = (
            self.db.query(models.AuditLog)
            .filter(models.AuditLog.action == "UPDATE", models.AuditLog.bill_id == bill.id)
            .all()
        )
        self.assertEqual(len(updates), 0)

    # ---- 有变更时金额在审计 JSON 里归一为字符串 ----
    def test_update_bill_normalizes_money_in_audit(self):
        sp = self.db.query(models.Species).first()
        bill = self._bill(sp, d=date.today())
        self.db.query(models.AuditLog).delete()
        self.db.commit()

        update_bill(
            bill.id,
            schemas.BillCreate(
                species_id=sp.id, weight=2, unit_price=1.5, fee_value=0,
                release_date=date.today(), status="DRAFT",
            ),
            self.user,
            self.db,
        )
        log = (
            self.db.query(models.AuditLog)
            .filter(models.AuditLog.action == "UPDATE", models.AuditLog.bill_id == bill.id)
            .one()
        )
        new_data = json.loads(log.new_data)
        old_data = json.loads(log.old_data)
        self.assertEqual(new_data["weight"], "2.00")
        self.assertEqual(old_data["weight"], "1.00")
        self.assertEqual(new_data["unit_price"], "1.50")

    # ---- 域校验 ----
    def test_bill_create_rejects_invalid_domain_values(self):
        base = dict(species_id=1, weight=1, unit_price=1, fee_value=0)
        with self.assertRaises(pydantic.ValidationError):
            schemas.BillCreate(**base, status="FOO")
        with self.assertRaises(pydantic.ValidationError):
            schemas.BillCreate(**base, currency="USD")
        with self.assertRaises(pydantic.ValidationError):
            schemas.BillCreate(**base, fee_type="PERCENTAGE")

    # ---- 未改密用户后端强制 403 ----
    def test_must_change_password_enforced(self):
        user = models.User(
            username="fresh", password_hash="x", role="operator",
            must_change_password=True,
        )
        self.db.add(user)
        self.db.commit()
        token = auth_mod.create_access_token(data={"sub": "fresh"})

        # 普通业务接口 403
        with self.assertRaises(HTTPException) as ctx:
            auth_mod.get_current_user(
                request=SimpleNamespace(url=SimpleNamespace(path="/api/bills")),
                token=token,
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

        # 改密页接口放行
        allowed = auth_mod.get_current_user(
            request=SimpleNamespace(url=SimpleNamespace(path="/api/change-password")),
            token=token,
            db=self.db,
        )
        self.assertEqual(allowed.username, "fresh")

    # ---- exclude_packaging ----
    def test_list_bills_exclude_packaging(self):
        sp = self.db.query(models.Species).first()
        ice = self._mk_species("冰块")
        self._bill(sp, d=date(2026, 11, 7))
        self._bill(ice, d=date(2026, 11, 7))
        self.db.commit()

        result = list_bills(self.db, limit=0, exclude_packaging=True)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0].species_id, sp.id)

    # ---- 品种服务端分页 ----
    def test_list_species_paginated(self):
        sp = self.db.query(models.Species).first()
        self._mk_species("鲫鱼")
        self._mk_species("甲鱼")
        self.db.commit()

        items, total = list_species_paginated(self.db, None, page=1, page_size=2)
        self.assertEqual(total, 3)
        self.assertEqual(len(items), 2)
        items2, total2 = list_species_paginated(self.db, None, page=2, page_size=2)
        self.assertEqual(total2, 3)
        self.assertEqual(len(items2), 1)

    # ---- 非 admin 账号只读 ----
    def test_require_write_blocks_operator(self):
        operator = models.User(
            username="op_ro", password_hash="x", role="operator",
            must_change_password=False,
        )
        self.db.add(operator)
        self.db.commit()
        with self.assertRaises(HTTPException) as ctx:
            auth_mod.require_write(current_user=operator)
        self.assertEqual(ctx.exception.status_code, 403)
        admin = self.db.query(models.User).filter(models.User.username == "u").one()
        self.assertEqual(auth_mod.require_write(current_user=admin).username, "u")

    # ---- 注册新用户强制改密 ----
    def test_register_sets_must_change_password(self):
        admin = self.db.query(models.User).filter(models.User.username == "u").one()
        auth_router.register(
            user=schemas.UserCreate(username="newop", password="abcdef", role="operator"),
            db=self.db,
            current_user=admin,
        )
        created = self.db.query(models.User).filter(models.User.username == "newop").one()
        self.assertTrue(created.must_change_password)

    # ---- 启动探测：单查询版 _tables_exist ----
    def test_tables_exist_fast_probe(self):
        from app import _tables_exist

        models.Base.metadata.create_all(engine)
        self.assertTrue(_tables_exist())

    # ---- 启动探测：bootstrap 列检查幂等 ----
    def test_ensure_db_schema_updates_idempotent(self):
        import bootstrap
        from sqlalchemy import inspect as sa_inspect

        models.Base.metadata.create_all(engine)
        bootstrap.ensure_db_schema_updates()
        bootstrap.ensure_db_schema_updates()  # 第二遍不得报错（幂等）

        insp = sa_inspect(engine)
        bills_cols = {c["name"] for c in insp.get_columns("bills")}
        for needed in (
            "status", "is_deleted", "payment_method", "weekly_donation",
            "alipay_amount", "wechat_amount", "suixi_amount",
        ):
            self.assertIn(needed, bills_cols)
        species_cols = {c["name"] for c in insp.get_columns("species")}
        for needed in ("image_url", "default_price", "supplier_name", "supplier_note", "is_deleted"):
            self.assertIn(needed, species_cols)
        user_cols = {c["name"] for c in insp.get_columns("users")}
        self.assertIn("must_change_password", user_cols)


if __name__ == "__main__":
    unittest.main()
