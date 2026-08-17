from pydantic import BaseModel, field_serializer, field_validator, Field
from datetime import datetime, date
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    role: str = Field("operator", max_length=20)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class SpeciesBase(BaseModel):
    name_zh: str = Field(..., max_length=100)
    default_unit: str = Field(..., max_length=20)
    default_price: float = 0.0
    image_url: Optional[str] = None
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_note: Optional[str] = Field(None, max_length=500)
    release_date: Optional[date] = None
    created_at: Optional[date] = None

class SpeciesCreate(SpeciesBase):
    pass

class SpeciesUpdate(SpeciesBase):
    pass

class Species(SpeciesBase):
    id: int

    class Config:
        from_attributes = True

    @field_serializer('release_date')
    def serialize_release_date(self, v: Optional[date]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime('%Y-%m-%d')

class SpeciesInBill(BaseModel):
    id: int
    name_zh: str
    default_unit: str
    release_date: Optional[date] = None
    
    class Config:
        from_attributes = True

    @field_serializer('release_date')
    def serialize_release_date(self, v: Optional[date]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime('%Y-%m-%d')

class BillBase(BaseModel):
    species_id: int
    weight: float
    unit_price: float
    currency: str = Field("CNY", max_length=10)
    fee_type: str = Field("FIXED", max_length=20)
    fee_value: float
    status: str = Field("DRAFT", max_length=20)
    release_date: Optional[date] = None

class BillCreate(BillBase):
    pass

class Bill(BillBase):
    id: int
    user_id: int
    subtotal: float
    total_amount: float
    created_at: date
    species: Optional[SpeciesInBill] = None

    class Config:
        from_attributes = True

    @field_serializer('release_date')
    def serialize_release_date(self, v: Optional[date]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime('%Y-%m-%d')

    @field_serializer('created_at')
    def serialize_created_at(self, v: date) -> str:
        return v.strftime('%Y-%m-%d')

class AuditLogBase(BaseModel):
    bill_id: Optional[int] = None
    species_id: Optional[int] = None
    entity_type: str = Field("BILL", max_length=50)
    action: str = Field(..., max_length=50)
    old_data: Optional[str] = None
    new_data: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SyncRequest(BaseModel):
    date: str

class ArchiveRequest(BaseModel):
    bill_ids: list[int]


class BatchImportRow(BaseModel):
    name_zh: str = Field(..., max_length=100)
    weight: float = 0.0
    unit_price: float = 0.0
    fee_value: float = 0.0
    release_date: Optional[date] = None

    @field_validator('release_date', mode='before')
    @classmethod
    def coerce_release_date(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, date):
            return v
        s = str(v).strip()
        for fmt in ('%Y-%m-%d', '%Y-%m', '%Y/%m/%d', '%Y.%m.%d'):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s).date()
        except (ValueError, TypeError):
            return None

class BatchImportRequest(BaseModel):
    rows: list[BatchImportRow] = Field(..., max_length=5000)
    replace: bool = False

class BatchImportResult(BaseModel):
    success_count: int
    skip_count: int
    bills: list[Bill]
    errors: list[str] = []
