from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Boolean, Date, DateTime, Text, Index
from sqlalchemy.orm import relationship
from datetime import date, datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(128))
    role = Column(String(20), default="operator")
    must_change_password = Column(Boolean, default=False)

class Species(Base):
    __tablename__ = "species"
    id = Column(Integer, primary_key=True, index=True)
    name_zh = Column(String(100), unique=True, index=True)
    default_unit = Column(String(20), default="kg")
    default_price = Column(Numeric(12, 2), default=0)
    image_url = Column(Text, nullable=True)
    supplier_name = Column(String(200), nullable=True)
    supplier_note = Column(String(500), nullable=True)
    release_date = Column(Date, nullable=True)
    created_at = Column(Date, default=date.today)
    is_deleted = Column(Boolean, default=False, index=True)

class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (
        Index("ix_bills_species_release", "species_id", "release_date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    species_id = Column(Integer, ForeignKey("species.id"), index=True)
    weight = Column(Numeric(12, 2))
    unit_price = Column(Numeric(12, 2))
    # 原始计价单位：模板里按「件/个」报价的行（如「蛏子（件）」「带子（个）」）原样记下来，
    # 导出时才能还原成「蛏子（件） 2 件 × 120 元/件」；None 表示按斤（系统默认）。
    unit = Column(String(10), nullable=True)
    # 1 件/个 合多少斤，配合 unit 还原导出数量/单价（金额不变）
    unit_jin = Column(Numeric(10, 4), nullable=True)
    currency = Column(String(10))
    subtotal = Column(Numeric(12, 2))
    fee_type = Column(String(20), default="FIXED")
    fee_value = Column(Numeric(12, 2))
    total_amount = Column(Numeric(12, 2))
    status = Column(String(20), default="DRAFT", index=True)
    release_date = Column(Date, nullable=True, index=True)
    payment_method = Column(String(20), nullable=True)
    weekly_donation = Column(Numeric(12, 2), nullable=True)
    alipay_amount = Column(Numeric(12, 2), nullable=True)
    wechat_amount = Column(Numeric(12, 2), nullable=True)
    suixi_amount = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    is_deleted = Column(Boolean, default=False, index=True)

    user = relationship("User")
    species = relationship("Species")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="SET NULL"), nullable=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = Column(String(50), default="BILL", index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), index=True)
    old_data = Column(String, nullable=True)
    new_data = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
