from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
import auth
from database import get_db
from services.bill_service import get_price_trend, get_price_trends_batch

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats/price-trend")
def get_price_trend_route(
    species_id: int,
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return get_price_trend(species_id, db, year=year)


@router.get("/stats/price-trend-batch")
def get_price_trends_batch_route(
    species_ids: str = Query(..., description="Comma-separated species IDs"),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ids = [int(i.strip()) for i in species_ids.split(",") if i.strip()]
    return get_price_trends_batch(ids, db, year=year)
