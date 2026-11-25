"""一次性维护接口：把线上已有实付按批次分摊到每一行（跑完即删）。"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import auth
import models
from database import get_db
from services.paid_service import apportion_existing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.post("/apportion-paid")
def apportion_paid(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """按（放生日期 + 顺序）把每批实付按小计比例摊到该批每一行，批次合计不变。"""
    result = apportion_existing(db)
    logger.info("apportion-paid: %s", result)
    return result
