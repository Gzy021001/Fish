import json
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

import models


def _json_default(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
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


def record_replace(
    db: Session,
    entity_type: str,
    user_id: int,
    *,
    details: dict,
):
    """批量导入「覆盖同日已有单据」的汇总审计：一条记录写清被软删的日期与数量。

    覆盖会一次性软删除整日单据，逐条写 DELETE 会刷屏且引用关系复杂，
    这里用 REPLACE 动作记录汇总信息，保留"谁在何时覆盖了哪些日期"的追溯链。
    """
    log = models.AuditLog(
        bill_id=None,
        species_id=None,
        entity_type=entity_type,
        user_id=user_id,
        action="REPLACE",
        old_data=json.dumps(details, default=_json_default),
        new_data=None,
    )
    db.add(log)
