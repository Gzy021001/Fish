# ============================================================
#  Fish Price Platform — 后端 API 主入口
#  FastAPI + SQLite + SQLAlchemy + JWT
# ============================================================

from pathlib import Path
import json
import shutil
import uuid

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, text, cast, String
from typing import List
from datetime import datetime, timedelta

import models
import schemas
import auth
from database import engine, get_db, Base
from utils import (
    get_species_or_404,
    get_bill_or_404,
    calculate_bill_amounts,
    delete_species_image_file,
    BASE_DIR,
    UPLOAD_DIR,
    SPECIES_UPLOAD_DIR,
)

# ============================================================
#  应用初始化
# ============================================================

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fish Price Platform API")

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（品种图片上传目录）
UPLOAD_DIR.mkdir(exist_ok=True)
SPECIES_UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ============================================================
#  数据库 Schema 迁移（兼容已有数据的增量更新）
# ============================================================

def ensure_db_schema_updates():
    """确保数据库中包含所有必要字段，兼容旧版本数据库"""
    with engine.begin() as connection:
        # species 表字段补充
        columns = connection.execute(text("PRAGMA table_info(species)")).fetchall()
        column_names = {column[1] for column in columns}
        if "image_url" not in column_names:
            connection.execute(text("ALTER TABLE species ADD COLUMN image_url VARCHAR(255)"))
        if "default_price" not in column_names:
            connection.execute(text("ALTER TABLE species ADD COLUMN default_price FLOAT DEFAULT 0.0"))

        # audit_logs 表字段补充
        columns = connection.execute(text("PRAGMA table_info(audit_logs)")).fetchall()
        column_names = {column[1] for column in columns}
        if "species_id" not in column_names:
            connection.execute(text("ALTER TABLE audit_logs ADD COLUMN species_id INTEGER"))
        if "entity_type" not in column_names:
            connection.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_type VARCHAR(50) DEFAULT 'BILL'"))

        # bills 表字段补充
        columns = connection.execute(text("PRAGMA table_info(bills)")).fetchall()
        column_names = {column[1] for column in columns}
        if "status" not in column_names:
            connection.execute(text("ALTER TABLE bills ADD COLUMN status VARCHAR(20) DEFAULT 'DRAFT'"))


# ============================================================
#  认证相关端点
# ============================================================

@app.post("/api/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """登录获取 JWT Token"""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """获取当前登录用户信息"""
    return current_user


# ============================================================
#  品种 (Species) 端点
# ============================================================

@app.get("/api/species", response_model=List[schemas.Species])
def get_species(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取全部品种列表"""
    return db.query(models.Species).order_by(models.Species.id.asc()).all()


@app.get("/api/species/{species_id}", response_model=schemas.Species)
def get_species_detail(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取单个品种详情"""
    return get_species_or_404(species_id, db)


@app.post("/api/species", response_model=schemas.Species)
def create_species(
    species: schemas.SpeciesCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """新增品种"""
    # 价格校验
    if species.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    # 名称重复检查
    if db.query(models.Species).filter(models.Species.name_zh == species.name_zh).first():
        raise HTTPException(status_code=400, detail="Species already registered")

    # 创建品种
    new_species = models.Species(**species.model_dump())
    db.add(new_species)
    db.commit()
    db.refresh(new_species)

    # 记录审计日志
    log = models.AuditLog(
        species_id=new_species.id,
        entity_type="SPECIES",
        user_id=current_user.id,
        action="CREATE",
        old_data=None,
        new_data=json.dumps({
            "name_zh": new_species.name_zh,
            "default_unit": new_species.default_unit,
            "default_price": new_species.default_price
        })
    )
    db.add(log)
    db.commit()

    return new_species


@app.put("/api/species/{species_id}", response_model=schemas.Species)
def update_species(
    species_id: int,
    species_update: schemas.SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """更新品种信息"""
    # 价格校验
    if species_update.default_price <= 0:
        raise HTTPException(status_code=400, detail="单价必须大于0")

    species = get_species_or_404(species_id, db)

    # 名称重复检查（排除自身）
    if db.query(models.Species).filter(
        models.Species.name_zh == species_update.name_zh,
        models.Species.id != species_id
    ).first():
        raise HTTPException(status_code=400, detail="Species name already exists")

    # 保存旧数据用于审计
    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price
    }

    # 逐字段更新
    for field, value in species_update.model_dump().items():
        setattr(species, field, value)
    db.commit()
    db.refresh(species)

    # 仅在有实际变更时记录审计日志
    new_data = species_update.model_dump()
    if old_data != new_data:
        log = models.AuditLog(
            species_id=species.id,
            entity_type="SPECIES",
            user_id=current_user.id,
            action="UPDATE",
            old_data=json.dumps(old_data),
            new_data=json.dumps(new_data)
        )
        db.add(log)
        db.commit()

    return species


@app.post("/api/species/{species_id}/image", response_model=schemas.Species)
def upload_species_image(
    species_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """上传品种图片"""
    species = get_species_or_404(species_id, db)

    # 文件类型校验
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file")

    # 生成唯一文件名并保存
    extension = Path(image.filename or "").suffix.lower() or ".jpg"
    file_name = f"{species_id}_{uuid.uuid4().hex}{extension}"
    file_path = SPECIES_UPLOAD_DIR / file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # 删除旧图片 → 更新数据库
    delete_species_image_file(species.image_url)
    species.image_url = f"/uploads/species/{file_name}"
    db.commit()
    db.refresh(species)
    return species


@app.delete("/api/species/{species_id}")
def delete_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """删除品种"""
    species = get_species_or_404(species_id, db)

    # 检查是否有关联单据
    if db.query(models.Bill).filter(models.Bill.species_id == species_id).first():
        raise HTTPException(
            status_code=400,
            detail="This species is already used in bills and cannot be deleted"
        )

    old_data = {
        "name_zh": species.name_zh,
        "default_unit": species.default_unit,
        "default_price": species.default_price
    }

    # 删除图片文件 → 删除数据库记录
    delete_species_image_file(species.image_url)
    db.delete(species)

    # 记录审计日志
    log = models.AuditLog(
        species_id=species.id,
        entity_type="SPECIES",
        user_id=current_user.id,
        action="DELETE",
        old_data=json.dumps(old_data),
        new_data=None
    )
    db.add(log)
    db.commit()

    return {"message": "Species deleted successfully"}


# ============================================================
#  单据 (Billing) 端点
# ============================================================

@app.post("/api/bills", response_model=schemas.Bill)
def create_bill(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """新增单据"""
    # 参数校验
    if bill.weight <= 0 or bill.unit_price <= 0:
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    # 计算金额（统一使用共享函数）
    subtotal, fee, total_amount = calculate_bill_amounts(
        bill.weight, bill.unit_price, bill.fee_type, bill.fee_value
    )

    # 创建单据（初始状态为 DRAFT）
    new_bill = models.Bill(
        user_id=current_user.id,
        species_id=bill.species_id,
        weight=bill.weight,
        unit_price=bill.unit_price,
        currency=bill.currency,
        subtotal=subtotal,
        fee_type=bill.fee_type,
        fee_value=bill.fee_value,
        total_amount=total_amount,
        status="DRAFT"
    )
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)

    # 记录审计日志
    log = models.AuditLog(
        bill_id=new_bill.id,
        user_id=current_user.id,
        action="CREATE",
        old_data=None,
        new_data=json.dumps(bill.model_dump())
    )
    db.add(log)
    db.commit()

    return new_bill


@app.post("/api/bills/sync")
def sync_bills(
    payload: schemas.SyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """将指定日期的草稿单据同步为历史单据"""
    draft_bills = db.query(models.Bill).filter(models.Bill.status == "DRAFT").all()
    count = 0
    for bill in draft_bills:
        if bill.created_at and bill.created_at.isoformat().startswith(payload.date):
            bill.status = "COMPLETED"
            count += 1

            # 每条同步记录生成审计日志
            log = models.AuditLog(
                bill_id=bill.id,
                entity_type="BILL",
                user_id=current_user.id,
                action="UPDATE",
                old_data=json.dumps({"status": "DRAFT"}),
                new_data=json.dumps({"status": "COMPLETED"})
            )
            db.add(log)

    db.commit()
    return {"message": f"成功同步 {count} 条单据到历史记录", "count": count}


@app.get("/api/bills", response_model=List[schemas.Bill])
def get_bills(
    limit: int = 100,
    status: str = None,
    date: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取单据列表，支持按状态和日期筛选"""
    query = db.query(models.Bill).order_by(models.Bill.created_at.desc())
    if status:
        query = query.filter(models.Bill.status == status)
    if date:
        query = query.filter(cast(models.Bill.created_at, String).startswith(date))
    if limit > 0:
        query = query.limit(limit)
    return query.all()


@app.put("/api/bills/{bill_id}", response_model=schemas.Bill)
def update_bill(
    bill_id: int,
    bill_update: schemas.BillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """更新单据"""
    # 参数校验
    if bill_update.weight <= 0 or bill_update.unit_price <= 0:
        raise HTTPException(status_code=400, detail="重量和单价必须大于0")

    bill = get_bill_or_404(bill_id, db)

    # 保存旧数据用于审计
    old_data = {
        "species_id": bill.species_id,
        "weight": bill.weight,
        "unit_price": bill.unit_price,
        "currency": bill.currency,
        "fee_type": bill.fee_type,
        "fee_value": bill.fee_value
    }

    # 重新计算金额
    subtotal, fee, total_amount = calculate_bill_amounts(
        bill_update.weight, bill_update.unit_price, bill_update.fee_type, bill_update.fee_value
    )

    # 更新字段
    bill.species_id = bill_update.species_id
    bill.weight = bill_update.weight
    bill.unit_price = bill_update.unit_price
    bill.currency = bill_update.currency
    bill.fee_type = bill_update.fee_type
    bill.fee_value = bill_update.fee_value
    bill.status = bill_update.status
    bill.subtotal = subtotal
    bill.total_amount = total_amount

    db.commit()
    db.refresh(bill)

    # 仅在有实际变更时记录审计日志
    new_data = bill_update.model_dump()
    if old_data != new_data:
        log = models.AuditLog(
            bill_id=bill.id,
            entity_type="BILL",
            user_id=current_user.id,
            action="UPDATE",
            old_data=json.dumps(old_data),
            new_data=json.dumps(new_data)
        )
        db.add(log)
        db.commit()

    return bill


@app.delete("/api/bills/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """删除单据"""
    bill = get_bill_or_404(bill_id, db)

    # 保存旧数据用于审计
    old_data = {
        "species_id": bill.species_id,
        "weight": bill.weight,
        "unit_price": bill.unit_price,
        "currency": bill.currency,
        "fee_type": bill.fee_type,
        "fee_value": bill.fee_value
    }

    db.delete(bill)

    # 记录审计日志
    log = models.AuditLog(
        bill_id=bill.id,
        entity_type="BILL",
        user_id=current_user.id,
        action="DELETE",
        old_data=json.dumps(old_data),
        new_data=None
    )
    db.add(log)
    db.commit()

    return {"message": "Bill deleted successfully"}


# ============================================================
#  审计日志查询端点
# ============================================================

@app.get("/api/logs", response_model=List[schemas.AuditLog])
def get_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取全部审计日志"""
    return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).all()


@app.get("/api/logs/bill/{bill_id}", response_model=List[schemas.AuditLog])
def get_logs_for_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取指定单据的操作日志"""
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.bill_id == bill_id, models.AuditLog.entity_type == "BILL")
        .order_by(models.AuditLog.created_at.desc())
        .all()
    )


@app.get("/api/logs/species/{species_id}", response_model=List[schemas.AuditLog])
def get_logs_for_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取指定品种的操作日志"""
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.species_id == species_id, models.AuditLog.entity_type == "SPECIES")
        .order_by(models.AuditLog.created_at.desc())
        .all()
    )


# ============================================================
#  统计端点
# ============================================================

@app.get("/api/stats/price-trend")
def get_price_trend(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """获取指定品种近30天价格趋势"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    species = get_species_or_404(species_id, db)

    # 按日期分组，计算日均价
    results = (
        db.query(
            func.date(models.Bill.created_at).label('date'),
            func.avg(models.Bill.unit_price).label('avg_price')
        )
        .filter(
            models.Bill.species_id == species.id,
            models.Bill.created_at >= thirty_days_ago
        )
        .group_by(func.date(models.Bill.created_at))
        .all()
    )

    trend = [{"date": str(r.date), "avg_price": float(r.avg_price)} for r in results]
    return trend


# ============================================================
#  应用启动事件
# ============================================================

@app.on_event("startup")
def startup_event():
    """启动时执行数据库迁移，插入默认测试数据"""
    ensure_db_schema_updates()

    db = next(get_db())

    # 插入默认管理员账号
    if not db.query(models.User).first():
        admin = models.User(
            username="admin",
            password_hash=auth.get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()

    # 插入默认品种
    if not db.query(models.Species).first():
        s1 = models.Species(name_zh="东星斑", default_unit="斤")
        s2 = models.Species(name_zh="老虎斑", default_unit="斤")
        db.add_all([s1, s2])
        db.commit()
