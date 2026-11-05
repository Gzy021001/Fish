from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/api", tags=["logs"])

# 单条实体的日志上限，防止单表全量返回
_ENTITY_LOGS_LIMIT = 500


@router.get("/logs")
def list_logs_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    total = db.query(models.AuditLog).count()
    items = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "items": items}


@router.get("/logs/bill/{bill_id}", response_model=List[schemas.AuditLog])
def list_logs_for_bill_route(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.bill_id == bill_id, models.AuditLog.entity_type == "BILL")
        .order_by(models.AuditLog.created_at.desc())
        .limit(_ENTITY_LOGS_LIMIT)
        .all()
    )


@router.get("/logs/species/{species_id}", response_model=List[schemas.AuditLog])
def list_logs_for_species_route(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.species_id == species_id, models.AuditLog.entity_type == "SPECIES")
        .order_by(models.AuditLog.created_at.desc())
        .limit(_ENTITY_LOGS_LIMIT)
        .all()
    )
