import json
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
from utils import calculate_bill_amounts, get_bill_or_404, money
from services.audit_service import record_create, record_update, record_delete, record_replace


def _money_or_none(value):
    """金额归一为 Decimal 字符串化；None 保持 None（与列值语义一致）。"""
    if value is None:
        return None
    return money(value)


def create_bill(data: schemas.BillCreate, user: models.User, db: Session, commit: bool = True, allow_zero_weight: bool = False):
    # 批量导入兼容源表"重量未填"的行：仅批量路径（allow_zero_weight=True）允许重量为 0 的单据入账，
    # 手工录入路径保持"重量必须大于 0"的原有校验不变。
    if data.unit_price <= 0 or (data.weight <= 0 and not allow_zero_weight):
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    species = db.query(models.Species).filter(
        models.Species.id == data.species_id, models.Species.is_deleted.is_(False)
    ).first()
    if not species:
        raise HTTPException(status_code=400, detail="所选品种不存在")

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
        payment_method=data.payment_method,
        weekly_donation=data.weekly_donation,
        alipay_amount=data.alipay_amount,
        wechat_amount=data.wechat_amount,
        suixi_amount=data.suixi_amount,
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


def _apply_bill_filters(query, status=None, date_from=None, date_to=None, date_str=None, q=None, exclude_packaging=False):
    try:
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
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式无效")
        
    if q:
        query = query.filter(models.Species.name_zh.ilike(f"%{q}%"))
    # 历史单据视图排除打包耗材（冰/打包/袋），与前端 isPackagingItem 口径一致
    if exclude_packaging:
        query = query.filter(
            ~or_(
                models.Species.name_zh.like("%冰%"),
                models.Species.name_zh.like("%打包%"),
                models.Species.name_zh.like("%袋%"),
            )
        )
    return query

def list_bills(db: Session, page: int = 1, page_size: int = 10, limit: int = 100, status: str = None, date: str = None, date_from: str = None, date_to: str = None, q: str = None, exclude_packaging: bool = False):
    from sqlalchemy.orm import joinedload

    # 单页硬上限 200 条；page_size=-1（全量）语义保留，供导出/历史页使用
    if page_size > 200:
        page_size = 200
    if limit > 200:
        limit = 200

    query = db.query(models.Bill).join(models.Species).options(joinedload(models.Bill.species)).filter(models.Bill.is_deleted.is_(False)).order_by(func.coalesce(models.Bill.release_date, models.Species.release_date).desc().nullslast(), models.Bill.created_at.desc(), models.Bill.id.desc())
    query = _apply_bill_filters(query, status, date_from, date_to, date, q, exclude_packaging)

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
    ).join(models.Species).filter(models.Bill.is_deleted.is_(False))
    sum_query = _apply_bill_filters(sum_query, status, date_from, date_to, date, q, exclude_packaging)

    sum_result = sum_query.first()
    sum_weight = (sum_result[0] or 0.0) if sum_result else 0.0
    sum_subtotal = (sum_result[1] or 0.0) if sum_result else 0.0
    sum_total_amount = (sum_result[2] or 0.0) if sum_result else 0.0

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

    bill = (
        db.query(models.Bill)
        .options(joinedload(models.Bill.species))
        .filter(models.Bill.id == bill_id, models.Bill.is_deleted.is_(False))
        .first()
    )
    if not bill:
        raise HTTPException(status_code=404, detail="未找到该单据")
    return bill


def update_bill(bill_id: int, data: schemas.BillCreate, user: models.User, db: Session):
    if data.weight <= 0 or data.unit_price <= 0:
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    bill = get_bill_or_404(bill_id, db)

    species = db.query(models.Species).filter(
        models.Species.id == data.species_id, models.Species.is_deleted.is_(False)
    ).first()
    if not species:
        raise HTTPException(status_code=400, detail="所选品种不存在")

    old_data = {
        "species_id": bill.species_id,
        "weight": bill.weight,
        "unit_price": bill.unit_price,
        "currency": bill.currency,
        "fee_type": bill.fee_type,
        "fee_value": bill.fee_value,
        "release_date": bill.release_date,
        "status": bill.status,
        "payment_method": bill.payment_method,
        "weekly_donation": bill.weekly_donation,
        "alipay_amount": bill.alipay_amount,
        "wechat_amount": bill.wechat_amount,
        "suixi_amount": bill.suixi_amount,
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
        bill.status = data.status or "DRAFT"
    bill.subtotal = subtotal
    bill.total_amount = total_amount
    if data.release_date is not None:
        bill.release_date = data.release_date
    bill.payment_method = data.payment_method
    bill.weekly_donation = data.weekly_donation
    bill.alipay_amount = data.alipay_amount
    bill.wechat_amount = data.wechat_amount
    bill.suixi_amount = data.suixi_amount

    db.flush()

    # 与 old_data 同口径归一（Decimal 化），避免日志里 "12.30"(str) 与 12.3(float) 混用
    new_data = {
        "species_id": bill.species_id,
        "weight": money(data.weight),
        "unit_price": money(data.unit_price),
        "currency": data.currency,
        "fee_type": data.fee_type,
        "fee_value": money(data.fee_value),
        "release_date": bill.release_date,
        "status": bill.status,
        "payment_method": bill.payment_method,
        "weekly_donation": _money_or_none(data.weekly_donation),
        "alipay_amount": _money_or_none(data.alipay_amount),
        "wechat_amount": _money_or_none(data.wechat_amount),
        "suixi_amount": _money_or_none(data.suixi_amount),
    }
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
        "release_date": bill.release_date,
        "status": bill.status,
        "payment_method": bill.payment_method,
        "weekly_donation": bill.weekly_donation,
        "alipay_amount": bill.alipay_amount,
        "wechat_amount": bill.wechat_amount,
        "suixi_amount": bill.suixi_amount,
    }

    record_delete(
        db,
        entity_type="BILL",
        user_id=user.id,
        bill_id=bill.id,
        old_data=old_data,
    )

    # 软删除：保留审计日志的 bill_id 引用，审计链不断
    bill.is_deleted = True
    db.commit()
    return {"message": "Bill deleted successfully"}



def batch_create_bills(data: schemas.BatchImportRequest, user: models.User, db: Session):
    success_count = 0
    skip_count = 0
    affected_species_ids: set[int] = set()
    errors = []

    if data.replace:
        dates_to_replace = set()
        # 分片导入时首片会带上整份文件的全部放生日期，保证所有日期都被覆盖清空
        if data.replace_dates:
            dates_to_replace.update(d for d in data.replace_dates if d)
        for row in data.rows:
            if row.release_date:
                dates_to_replace.add(row.release_date)
        deleted_count = 0
        for d in dates_to_replace:
            # 软删除当天已有单据（保留审计引用），再插入新单据
            result = db.query(models.Bill).filter(
                models.Bill.release_date >= d,
                models.Bill.release_date < (d + timedelta(days=1)),
                models.Bill.is_deleted.is_(False),
            ).update({"is_deleted": True}, synchronize_session=False)
            deleted_count += result or 0
        db.flush()
        if dates_to_replace:
            # 覆盖软删不走逐条 DELETE 审计，写一条汇总 REPLACE 审计保留追溯链
            record_replace(
                db,
                entity_type="BILL",
                user_id=user.id,
                details={
                    "action": "导入覆盖",
                    "dates": sorted(d.isoformat() for d in dates_to_replace),
                    "deleted_bills": deleted_count,
                },
            )

    existing_species = {s.name_zh: s for s in db.query(models.Species).filter(models.Species.is_deleted.is_(False)).all()}

    for row in data.rows:
        name_zh = row.name_zh.strip()
        # 兼容源表「重量未填」的行：重量为 0 照常入账（金额=服务费），仅负数重量视为无效跳过。
        if not name_zh or row.unit_price <= 0 or (row.weight or 0) < 0:
            skip_count += 1
            errors.append(f'跳过 "{name_zh or "(空)"}": 名称无效、单价 <= 0 或重量为负')
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
            status=None,
            payment_method=row.payment_method,
            alipay_amount=row.alipay_amount,
            wechat_amount=row.wechat_amount,
            suixi_amount=row.suixi_amount,
        )
        create_bill(bill_create, user, db, commit=False, allow_zero_weight=True)
        affected_species_ids.add(species.id)
        success_count += 1

    db.commit()

    return schemas.BatchImportResult(
        success_count=success_count,
        skip_count=skip_count,
        affected_species_ids=sorted(affected_species_ids),
        errors=errors,
    )


def get_price_trend(species_id: int, db: Session, year: int = None):
    species = db.query(models.Species).filter(models.Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="未找到该品种")

    # 放生日期口径与列表/看板一致：单据日期缺失时回退品种日期
    bill_day = func.coalesce(models.Bill.release_date, models.Species.release_date)
    query = (
        db.query(
            bill_day.label("date"),
            func.avg(models.Bill.unit_price).label("avg_price"),
        )
        .join(models.Species, models.Bill.species_id == models.Species.id)
        .filter(models.Bill.species_id == species.id)
        .filter(bill_day.isnot(None))
        .filter(models.Bill.is_deleted.is_(False))
        .filter(models.Bill.status == "COMPLETED")
    )

    if year:
        query = query.filter(
            bill_day >= date(year, 1, 1),
            bill_day < date(year + 1, 1, 1),
        )
    else:
        thirty_days_ago = date.today() - timedelta(days=30)
        query = query.filter(bill_day >= thirty_days_ago)

    results = query.group_by(bill_day).all()

    return [{"date": r.date.strftime('%Y-%m-%d'), "avg_price": float(r.avg_price)} for r in results]


def get_price_trends_batch(species_ids: list[int], db: Session, year: int = None):
    if not species_ids:
        return {}

    bill_day = func.coalesce(models.Bill.release_date, models.Species.release_date)
    query = (
        db.query(
            models.Bill.species_id,
            bill_day.label("date"),
            func.avg(models.Bill.unit_price).label("avg_price"),
        )
        .join(models.Species, models.Bill.species_id == models.Species.id)
        .filter(models.Bill.species_id.in_(species_ids))
        .filter(bill_day.isnot(None))
        .filter(models.Bill.is_deleted.is_(False))
        .filter(models.Bill.status == "COMPLETED")
    )

    if year:
        query = query.filter(
            bill_day >= date(year, 1, 1),
            bill_day < date(year + 1, 1, 1),
        )
    else:
        thirty_days_ago = date.today() - timedelta(days=30)
        query = query.filter(bill_day >= thirty_days_ago)

    results = query.group_by(models.Bill.species_id, bill_day).all()

    trends = {}
    for r in results:
        sp_id = r.species_id
        if sp_id not in trends:
            trends[sp_id] = []
        trends[sp_id].append({"date": r.date.strftime('%Y-%m-%d'), "avg_price": float(r.avg_price)})

    return trends
