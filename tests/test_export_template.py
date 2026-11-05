# -*- coding: utf-8 -*-
"""按日期导出模板 xlsx 的本地回归测试（SQLite 覆盖，避免连接生产库）。

验证点：
- 每个放生日期一个 sheet，sheet 名「M月D日」
- 同日期有服务费 -> 7 列版（B2:H2 合并）；全无服务费 -> 6 列版（B2:G2 合并）
- 数据行：总计=公式 D*E、实付=公式 F+G（7 列版）；6 列版实付为数值
- 收款区：逐笔输出录入的 支付宝/微信/随喜放生 金额，末行「本周随喜」=SUM 公式；
  未录入金额的单据按 随喜类型+实付 兜底
- 表尾汇总块：购生总重量/慈悲护生购生实付金额/上周余款（链式）/本周随喜/本周现场随喜/
  本周随喜累计/本周余款，公式与模板一致
- 模板样式：标题浅棕底、表头灰底、thin 边框、金额数字格式
"""
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"

# 必须在导入 backend 模块前设置，防止误连 .env.local 指向的生产库
_DB_PATH = BACKEND_ROOT / "test_export_template.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import openpyxl
from datetime import date
from io import BytesIO
from urllib.parse import unquote

import models
import schemas
from database import engine, SessionLocal
from services.bill_service import create_bill
from services.export_service import build_bills_export


class ExportTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        models.Base.metadata.create_all(engine)
        cls.db = SessionLocal()
        user = models.User(
            username="export_test", password_hash="x", role="admin", must_change_password=False
        )
        cls.db.add(user)
        cls.db.flush()
        cls.user = user

        def make_species(name):
            s = models.Species(name_zh=name, default_unit="斤", default_price=0, is_deleted=False)
            cls.db.add(s)
            cls.db.flush()
            return s

        sp1, sp2, sp3, sp4 = (
            make_species("小草鱼"),
            make_species("大头（鳙鱼）"),
            make_species("赤贝"),
            make_species("沙白"),
        )
        cls.sp1, cls.sp2, cls.sp3, cls.sp4 = sp1, sp2, sp3, sp4

        def make_bill(sp_obj, w, p, fee, rdate, pm=None, wd=None,
                      alipay=None, wechat=None, suixi=None):
            data = schemas.BillCreate(
                species_id=sp_obj.id,
                weight=w,
                unit_price=p,
                fee_value=fee,
                release_date=rdate,
                status="COMPLETED",
                payment_method=pm,
                weekly_donation=wd,
                alipay_amount=alipay,
                wechat_amount=wechat,
                suixi_amount=suixi,
            )
            return create_bill(data, user, cls.db, commit=False)

        # 1月3日：带服务费 + 三种随喜金额 + 本周现场随喜
        make_bill(sp1, 310.2, 5.8, 304.22, date(2026, 1, 3), "支付宝", 24726.69, alipay=263.88)
        make_bill(sp2, 57.4, 6.5, 0, date(2026, 1, 3), "微信", wechat=3594.09)
        make_bill(sp2, 285.2, 7.8, 0, date(2026, 1, 3), "微信", wechat=15568.72)
        make_bill(sp1, 60.4, 5.0, 0, date(2026, 1, 3), "随喜放生", suixi=5300)
        # 1月10日：无服务费；一条旧数据（只填随喜类型无金额，走实付兜底），一条全空
        make_bill(sp3, 104, 18, 0, date(2026, 1, 10), "支付宝")
        make_bill(sp4, 100, 6, 0, date(2026, 1, 10))
        # 1月17日：逐笔收款行（4 条单据各一笔，对应模板的四行收款）
        make_bill(sp3, 50, 10, 0, date(2026, 1, 17), "支付宝", alipay=364)
        make_bill(sp4, 20, 15, 0, date(2026, 1, 17), "微信", wechat=387)
        make_bill(sp1, 30, 10, 0, date(2026, 1, 17), "微信", wechat=19278.03)
        make_bill(sp2, 25, 10, 0, date(2026, 1, 17), "随喜放生", suixi=1300)
        # 1月24日：随喜金额全空（没填值也要能正常导出，收款区四行留空）
        make_bill(sp1, 10, 6, 0, date(2026, 1, 24))
        make_bill(sp2, 5, 8, 0, date(2026, 1, 24))
        cls.db.commit()

        cls.out_path = REPO_ROOT / "test_export_template_out.xlsx"
        content, cls.filename = build_bills_export(cls.db, "2026-01-03", "2026-01-10")
        with open(cls.out_path, "wb") as f:
            f.write(content.read())
        cls.wb = openpyxl.load_workbook(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()
        for p in (_DB_PATH, cls.out_path):
            if p.exists():
                p.unlink()

    def test_sheets_per_date(self):
        self.assertEqual(self.wb.sheetnames, ["1月3日", "1月10日"])
        self.assertIn("20260103", self.filename)

    def test_seven_col_sheet_with_fee(self):
        ws = self.wb["1月3日"]
        self.assertEqual(ws["B2"].value, "2026年1月3日购生付款明细")
        self.assertIn("B2:H2", [str(r) for r in ws.merged_cells.ranges])
        headers = [ws.cell(row=3, column=c).value for c in range(2, 9)]
        self.assertEqual(headers, ["序号", "品种", "重量(斤)", "单价(元)", "总计", "服务费", "实付"])
        self.assertEqual(ws["C4"].value, "小草鱼")
        self.assertEqual(ws["F4"].value, "=D4*E4")
        self.assertAlmostEqual(ws["G4"].value, 304.22)
        self.assertEqual(ws["H4"].value, "=F4+G4")

    def test_six_col_sheet_without_fee(self):
        ws = self.wb["1月10日"]
        self.assertIn("B2:G2", [str(r) for r in ws.merged_cells.ranges])
        headers = [ws.cell(row=3, column=c).value for c in range(2, 8)]
        self.assertEqual(headers, ["序号", "品种", "重量(斤)", "单价(元)", "总计", "实付"])
        self.assertEqual(ws["F4"].value, "=D4*E4")
        self.assertAlmostEqual(ws["G4"].value, 1872.0)
        self.assertIsNone(ws.cell(row=3, column=8).value)

    def test_payment_block_uses_entered_amounts(self):
        ws = self.wb["1月3日"]
        # 收款区逐笔输出录入金额（而非实付合计）
        self.assertEqual(ws["J4"].value, "支付宝")
        self.assertAlmostEqual(ws["K4"].value, 263.88)
        self.assertEqual(ws["J5"].value, "微信")
        self.assertAlmostEqual(ws["K5"].value, 3594.09)
        self.assertEqual(ws["J6"].value, "微信")
        self.assertAlmostEqual(ws["K6"].value, 15568.72)
        self.assertEqual(ws["J7"].value, "随喜放生")
        self.assertAlmostEqual(ws["K7"].value, 5300)
        self.assertEqual(ws["J8"].value, "本周随喜")
        self.assertEqual(ws["K8"].value, "=SUM(K4:K7)")

    def test_payment_block_legacy_fallback(self):
        ws6 = self.wb["1月10日"]
        # 未录入金额的旧单据：按 随喜类型 + 实付 兜底进对应收款行
        self.assertEqual(ws6["I4"].value, "支付宝")
        self.assertAlmostEqual(ws6["J4"].value, 1872.0)
        # 固定四行：其余行没有金额也照样输出标签
        self.assertEqual(ws6["I5"].value, "微信")
        self.assertIsNone(ws6["J5"].value)
        self.assertEqual(ws6["I6"].value, "微信")
        self.assertEqual(ws6["I7"].value, "随喜放生")
        self.assertEqual(ws6["I8"].value, "本周随喜")
        self.assertEqual(ws6["J8"].value, "=SUM(J4:J7)")

    def test_summary_block(self):
        ws = self.wb["1月3日"]
        # 车费灰底 / 船费黄底（留空行，金额手工填）
        self.assertEqual(ws["C8"].value, "车费")
        self.assertEqual(ws["C8"].fill.fgColor.rgb, "FFD9D9D9")
        self.assertEqual(ws["C9"].value, "船费")
        self.assertEqual(ws["C9"].fill.fgColor.rgb, "FFFFFF00")
        # 购生总重量 / 实付金额
        self.assertEqual(ws["C10"].value, "购生总重量")
        self.assertEqual(ws["D10"].value, "=SUM(D4:D7)")
        self.assertEqual(ws["C11"].value, "慈悲护生购生实付金额")
        self.assertIn("C11:F11", [str(r) for r in ws.merged_cells.ranges])
        self.assertEqual(ws["H11"].value, "=SUM(H4:H9)")
        self.assertEqual(ws["H11"].fill.fgColor.rgb, "FF70AD47")
        # 余款链条：首 sheet 上周余款留空
        self.assertEqual(ws["C12"].value, "上周余款")
        self.assertIsNone(ws["F12"].value)
        self.assertEqual(ws["C13"].value, "本周随喜")
        self.assertEqual(ws["F13"].value, "=K8")
        self.assertEqual(ws["C14"].value, "本周现场随喜")
        self.assertAlmostEqual(ws["F14"].value, 24726.69)
        self.assertEqual(ws["C15"].value, "本周随喜累计")
        self.assertEqual(ws["F15"].value, "=SUM(F12:F14)")
        self.assertEqual(ws["C16"].value, "本周余款")
        self.assertEqual(ws["F16"].value, "=F15-H11")
        # 本周余款整行粉米色底
        self.assertEqual(ws["B16"].fill.fgColor.rgb, "FFF8CBAD")
        self.assertEqual(ws["C16"].fill.fgColor.rgb, "FFF8CBAD")

    def test_summary_block_carry_chain(self):
        ws6 = self.wb["1月10日"]
        self.assertEqual(ws6["C8"].value, "购生总重量")
        self.assertEqual(ws6["D8"].value, "=SUM(D4:D5)")
        self.assertEqual(ws6["G9"].value, "=SUM(G4:G7)")
        # 上周余款 = 上个 sheet 的本周余款（0 + 收款合计 + 现场随喜 - 实付）
        expected = 0 + (263.88 + 3594.09 + 15568.72 + 5300) + 24726.69 \
            - (2103.38 + 373.10 + 2224.56 + 302.0)
        self.assertAlmostEqual(ws6["F10"].value, expected, places=2)
        self.assertEqual(ws6["F11"].value, "=J8")
        self.assertIsNone(ws6["F12"].value)  # 本周现场随喜未填
        self.assertEqual(ws6["F13"].value, "=SUM(F10:F12)")
        self.assertEqual(ws6["F14"].value, "=F13-G9")

    def test_export_by_selected_ids(self):
        from services.export_service import build_bills_export_by_ids

        ids = [
            b.id
            for b in self.db.query(models.Bill)
            .filter(models.Bill.release_date == date(2026, 1, 10))
            .order_by(models.Bill.id.asc())
            .all()
        ]
        content, filename = build_bills_export_by_ids(self.db, ids)
        wb = openpyxl.load_workbook(BytesIO(content.read()))
        self.assertEqual(wb.sheetnames, ["1月10日"])
        self.assertIn("20260110", filename)
        # 勾选两条单据 -> 数据行 2 行
        ws = wb["1月10日"]
        self.assertEqual(ws["C4"].value, "赤贝")
        self.assertEqual(ws["C5"].value, "沙白")

    def test_export_by_ids_rejects_empty(self):
        from services.export_service import build_bills_export_by_ids
        from fastapi import HTTPException

        with self.assertRaises(HTTPException):
            build_bills_export_by_ids(self.db, [])

    def test_export_all_without_filters(self):
        """未勾选单据、未设日期范围 -> 全量导出，包含全部放生日 sheet。"""
        from services.export_service import build_bills_export_all

        content, filename = build_bills_export_all(self.db)
        wb = openpyxl.load_workbook(BytesIO(content.read()))
        self.assertEqual(wb.sheetnames, ["1月3日", "1月10日", "1月17日", "1月24日"])
        self.assertIn("20260103", filename)
        self.assertIn("20260124", filename)
        # 全量导出时 sheets 间仍有上周余款链条
        self.assertIsNone(wb["1月3日"]["F12"].value)
        self.assertIsNotNone(wb["1月10日"]["F10"].value)

    def test_payment_rows_fixed_four_rows(self):
        """逐笔收款（每条单据一笔）-> 收款区固定四行 支付宝/微信/微信/随喜放生 + 本周随喜。"""
        from services.export_service import build_bills_export_all

        content, _ = build_bills_export_all(self.db)
        wb = openpyxl.load_workbook(BytesIO(content.read()))
        ws = wb["1月17日"]
        self.assertEqual(ws["I4"].value, "支付宝")
        self.assertAlmostEqual(ws["J4"].value, 364)
        self.assertEqual(ws["I5"].value, "微信")
        self.assertAlmostEqual(ws["J5"].value, 387)
        self.assertEqual(ws["I6"].value, "微信")
        self.assertAlmostEqual(ws["J6"].value, 19278.03)
        self.assertEqual(ws["I7"].value, "随喜放生")
        self.assertAlmostEqual(ws["J7"].value, 1300)
        self.assertEqual(ws["I8"].value, "本周随喜")
        self.assertEqual(ws["J8"].value, "=SUM(J4:J7)")

    def test_payment_rows_empty_amounts_still_export(self):
        """三个随喜金额全空 -> 收款区四行标签仍在、金额留空，导出不报错。"""
        from services.export_service import build_bills_export_all

        content, _ = build_bills_export_all(self.db)
        wb = openpyxl.load_workbook(BytesIO(content.read()))
        ws = wb["1月24日"]
        self.assertEqual(
            [ws.cell(row=r, column=9).value for r in range(4, 8)],
            ["支付宝", "微信", "微信", "随喜放生"],
        )
        for r in range(4, 8):
            self.assertIsNone(ws.cell(row=r, column=10).value)
        self.assertEqual(ws["I8"].value, "本周随喜")
        self.assertEqual(ws["J8"].value, "=SUM(J4:J7)")

    def test_species_export(self):
        from services.export_service import build_species_export

        content, filename = build_species_export(self.db)
        wb = openpyxl.load_workbook(BytesIO(content.read()))
        ws = wb.active
        self.assertEqual(ws.title, "品种库")
        headers = [ws.cell(row=1, column=c).value for c in range(1, 6)]
        self.assertEqual(headers, ["序号", "品种", "单价（元）", "放生日期", "默认单位"])
        self.assertIn("品种库", unquote(filename))

    def test_species_export_by_ids(self):
        from services.export_service import build_species_export

        content, _ = build_species_export(self.db, [self.sp1.id, self.sp3.id])
        ws = openpyxl.load_workbook(BytesIO(content.read())).active
        names = [ws.cell(row=r, column=2).value for r in range(2, ws.max_row + 1)]
        self.assertEqual(sorted(names), sorted(["小草鱼", "赤贝"]))

    def test_template_styles(self):
        ws = self.wb["1月3日"]
        self.assertEqual(ws["B2"].fill.fgColor.rgb, "FFF8CBAD")
        self.assertTrue(ws["B2"].font.bold)
        self.assertEqual(ws["B3"].fill.fgColor.rgb, "FFD9D9D9")
        self.assertTrue(ws["B3"].font.bold)
        self.assertEqual(ws["D4"].border.left.style, "thin")
        self.assertEqual(ws["F4"].number_format, "0.00;[Red]0.00")
        self.assertAlmostEqual(ws.column_dimensions["C"].width, 17.77)

    def test_summary_block_fills_and_borders(self):
        ws = self.wb["1月3日"]
        # 汇总块整行边框（含空单元格）
        for coord in ("E8", "F8", "D10", "E13", "F13", "G16"):
            self.assertEqual(ws[coord].border.left.style, "thin", coord)
        # 车费行整行灰底（含空单元格）
        for col in range(2, 9):
            self.assertEqual(
                ws.cell(row=8, column=col).fill.fgColor.rgb, "FFD9D9D9"
            )
        # 船费行整行黄底
        for col in range(2, 9):
            self.assertEqual(
                ws.cell(row=9, column=col).fill.fgColor.rgb, "FFFFFF00"
            )
        # 实付金额行绿色（合并区 C:F 由锚点 C 提供底色，Excel 会铺满合并区）
        for col in (2, 3, 7, 8):
            self.assertEqual(
                ws.cell(row=11, column=col).fill.fgColor.rgb, "FF70AD47"
            )
        # 本周随喜/现场随喜/累计行米色底
        for r in (13, 14, 15):
            self.assertEqual(
                ws.cell(row=r, column=2).fill.fgColor.rgb, "FFFFF2CC"
            )
        # 红字：购生总重量、本周余款数值
        self.assertEqual(ws["C10"].font.color.rgb, "FFFF0000")
        self.assertEqual(ws["F16"].font.color.rgb, "FFFF0000")


if __name__ == "__main__":
    unittest.main()
