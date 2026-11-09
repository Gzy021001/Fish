# -*- coding: utf-8 -*-
"""导出时保留源表「件/个」原始计价单位（回归测试，独立 SQLite，不连生产库）。

源表《慈悲组购生明细表》里按件/个报价的行（蛏子（件）2 件×120、带子（个）100 个×4.5），
单据入库时按 公斤/元/公斤 记账，但导出要还原成模板写法，而不是统一折成斤。
"""
import os
import sys
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
_DB_PATH = BACKEND_ROOT / "test_export_unit.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import openpyxl

import models
import schemas
from database import engine, SessionLocal
from services.bill_service import create_bill
from services.export_service import build_bills_export


class ExportUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if _DB_PATH.exists():
            _DB_PATH.unlink()
        models.Base.metadata.create_all(engine)
        cls.db = SessionLocal()
        user = models.User(username="unit_test", password_hash="x", role="admin", must_change_password=False)
        cls.db.add(user)
        cls.db.flush()
        cls.user = user

        def species(name):
            s = models.Species(name_zh=name, default_unit="公斤", default_price=0, is_deleted=False)
            cls.db.add(s)
            cls.db.flush()
            return s

        cls.sp_clam = species("蛏子")
        cls.sp_scallop = species("带子")
        cls.sp_turtle = species("草龟")

        day = date(2026, 8, 8)
        # 蛏子（件）：2 件 × 120 元/件 → 10 公斤 × 24 元/公斤
        create_bill(schemas.BillCreate(
            species_id=cls.sp_clam.id, weight=10, unit_price=24, fee_value=0,
            release_date=day, unit="件", unit_jin=10,
        ), cls.user, cls.db)
        # 带子（个）：100 个 × 4.5 元/个 → 50 公斤 × 9 元/公斤
        create_bill(schemas.BillCreate(
            species_id=cls.sp_scallop.id, weight=50, unit_price=9, fee_value=0,
            release_date=day, unit="个", unit_jin=1,
        ), cls.user, cls.db)
        # 小草龟（个）：30 个 × 5.5 元/个 → 3.3 公斤 × 50 元/公斤（1 个 = 0.22 斤）
        create_bill(schemas.BillCreate(
            species_id=cls.sp_turtle.id, weight=3.3, unit_price=50, fee_value=0,
            release_date=day, unit="个", unit_jin=0.22,
        ), cls.user, cls.db)
        cls.db.commit()

        content, _ = build_bills_export(cls.db, "2026-08-08", "2026-08-08")
        cls.wb = openpyxl.load_workbook(BytesIO(content.getvalue()), data_only=False)
        cls.ws = cls.wb.worksheets[0]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _row_of(self, prefix, unit=None):
        for r in range(4, self.ws.max_row + 1):
            name = self.ws.cell(row=r, column=3).value or ""
            if name.startswith(prefix) and (unit is None or f"（{unit}）" in name):
                return r
        self.fail(f"导出表里找不到 {prefix}（{unit}）行")

    def test_piece_row_keeps_jian(self):
        r = self._row_of("蛏子", "件")
        self.assertEqual(self.ws.cell(row=r, column=4).value, 2)      # 2 件
        self.assertEqual(self.ws.cell(row=r, column=5).value, 120)    # 120 元/件
        self.assertEqual(self.ws.cell(row=r, column=6).value, f"=D{r}*E{r}")

    def test_count_row_keeps_ge(self):
        r = self._row_of("带子", "个")
        self.assertEqual(self.ws.cell(row=r, column=4).value, 100)    # 100 个
        self.assertEqual(self.ws.cell(row=r, column=5).value, 4.5)    # 4.5 元/个

    def test_small_turtle_count_row(self):
        r = self._row_of("草龟", "个")
        self.assertEqual(self.ws.cell(row=r, column=4).value, 30)     # 30 个
        self.assertEqual(self.ws.cell(row=r, column=5).value, 5.5)    # 5.5 元/个

    def test_plain_jin_row_unchanged(self):
        # 同一张表里按斤录入的行仍写 斤价（重量×2、单价÷2）
        day = date(2026, 8, 9)
        create_bill(schemas.BillCreate(
            species_id=self.sp_clam.id, weight=23.5, unit_price=24, fee_value=0, release_date=day,
        ), self.user, self.db)
        self.db.commit()
        content, _ = build_bills_export(self.db, "2026-08-09", "2026-08-09")
        ws = openpyxl.load_workbook(BytesIO(content.getvalue()), data_only=False).worksheets[0]
        self.assertEqual(ws.cell(row=4, column=3).value, "蛏子")
        self.assertEqual(ws.cell(row=4, column=4).value, 47)
        self.assertEqual(ws.cell(row=4, column=5).value, 12)


if __name__ == "__main__":
    unittest.main()
