from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    role: str = "operator"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class SpeciesBase(BaseModel):
    name_zh: str
    default_unit: str
    default_price: float = 0.0
    image_url: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_note: Optional[str] = None
    release_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

class SpeciesCreate(SpeciesBase):
    pass

class SpeciesUpdate(SpeciesBase):
    pass

class Species(SpeciesBase):
    id: int

    class Config:
        from_attributes = True

class BillBase(BaseModel):
    species_id: int
    weight: float
    unit_price: float
    currency: str = "CNY"
    fee_type: str = "FIXED"
    fee_value: float
    status: str = "DRAFT"
    release_date: Optional[datetime] = None

class BillCreate(BillBase):
    pass

class Bill(BillBase):
    id: int
    user_id: int
    subtotal: float
    total_amount: float
    created_at: datetime
    species: Optional[Species] = None

    class Config:
        from_attributes = True

class AuditLogBase(BaseModel):
    bill_id: Optional[int] = None
    species_id: Optional[int] = None
    entity_type: str = "BILL"
    action: str
    old_data: Optional[str] = None
    new_data: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SyncRequest(BaseModel):
    date: str
