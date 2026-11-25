"""实付分摊：把模板「实付」按批次摊到每一行，避免列表里大量空白。

模板语义：一次采购的实付款往往只写在该批的第一行；其后没写实付的行属于同一批。
批次边界 = 从有实付的行开始，到下一个有实付的行为止（同一天、按表内顺序）。

分摊规则：按各行小计（重量×单价）比例分摊，最后一行取余数，保证**批次合计不变**。
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from sqlalchemy import asc
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
        while i < len(group):
            if group[i].paid_amount is None:
                i += 1
                continue
            j = i + 1
            while j < len(group) and group[j].paid_amount is None:
                j += 1
            batch = group[i:j]
            total_paid = Decimal(str(group[i].paid_amount or 0))
            for row, share in zip(batch, _split_batch(batch, total_paid)):
                row.paid_amount = float(share)
            i = j


def apportion_existing(db: Session) -> dict:
    """把库里已有的实付按批次重新分摊（幂等：只按“当前有值的行”重新分批）。"""
    dates = [
        row[0]
        for row in db.query(models.Bill.release_date)
        .filter(models.Bill.is_deleted.is_(False), models.Bill.release_date.isnot(None))
        .distinct()
        .all()
    ]
    updated = 0
    for day in dates:
        bills = (
            db.query(models.Bill)
            .filter(models.Bill.release_date == day, models.Bill.is_deleted.is_(False))
            .order_by(asc(models.Bill.created_at), asc(models.Bill.id))
            .all()
        )
        if not bills or not any(b.paid_amount is not None for b in bills):
            continue
        i = 0
        while i < len(bills):
            if bills[i].paid_amount is None:
                i += 1
                continue
            j = i + 1
            while j < len(bills) and bills[j].paid_amount is None:
                j += 1
            batch = bills[i:j]
            total_paid = Decimal(str(batch[0].paid_amount or 0))
            for bill, share in zip(batch, _split_batch(batch, total_paid)):
                bill.paid_amount = share
                updated += 1
            i = j
    db.commit()
    return {"dates": len(dates), "updated": updated}
