import logging
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
from utils import money
from services.audit_service import record_create, record_update, record_delete
from services.image_storage import store_image_asset

logger = logging.getLogger(__name__)


def list_species(db: Session, q: Optional[str] = None):
    query = db.query(models.Species).filter(models.Species.is_deleted.is_(False))
    if q:
        query = query.filter(models.Species.name_zh.ilike(f"%{q}%"))
    # 放生日期最新的品种排前面，未填日期的排最后；同日按 id 倒序兜底
    return (
        query.order_by(
            models.Species.release_date.desc().nullslast(),
            models.Species.id.desc(),
        )
        .all()
    )


def list_species_paginated(db: Session, q: Optional[str], page: int, page_size: int):
    """服务端分页版品种列表（page/page_size 均 > 0 时使用），返回 (items, total)。"""
    query = db.query(models.Species).filter(models.Species.is_deleted.is_(False))
    if q:
        query = query.filter(models.Species.name_zh.ilike(f"%{q}%"))
    total = query.count()
    items = (
        query.order_by(
            models.Species.release_date.desc().nullslast(),
            models.Species.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def serialize_species_list(items, include_images: bool = True):
    result = []
    for item in items:
        image_url = item.image_url
        # base64 data URI（Vercel 模式）不进列表接口，避免列表响应膨胀；单查接口不受影响
        if not include_images or (image_url and str(image_url).startswith("data:")):
            image_url = None
        result.append(
            {
                "id": item.id,
                "name_zh": item.name_zh,
                "default_unit": item.default_unit,
                "default_price": item.default_price,
                "image_url": image_url,
                "supplier_name": item.supplier_name,
                "supplier_note": item.supplier_note,
                "release_date": item.release_date,
                "created_at": item.created_at,
            }
        )
    return result


def get_species(species_id: int, db: Session):
    species = db.query(models.Species).filter(models.Species.id == species_id).first()
    if not species or species.is_deleted:
        raise HTTPException(status_code=404, detail="未找到该品种")
    return species


def create_species(data: schemas.SpeciesCreate, user: models.User, db: Session):
    if not data.release_date:
        raise HTTPException(status_code=400, detail="请选择放生日期")
    if data.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    if db.query(models.Species).filter(
        models.Species.name_zh == data.name_zh,
        models.Species.is_deleted.is_(False),
    ).first():
        raise HTTPException(status_code=400, detail="品种名称已存在，请勿重复添加")

    species = models.Species(**data.model_dump())
    db.add(species)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="品种名称已存在，请勿重复添加")

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
        models.Species.is_deleted.is_(False),
    ).first():
        raise HTTPException(status_code=400, detail="品种名称已存在，请勿重复添加")

    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price,
        "supplier_name": species.supplier_name,
        "supplier_note": species.supplier_note,
        "release_date": species.release_date,
        "image_url": species.image_url,
    }

    for field, value in data.model_dump(exclude={"created_at"}).items():
        setattr(species, field, value)

    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="品种名称已存在，请勿重复添加")

    new_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": money(species.default_price),
        "supplier_name": species.supplier_name,
        "supplier_note": species.supplier_note,
        "release_date": species.release_date,
        "image_url": species.image_url,
    }
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

    if getattr(image, "size", 0) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    try:
        contents = image.file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")
        species.image_url = store_image_asset(contents, image.content_type, folder="species")
        db.commit()
        db.refresh(species)
        return species
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing image: %s", e)
        raise HTTPException(status_code=500, detail="图片处理失败，请稍后重试")


def delete_species(species_id: int, user: models.User, db: Session):
    species = get_species(species_id, db)

    if db.query(models.Bill).filter(
        models.Bill.species_id == species_id,
        models.Bill.is_deleted.is_(False),
    ).first():
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

    # 软删除：保留审计日志的 species_id 引用，审计链不断
    species.is_deleted = True
    # 释放唯一索引：名称加前缀，允许以后重建同名品种
    species.name_zh = f"#deleted#{species.id}#{species.name_zh}"[:100]
    db.commit()
    return {"message": "Species deleted successfully"}
 