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

        if not db.query(models.User).filter(models.User.username == "admin").first():
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin = models.User(
                username="admin",
                password_hash=auth.get_password_hash(admin_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
            logger.info("Admin user created.")

        if not db.query(models.Species).first():
            s1 = models.Species(name_zh="东星斑", default_unit="斤")
            s2 = models.Species(name_zh="老虎斑", default_unit="斤")
            db.add_all([s1, s2])
            db.commit()
            logger.info("Seed species created.")

        db.close()
    except Exception as e:
        logger.error(f"Error during seed data initialization: {e}")


def run():
    logger.info("Running bootstrap...")
    ensure_db_schema_updates()
    init_seed_data()
    logger.info("Bootstrap finished.")
