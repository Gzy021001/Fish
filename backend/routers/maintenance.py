"""一次性维护接口：补 week_carry_in 列并回填每周「上周余款」（跑完即删）。"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class CarryRow(BaseModel):
    date: str
    value: float


class CarryPayload(BaseModel):
    rows: list[CarryRow] = Field(default_factory=list, max_length=1000)


@router.post("/backfill-carry")
def backfill_carry(
    payload: CarryPayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """按模板把「上周余款」写到当天第一张单据上（先幂等补列）。"""
    try:
        db.execute(text("ALTER TABLE bills ADD COLUMN IF NOT EXISTS week_carry_in NUMERIC(12,2)"))
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("add week_carry_in failed: %s", exc)

    updated = 0
    missing: list[str] = []
    for row in payload.rows:
        result = db.execute(
            text(
                "UPDATE bills SET week_carry_in = :v WHERE id = ("
                " SELECT id FROM bills WHERE release_date = :d AND is_deleted = false"
                " ORDER BY id LIMIT 1)"
            ),
            {"v": row.value, "d": row.date},
        )
        if result.rowcount:
            updated += 1
        else:
            missing.append(row.date)
    db.commit()
    return {"updated": updated, "missing": missing[:10], "missing_count": len(missing)}
