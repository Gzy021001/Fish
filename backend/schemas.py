from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime, date
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

    @field_serializer('release_date')
    def serialize_release_date(self, v: Optional[datetime]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime('%Y-%m-%d')

class SpeciesInBill(BaseModel):
    id: int
    name_zh: str
    default_unit: str
    
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
    species: Optional[SpeciesInBill] = None

    class Config:
        from_attributes = True

    @field_serializer('release_date')
    def serialize_release_date(self, v: Optional[datetime]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime('%Y-%m-%d')

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


class BatchImportRow(BaseModel):
    name_zh: str
    weight: float = 0.0
    unit_price: float = 0.0
    fee_value: float = 0.0
    release_date: Optional[datetime] = None

    @field_validator('release_date', mode='before')
    @classmethod
    def coerce_release_date(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            return v
        s = str(v).strip()
        for fmt in ('%Y-%m-%d', '%Y-%m', '%Y/%m/%d', '%Y.%m.%d'):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        # Last resort: try ISO format
        try:
            return datetime.fromisoformat(s)
        except (ValueError, TypeError):
            return None

class BatchImportRequest(BaseModel):
    rows: list[BatchImportRow]
    replace: bool = False  # If True, delete existing bills with same release_date before import

class BatchImportResult(BaseModel):
    success_count: int
    skip_count: int
    bills: list[Bill]
    errors: list[str] = []

