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

    # ---- 随喜汇总：只留有随喜记录的单据，并回三分类合计 ----
    def test_list_bills_has_suixi_filter_and_sums(self):
        sp = self.db.query(models.Species).first()
        # 有随喜金额的单据
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=2, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 8), status="COMPLETED",
                payment_method="微信", alipay_amount=0,
                wechat_amount=25.5, suixi_amount=0,
            ),
            self.user, self.db, commit=True,
        )
        # 只填了随喜类型、没填金额的历史单据也要保留
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 8), status="COMPLETED",
                payment_method="支付宝",
            ),
            self.user, self.db, commit=True,
        )
        # 没有任何随喜记录的单据应被过滤
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 8), status="COMPLETED",
            ),
            self.user, self.db, commit=True,
        )
        self.db.commit()

        result = list_bills(
            self.db, page=1, page_size=10, limit=0,
            status="COMPLETED", has_suixi=True,
        )
        self.assertEqual(result["total"], 2)
        self.assertEqual(float(result["sum_wechat"]), 25.5)
        self.assertEqual(float(result["sum_alipay"]), 0.0)
        self.assertEqual(float(result["sum_suixi"]), 0.0)

        # 不带 has_suixi 时三张单据都在，合计口径不变
        all_bills = list_bills(self.db, page=1, page_size=10, limit=0, status="COMPLETED")
        self.assertEqual(all_bills["total"], 3)
        self.assertEqual(float(all_bills["sum_wechat"]), 25.5)

    # ---- 导入实付与车费/船费：paid_amount 落库、费用单独成表、列表合计口径 ----
    def test_batch_import_paid_amount_and_expenses(self):
        payload = schemas.BatchImportRequest(
            rows=[
                schemas.BatchImportRow(
                    name_zh="回填测试鱼", weight=10, unit_price=5, fee_value=0,
                    release_date=date(2026, 11, 21), paid_amount=48,
                ),
                schemas.BatchImportRow(
                    name_zh="回填测试鱼", weight=4, unit_price=5, fee_value=0,
                    release_date=date(2026, 11, 21),
                ),
            ],
            expenses=[
                schemas.BatchExpenseRow(name="车费", amount=30, release_date=date(2026, 11, 21)),
                schemas.BatchExpenseRow(name="船费", amount=20, release_date=date(2026, 11, 21)),
            ],
        )
        result = batch_create_bills(payload, self.user, self.db)
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.expense_count, 2)

        bills = self.db.query(models.Bill).filter(models.Bill.release_date == date(2026, 11, 21)).all()
        # 实付按批次分摊到每一行：两行合计仍为 48，且都不为空
        paid_values = sorted(float(b.paid_amount or 0) for b in bills)
        self.assertEqual(len(paid_values), 2)
        self.assertAlmostEqual(sum(paid_values), 48.0, places=2)
        self.assertTrue(all(v > 0 for v in paid_values))
        # 同批每一行都记着原始批次总额
        self.assertEqual([float(b.batch_paid) for b in bills], [48.0, 48.0])
        expenses = self.db.query(models.WeekExpense).all()
        self.assertEqual(sorted(float(e.amount) for e in expenses), [20.0, 30.0])

        summary = list_bills(self.db, page=1, page_size=10, date="2026-11-21")
        self.assertEqual(float(summary["sum_paid_amount"]), 48.0)
        self.assertEqual(float(summary["sum_expense"]), 50.0)

    # ---- 随喜汇总按放生日期聚合：一行一天，金额取当天合计，微信拆两列 ----
    def test_list_bills_group_by_date(self):
        sp = self.db.query(models.Species).first()
        # 11-08 两张单据：支付宝 10 + 微信 25.5 + 随喜放生 1300；当天第一张带本周现场随喜
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=2, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 8), status="COMPLETED",
                payment_method="微信", alipay_amount=10,
                wechat_amount=25.5, suixi_amount=0,
                weekly_donation=1234.56,
            ),
            self.user, self.db, commit=True,
        )
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 8), status="COMPLETED",
                payment_method="随喜放生", alipay_amount=0,
                wechat_amount=0, suixi_amount=1300,
            ),
            self.user, self.db, commit=True,
        )
        # 同一天的第二笔微信：进「微信2」，不与第一笔合并
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 8), status="COMPLETED",
                payment_method="微信", alipay_amount=0,
                wechat_amount=40, suixi_amount=0,
            ),
            self.user, self.db, commit=True,
        )
        # 11-09 一张支付宝单据
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 9), status="COMPLETED",
                payment_method="支付宝", alipay_amount=5,
                wechat_amount=0, suixi_amount=0,
            ),
            self.user, self.db, commit=True,
        )
        # 没有随喜记录的单据不进随喜汇总
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 9), status="COMPLETED",
            ),
            self.user, self.db, commit=True,
        )
        self.db.commit()

        result = list_bills(
            self.db, page=1, page_size=10, limit=0,
            status="COMPLETED", has_suixi=True, group_by_date=True,
        )
        # 两个放生日期 -> 两行，按日期倒序
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["items"]), 2)
        newest, older = result["items"]
        self.assertEqual(newest["release_date"], "2026-11-09")
        self.assertEqual(float(newest["alipay_amount"]), 5.0)
        self.assertEqual(float(newest["wechat1_amount"]), 0.0)
        self.assertEqual(float(newest["wechat2_amount"]), 0.0)
        self.assertEqual(float(newest["suixi_amount"]), 0.0)
        self.assertEqual(older["release_date"], "2026-11-08")
        self.assertEqual(float(older["alipay_amount"]), 10.0)
        # 当天第一笔微信 25.5 -> 微信1；第二笔 40 -> 微信2（不合并）
        self.assertEqual(float(older["wechat1_amount"]), 25.5)
        self.assertEqual(float(older["wechat2_amount"]), 40.0)
        self.assertEqual(float(older["suixi_amount"]), 1300.0)
        # 本周现场随喜按天带出（整周一个值，落在该周第一张单据那天）
        self.assertEqual(float(older["weekly_donation"]), 1234.56)
        self.assertEqual(float(newest["weekly_donation"]), 0.0)

        # 表尾合计仍按全量口径（与分页无关）
        self.assertEqual(float(result["sum_alipay"]), 15.0)
        self.assertEqual(float(result["sum_wechat"]), 65.5)
        self.assertEqual(float(result["sum_wechat1"]), 25.5)
        self.assertEqual(float(result["sum_wechat2"]), 40.0)
        self.assertEqual(float(result["sum_suixi"]), 1300.0)
        # 现场随喜合计（随喜汇总顶部卡片/表尾用）
        self.assertEqual(float(result["sum_weekly_donation"]), 1234.56)

        # 分页按天：第 2 页只剩更早的一天
        paged = list_bills(
            self.db, page=2, page_size=1, limit=0,
            status="COMPLETED", has_suixi=True, group_by_date=True,
        )
        self.assertEqual(paged["total"], 2)
        self.assertEqual(len(paged["items"]), 1)
        self.assertEqual(paged["items"][0]["release_date"], "2026-11-08")
        self.assertEqual(float(paged["items"][0]["wechat2_amount"]), 40.0)

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

    # ---- 品种库列表补「放生日期」：取最近一次有单据的放生日期 ----
    def test_attach_species_last_release(self):
        from services.species_service import (
            attach_species_last_release,
            serialize_species_list,
        )

        sp = self.db.query(models.Species).first()
        unused = self._mk_species("未使用品种")
        unused.release_date = date(2026, 10, 1)
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 7), status="COMPLETED",
            ),
            self.user, self.db, commit=True,
        )
        create_bill(
            schemas.BillCreate(
                species_id=sp.id, weight=1, unit_price=10, fee_value=0,
                release_date=date(2026, 11, 14), status="COMPLETED",
            ),
            self.user, self.db, commit=True,
        )
        self.db.commit()

        rows = serialize_species_list([sp, unused], include_images=False)
        attach_species_last_release(self.db, rows)
        by_name = {row["name_zh"]: row for row in rows}
        # 有单据：取最近一单（最近一周）的放生日期
        self.assertEqual(by_name[sp.name_zh]["last_release_date"], "2026-11-14")
        # 没有单据：回退品种自身的放生日期
        self.assertEqual(by_name["未使用品种"]["last_release_date"], "2026-10-01")

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
