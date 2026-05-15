from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from services.bill_service import (
    create_bill,
    sync_bills,
    list_bills,
    update_bill,
    delete_bill,
)

router = APIRouter(prefix="/api", tags=["bills"])


@router.post("/bills", response_model=schemas.Bill)
def create_bill_route(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return create_bill(bill, current_user, db)


@router.post("/bills/sync")
def sync_bills_route(
    payload: schemas.SyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    count = sync_bills(payload.date, current_user, db)
    return {"message": f"已归档 {count} 条至历史", "count": count}


@router.get("/bills", response_model=List[schemas.Bill])
def list_bills_route(
    limit: int = 100,
    status: str = None,
    date: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return list_bills(db, limit=limit, status=status, date=date, date_from=date_from, date_to=date_to)


@router.put("/bills/{bill_id}", response_model=schemas.Bill)
def update_bill_route(
    bill_id: int,
    bill_update: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return update_bill(bill_id, bill_update, current_user, db)


@router.delete("/bills/{bill_id}")
def delete_bill_route(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return delete_bill(bill_id, current_user, db)
