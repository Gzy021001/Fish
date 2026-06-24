import logging
from sqlalchemy import text, inspect
import os

import models
import auth
from database import engine, get_db

logger = logging.getLogger(__name__)


def ensure_db_schema_updates():
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "species" not in tables:
            logger.info("Species table does not exist yet, skipping manual column checks.")
            return

        with engine.begin() as conn:
            # Species 表检查
            existing = {col["name"] for col in inspector.get_columns("species")}
            if "image_url" not in existing:
                conn.execute(text("ALTER TABLE species ADD COLUMN image_url VARCHAR(255)"))
            if "default_price" not in existing:
                conn.execute(text("ALTER TABLE species ADD COLUMN default_price FLOAT DEFAULT 0.0"))
            if "supplier_name" not in existing:
                conn.execute(text("ALTER TABLE species ADD COLUMN supplier_name VARCHAR(200)"))
            if "supplier_note" not in existing:
                conn.execute(text("ALTER TABLE species ADD COLUMN supplier_note VARCHAR(500)"))

            # Audit Logs 表检查
            if "audit_logs" in tables:
                existing = {col["name"] for col in inspector.get_columns("audit_logs")}
                if "species_id" not in existing:
                    conn.execute(text("ALTER TABLE audit_logs ADD COLUMN species_id INTEGER"))
                if "entity_type" not in existing:
                    conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_type VARCHAR(50) DEFAULT 'BILL'"))

            # Bills 表检查
            if "bills" in tables:
                existing = {col["name"] for col in inspector.get_columns("bills")}
                if "status" not in existing:
                    conn.execute(text("ALTER TABLE bills ADD COLUMN status VARCHAR(20) DEFAULT 'DRAFT'"))
    except Exception as e:
        logger.error(f"Error during schema updates: {e}")


def init_seed_data():
    try:
        db = next(get_db())

        # 预设用户列表
        users_to_create = [
            {"username": "admin", "password": os.getenv("ADMIN_PASSWORD", "admin123"), "role": "admin"},
            {"username": "operator1", "password": "op123456", "role": "operator"},
            {"username": "operator2", "password": "op123456", "role": "operator"},
            {"username": "operator3", "password": "op123456", "role": "operator"},
        ]

        for user_info in users_to_create:
            if not db.query(models.User).filter(models.User.username == user_info["username"]).first():
                new_user = models.User(
                    username=user_info["username"],
                    password_hash=auth.get_password_hash(user_info["password"]),
                    role=user_info["role"],
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
