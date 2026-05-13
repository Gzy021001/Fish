import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session

import models
import schemas
from utils import calculate_bill_amounts, get_bill_or_404
from services.audit_service import record_create, record_update, record_delete


def create_bill(data: schemas.BillCreate, user: models.User, db: Session):
    if data.weight <= 0 or data.unit_price <= 0:
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    subtotal, fee, total_amount = calculate_bill_amounts(
        data.weight, data.unit_price, data.fee_value
    )

    bill = models.Bill(
        user_id=user.id,
        species_id=data.species_id,
        weight=data.weight,
        unit_price=data.unit_price,
        currency=data.currency,
        subtotal=subtotal,
        fee_type=data.fee_type,
        fee_value=data.fee_value,
        total_amount=total_amount,
        status="DRAFT",
        release_date=data.release_date,
    )
    db.add(bill)
    db.flush()

    record_create(
        db,
        entity_type="BILL",
        user_id=user.id,
        bill_id=bill.id,
        data=data.model_dump(),
    )

    db.commit()
    db.refresh(bill)
    return bill


def sync_bills(date: str, user: models.User, db: Session):
    draft_bills = db.query(models.Bill).filter(models.Bill.status == "DRAFT").all()
    count = 0
    for bill in draft_bills:
        if bill.created_at and bill.created_at.isoformat().startswith(date):
            bill.status = "COMPLETED"
            count += 1

            record_update(
                db,
                entity_type="BILL",
                user_id=user.id,
                bill_id=bill.id,
                old_data={"status": "DRAFT"},
                new_data={"status": "COMPLETED"},
            )

    db.commit()
    return count


def list_bills(db: Session, limit: int = 100, status: str = None, date: str = None, date_from: str = None, date_to: str = None):
    query = db.query(models.Bill).order_by(models.Bill.created_at.desc())
    if status:
        query = query.filter(models.Bill.status == status)
    if date_from:
        date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(
            func.coalesce(models.Bill.release_date, models.Bill.created_at) >= date_from_dt
        )
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(
            func.coalesce(models.Bill.release_date, models.Bill.created_at) < end
        )
    if date:
        query = query.filter(cast(models.Bill.release_date, String).startswith(date))
    if limit > 0:
        query = query.limit(limit)
    return query.all()


def update_bill(bill_id: int, data: schemas.BillCreate, user: models.User, db: Session):
    if data.weight <= 0 or data.unit_price <= 0:
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    bill = get_bill_or_404(bill_id, db)

    old_data = {
        "species_id": bill.species_id,
        "weight": bill.weight,
        "unit_price": bill.unit_price,
        "currency": bill.currency,
        "fee_type": bill.fee_type,
        "fee_value": bill.fee_value,
    }

    subtotal, fee, total_amount = calculate_bill_amounts(
        data.weight, data.unit_price, data.fee_value
    )

    bill.species_id = data.species_id
    bill.weight = data.weight
    bill.unit_price = data.unit_price
    bill.currency = data.currency
    bill.fee_type = data.fee_type
    bill.fee_value = data.fee_value
    bill.status = data.status
    bill.subtotal = subtotal
    bill.total_amount = total_amount
    if data.release_date is not None:
        bill.release_date = data.release_date

    db.flush()

    new_data = data.model_dump()
    record_update(
        db,
        entity_type="BILL",
        user_id=user.id,
        bill_id=bill.id,
        old_data=old_data,
        new_data=new_data,
    )

    db.commit()
    db.refresh(bill)
    return bill


def delete_bill(bill_id: int, user: models.User, db: Session):
    bill = get_bill_or_404(bill_id, db)

    old_data = {
        "species_id": bill.species_id,
        "weight": bill.weight,
        "unit_price": bill.unit_price,
        "currency": bill.currency,
        "fee_type": bill.fee_type,
        "fee_value": bill.fee_value,
    }

    record_delete(
        db,
        entity_type="BILL",
        user_id=user.id,
        bill_id=bill.id,
        old_data=old_data,
    )

    db.delete(bill)
    db.commit()
    return {"message": "Bill deleted successfully"}


def get_price_trend(species_id: int, db: Session, year: int = None):
    species = db.query(models.Species).filter(models.Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="未找到该品种")

    query = (
        db.query(
            func.date(models.Bill.release_date).label("date"),
            func.avg(models.Bill.unit_price).label("avg_price"),
        )
        .filter(models.Bill.species_id == species.id)
        .filter(models.Bill.release_date.isnot(None))
    )

    if year:
        query = query.filter(
            models.Bill.release_date >= datetime(year, 1, 1),
            models.Bill.release_date < datetime(year + 1, 1, 1),
        )
    else:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(models.Bill.release_date >= thirty_days_ago)

    results = query.group_by(func.date(models.Bill.release_date)).all()

    return [{"date": str(r.date), "avg_price": float(r.avg_price)} for r in results]
