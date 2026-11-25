"""一次性维护接口：线上补 batch_paid 列并写入「本批实付 / 本行分摊」（跑完即删）。"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import models
from database import get_db
from services.paid_service import apply_paid_rows

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class PaidRow(BaseModel):
    date: str
    name: Optional[str] = None
    weight: float
    unit_price: float
    paid: float
    batch_paid: float


class PaidPayload(BaseModel):
    rows: list[PaidRow] = Field(default_factory=list, max_length=5000)


@router.post("/apply-batch-paid")
def apply_batch_paid(
    payload: PaidPayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """先补列（幂等），再按日期+重量+单价写入本行分摊与本批实付。"""
    try:
        db.execute(text("ALTER TABLE bills ADD COLUMN IF NOT EXISTS batch_paid NUMERIC(12,2)"))
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("add batch_paid failed: %s", exc)

    result = apply_paid_rows(db, [row.model_dump() for row in payload.rows])
    logger.info("apply-batch-paid: %s", result)
    return result
