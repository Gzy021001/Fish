from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session
import models

CENT = Decimal("0.01")

def money(value) -> Decimal:
    """金额统一入口：转 Decimal 并保留两位小数（四舍五入到分）。"""
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(CENT, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)

def get_bill_or_404(bill_id: int, db: Session):
    """按 ID 查找单据，不存在则返回 404"""
    bill = (
        db.query(models.Bill)
        .filter(models.Bill.id == bill_id, models.Bill.is_deleted.is_(False))
        .first()
    )
    if not bill:
        raise HTTPException(status_code=404, detail="未找到该单据")
    return bill

def calculate_bill_amounts(weight, unit_price, fee_value):
    subtotal = (money(weight) * money(unit_price)).quantize(CENT, rounding=ROUND_HALF_UP)
    fee = money(fee_value)
    total_amount = (subtotal + fee).quantize(CENT, rounding=ROUND_HALF_UP)
    return subtotal, fee, total_amount
