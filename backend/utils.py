from fastapi import HTTPException
from sqlalchemy.orm import Session
import models

def get_bill_or_404(bill_id: int, db: Session):
    """按 ID 查找单据，不存在则返回 404"""
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="未找到该单据")
    return bill

def calculate_bill_amounts(weight: float, unit_price: float, fee_value: float):
    subtotal = round(weight * unit_price, 2)
    fee = round(fee_value, 2)
    total_amount = round(subtotal + fee, 2)
    return subtotal, fee, total_amount
