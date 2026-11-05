# -*- coding: utf-8 -*-
"""批量导入覆盖（replace / replace_dates）回归测试（SQLite 覆盖，不连生产库）。"""
import os
import sys
import unittest
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
_DB_PATH = BACKEND_ROOT / "test_batch_import.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import models
import schemas
from database import engine, SessionLocal
from services.bill_service import batch_create_bills, create_bill


class BatchImportReplaceTests(unittest.TestCase):
    def setUp(self):
        models.Base.metadata.drop_all(engine)
        models.Base.metadata.create_all(engine)
        self.db = SessionLocal()
        self.user = models.User(username="u", password_hash="x", role="admin")
        self.db.add(self.user)
        self.db.flush()
        self.sp = models.Species(name_zh="草鱼", default_unit="公斤", default_price=1)
        self.db.add(self.sp)
        self.db.flush()

    def tearDown(self):
        self.db.close()

    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        if _DB_PATH.exists():
            _DB_PATH.unlink()

    def _bill(self, d, w=1.0):
        return create_bill(
            schemas.BillCreate(
                species_id=self.sp.id, weight=w, unit_price=1, fee_value=0, release_date=d
            ),
            self.user,
            self.db,
            commit=False,
        )

    def test_replace_dates_clears_given_dates_even_if_absent_from_rows(self):
        """首片带上整份文件的日期集合时，即使某日期不在这片 rows 里也要被清空。"""
        self._bill(date(2026, 10, 31))
        self._bill(date(2026, 10, 31))
        self.db.commit()

        req = schemas.BatchImportRequest(
            rows=[
                schemas.BatchImportRow(
                    name_zh="草鱼", weight=2, unit_price=3, fee_value=0,
                    release_date=date(2026, 11, 7),
                )
            ],
            replace=True,
            replace_dates=[date(2026, 10, 31), date(2026, 11, 7)],
        )
        batch_create_bills(req, self.user, self.db)

        active = self.db.query(models.Bill).filter(models.Bill.is_deleted.is_(False)).all()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].release_date, date(2026, 11, 7))
        old = (
            self.db.query(models.Bill)
            .filter(models.Bill.release_date == date(2026, 10, 31))
            .all()
        )
        self.assertEqual(len(old), 2)
        self.assertTrue(all(b.is_deleted for b in old))

    def test_without_replace_keeps_existing_rows(self):
        self._bill(date(2026, 10, 31))
        self.db.commit()

        req = schemas.BatchImportRequest(
            rows=[
                schemas.BatchImportRow(
                    name_zh="草鱼", weight=2, unit_price=3, fee_value=0,
                    release_date=date(2026, 10, 31),
                )
            ],
            replace=False,
        )
        batch_create_bills(req, self.user, self.db)

        active = self.db.query(models.Bill).filter(models.Bill.is_deleted.is_(False)).count()
        self.assertEqual(active, 2)

    def test_replace_soft_deletes_dates_from_rows(self):
        self._bill(date(2026, 11, 7))
        self.db.commit()

        req = schemas.BatchImportRequest(
            rows=[
                schemas.BatchImportRow(
                    name_zh="草鱼", weight=2, unit_price=3, fee_value=0,
                    release_date=date(2026, 11, 7),
                )
            ],
            replace=True,
        )
        batch_create_bills(req, self.user, self.db)

        active = self.db.query(models.Bill).filter(models.Bill.is_deleted.is_(False)).count()
        self.assertEqual(active, 1)

    def test_import_rows_keep_payment_amounts(self):
        """导入行携带的三个随喜金额 + 随喜类型要落库（列表/导出都要用）。"""
        req = schemas.BatchImportRequest(
            rows=[
                schemas.BatchImportRow(
                    name_zh="草鱼", weight=2, unit_price=3, fee_value=0,
                    release_date=date(2026, 11, 7),
                    alipay_amount=364, payment_method="支付宝",
                ),
                schemas.BatchImportRow(
                    name_zh="鲫鱼", weight=1, unit_price=3, fee_value=0,
                    release_date=date(2026, 11, 7),
                    wechat_amount=387, payment_method="微信",
                ),
                schemas.BatchImportRow(
                    name_zh="甲鱼", weight=1, unit_price=3, fee_value=0,
                    release_date=date(2026, 11, 7),
                    suixi_amount=1300, payment_method="随喜放生",
                ),
            ],
            replace=True,
        )
        batch_create_bills(req, self.user, self.db)

        bills = (
            self.db.query(models.Bill)
            .filter(models.Bill.is_deleted.is_(False))
            .order_by(models.Bill.id.asc())
            .all()
        )
        self.assertEqual(len(bills), 3)
        self.assertEqual(float(bills[0].alipay_amount), 364.0)
        self.assertEqual(bills[0].payment_method, "支付宝")
        self.assertEqual(float(bills[1].wechat_amount), 387.0)
        self.assertEqual(bills[1].payment_method, "微信")
        self.assertEqual(float(bills[2].suixi_amount), 1300.0)
        self.assertEqual(bills[2].payment_method, "随喜放生")


if __name__ == "__main__":
    unittest.main()
