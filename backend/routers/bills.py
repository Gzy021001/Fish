from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from cache import trends_cache, species_cache
from services.bill_service import (
    create_bill,
    get_bill,
    sync_bills,
    list_bills,
    update_bill,
    delete_bill,
    batch_create_bills,
)

router = APIRouter(prefix="/api", tags=["bills"])

# 重复提交检测窗口：同用户 + 同业务键的单据在 10 秒内再次创建，视为重复提交
_DUP_WINDOW_SECONDS = 10


@router.post("/bills", response_model=schemas.Bill)
def create_bill_route(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    since = datetime.now() - timedelta(seconds=_DUP_WINDOW_SECONDS)
    dup_query = db.query(models.Bill).filter(
        models.Bill.user_id == current_user.id,
        models.Bill.species_id == bill.species_id,
        models.Bill.weight == bill.weight,
        models.Bill.unit_price == bill.unit_price,
        models.Bill.fee_value == bill.fee_value,
        models.Bill.status == "DRAFT",
        models.Bill.is_deleted.is_(False),
        models.Bill.created_at >= since,
    )
    if bill.release_date is None:
        dup_query = dup_query.filter(models.Bill.release_date.is_(None))
    else:
        dup_query = dup_query.filter(models.Bill.release_date == bill.release_date)
    if dup_query.first():
        raise HTTPException(status_code=409, detail="疑似重复提交：10 秒内已创建相同单据，请勿重复提交")

    result = create_bill(bill, current_user, db)
    if result.species_id:
        trends_cache.invalidate_by_species([result.species_id])
    return result


@router.post("/bills/sync")
def sync_bills_route(
    payload: schemas.SyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    count = sync_bills(payload.date, current_user, db)
    trends_cache.clear()
    return {"message": f"已归档 {count} 条至历史", "count": count}


@router.post("/bills/archive")
def archive_bills_route(
    payload: schemas.ArchiveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    from services.bill_service import archive_bills
    count = archive_bills(payload.bill_ids, current_user, db)
    trends_cache.clear()
    return {"message": f"成功归档 {count} 条单据", "count": count}


@router.get("/bills")
def list_bills_route(
    page: int = 1,
    page_size: int = 10,
    limit: int = 100,
    status: str = None,
    date: str = None,
    date_from: str = None,
    date_to: str = None,
    q: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return list_bills(db, page=page, page_size=page_size, limit=limit, status=status, date=date, date_from=date_from, date_to=date_to, q=q)


@router.post("/bills/batch", response_model=schemas.BatchImportResult)
def batch_create_bills_route(
    payload: schemas.BatchImportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    result = batch_create_bills(payload, current_user, db)
    affected_ids = list(set(b.species_id for b in result.bills))
    if affected_ids:
        trends_cache.invalidate_by_species(affected_ids)
    # 批量导入可能创建新品种：清掉 /species 列表缓存，避免前端品种列表
    # 缺失新品种而把单据显示成“未知品种(id)”（缓存 TTL 最长 5 分钟）
    species_cache.clear()
    return result


@router.get("/bills/export")
def export_bills_route(
    date_from: str = None,
    date_to: str = None,
    bill_ids: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """导出购生明细表（模板样式 xlsx）：按日期范围，或按勾选的单据 id 批量导出。"""
    from fastapi.responses import StreamingResponse

    if bill_ids:
        ids = [int(x) for x in bill_ids.split(",") if x.strip().isdigit()]
        from services.export_service import build_bills_export_by_ids

        content, quoted_filename = build_bills_export_by_ids(db, ids)
    elif date_from and date_to:
        from services.export_service import build_bills_export

        content, quoted_filename = build_bills_export(db, date_from, date_to)
    else:
        # 未勾选单据且未指定日期范围：全量导出
        from services.export_service import build_bills_export_all

        content, quoted_filename = build_bills_export_all(db)
    return StreamingResponse(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted_filename}"},
    )


@router.get("/bills/{bill_id}", response_model=schemas.Bill)
def get_bill_route(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return get_bill(bill_id, db)


@router.put("/bills/{bill_id}", response_model=schemas.Bill)
def update_bill_route(
    bill_id: int,
    bill_update: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = update_bill(bill_id, bill_update, current_user, db)
    affected = set()
    if result.species_id:
        affected.add(result.species_id)
    if bill_update.species_id:
        affected.add(bill_update.species_id)
    if affected:
        trends_cache.invalidate_by_species(list(affected))
    return result


@router.delete("/bills/{bill_id}")
def delete_bill_route(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    bill = get_bill(bill_id, db)
    result = delete_bill(bill_id, current_user, db)
    if bill and bill.species_id:
        trends_cache.invalidate_by_species([bill.species_id])
    return result
