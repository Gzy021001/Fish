import json
from datetime import datetime, timedelta, timezone

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
        status=data.status or "DRAFT",
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


def list_bills(db: Session, page: int = 1, page_size: int = 10, limit: int = 100, status: str = None, date: str = None, date_from: str = None, date_to: str = None, q: str = None):
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_
    query = db.query(models.Bill).join(models.Species).options(joinedload(models.Bill.species)).order_by(models.Bill.release_date.desc().nullslast(), models.Bill.id.desc())
    if status:
        query = query.filter(models.Bill.status == status)
    if date_from:
        date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(
            or_(
                models.Bill.release_date >= date_from_dt,
                (models.Bill.release_date.is_(None) & (models.Bill.created_at >= date_from_dt))
            )
        )
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(
            or_(
                models.Bill.release_date < end,
                (models.Bill.release_date.is_(None) & (models.Bill.created_at < end))
            )
        )
    if date:
        date_dt = datetime.strptime(date, "%Y-%m-%d")
        date_end = date_dt + timedelta(days=1)
        query = query.filter(models.Bill.release_date >= date_dt, models.Bill.release_date < date_end)
        
    if q:
        query = query.filter(models.Species.name_zh.ilike(f"%{q}%"))
        
    # 为了兼容以前的调用（如果 limit > 0，则忽略分页，返回最多 limit 条）
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
    
    # 真正的后端分页
    # 必须在修改 SELECT 子句之前计算 count
    total = query.count()
    
    # 为了避免 with_entities 修改 query 的状态，我们使用 session 构建一个新的汇总查询
    from sqlalchemy import func
    
    # 构建基础的 where 条件
    base_filters = []
    if status:
        base_filters.append(models.Bill.status == status)
    if date_from:
        date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        base_filters.append(
            or_(
                models.Bill.release_date >= date_from_dt,
                (models.Bill.release_date.is_(None) & (models.Bill.created_at >= date_from_dt))
            )
        )
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        base_filters.append(
            or_(
                models.Bill.release_date < end,
                (models.Bill.release_date.is_(None) & (models.Bill.created_at < end))
            )
        )
    if date:
        date_dt = datetime.strptime(date, "%Y-%m-%d")
        date_end = date_dt + timedelta(days=1)
        base_filters.append(models.Bill.release_date >= date_dt)
        base_filters.append(models.Bill.release_date < date_end)
        
    # 汇总查询
    sum_query = db.query(
        func.sum(models.Bill.weight),
        func.sum(models.Bill.subtotal),
        func.sum(models.Bill.total_amount)
    )
    
    # 如果有 q（品种名），我们需要 join Species
    if q:
        sum_query = sum_query.join(models.Species).filter(models.Species.name_zh.ilike(f"%{q}%"))
        
    for f in base_filters:
        sum_query = sum_query.filter(f)
        
    sum_result = sum_query.first()
    
    sum_weight = sum_result[0] or 0.0 if sum_result else 0.0
    sum_subtotal = sum_result[1] or 0.0 if sum_result else 0.0
    sum_total_amount = sum_result[2] or 0.0 if sum_result else 0.0
    
    # 对于导出功能，如果 page_size == -1，则返回全部满足条件的数据
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



def batch_create_bills(data: schemas.BatchImportRequest, user: models.User, db: Session):
    success_count = 0
    skip_count = 0
    bills = []
    errors = []

    # If replace mode: delete existing bills with same release dates
    if data.replace:
        from datetime import datetime, timedelta
        dates_to_replace = set()
        for row in data.rows:
            if row.release_date:
                dates_to_replace.add(row.release_date)
        for d in dates_to_replace:
            db.query(models.Bill).filter(
                models.Bill.release_date >= d,
                models.Bill.release_date < (d + timedelta(days=1))
            ).delete()
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
            species = models.Species(
                name_zh=name_zh,
                default_price=row.unit_price,
                default_unit="公斤",
                release_date=row.release_date,
            )
            db.add(species)
            db.flush()
            existing_species[name_zh] = species

        bill_create = schemas.BillCreate(
            species_id=species.id,
            weight=row.weight or 0,
            unit_price=row.unit_price,
            fee_value=row.fee_value or 0,
            release_date=row.release_date,
        )
        bill = create_bill(bill_create, user, db)
        bills.append(bill)
        success_count += 1

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
        thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        query = query.filter(models.Bill.release_date >= thirty_days_ago)

    results = query.group_by(func.date(models.Bill.release_date)).all()

    return [{"date": str(r.date), "avg_price": float(r.avg_price)} for r in results]


def get_price_trends_batch(species_ids: list[int], db: Session, year: int = None):
    if not species_ids:
        return {}

    query = (
        db.query(
            models.Bill.species_id,
            func.date(models.Bill.release_date).label("date"),
            func.avg(models.Bill.unit_price).label("avg_price"),
        )
        .filter(models.Bill.species_id.in_(species_ids))
        .filter(models.Bill.release_date.isnot(None))
    )

    if year:
        query = query.filter(
            models.Bill.release_date >= datetime(year, 1, 1),
            models.Bill.release_date < datetime(year + 1, 1, 1),
        )
    else:
        thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        query = query.filter(models.Bill.release_date >= thirty_days_ago)

    results = query.group_by(models.Bill.species_id, func.date(models.Bill.release_date)).all()

    trends = {}
    for r in results:
        sp_id = r.species_id
        if sp_id not in trends:
            trends[sp_id] = []
        trends[sp_id].append({"date": str(r.date), "avg_price": float(r.avg_price)})

    return trends
