from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, Response
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from cache import species_cache
from services.species_service import (
    list_species,
    list_species_paginated,
    get_species,
    create_species,
    update_species,
    upload_image,
    delete_species,
    serialize_species_list,
)

router = APIRouter(prefix="/api", tags=["species"])


@router.get("/species", response_model=List[schemas.Species])
def list_species_route(
    q: Optional[str] = Query(None, description="搜索品种名称"),
    include_images: bool = Query(False, description="是否在列表中包含图片字段（base64 图片不会进列表）"),
    page: int = 0,
    page_size: int = 0,
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # 服务端分页参数（0 表示不分页返回全部，保持旧行为）；page_size 上限 200
    if page < 0:
        page = 0
    if page_size < 0:
        page_size = 0
    if page_size > 200:
        page_size = 200

    if page > 0 and page_size > 0:
        # 服务端分页模式：总数放 X-Total-Count 头，分页结果不进缓存
        items, total = list_species_paginated(db, q, page, page_size)
        if response is not None:
            response.headers["X-Total-Count"] = str(total)
        return serialize_species_list(items, include_images=include_images)

    cache_key = f"species_list_{q or 'all'}_{'with_images' if include_images else 'lite'}"
    cached_result = species_cache.get(cache_key)
    if cached_result is not None:
        if response is not None:
            response.headers["X-Total-Count"] = str(len(cached_result))
        return cached_result

    result = serialize_species_list(list_species(db, q), include_images=include_images)
    species_cache.set(cache_key, result)
    if response is not None:
        response.headers["X-Total-Count"] = str(len(result))
    return result


@router.get("/species/export")
def export_species_route(
    species_ids: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """导出品种库 xlsx（勾选品种则只导选中的，否则全量）。"""
    from fastapi.responses import StreamingResponse
    from services.export_service import build_species_export

    ids = [int(x) for x in (species_ids or "").split(",") if x.strip().isdigit()] or None
    content, quoted_filename = build_species_export(db, ids)
    return StreamingResponse(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted_filename}"},
    )


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
    current_user: models.User = Depends(auth.require_write),
):
    result = create_species(species, current_user, db)
    species_cache.clear()
    return result


@router.put("/species/{species_id}", response_model=schemas.Species)
def update_species_route(
    species_id: int,
    species_update: schemas.SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_write),
):
    result = update_species(species_id, species_update, current_user, db)
    species_cache.clear()
    return result


@router.post("/species/{species_id}/image", response_model=schemas.Species)
def upload_species_image_route(
    species_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_write),
):
    result = upload_image(species_id, image, db)
    species_cache.clear()
    return result


@router.delete("/species/{species_id}")
def delete_species_route(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_write),
):
    result = delete_species(species_id, current_user, db)
    species_cache.clear()
    return result
