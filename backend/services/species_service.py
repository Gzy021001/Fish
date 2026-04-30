import json
from pathlib import Path
import shutil
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
from utils import delete_species_image_file, SPECIES_UPLOAD_DIR
from services.audit_service import record_create, record_update, record_delete


def list_species(db: Session):
    return db.query(models.Species).order_by(models.Species.id.asc()).all()


def get_species(species_id: int, db: Session):
    species = db.query(models.Species).filter(models.Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="未找到该品种")
    return species


def create_species(data: schemas.SpeciesCreate, user: models.User, db: Session):
    if data.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    if db.query(models.Species).filter(models.Species.name_zh == data.name_zh).first():
        raise HTTPException(status_code=400, detail="Species already registered")

    species = models.Species(**data.model_dump())
    db.add(species)
    db.flush()

    record_create(
        db,
        entity_type="SPECIES",
        user_id=user.id,
        species_id=species.id,
        data={
            "name_zh": species.name_zh,
            "default_unit": species.default_unit,
            "default_price": species.default_price,
        },
    )

    db.commit()
    db.refresh(species)
    return species


def update_species(species_id: int, data: schemas.SpeciesUpdate, user: models.User, db: Session):
    if data.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    species = get_species(species_id, db)

    if db.query(models.Species).filter(
        models.Species.name_zh == data.name_zh,
        models.Species.id != species_id,
    ).first():
        raise HTTPException(status_code=400, detail="Species name already exists")

    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price,
    }

    for field, value in data.model_dump().items():
        setattr(species, field, value)

    db.flush()

    new_data = data.model_dump()
    record_update(
        db,
        entity_type="SPECIES",
        user_id=user.id,
        species_id=species.id,
        old_data=old_data,
        new_data=new_data,
    )

    db.commit()
    db.refresh(species)
    return species


def upload_image(species_id: int, image: UploadFile, db: Session):
    species = get_species(species_id, db)

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file")

    extension = Path(image.filename or "").suffix.lower() or ".jpg"
    file_name = f"{species_id}_{uuid.uuid4().hex}{extension}"
    file_path = SPECIES_UPLOAD_DIR / file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    delete_species_image_file(species.image_url)
    species.image_url = f"/uploads/species/{file_name}"
    db.commit()
    db.refresh(species)
    return species


def delete_species(species_id: int, user: models.User, db: Session):
    species = get_species(species_id, db)

    if db.query(models.Bill).filter(models.Bill.species_id == species_id).first():
        raise HTTPException(
            status_code=400,
            detail="This species is already used in bills and cannot be deleted",
        )

    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price,
    }

    delete_species_image_file(species.image_url)

    record_delete(
        db,
        entity_type="SPECIES",
        user_id=user.id,
        species_id=species.id,
        old_data=old_data,
    )

    db.delete(species)
    db.commit()
    return {"message": "Species deleted successfully"}
