import json
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
from utils import calculate_bill_amounts, get_bill_or_404
from services.audit_service import record_create, record_update, record_delete


def create_bill(data: schemas.BillCreate, user: models.User, db: Session, commit: bool = True):
    if data.weight <= 0 or data.unit_price <= 0:
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    subtotal, fee, total_amount = calculate_bill_amounts(
        data.weight, data.unit_price, data.fee_value
    )

    if data.status:
        new_status = data.status
    elif data.release_date and data.release_date <= date.today() - timedelta(days=1):
        new_status = "COMPLETED"
    else:
        new_status = "DRAFT"

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
        status=new_status,
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

    if commit:
        db.commit()
        db.refresh(bill)
    return bill


def sync_bills(date_str: str, user: models.User, db: Session):
    draft_bills = db.query(models.Bill).filter(models.Bill.status == "DRAFT").all()
    count = 0
    for bill in draft_bills:
        if bill.created_at and bill.created_at.isoformat() == date_str:
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


def _apply_bill_filters(query, status=None, date_from=None, date_to=None, date_str=None, q=None):
    from sqlalchemy import or_
    if status:
        query = query.filter(models.Bill.status == status)
    if date_from:
        date_from_dt = date.fromisoformat(date_from)
        query = query.filter(
            or_(
                models.Bill.release_date >= date_from_dt,
                (models.Bill.release_date.is_(None) & (models.Species.release_date >= date_from_dt))
            )
        )
    if date_to:
        end = date.fromisoformat(date_to) + timedelta(days=1)
        query = query.filter(
            or_(
                models.Bill.release_date < end,
                (models.Bill.release_date.is_(None) & (models.Species.release_date < end))
            )
        )
    if date_str:
        date_dt = date.fromisoformat(date_str)
        date_end = date_dt + timedelta(days=1)
        query = query.filter(models.Bill.release_date >= date_dt, models.Bill.release_date < date_end)
    if q:
        query = query.filter(models.Species.name_zh.ilike(f"%{q}%"))
    return query

def list_bills(db: Session, page: int = 1, page_size: int = 10, limit: int = 100, status: str = None, date: str = None, date_from: str = None, date_to: str = None, q: str = None):
    from sqlalchemy.orm import joinedload
    query = db.query(models.Bill).join(models.Species).options(joinedload(models.Bill.species)).order_by(func.coalesce(models.Bill.release_date, models.Species.release_date).desc().nullslast(), models.Bill.id.desc())
    query = _apply_bill_filters(query, status, date_from, date_to, date, q)

    if limit > 0:
        query = query.limit(limit)
        items = query.all()

        sum_weight = sum((item.weight or 0) for item in items)
        sum_subtotal = sum((item.subtotal or 0) for item in items)
        sum_total_amount = sum((item.total_amount or 0) for item in items)

        return {
            "total": len(items),
            "items": items,
            "sum_weight": sum_weight,
            "sum_subtotal": sum_subtotal,
            "sum_total_amount": sum_total_amount
        }

    total = query.count()

    sum_query = db.query(
        func.sum(models.Bill.weight),
        func.sum(models.Bill.subtotal),
        func.sum(models.Bill.total_amount)
    ).join(models.Species)
    sum_query = _apply_bill_filters(sum_query, status, date_from, date_to, date, q)

    sum_result = sum_query.first()
    sum_weight = sum_result[0] or 0.0 if sum_result else 0.0
    sum_subtotal = sum_result[1] or 0.0 if sum_result else 0.0
    sum_total_amount = sum_result[2] or 0.0 if sum_result else 0.0

    if page_size == -1:
        items = query.all()
        return {
            "total": total,
            "items": items,
            "sum_weight": sum_weight,
            "sum_subtotal": sum_subtotal,
            "sum_total_amount": sum_total_amount
        }

    if page_size > 0:
        query = query.offset((page - 1) * page_size).limit(page_size)
    items = query.all()

    return {
        "total": total,
        "items": items,
        "sum_weight": sum_weight,
        "sum_subtotal": sum_subtotal,
        "sum_total_amount": sum_total_amount
    }


def get_bill(bill_id: int, db: Session):
    from sqlalchemy.orm import joinedload

    return (
        db.query(models.Bill)
        .options(joinedload(models.Bill.species))
        .filter(models.Bill.id == bill_id)
        .first()
    ) or get_bill_or_404(bill_id, db)


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
    if data.release_date and data.release_date <= date.today() - timedelta(days=1):
        bill.status = "COMPLETED"
    else:
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

    # 避免外键约束报错
    db.query(models.AuditLog).filter(models.AuditLog.bill_id == bill.id).update({"bill_id": None})
    
    db.delete(bill)
    db.commit()
    return {"message": "Bill deleted successfully"}



def batch_create_bills(data: schemas.BatchImportRequest, user: models.User, db: Session):
    success_count = 0
    skip_count = 0
    bills = []
    errors = []

    if data.replace:
        dates_to_replace = set()
        for row in data.rows:
            if row.release_date:
                dates_to_replace.add(row.release_date)
        for d in dates_to_replace:
            # 查出要删除的账单
            bills_to_delete = db.query(models.Bill.id).filter(
                models.Bill.release_date >= d,
                models.Bill.release_date < (d + timedelta(days=1))
            ).all()
            
            if bills_to_delete:
                bill_ids = [b.id for b in bills_to_delete]
                # 解除 audit_logs 中的外键引用，防止 Postgres 的 IntegrityError (Foreign Key Violation)
                db.query(models.AuditLog).filter(models.AuditLog.bill_id.in_(bill_ids)).update(
                    {"bill_id": None}, synchronize_session=False
                )
                # 然后再删除单据
                db.query(models.Bill).filter(models.Bill.id.in_(bill_ids)).delete(synchronize_session=False)
        db.flush()

    existing_species = {s.name_zh: s for s in db.query(models.Species).all()}

    for row in data.rows:
        name_zh = row.name_zh.strip()
        if not name_zh or row.unit_price <= 0:
            skip_count += 1
            errors.append(f'跳过 "{name_zh or "(空)"}": 名称无效或单价 <= 0')
            continue

        species = existing_species.get(name_zh)
        if not species:
            try:
                with db.begin_nested():
                    species = models.Species(
                        name_zh=name_zh,
                        default_price=row.unit_price,
                        default_unit="公斤",
                        release_date=row.release_date,
                    )
                    db.add(species)
                    db.flush()
            except IntegrityError:
                # 并发情况下，另一个请求可能刚刚创建了这个品种
                species = db.query(models.Species).filter(models.Species.name_zh == name_zh).first()
                if not species:
                    raise  # 如果查不到，说明是其他的完整性错误，继续向上抛出
            existing_species[name_zh] = species

        bill_create = schemas.BillCreate(
            species_id=species.id,
            weight=row.weight or 0,
            unit_price=row.unit_price,
            fee_value=row.fee_value or 0,
            release_date=row.release_date,
            status="DRAFT",
        )
        bill = create_bill(bill_create, user, db, commit=False)
        bills.append(bill)
        success_count += 1

    db.commit()

    return schemas.BatchImportResult(
        success_count=success_count,
        skip_count=skip_count,
        bills=bills,
        errors=errors,
    )


def get_price_trend(species_id: int, db: Session, year: int = None):
    species = db.query(models.Species).filter(models.Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="未找到该品种")

    query = (
        db.query(
            models.Bill.release_date.label("date"),
            func.avg(models.Bill.unit_price).label("avg_price"),
        )
        .filter(models.Bill.species_id == species.id)
        .filter(models.Bill.release_date.isnot(None))
    )

    if year:
        query = query.filter(
            models.Bill.release_date >= date(year, 1, 1),
            models.Bill.release_date < date(year + 1, 1, 1),
        )
    else:
        thirty_days_ago = date.today() - timedelta(days=30)
        query = query.filter(models.Bill.release_date >= thirty_days_ago)

    results = query.group_by(models.Bill.release_date).all()

    return [{"date": r.date.strftime('%Y-%m-%d'), "avg_price": float(r.avg_price)} for r in results]


def get_price_trends_batch(species_ids: list[int], db: Session, year: int = None):
    if not species_ids:
        return {}

    query = (
        db.query(
            models.Bill.species_id,
            models.Bill.release_date.label("date"),
            func.avg(models.Bill.unit_price).label("avg_price"),
        )
        .filter(models.Bill.species_id.in_(species_ids))
        .filter(models.Bill.release_date.isnot(None))
    )

    if year:
        query = query.filter(
            models.Bill.release_date >= date(year, 1, 1),
            models.Bill.release_date < date(year + 1, 1, 1),
        )
    else:
        thirty_days_ago = date.today() - timedelta(days=30)
        query = query.filter(models.Bill.release_date >= thirty_days_ago)

    results = query.group_by(models.Bill.species_id, models.Bill.release_date).all()

    trends = {}
    for r in results:
        sp_id = r.species_id
        if sp_id not in trends:
            trends[sp_id] = []
        trends[sp_id].append({"date": r.date.strftime('%Y-%m-%d'), "avg_price": float(r.avg_price)})

    return trends
