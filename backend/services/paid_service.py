"""实付分摊与回填：把模板「实付」按批次摊到每一行，并保留「本批实付」原值。

模板语义：一次采购的实付款往往只写在该批的第一行；其后没写实付的行属于同一批。
批次边界 = 从有实付的行开始，到下一个有实付的行为止（同一天、按表内顺序）。

分摊规则：按各行小计（重量×单价）比例分摊，最后一行取余数，保证**批次合计不变**；
同时把该批的原始总额写进 batch_paid（同批每行相同），供详情弹窗展示「本批实付」。
"""
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

import models

TWO = Decimal("0.01")


def _split_batch(batch: list, total_paid: Decimal) -> list[Decimal]:
    """把一批实付按小计比例拆到各行，返回与 batch 等长的金额列表。"""
    weights = [Decimal(str((float(r.weight or 0)) * (float(r.unit_price or 0)))) for r in batch]
    weight_sum = sum(weights, Decimal("0"))
    shares: list[Decimal] = []
    allocated = Decimal("0")
    for idx, weight in enumerate(weights):
        if idx == len(batch) - 1:
            share = (total_paid - allocated).quantize(TWO, rounding=ROUND_HALF_UP)
        elif weight_sum > 0:
            share = (total_paid * weight / weight_sum).quantize(TWO, rounding=ROUND_HALF_UP)
        else:
            share = (total_paid / len(batch)).quantize(TWO, rounding=ROUND_HALF_UP)
        allocated += share
        shares.append(share)
    return shares


def apportion_rows(rows: Iterable) -> None:
    """就地分摊（用于导入的行对象，字段名 paid_amount/release_date/weight/unit_price）。"""
    by_date: dict = {}
    for row in rows:
        by_date.setdefault(row.release_date, []).append(row)

    for group in by_date.values():
        i = 0
        n = len(group)
        while i < n:
            if group[i].paid_amount is None:
                i += 1
                continue
            # 一批 = 该行 + 后面没写实付的行；中间重复写了同一批次金额（例如导出合并单元格
            # 再导入时被广播到每行）也算同一批，避免整批金额被当成多笔钱重复计。
            value = group[i].paid_amount
            j = i + 1
            while j < n and (group[j].paid_amount is None or group[j].paid_amount == value):
                j += 1
            batch = group[i:j]
            total_paid = Decimal(str(value or 0))
            for row, share in zip(batch, _split_batch(batch, total_paid)):
                row.paid_amount = float(share)
                row.batch_paid = float(total_paid)
            i = j


def _match_bill(db: Session, row: dict, used: set[int]):
    """按（日期 + 重量 + 单价）找单据；找不到再按品种名在同一日期里找唯一候选。"""
    candidates = (
        db.query(models.Bill)
        .filter(
            models.Bill.release_date == row["date"],
            models.Bill.is_deleted.is_(False),
            models.Bill.weight.between(row["weight"] - 0.02, row["weight"] + 0.02),
            models.Bill.unit_price.between(row["unit_price"] - 0.02, row["unit_price"] + 0.02),
        )
        .order_by(models.Bill.id)
        .all()
    )
    for bill in candidates:
        if bill.id not in used:
            return bill

    name = re.sub(r"[（(][^）)]*[）)]", "", str(row.get("name") or "")).strip()
    if not name:
        return None
    named = (
        db.query(models.Bill)
        .join(models.Species, models.Bill.species_id == models.Species.id)
        .filter(
            models.Bill.release_date == row["date"],
            models.Bill.is_deleted.is_(False),
            models.Species.name_zh == name,
        )
        .order_by(models.Bill.id)
        .all()
    )
    free = [b for b in named if b.id not in used]
    return free[0] if len(free) == 1 else None


def apply_paid_rows(db: Session, rows: list[dict]) -> dict:
    """把「本行分摊 / 本批实付」写进对应单据（按日期+重量+单价匹配，重量=公斤、单价=元/公斤）。

    模板里打包耗材（冰块/打包袋）等没有单据的行：把该行份额记成当天支出，保证与模板合计一致。
    """
    updated = 0
    missing = 0
    expense_added = 0
    used: set[int] = set()
    dates = sorted({row["date"] for row in rows})
    # 先把这些日期的实付与本批实付清空（重跑幂等），顺带清掉上一次回填生成的杂项支出
    for day in dates:
        db.execute(
            text(
                "UPDATE bills SET paid_amount = NULL, batch_paid = NULL "
                "WHERE release_date = :d AND is_deleted = false"
            ),
            {"d": day},
        )
        db.execute(
            text("DELETE FROM week_expenses WHERE release_date = :d AND name NOT IN ('车费', '船费')"),
            {"d": day},
        )
    for row in rows:
        bill = _match_bill(db, row, used)
        if bill is None:
            if row.get("paid"):
                db.execute(
                    text(
                        "INSERT INTO week_expenses (release_date, name, amount, created_at, is_deleted) "
                        "VALUES (:d, :n, :a, :ts, false)"
                    ),
                    {
                        "d": row["date"],
                        "n": str(row.get("name") or "其他")[:20],
                        "a": row["paid"],
                        "ts": datetime.utcnow(),
                    },
                )
                expense_added += 1
            missing += 1
            continue
        used.add(bill.id)
        bill.paid_amount = Decimal(str(row["paid"]))
        bill.batch_paid = Decimal(str(row["batch_paid"]))
        updated += 1
    db.commit()
    return {"updated": updated, "missing": missing, "expense_added": expense_added}
