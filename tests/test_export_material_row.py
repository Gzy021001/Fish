# -*- coding: utf-8 -*-
"""导出不应凭空生成「耗材」行（回归测试，独立 SQLite，不连生产库）。

背景：导入按 25 行分片，后端 apportion_rows 只在单个分片内分摊实付。同一批实付被分片
切断时两片各摊一遍，库里就会出现「已摊实付(paid_sum) > 批次实付合计(batch_sum)」。
旧导出用 `其它支出 - (batch_sum - paid_sum)` 反推耗材份额，差值变负后反而生成一条
金额为正的「耗材」行（例：2026-03-01 多出 5056），把实付合计和本周余款一起抬高。
"""
import os
import sys
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
_DB_PATH = BACKEND_ROOT / "test_export_material.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import openpyxl

import models
import schemas
from database import engine, SessionLocal
from services.bill_service import create_bill
from services.export_service import build_bills_export


class ExportMaterialRowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if _DB_PATH.exists():
            _DB_PATH.unlink()
        models.Base.metadata.create_all(engine)
        cls.db = SessionLocal()
        user = models.User(username="material_test", password_hash="x", role="admin", must_change_password=False)
        cls.db.add(user)
        cls.db.flush()
        cls.user = user

        species = models.Species(name_zh="珍珠斑", default_unit="公斤", default_price=0, is_deleted=False)
        cls.db.add(species)
        cls.db.flush()

        def make_bill(day, weight, price, paid, batch_paid):
            create_bill(
                schemas.BillCreate(
                    species_id=species.id, weight=weight, unit_price=price, fee_value=0,
                    release_date=day, status="COMPLETED",
                    paid_amount=paid, batch_paid=batch_paid,
                ),
                user, cls.db,
            )

        # 2026-03-01：同一批 5056 被重复摊（3 行分摊 + 1 行又记整批），paid_sum 比 batch_sum 多 5056
        bad_day = date(2026, 3, 1)
        make_bill(bad_day, 32.25, 48, 2552.57, 5056)
        make_bill(bad_day, 19.75, 68, 2214.54, 5056)
        make_bill(bad_day, 3.65, 48, 288.89, 5056)
        make_bill(bad_day, 38, 50, 5056, 5056)
        cls.db.add(models.WeekExpense(release_date=bad_day, name="车费", amount=350))
        cls.db.commit()

        # 2026-03-08：真的记了一笔耗材（冰块 90），这一行仍应照常导出
        good_day = date(2026, 3, 8)
        make_bill(good_day, 10, 50, 500, 500)
        cls.db.add(models.WeekExpense(release_date=good_day, name="冰块", amount=90))
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()
        if _DB_PATH.exists():
            _DB_PATH.unlink()

    @staticmethod
    def _rows(ws):
        """{标签: 行号}，只看 C 列的表尾标签。"""
        return {
            str(ws.cell(row=r, column=3).value): r
            for r in range(4, ws.max_row + 1)
            if ws.cell(row=r, column=3).value
        }

    def _load(self, day_from, day_to):
        content, _ = build_bills_export(self.db, day_from, day_to)
        return openpyxl.load_workbook(BytesIO(content.read()), data_only=False)

    def test_no_material_row_when_batch_already_covers_it(self):
        wb = self._load("2026-03-01", "2026-03-01")
        ws = wb.worksheets[0]
        rows = self._rows(ws)
        self.assertNotIn("耗材", rows)
        # 实付合计的范围只能到车费/船费，不能多出一行
        total_row = rows["慈悲护生购生实付金额"]
        self.assertLess(rows["船费"], total_row)
        self.assertEqual(rows["船费"] + 2, total_row)
        self.assertEqual(ws.cell(row=total_row, column=7).value, f"=SUM(G4:G{rows['船费']})")

    def test_real_material_expense_still_exported(self):
        wb = self._load("2026-03-08", "2026-03-08")
        ws = wb.worksheets[0]
        rows = self._rows(ws)
        self.assertIn("耗材", rows)
        self.assertAlmostEqual(float(ws.cell(row=rows["耗材"], column=7).value), 90.0)
        self.assertLess(rows["船费"], rows["耗材"])
        self.assertLess(rows["耗材"], rows["慈悲护生购生实付金额"])


if __name__ == "__main__":
    unittest.main()
