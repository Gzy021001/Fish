#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按《慈悲组购生明细表》模板回填「实付」与车费/船费。

用法（默认读 .env.local 里的 DATABASE_URL）：
    python backend/scripts/backfill_paid_from_excel.py "C:\\path\\慈悲组购生明细表2026.xlsx"
    python backend/scripts/backfill_paid_from_excel.py <xlsx> --db-url "postgresql://..."   # 指定库（如生产）

规则：
- 模板每次放生一个 sheet，标题行含「2026年X月X日」，表头行含 品种/重量/单价/实付。
- 「实付」列是该批实际付款，一般只写在该批第一行；回填时原样写到对应单据的 paid_amount。
- 「车费」「船费」行不是物命单据，金额取「实付」列，写入 week_expenses。
- 匹配方式：按（放生日期 + 重量(kg) + 单价(元/kg)）匹配已有单据，重量/单价一致即可；
  匹配不到的行会计入 unmatched 统计（通常是按件/个折算过的行）。
- 幂等：每次先把涉及日期范围的 paid_amount 置空、删除这些日期的 week_expenses，再重新写入。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine, delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import models  # noqa: E402

EXPENSE_NAMES = ("车费", "船费")
NON_BILL_KW = (
    "购生总重量", "购生总斤数", "实付金额", "余款", "随喜", "车费", "船费",
    "打包袋", "购生付款明细", "上周", "本周", "现场随喜", "随喜累计",
    "慈悲护生", "购买总重量", "购买总斤数",
)
TOL = Decimal("0.02")


def norm_header(value) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("（", "(").replace("）", ")")


def parse_sheet_date(title: str) -> date | None:
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", str(title or ""))
    if not m:
        return None
    y, mo, d = (int(x) for x in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def find_header(ws) -> tuple[int, dict] | tuple[None, dict]:
    for r in range(1, 15):
        cells = [norm_header(ws.cell(row=r, column=c).value) for c in range(1, 15)]
        if any("品种" == c or c.startswith("品种") for c in cells) and any(
            c.startswith("重量") for c in cells
        ):
            cols = {}
            for idx, h in enumerate(cells, start=1):
                if not h:
                    continue
                if h.startswith("品种"):
                    cols["name"] = idx
                elif h.startswith("重量"):
                    cols["weight"] = idx
                elif h.startswith("单价"):
                    cols["price"] = idx
                elif h.startswith("服务费"):
                    cols["fee"] = idx
                elif h.startswith("实付"):
                    cols["paid"] = idx
            if {"name", "weight", "price"} <= cols.keys():
                return r, cols
    return None, {}


def as_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("excel", help="模板文件路径")
    parser.add_argument("--db-url", default=None, help="数据库连接串（默认取 backend/.env.local 或环境变量）")
    args = parser.parse_args()

    if args.db_url:
        url = args.db_url
    else:
        sys.path.insert(0, str(ROOT / "backend"))
        from database import DATABASE_URL  # noqa: E402  (延迟导入，读取项目配置)

        url = DATABASE_URL

    engine = create_engine(url)
    wb = openpyxl.load_workbook(args.excel, data_only=True)

    total_rows = 0
    matched = 0
    unmatched: list[str] = []
    expense_count = 0
    dates: list[date] = []

    with Session(engine) as db:
        species_by_name = {
            s.name_zh: s.id
            for s in db.query(models.Species).filter(models.Species.is_deleted.is_(False)).all()
        }
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            day = parse_sheet_date(ws.cell(row=2, column=2).value or sheet_name)
            if not day:
                continue
            header_row, cols = find_header(ws)
            if not header_row:
                continue
            dates.append(day)

            # 先清空该日期的实付与费用行，保证可重复执行
            db.query(models.Bill).filter(models.Bill.release_date == day).update(
                {"paid_amount": None}, synchronize_session=False
            )
            db.execute(delete(models.WeekExpense).where(models.WeekExpense.release_date == day))

            bills = db.execute(
                select(models.Bill).where(models.Bill.release_date == day, models.Bill.is_deleted.is_(False))
            ).scalars().all()
            used: set[int] = set()

            for r in range(header_row + 1, min(ws.max_row, header_row + 400) + 1):
                raw_name = str(ws.cell(row=r, column=cols["name"]).value or "").strip()
                if not raw_name:
                    continue
                paid = as_float(ws.cell(row=r, column=cols["paid"]).value) if "paid" in cols else None
                weight = as_float(ws.cell(row=r, column=cols["weight"]).value)
                price = as_float(ws.cell(row=r, column=cols["price"]).value)

                if any(k in raw_name for k in EXPENSE_NAMES):
                    if paid and paid > 0:
                        db.add(
                            models.WeekExpense(
                                release_date=day,
                                name="车费" if "车" in raw_name else "船费",
                                amount=Decimal(str(paid)),
                            )
                        )
                        expense_count += 1
                    continue

                if any(k in raw_name for k in NON_BILL_KW):
                    continue
                if weight is None or price is None:
                    continue

                total_rows += 1
                jin_w = Decimal(str(weight))
                jin_p = Decimal(str(price))
                kg = jin_w / 2
                per_kg = jin_p * 2

                target = None
                for bill in bills:
                    if bill.id in used:
                        continue
                    bw = Decimal(str(bill.weight or 0))
                    bp = Decimal(str(bill.unit_price or 0))
                    if abs(bw - kg) <= TOL and abs(bp - per_kg) <= TOL:
                        target = bill
                        break

                # 按件/个折算过的行（重量/单价与源表不同）：退回按品种名匹配
                if target is None:
                    base = re.sub(r"[（(][^）)]*[）)]", "", raw_name).strip()
                    species_id = species_by_name.get(base)
                    if species_id:
                        candidates = [
                            b for b in bills if b.id not in used and b.species_id == species_id
                        ]
                        if len(candidates) == 1:
                            target = candidates[0]

                if target is None:
                    # 打包耗材等没有对应单据的行：把实付记成当天支出，保证合计与模板一致
                    if paid and paid > 0:
                        db.add(
                            models.WeekExpense(
                                release_date=day,
                                name=re.sub(r"[（(][^）)]*[）)]", "", raw_name).strip()[:20],
                                amount=Decimal(str(paid)),
                            )
                        )
                        expense_count += 1
                    else:
                        unmatched.append(f"{day} {raw_name} 重量{weight} 单价{price}")
                    continue

                used.add(target.id)
                matched += 1
                if paid and paid > 0:
                    target.paid_amount = Decimal(str(paid))

            db.commit()

    print(f"sheets: {len(dates)}  dates: {dates[0] if dates else '-'} ~ {dates[-1] if dates else '-'}")
    print(f"数据行: {total_rows}  匹配成功: {matched}  未匹配: {len(unmatched)}  车费/船费: {expense_count}")
    for row in unmatched[:20]:
        print("  未匹配:", row)


if __name__ == "__main__":
    main()
