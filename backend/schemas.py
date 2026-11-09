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
    # 图片只能走 /species/{id}/image 上传接口（有大小/格式校验），
    # 禁止通过 PUT 直接覆盖 image_url（exclude=True 使其不进 model_dump，前端传了也会被忽略）
    image_url: Optional[str] = Field(None, exclude=True)

    @field_validator('default_price', mode='before')
    @classmethod
    def check_price(cls, v):
        if v is None or v == '':
            raise ValueError('单价必须大于0')
        return v

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
    status: Optional[str] = Field("DRAFT", max_length=20)
    release_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=20)
    weekly_donation: Optional[float] = None
    alipay_amount: Optional[float] = None
    wechat_amount: Optional[float] = None
    suixi_amount: Optional[float] = None

    @field_validator('currency')
    @classmethod
    def check_currency(cls, v):
        if v != 'CNY':
            raise ValueError('币种仅支持 CNY')
        return v

    @field_validator('fee_type')
    @classmethod
    def check_fee_type(cls, v):
        if v != 'FIXED':
            raise ValueError('服务费类型仅支持 FIXED')
        return v

    @field_validator('status', mode='before')
    @classmethod
    def check_status(cls, v):
        # None 表示"由后端按放生日期自动判定"（批量导入路径），保持原语义
        if v is None or v == '':
            return None
        if v not in ('DRAFT', 'COMPLETED'):
            raise ValueError('单据状态仅支持 DRAFT/COMPLETED')
        return v

    @field_validator('payment_method', mode='before')
    @classmethod
    def coerce_payment_method(cls, v):
        if v is None or v == '':
            return None
        if v not in ('支付宝', '微信', '随喜放生'):
            raise ValueError('随喜类型仅支持：支付宝/微信/随喜放生')
        return v

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
    def serialize_release_date(self, v: Optional[date]) -> Optional[str]:
        if v is None:
            return None
        return v.strftime('%Y-%m-%d')

    @field_serializer('created_at')
    def serialize_created_at(self, v: datetime) -> str:
        return v.strftime('%Y-%m-%d %H:%M:%S')

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
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, v: datetime) -> str:
        return v.strftime('%Y-%m-%d %H:%M:%S')

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=100)


class BatchImportRow(BaseModel):
    name_zh: str = Field(..., max_length=100)
    weight: float = 0.0
    unit_price: float = 0.0
    fee_value: float = 0.0
    release_date: Optional[date] = None
    alipay_amount: Optional[float] = None
    wechat_amount: Optional[float] = None
    suixi_amount: Optional[float] = None
    payment_method: Optional[str] = Field(None, max_length=20)

    @field_validator('payment_method', mode='before')
    @classmethod
    def coerce_import_payment_method(cls, v):
        if v is None or v == '':
            return None
        if v not in ('支付宝', '微信', '随喜放生'):
            raise ValueError('随喜类型仅支持：支付宝/微信/随喜放生')
        return v

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
    # 覆盖模式下一次清空哪些放生日的数据（分片导入时由首片带上全量日期，避免跨片重复）
    replace_dates: Optional[list[date]] = None

class BatchImportResult(BaseModel):
    success_count: int
    skip_count: int
    # 不再回传完整 bills（会触发每行一次 species 懒加载 N+1，且前端只用数量/错误）
    affected_species_ids: list[int] = []
    errors: list[str] = []
