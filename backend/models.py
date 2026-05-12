from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(128))
    role = Column(String(20), default="operator")

class Species(Base):
    __tablename__ = "species"
    id = Column(Integer, primary_key=True, index=True)
    name_zh = Column(String(100), unique=True, index=True)
    default_unit = Column(String(20), default="kg")
    default_price = Column(Float, default=0.0)
    image_url = Column(String(255), nullable=True)
    supplier_name = Column(String(200), nullable=True)
    supplier_note = Column(String(500), nullable=True)
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    species_id = Column(Integer, ForeignKey("species.id"))
    weight = Column(Float)
    unit_price = Column(Float)
    currency = Column(String(10))
    subtotal = Column(Float)
    fee_type = Column(String(20), default="FIXED")
    fee_value = Column(Float)
    total_amount = Column(Float)
    status = Column(String(20), default="DRAFT")
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    species = relationship("Species")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=True)
    entity_type = Column(String(50), default="BILL") # "BILL" or "SPECIES"
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50)) # "CREATE", "UPDATE", "DELETE"
    old_data = Column(String, nullable=True) # JSON string
    new_data = Column(String, nullable=True) # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
