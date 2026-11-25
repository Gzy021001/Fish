import json
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
from utils import calculate_bill_amounts, get_bill_or_404, money
from services.audit_service import record_create, record_update, record_delete, record_replace
from services.paid_service import apportion_rows


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
        unit=data.unit,
        unit_jin=data.unit_jin,
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
        paid_amount=data.paid_amount,
        batch_paid=data.batch_paid,
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


def _apply_bill_filters(query, status=None, date_from=None, date_to=None, date_str=None, q=None, exclude_packaging=False, has_suixi=False):
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
    # 随喜汇总视图：只留真正带随喜记录的单据（有随喜类型，或三类金额至少一项大于 0），
    # 避免历史导入的 700+ 条空记录把明细淹掉
    if has_suixi:
        query = query.filter(
            or_(
                models.Bill.payment_method.isnot(None) & (models.Bill.payment_method != ""),
                models.Bill.alipay_amount > 0,
                models.Bill.wechat_amount > 0,
                models.Bill.suixi_amount > 0,
            )
        )
    return query

def _bill_day():
    """放生日期口径：单据日期缺失时回退品种日期（与列表/看板一致）。"""
    return func.coalesce(models.Bill.release_date, models.Species.release_date)


def _week_expense_totals(db: Session, date_str: str = None, date_from: str = None, date_to: str = None):
    """车费/船费合计（按放生日期范围过滤）；返回 (合计, 车费, 船费)。"""
    query = db.query(
        models.WeekExpense.name, func.sum(models.WeekExpense.amount)
    ).filter(models.WeekExpense.is_deleted.is_(False))
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            d = None
        if d:
            query = query.filter(models.WeekExpense.release_date == d)
    if date_from:
        query = query.filter(models.WeekExpense.release_date >= date_from)
    if date_to:
        query = query.filter(models.WeekExpense.release_date <= date_to)
    by_name = {name: float(amount or 0) for name, amount in query.group_by(models.WeekExpense.name).all()}
    return sum(by_name.values()), by_name.get("车费", 0.0), by_name.get("船费", 0.0)


def _bill_totals(db: Session, status: str = None, date_str: str = None, date_from: str = None, date_to: str = None, q: str = None, exclude_packaging: bool = False, has_suixi: bool = False):
    """全量口径合计（与分页无关）：重量/小计/总金额/实付 + 随喜三分类，供列表表尾直接展示。"""
    sum_query = db.query(
        func.sum(models.Bill.weight),
        func.sum(models.Bill.subtotal),
        func.sum(models.Bill.total_amount),
        func.sum(models.Bill.alipay_amount),
        func.sum(models.Bill.wechat_amount),
        func.sum(models.Bill.suixi_amount),
        func.sum(models.Bill.paid_amount)
    ).join(models.Species).filter(models.Bill.is_deleted.is_(False))
    sum_query = _apply_bill_filters(sum_query, status, date_from, date_to, date_str, q, exclude_packaging, has_suixi)

    sum_result = sum_query.first()
    if not sum_result:
        return (0, 0, 0, 0, 0, 0, 0)
    return tuple((value or 0) for value in sum_result)


def _day_key(value):
    """按天聚合的键：date -> ISO 字符串，字符串原样返回（SQLite/PG 结果类型统一）。"""
    return value.isoformat() if hasattr(value, "isoformat") else value


def _split_wechat_by_day(db: Session, status: str = None, date_str: str = None, date_from: str = None, date_to: str = None, q: str = None, exclude_packaging: bool = False, has_suixi: bool = False):
    """微信两列口径（与导出模板的「微信 / 微信」两行一致）：
    当天第一笔微信 -> 微信1，当天其余微信合计 -> 微信2；按单据创建顺序取「第一笔」。"""
    day = _bill_day()
    query = (
        db.query(day.label("day"), models.Bill.wechat_amount)
        .join(models.Species)
        .filter(models.Bill.is_deleted.is_(False), models.Bill.wechat_amount > 0)
    )
    query = _apply_bill_filters(query, status, date_from, date_to, date_str, q, exclude_packaging, has_suixi)
    query = query.order_by(day.asc(), models.Bill.created_at.asc(), models.Bill.id.asc())

    first: dict = {}
    rest: dict = {}
    for day_value, amount in query.all():
        key = _day_key(day_value)
        if key in first:
            rest[key] = rest.get(key, 0) + amount
        else:
            first[key] = amount
    return first, rest


def _list_bills_by_day(db: Session, page: int = 1, page_size: int = 10, status: str = None, date_str: str = None, date_from: str = None, date_to: str = None, q: str = None, exclude_packaging: bool = False, has_suixi: bool = False):
    """随喜汇总：按放生日期聚合，一行一天（分页按天）。
    微信拆两列（微信1 = 当天第一笔，微信2 = 当天其余合计），三分类合计供表尾使用。"""
    day = _bill_day()
    grouped = (
        db.query(
            day.label("release_date"),
            func.sum(models.Bill.alipay_amount).label("alipay_amount"),
            func.sum(models.Bill.suixi_amount).label("suixi_amount"),
        )
        .join(models.Species)
        .filter(models.Bill.is_deleted.is_(False))
    )
    grouped = _apply_bill_filters(grouped, status, date_from, date_to, date_str, q, exclude_packaging, has_suixi)
    grouped_sub = grouped.group_by(day).subquery()

    total = db.query(func.count()).select_from(grouped_sub).scalar() or 0

    rows_query = db.query(grouped_sub).order_by(grouped_sub.c.release_date.desc().nullslast())
    if page_size > 0:
        rows_query = rows_query.offset(max(0, page - 1) * page_size).limit(page_size)
    rows = rows_query.all()

    (
        sum_weight,
        sum_subtotal,
        sum_total_amount,
        sum_alipay,
        sum_wechat,
        sum_suixi,
        sum_paid_amount,
    ) = _bill_totals(
        db, status=status, date_str=date_str, date_from=date_from, date_to=date_to,
        q=q, exclude_packaging=exclude_packaging, has_suixi=has_suixi,
    )
    wechat_first, wechat_rest = _split_wechat_by_day(
        db, status=status, date_str=date_str, date_from=date_from, date_to=date_to,
        q=q, exclude_packaging=exclude_packaging, has_suixi=has_suixi,
    )
    sum_wechat1 = sum(wechat_first.values(), 0)
    sum_wechat2 = sum(wechat_rest.values(), 0)

    items = []
    for row in rows:
        release = row.release_date
        key = _day_key(release)
        items.append({
            "release_date": key,
            "alipay_amount": row.alipay_amount or 0,
            "wechat1_amount": wechat_first.get(key, 0),
            "wechat2_amount": wechat_rest.get(key, 0),
            "suixi_amount": row.suixi_amount or 0,
        })

    return {
        "total": total,
        "items": items,
        "sum_weight": sum_weight,
        "sum_subtotal": sum_subtotal,
        "sum_total_amount": sum_total_amount,
        "sum_alipay": sum_alipay,
        "sum_wechat": sum_wechat,
        "sum_wechat1": sum_wechat1,
        "sum_wechat2": sum_wechat2,
        "sum_suixi": sum_suixi,
        "sum_paid_amount": sum_paid_amount,
    }


def list_bills(db: Session, page: int = 1, page_size: int = 10, limit: int = 100, status: str = None, date: str = None, date_from: str = None, date_to: str = None, q: str = None, exclude_packaging: bool = False, has_suixi: bool = False, group_by_date: bool = False):
    from sqlalchemy.orm import joinedload

    # 单页硬上限 200 条；page_size=-1（全量）语义保留，供导出/历史页使用
    if page_size > 200:
        page_size = 200
    if limit > 200:
        limit = 200

    # 随喜汇总按放生日期聚合（一行一天），走独立的分组查询
    if group_by_date:
        return _list_bills_by_day(
            db, page=page, page_size=page_size, status=status, date_str=date,
            date_from=date_from, date_to=date_to, q=q,
            exclude_packaging=exclude_packaging, has_suixi=has_suixi,
        )

    query = db.query(models.Bill).join(models.Species).options(joinedload(models.Bill.species)).filter(models.Bill.is_deleted.is_(False)).order_by(func.coalesce(models.Bill.release_date, models.Species.release_date).desc().nullslast(), models.Bill.created_at.desc(), models.Bill.id.desc())
    query = _apply_bill_filters(query, status, date_from, date_to, date, q, exclude_packaging, has_suixi)

    if limit > 0:
        query = query.limit(limit)
        items = query.all()

        sum_weight = sum((item.weight or 0) for item in items)
        sum_subtotal = sum((item.subtotal or 0) for item in items)
        sum_total_amount = sum((item.total_amount or 0) for item in items)
        # 随喜三分类合计（支付宝 / 微信 / 随喜放生）：供「随喜汇总」页签直接展示，
        # 金额一律按 Decimal 相加，不引入 float 误差
        sum_alipay = sum((item.alipay_amount or 0) for item in items)
        sum_wechat = sum((item.wechat_amount or 0) for item in items)
        sum_suixi = sum((item.suixi_amount or 0) for item in items)
        sum_paid_amount = sum((item.paid_amount or 0) for item in items)
        sum_expense, sum_expense_car, sum_expense_ship = _week_expense_totals(db, date, date_from, date_to)

        return {
            "total": len(items),
            "items": items,
            "sum_weight": sum_weight,
            "sum_subtotal": sum_subtotal,
            "sum_total_amount": sum_total_amount,
            "sum_alipay": sum_alipay,
            "sum_wechat": sum_wechat,
            "sum_suixi": sum_suixi,
            "sum_paid_amount": sum_paid_amount,
            "sum_expense": sum_expense,
            "sum_expense_car": sum_expense_car,
            "sum_expense_ship": sum_expense_ship,
        }

    total = query.count()

    (
        sum_weight,
        sum_subtotal,
        sum_total_amount,
        sum_alipay,
        sum_wechat,
        sum_suixi,
        sum_paid_amount,
    ) = _bill_totals(
        db, status=status, date_str=date, date_from=date_from, date_to=date_to,
        q=q, exclude_packaging=exclude_packaging, has_suixi=has_suixi,
    )
    sum_expense, sum_expense_car, sum_expense_ship = _week_expense_totals(db, date, date_from, date_to)

    if page_size == -1:
        items = query.all()
        return {
            "total": total,
            "items": items,
            "sum_weight": sum_weight,
            "sum_subtotal": sum_subtotal,
            "sum_total_amount": sum_total_amount,
            "sum_alipay": sum_alipay,
            "sum_wechat": sum_wechat,
            "sum_suixi": sum_suixi,
            "sum_paid_amount": sum_paid_amount,
            "sum_expense": sum_expense,
            "sum_expense_car": sum_expense_car,
            "sum_expense_ship": sum_expense_ship,
        }

    if page_size > 0:
        query = query.offset((page - 1) * page_size).limit(page_size)
    items = query.all()

    return {
        "total": total,
        "items": items,
        "sum_weight": sum_weight,
        "sum_subtotal": sum_subtotal,
        "sum_total_amount": sum_total_amount,
        "sum_alipay": sum_alipay,
        "sum_wechat": sum_wechat,
        "sum_suixi": sum_suixi,
        "sum_paid_amount": sum_paid_amount,
        "sum_expense": sum_expense,
        "sum_expense_car": sum_expense_car,
        "sum_expense_ship": sum_expense_ship,
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
        "unit": bill.unit,
        "unit_jin": bill.unit_jin,
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
        "paid_amount": bill.paid_amount,
    }

    subtotal, fee, total_amount = calculate_bill_amounts(
        data.weight, data.unit_price, data.fee_value
    )

    bill.species_id = data.species_id
    bill.weight = data.weight
    bill.unit_price = data.unit_price
    bill.unit = data.unit
    bill.unit_jin = data.unit_jin
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
    bill.paid_amount = data.paid_amount
    # 编辑表单不带本批实付：为空时保留原值，避免手工改单价把「本批实付」清掉
    if data.batch_paid is not None:
        bill.batch_paid = data.batch_paid

    db.flush()

    # 与 old_data 同口径归一（Decimal 化），避免日志里 "12.30"(str) 与 12.3(float) 混用
    new_data = {
        "species_id": bill.species_id,
        "weight": money(data.weight),
        "unit_price": money(data.unit_price),
        "unit": data.unit,
        "unit_jin": money(data.unit_jin) if data.unit_jin is not None else None,
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
        "paid_amount": _money_or_none(data.paid_amount),
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
        "unit": bill.unit,
        "unit_jin": bill.unit_jin,
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
        for expense in data.expenses:
            if expense.release_date:
                dates_to_replace.add(expense.release_date)
        deleted_count = 0
        for d in dates_to_replace:
            # 软删除当天已有单据（保留审计引用），再插入新单据
            result = db.query(models.Bill).filter(
                models.Bill.release_date >= d,
                models.Bill.release_date < (d + timedelta(days=1)),
                models.Bill.is_deleted.is_(False),
            ).update({"is_deleted": True}, synchronize_session=False)
            deleted_count += result or 0
        # 车费/船费同样按日期覆盖
        for d in dates_to_replace:
            db.query(models.WeekExpense).filter(
                models.WeekExpense.release_date >= d,
                models.WeekExpense.release_date < (d + timedelta(days=1)),
                models.WeekExpense.is_deleted.is_(False),
            ).update({"is_deleted": True}, synchronize_session=False)
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

    # 模板「实付」只写在该批首行：导入时按小计比例摊到同一批的每一行，列表才不会一片空白
    apportion_rows(data.rows)

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
                        default_unit="斤",
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
            unit=row.unit,
            unit_jin=row.unit_jin,
            fee_value=row.fee_value or 0,
            release_date=row.release_date,
            status=None,
            payment_method=row.payment_method,
            alipay_amount=row.alipay_amount,
            wechat_amount=row.wechat_amount,
            suixi_amount=row.suixi_amount,
            paid_amount=row.paid_amount,
        )
        create_bill(bill_create, user, db, commit=False, allow_zero_weight=True)
        affected_species_ids.add(species.id)
        success_count += 1

    # 车费/船费等表尾支出（模板里不打进物命单据，单独落库，实付合计时才计入）
    expense_count = 0
    for expense in data.expenses:
        name = (expense.name or "").strip()
        if not name or expense.amount is None:
            continue
        db.add(
            models.WeekExpense(
                release_date=expense.release_date,
                name=name[:20],
                amount=money(expense.amount),
            )
        )
        expense_count += 1

    db.commit()

    return schemas.BatchImportResult(
        success_count=success_count,
        skip_count=skip_count,
        expense_count=expense_count,
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
