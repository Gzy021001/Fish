from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return list_species(db)


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
    return create_species(species, current_user, db)


@router.put("/species/{species_id}", response_model=schemas.Species)
def update_species_route(
    species_id: int,
    species_update: schemas.SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return update_species(species_id, species_update, current_user, db)


@router.post("/species/{species_id}/image", response_model=schemas.Species)
def upload_species_image_route(
    species_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return upload_image(species_id, image, db)


@router.delete("/species/{species_id}")
def delete_species_route(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return delete_species(species_id, current_user, db)
