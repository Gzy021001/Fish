from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from cache import species_cache
from services.species_service import (
    list_species,
    get_species,
    create_species,
    update_species,
    upload_image,
    delete_species,
)

router = APIRouter(prefix="/api", tags=["species"])


@router.get("/species", response_model=List[schemas.Species])
def list_species_route(
    q: Optional[str] = Query(None, description="搜索品种名称"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    cache_key = f"species_list_{q or 'all'}"
    cached_result = species_cache.get(cache_key)
    if cached_result is not None:
        return cached_result
        
    result = list_species(db, q)
    species_cache.set(cache_key, result)
    return result


@router.get("/species/{species_id}", response_model=schemas.Species)
def get_species_route(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return get_species(species_id, db)


@router.post("/species", response_model=schemas.Species)
def create_species_route(
    species: schemas.SpeciesCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = create_species(species, current_user, db)
    species_cache.clear()
    return result


@router.put("/species/{species_id}", response_model=schemas.Species)
def update_species_route(
    species_id: int,
    species_update: schemas.SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = update_species(species_id, species_update, current_user, db)
    species_cache.clear()
    return result


@router.post("/species/{species_id}/image", response_model=schemas.Species)
def upload_species_image_route(
    species_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = upload_image(species_id, image, db)
    species_cache.clear()
    return result


@router.delete("/species/{species_id}")
def delete_species_route(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = delete_species(species_id, current_user, db)
    species_cache.clear()
    return result
