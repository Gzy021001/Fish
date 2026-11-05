"""统计看板聚合服务。

看板原先由前端拉取整年全部单据再聚合（`/bills?page_size=-1`），数据量随年份线性增长，
既慢又违反“聚合放后端”的约定。这里改为后端 GROUP BY 聚合，只返回看板需要的三个维度：
  - totals          年合计（重量 / 金额 / 单据数）
  - by_date         按放生日期汇总（重量 / 金额）
  - by_date_species 按放生日期 + 品种汇总（重量，供分类走势与饼图使用）
  - available_years 有单据的年份列表（供年份筛选）
放生日期口径与列表一致：单据放生日期缺失时回退到品种放生日期。
"""
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def _bill_day_expr():
    """放生日期表达式：单据日期优先，缺失时回退品种日期（与列表/导出口径一致）。"""
    return func.coalesce(models.Bill.release_date, models.Species.release_date)


def _year_bounds(year: int):
    return date(year, 1, 1), date(year + 1, 1, 1)


def get_available_years(db: Session) -> list[int]:
    day = _bill_day_expr()
    rows = (
        db.query(func.extract("year", day).label("y"))
        .join(models.Species, models.Bill.species_id == models.Species.id)
        .filter(models.Bill.is_deleted.is_(False))
        .filter(models.Bill.status == "COMPLETED")
        .filter(day.isnot(None))
        .distinct()
        .all()
    )
    years = sorted({int(r.y) for r in rows if r.y is not None})
    return years


def get_dashboard_summary(db: Session, year: int) -> dict:
    start, end = _year_bounds(year)
    day = _bill_day_expr()
    # 口径：只看已归档（COMPLETED）单据，草稿不计入看板
    base_filters = (
        models.Bill.is_deleted.is_(False),
        models.Bill.status == "COMPLETED",
        day >= start,
        day < end,
    )

    by_date_rows = (
        db.query(
            day.label("day"),
            func.sum(models.Bill.weight).label("weight"),
            func.sum(models.Bill.total_amount).label("amount"),
            func.count(models.Bill.id).label("cnt"),
        )
        .join(models.Species, models.Bill.species_id == models.Species.id)
        .filter(*base_filters)
        .group_by(day)
        .order_by(day)
        .all()
    )

    by_date = [
        {
            "date": r.day.strftime("%Y-%m-%d"),
            "weight": round(float(r.weight or 0), 2),
            "amount": round(float(r.amount or 0), 2),
        }
        for r in by_date_rows
    ]

    by_date_species_rows = (
        db.query(
            day.label("day"),
            models.Bill.species_id.label("species_id"),
            func.sum(models.Bill.weight).label("weight"),
        )
        .join(models.Species, models.Bill.species_id == models.Species.id)
        .filter(*base_filters)
        .group_by(day, models.Bill.species_id)
        .order_by(day)
        .all()
    )

    by_date_species = [
        {
            "date": r.day.strftime("%Y-%m-%d"),
            "species_id": int(r.species_id),
            "weight": round(float(r.weight or 0), 2),
        }
        for r in by_date_species_rows
        if r.species_id is not None
    ]

    total_weight = round(sum(d["weight"] for d in by_date), 2)
    total_amount = round(sum(d["amount"] for d in by_date), 2)
    bill_count = sum(int(r.cnt or 0) for r in by_date_rows)

    return {
        "year": year,
        "available_years": get_available_years(db),
        "totals": {
            "weight": total_weight,
            "amount": total_amount,
            "bill_count": bill_count,
        },
        "by_date": by_date,
        "by_date_species": by_date_species,
    }
