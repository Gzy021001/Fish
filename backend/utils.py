from pathlib import Path
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
import models

BASE_DIR = Path(__file__).resolve().parent
if os.getenv("VERCEL"):
    UPLOAD_DIR = Path("/tmp/uploads")
else:
    UPLOAD_DIR = BASE_DIR / "uploads"
SPECIES_UPLOAD_DIR = UPLOAD_DIR / "species"


def get_bill_or_404(bill_id: int, db: Session):
    """按 ID 查找单据，不存在则返回 404"""
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="未找到该单据")
    return bill


# ============================================================
#  业务计算函数
# ============================================================

def calculate_bill_amounts(weight: float, unit_price: float, fee_value: float):
    subtotal = round(weight * unit_price, 2)
    fee = round(fee_value, 2)
    total_amount = round(subtotal + fee, 2)
    return subtotal, fee, total_amount


# ============================================================
#  文件处理函数
# ============================================================

def delete_species_image_file(image_url: str | None):
    """删除品种图片文件"""
    if not image_url:
        return
    filename = Path(image_url).name
    if not filename:
        return
    image_path = (SPECIES_UPLOAD_DIR / filename).resolve()
    if not str(image_path).startswith(str(SPECIES_UPLOAD_DIR.resolve())):
        return
    if image_path.exists() and image_path.is_file():
        image_path.unlink()
