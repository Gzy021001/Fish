from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from cache import trends_cache
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


@router.post("/bills", response_model=schemas.Bill)
def create_bill_route(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
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
    return result


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
