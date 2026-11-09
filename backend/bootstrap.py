import logging
from sqlalchemy import text, inspect, bindparam
import os

import models
import auth
from database import engine, get_db

logger = logging.getLogger(__name__)

# 各表缺列时补列的清单（列名 -> ALTER SQL）；与历史迁移保持一致
_COLUMN_FIXES = {
    "species": [
        ("image_url", "ALTER TABLE species ADD COLUMN image_url VARCHAR(255)"),
        ("default_price", "ALTER TABLE species ADD COLUMN default_price FLOAT DEFAULT 0.0"),
        ("supplier_name", "ALTER TABLE species ADD COLUMN supplier_name VARCHAR(200)"),
        ("supplier_note", "ALTER TABLE species ADD COLUMN supplier_note VARCHAR(500)"),
        ("is_deleted", "ALTER TABLE species ADD COLUMN is_deleted BOOLEAN DEFAULT {false}"),
    ],
    "audit_logs": [
        ("species_id", "ALTER TABLE audit_logs ADD COLUMN species_id INTEGER"),
        ("entity_type", "ALTER TABLE audit_logs ADD COLUMN entity_type VARCHAR(50) DEFAULT 'BILL'"),
    ],
    "bills": [
        ("status", "ALTER TABLE bills ADD COLUMN status VARCHAR(20) DEFAULT 'DRAFT'"),
        ("is_deleted", "ALTER TABLE bills ADD COLUMN is_deleted BOOLEAN DEFAULT {false}"),
        ("payment_method", "ALTER TABLE bills ADD COLUMN payment_method VARCHAR(20)"),
        ("weekly_donation", "ALTER TABLE bills ADD COLUMN weekly_donation NUMERIC(12,2)"),
        ("alipay_amount", "ALTER TABLE bills ADD COLUMN alipay_amount NUMERIC(12,2)"),
        ("wechat_amount", "ALTER TABLE bills ADD COLUMN wechat_amount NUMERIC(12,2)"),
        ("suixi_amount", "ALTER TABLE bills ADD COLUMN suixi_amount NUMERIC(12,2)"),
    ],
    "users": [
        ("must_change_password", "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT {false}"),
    ],
}


def _pg_table_columns(conn, table_names):
    """PostgreSQL：一条 SQL 取回所有目标表的列集合，替代 inspector 逐表往返。"""
    stmt = text(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name IN :names"
    ).bindparams(bindparam("names", expanding=True))
    rows = conn.execute(stmt, {"names": tuple(table_names)}).fetchall()
    result = {}
    for table_name, column_name in rows:
        result.setdefault(table_name, set()).add(column_name)
    return result


def ensure_db_schema_updates():
    try:
        is_pg = engine.dialect.name == "postgresql"
        # PostgreSQL 布尔列默认值用 FALSE；SQLite 用 0（方言差异）
        false_default = "FALSE" if is_pg else "0"

        with engine.begin() as conn:
            if is_pg:
                # 远程库：单条 SQL 拿全部目标表的列（少则 1 次往返，多则只有缺列时补 ALTER）
                tables_by_cols = _pg_table_columns(conn, list(_COLUMN_FIXES.keys()))
                if "species" not in tables_by_cols:
                    logger.info("Species table does not exist yet, skipping manual column checks.")
                    return
                for table_name, fixes in _COLUMN_FIXES.items():
                    if table_name not in tables_by_cols:
                        continue  # 表不存在则跳过该表的列检查（与历史行为一致）
                    existing = tables_by_cols[table_name]
                    for column_name, ddl in fixes:
                        if column_name not in existing:
                            conn.execute(text(ddl.format(false=false_default)))
            else:
                # SQLite：本地库，inspector 路径足够快
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                if "species" not in tables:
                    logger.info("Species table does not exist yet, skipping manual column checks.")
                    return
                for table_name, fixes in _COLUMN_FIXES.items():
                    if table_name not in tables:
                        continue
                    existing = {col["name"] for col in inspector.get_columns(table_name)}
                    for column_name, ddl in fixes:
                        if column_name not in existing:
                            conn.execute(text(ddl.format(false=false_default)))
    except Exception as e:
        logger.error(f"Error during schema updates: {e}")


def init_seed_data():
    try:
        db = next(get_db())
        # 护栏：非 SQLite（如误连生产库）默认不种初始账号，防止把 admin/admin123 种进生产库；
        # 确需在远程库初始化时显式设 ALLOW_SEED=true。
        if engine.url.get_backend_name() != "sqlite" and not os.getenv("ALLOW_SEED"):
            db.close()
            logger.info("Non-SQLite database detected, skipping seed data (set ALLOW_SEED=true to override).")
            return

        # 一条 COUNT 替代四次逐用户 SELECT，减少 DB 往返
        user_count = db.query(models.User).count()
        if user_count > 0:
            db.close()
            logger.info("Users already exist, skipping seed data.")
            return

        users_to_create = [
            {"username": "admin", "password": os.getenv("ADMIN_PASSWORD", "admin123"), "role": "admin"},
            {"username": "operator1", "password": "op123456", "role": "operator"},
            {"username": "operator2", "password": "op123456", "role": "operator"},
            {"username": "operator3", "password": "op123456", "role": "operator"},
        ]

        for user_info in users_to_create:
            new_user = models.User(
                username=user_info["username"],
                password_hash=auth.get_password_hash(user_info["password"]),
                role=user_info["role"],
                must_change_password=True,  # 初始账号首次登录强制改密
            )
            db.add(new_user)
            logger.info(f"User {user_info['username']} created.")
        
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Error during seed data initialization: {e}")


def run():
    logger.info("Running bootstrap...")
    ensure_db_schema_updates()
    init_seed_data()
    logger.info("Bootstrap finished.")
