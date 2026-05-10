from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
import auth
from database import get_db
from services.bill_service import get_price_trend

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats/price-trend")
def get_price_trend_route(
    species_id: int,
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return get_price_trend(species_id, db, year=year)
