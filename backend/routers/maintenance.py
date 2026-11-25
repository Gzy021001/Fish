"""一次性维护接口：删除（软删）某天某名称的支出行（跑完即删）。"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class DeleteExpenseRequest(BaseModel):
    date: str
    name: str


@router.post("/delete-expense")
def delete_expense(
    payload: DeleteExpenseRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """把一个记错的支出行软删掉（用于把误记为耗材的物命补成正式单据）。"""
    result = db.execute(
        text(
            "UPDATE week_expenses SET is_deleted = true "
            "WHERE release_date = :d AND name = :n AND is_deleted = false"
        ),
        {"d": payload.date, "n": payload.name},
    )
    db.commit()
    logger.info("delete-expense %s %s -> %s", payload.date, payload.name, result.rowcount)
    return {"deleted": result.rowcount}
