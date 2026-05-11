import json
from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session

import models


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def record_create(
    db: Session,
    entity_type: str,
    user_id: int,
    data: dict,
    *,
    bill_id: Optional[int] = None,
    species_id: Optional[int] = None,
):
    log = models.AuditLog(
        bill_id=bill_id,
        species_id=species_id,
        entity_type=entity_type,
        user_id=user_id,
        action="CREATE",
        old_data=None,
        new_data=json.dumps(data, default=_json_default),
    )
    db.add(log)


def record_update(
    db: Session,
    entity_type: str,
    user_id: int,
    old_data: dict,
    new_data: dict,
    *,
    bill_id: Optional[int] = None,
    species_id: Optional[int] = None,
):
    if old_data == new_data:
        return
    log = models.AuditLog(
        bill_id=bill_id,
        species_id=species_id,
        entity_type=entity_type,
        user_id=user_id,
        action="UPDATE",
        old_data=json.dumps(old_data, default=_json_default),
        new_data=json.dumps(new_data, default=_json_default),
    )
    db.add(log)


def record_delete(
    db: Session,
    entity_type: str,
    user_id: int,
    old_data: dict,
    *,
    bill_id: Optional[int] = None,
    species_id: Optional[int] = None,
):
    log = models.AuditLog(
        bill_id=bill_id,
        species_id=species_id,
        entity_type=entity_type,
        user_id=user_id,
        action="DELETE",
        old_data=json.dumps(old_data, default=_json_default),
        new_data=None,
    )
    db.add(log)
