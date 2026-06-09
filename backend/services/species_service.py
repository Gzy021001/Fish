from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
from services.audit_service import record_create, record_update, record_delete
from services.image_storage import store_image_asset


def list_species(db: Session, q: Optional[str] = None):
    query = db.query(models.Species)
    if q:
        query = query.filter(models.Species.name_zh.ilike(f"%{q}%"))
    return query.order_by(models.Species.id.asc()).all()


def serialize_species_list(items, include_images: bool = True):
    result = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "name_zh": item.name_zh,
                "default_unit": item.default_unit,
                "default_price": item.default_price,
                "image_url": item.image_url if include_images else None,
                "supplier_name": item.supplier_name,
                "supplier_note": item.supplier_note,
                "release_date": item.release_date,
                "created_at": item.created_at,
            }
        )
    return result


def get_species(species_id: int, db: Session):
    species = db.query(models.Species).filter(models.Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="未找到该品种")
    return species


def create_species(data: schemas.SpeciesCreate, user: models.User, db: Session):
    if not data.release_date:
        raise HTTPException(status_code=400, detail="请选择放生日期")
    if data.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    if db.query(models.Species).filter(models.Species.name_zh == data.name_zh).first():
        raise HTTPException(status_code=400, detail="品种名称已存在，请勿重复添加")

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
            "supplier_name": species.supplier_name,
            "supplier_note": species.supplier_note,
            "release_date": species.release_date,
        },
    )

    db.commit()
    db.refresh(species)
    return species


def update_species(species_id: int, data: schemas.SpeciesUpdate, user: models.User, db: Session):
    if not data.release_date:
        raise HTTPException(status_code=400, detail="请选择放生日期")
    if data.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    species = get_species(species_id, db)

    if db.query(models.Species).filter(
        models.Species.name_zh == data.name_zh,
        models.Species.id != species_id,
    ).first():
        raise HTTPException(status_code=400, detail="品种名称已存在，请勿重复添加")

    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price,
        "supplier_name": species.supplier_name,
        "supplier_note": species.supplier_note,
        "release_date": species.release_date,
    }

    for field, value in data.model_dump(exclude={"created_at"}).items():
        setattr(species, field, value)

    db.flush()

    new_data = data.model_dump(exclude={"created_at"})
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
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        contents = image.file.read()
        species.image_url = store_image_asset(contents, image.content_type, folder="species")
        db.commit()
        db.refresh(species)
        return species
    except Exception as e:
        print(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail="图片处理失败，请稍后重试")


def delete_species(species_id: int, user: models.User, db: Session):
    species = get_species(species_id, db)

    if db.query(models.Bill).filter(models.Bill.species_id == species_id).first():
        raise HTTPException(
            status_code=400,
            detail="该品种已被单据使用，无法删除",
        )

    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price,
        "supplier_name": species.supplier_name,
        "supplier_note": species.supplier_note,
        "release_date": species.release_date,
    }

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
