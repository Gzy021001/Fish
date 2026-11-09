import math
import time
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
import auth
from database import get_db

router = APIRouter(prefix="/api", tags=["auth"])

# ---- 登录限流（进程内内存实现，不引入外部依赖）----
# 同 IP+用户名：累计 5 次失败首次锁定 30 秒；解锁后再失败，锁定时长翻倍递增
# （60s/120s/240s/480s），封顶 15 分钟。登录成功后计数清零。
_LOGIN_MAX_FAILS = 5
_LOGIN_FIRST_LOCK_SECONDS = 30
_LOGIN_LOCK_MAX_SECONDS = 15 * 60
# key: "ip|username" -> {"fails": n, "lock_until": t, "lock_step": k}
_login_failures: dict = {}
# 防止恶意随机用户名把内存字典无限撑大：超过上限先清过期项，仍超限则淘汰最早插入的一半
_LOGIN_FAILURES_MAX_KEYS = 10000


def _prune_login_failures():
    if len(_login_failures) <= _LOGIN_FAILURES_MAX_KEYS:
        return
    now = time.time()
    expired = [k for k, e in _login_failures.items() if e["lock_until"] and e["lock_until"] < now]
    for k in expired:
        _login_failures.pop(k, None)
    if len(_login_failures) > _LOGIN_FAILURES_MAX_KEYS:
        overflow = len(_login_failures) - _LOGIN_FAILURES_MAX_KEYS
        for k in list(_login_failures)[:overflow]:
            _login_failures.pop(k, None)


def _login_key(username: str, request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    return f"{ip}|{username.strip().lower()}"


def _login_lock_remaining(key: str) -> int:
    entry = _login_failures.get(key)
    if not entry:
        return 0
    if entry["lock_until"] and time.time() < entry["lock_until"]:
        return math.ceil(entry["lock_until"] - time.time())
    return 0


def _record_login_failure(key: str):
    _prune_login_failures()
    entry = _login_failures.get(key)
    if not entry:
        entry = {"fails": 0, "lock_until": 0.0, "lock_step": 0}
        _login_failures[key] = entry
    entry["fails"] += 1
    # 累计失败达到阈值且当前未锁定 → 触发新一轮锁定，时长随轮次翻倍递增
    if entry["fails"] >= _LOGIN_MAX_FAILS and time.time() >= entry["lock_until"]:
        entry["lock_step"] += 1
        duration = min(
            _LOGIN_FIRST_LOCK_SECONDS * (2 ** (entry["lock_step"] - 1)),
            _LOGIN_LOCK_MAX_SECONDS,
        )
        entry["lock_until"] = time.time() + duration


def _clear_login_failures(key: str):
    _login_failures.pop(key, None)


@router.post("/register", response_model=schemas.User)
def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可创建用户")

    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    if not user.username or not user.username.strip():
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要6个字符")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username.strip(),
        password_hash=hashed_password,
        role=user.role if user.role in ("admin", "operator") else "operator",
        must_change_password=True,  # 管理员新建的账号同样首次登录强制改密
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户名已存在")
        
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    key = _login_key(form_data.username, request)
    remaining = _login_lock_remaining(key)
    if remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请 {remaining} 秒后再试",
        )

    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        _record_login_failure(key)
        entry = _login_failures[key]
        if time.time() < entry["lock_until"]:
            detail = f"登录失败次数过多，请 {_login_lock_remaining(key)} 秒后再试"
        else:
            detail = f"用户名或密码错误（剩余尝试次数 {_LOGIN_MAX_FAILS - entry['fails']}）"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_login_failures(key)

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role, "mcp": bool(user.must_change_password)},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要6个字符")

    current_user.password_hash = auth.get_password_hash(payload.password)
    current_user.must_change_password = False
    db.commit()
    return {"message": "密码修改成功"}
