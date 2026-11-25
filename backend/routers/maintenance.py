"""一次性维护接口：补 paid_amount 列与 week_expenses 表（仅管理员，跑完即删）。

用途：线上 Vercel 环境把迁移做进冷启动后仍报 ProgrammingError，需要逐条看 DDL 的真实报错。
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import models
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class PaidRow(BaseModel):
    date: str
    weight: float
    unit_price: float
    paid: float


class ExpenseRow(BaseModel):
    date: str
    name: str = Field(..., max_length=20)
    amount: float


class PaidBackfillRequest(BaseModel):
    rows: list[PaidRow] = Field(default_factory=list, max_length=5000)
    expenses: list[ExpenseRow] = Field(default_factory=list, max_length=1000)

_STATEMENTS = [
    (
        "add_paid_amount",
        "ALTER TABLE bills ADD COLUMN IF NOT EXISTS paid_amount NUMERIC(12,2)",
    ),
    (
        "create_week_expenses",
        "CREATE TABLE IF NOT EXISTS week_expenses ("
        "id SERIAL PRIMARY KEY, release_date DATE, name VARCHAR(20), "
        "amount NUMERIC(12,2), created_at TIMESTAMP WITHOUT TIME ZONE, "
        "is_deleted BOOLEAN DEFAULT FALSE)",
    ),
    (
        "index_release_date",
        "CREATE INDEX IF NOT EXISTS ix_week_expenses_release_date ON week_expenses (release_date)",
    ),
    (
        "index_is_deleted",
        "CREATE INDEX IF NOT EXISTS ix_week_expenses_is_deleted ON week_expenses (is_deleted)",
    ),
]


@router.post("/schema-fix")
def schema_fix(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """逐条执行补丁，返回每条的成功/报错，便于定位权限或语法问题。"""
    results = []
    for name, sql in _STATEMENTS:
        try:
            db.execute(text(sql))
            db.commit()
            results.append({"name": name, "ok": True, "error": None})
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.warning("schema_fix %s failed: %s", name, exc)
            results.append({"name": name, "ok": False, "error": str(exc)[:300]})
    # 顺带回报当前列/表是否存在，确认补丁是否真的生效
    try:
        has_column = bool(
            db.execute(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'bills' AND column_name = 'paid_amount'"
                )
            ).first()
        )
        has_table = bool(
            db.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'week_expenses'"
                )
            ).first()
        )
        current_user_name = db.execute(text("select current_user")).scalar()
    except Exception as exc:  # noqa: BLE001
        has_column = has_table = False
        current_user_name = f"error: {exc}"
    return {
        "results": results,
        "has_paid_amount": has_column,
        "has_week_expenses": has_table,
        "db_user": current_user_name,
    }


@router.post("/backfill-paid")
def backfill_paid(
    payload: PaidBackfillRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """按（放生日期 + 重量 + 单价）把模板「实付」写进对应单据，并重建这些日期的车费/船费。"""
    updated = 0
    missing = 0
    used_ids: set[int] = set()
    for row in payload.rows:
        candidates = db.execute(
            text(
                "SELECT id FROM bills WHERE release_date = :d AND is_deleted = false "
                "AND abs(weight - :w) < 0.02 AND abs(unit_price - :p) < 0.02 ORDER BY id"
            ),
            {"d": row.date, "w": row.weight, "p": row.unit_price},
        ).scalars().all()
        target = next((cid for cid in candidates if cid not in used_ids), None)
        if target is None:
            missing += 1
            continue
        used_ids.add(target)
        db.execute(
            text("UPDATE bills SET paid_amount = :paid WHERE id = :id"),
            {"paid": row.paid, "id": target},
        )
        updated += 1

    dates = sorted({e.date for e in payload.expenses})
    for d in dates:
        db.execute(text("DELETE FROM week_expenses WHERE release_date = :d"), {"d": d})
    for exp in payload.expenses:
        db.execute(
            text(
                "INSERT INTO week_expenses (release_date, name, amount, created_at, is_deleted) "
                "VALUES (:d, :n, :a, now(), false)"
            ),
            {"d": exp.date, "n": exp.name, "a": exp.amount},
        )

    db.commit()
    return {"updated": updated, "missing": missing, "expenses": len(payload.expenses)}
