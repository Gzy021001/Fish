from sqlalchemy import text

import models
import auth
from database import engine, get_db


def ensure_db_schema_updates():
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(species)")).fetchall()
        column_names = {column[1] for column in columns}
        if "image_url" not in column_names:
            connection.execute(text("ALTER TABLE species ADD COLUMN image_url VARCHAR(255)"))
        if "default_price" not in column_names:
            connection.execute(text("ALTER TABLE species ADD COLUMN default_price FLOAT DEFAULT 0.0"))
        if "supplier_name" not in column_names:
            connection.execute(text("ALTER TABLE species ADD COLUMN supplier_name VARCHAR(200)"))
        if "supplier_note" not in column_names:
            connection.execute(text("ALTER TABLE species ADD COLUMN supplier_note VARCHAR(500)"))

        columns = connection.execute(text("PRAGMA table_info(audit_logs)")).fetchall()
        column_names = {column[1] for column in columns}
        if "species_id" not in column_names:
            connection.execute(text("ALTER TABLE audit_logs ADD COLUMN species_id INTEGER"))
        if "entity_type" not in column_names:
            connection.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_type VARCHAR(50) DEFAULT 'BILL'"))

        columns = connection.execute(text("PRAGMA table_info(bills)")).fetchall()
        column_names = {column[1] for column in columns}
        if "status" not in column_names:
            connection.execute(text("ALTER TABLE bills ADD COLUMN status VARCHAR(20) DEFAULT 'DRAFT'"))


def init_seed_data():
    db = next(get_db())

    if not db.query(models.User).first():
        admin = models.User(
            username="admin",
            password_hash=auth.get_password_hash("admin123"),
            role="admin",
        )
        db.add(admin)
        db.commit()

    if not db.query(models.Species).first():
        s1 = models.Species(name_zh="东星斑", default_unit="斤")
        s2 = models.Species(name_zh="老虎斑", default_unit="斤")
        db.add_all([s1, s2])
        db.commit()

    db.close()


def run():
    ensure_db_schema_updates()
    init_seed_data()
