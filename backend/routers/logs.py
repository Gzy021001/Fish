from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs", response_model=List[schemas.AuditLog])
def list_logs_route(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).all()


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
        .all()
    )
