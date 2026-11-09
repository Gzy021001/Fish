from datetime import datetime, timedelta, timezone
import os
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
from database import get_db

_DEV_SECRET_KEY = "dunhuang-fish-platform-super-secret-key"

# 未改密用户只放行这两个接口（改密本身 + 查询自身信息），其余一律 403
_PASSWORD_CHANGE_EXEMPT_PATHS = {"/api/change-password", "/api/me"}


def _is_production() -> bool:
    return any(
        os.getenv(k)
        for k in ("VERCEL", "RENDER", "RAILWAY_ENVIRONMENT", "RAILWAY_SERVICE_ID")
    )


SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if _is_production():
        raise RuntimeError(
            "JWT_SECRET_KEY 未设置：生产环境禁止使用默认密钥，请在部署平台配置 JWT_SECRET_KEY"
        )
    SECRET_KEY = _DEV_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def verify_password(plain_password, hashed_password):
    if plain_password is None or hashed_password is None:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False

def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份信息",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception

    # 未改密的初始账号只能访问改密页相关接口（后端强制，前端路由守卫只是 UI 辅助）
    if user.must_change_password and request.url.path not in _PASSWORD_CHANGE_EXEMPT_PATHS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先修改初始密码后再使用系统",
        )
    return user

def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：仅管理员可执行此操作",
        )
    return current_user


def require_write(current_user: models.User = Depends(get_current_user)):
    """写操作依赖：非 admin 账号为只读，禁止新增/修改/删除（业务约定：只有 admin 能改数据）。"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：非管理员账号为只读，不能新增、修改或删除数据",
        )
    return current_user
