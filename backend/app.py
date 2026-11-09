import logging
import traceback
import os
import time
import json
import urllib.request
import asyncio
import threading
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from database import engine, Base
import bootstrap
from sqlalchemy.exc import OperationalError as SAOperationalError, DBAPIError as SADBAPIError, TimeoutError as SATimeoutError

from routers import auth, species, bills, logs, stats
from services.image_storage import get_uploads_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_initialized = False
_init_error = None
_init_in_progress = False
_last_init_attempt = 0.0
_init_lock = threading.Lock()
# 初始化失败后的重试间隔（秒）：冷启动时 DB 抖动导致的失败，后续请求会触发重试而不是永久 503
_INIT_RETRY_INTERVAL = 10.0


def _tables_exist():
    """快速检查：users 表存在说明 DB 已初始化，跳过 create_all。

    单连接单查询（方言分支）：相比 inspector 的 information_schema 多表查询，
    本地连远程库时把探测从多次往返降到一次 RTT。
    连接失败不再吞掉返回 False（那会误判"没有表"而触发 create_all 加重远程库压力），
    而是向上抛，让 init 快速失败并进入 10 秒重试。
    """
    from sqlalchemy import text

    if engine.dialect.name == "postgresql":
        sql = "SELECT to_regclass('public.users') IS NOT NULL"
    else:
        sql = "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'"
    with engine.connect() as conn:
        row = conn.execute(text(sql)).fetchone()
        return bool(row and row[0])


def init_app():
    global _initialized, _init_error, _init_in_progress, _last_init_attempt
    with _init_lock:
        if _initialized or _init_in_progress:
            return
        _init_in_progress = True
    _last_init_attempt = time.time()

    logger.info("Initializing application...")
    try:
        if os.getenv("VERCEL"):
            logger.info("Vercel environment detected. Skipping create_all and bootstrap for cold start speed.")
            _initialized = True
            return

        if os.getenv("RESET_DATABASE") == "true":
            logger.warning("RESET_DATABASE=true, dropping all tables...")
            Base.metadata.drop_all(bind=engine)

        # 已有表则跳过 create_all，节省 information_schema 查询
        if _tables_exist():
            logger.info("Tables already exist, skipping create_all.")
        else:
            Base.metadata.create_all(bind=engine)

        bootstrap.run()
        _initialized = True
        _init_error = None
        logger.info("Application initialized successfully in %.2fs", time.time() - _last_init_attempt)
    except Exception as exc:
        _init_error = str(exc)
        logger.error("Initialization failed: %s", _init_error)
        logger.error(traceback.format_exc())
    finally:
        _init_in_progress = False


def create_app() -> FastAPI:
    app = FastAPI(title="Fish Price Platform API")
    uploads_dir = get_uploads_dir()

    @app.on_event("startup")
    async def on_startup():
        if os.getenv("VERCEL"):
            # Vercel Serverless：不阻塞启动，通过 503 中间件优雅降级
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, init_app)
        else:
            # 本地开发：同步等待 init 完成，Uvicorn 的 "startup complete" 即为真正就绪信号
            init_app()

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    # 默认放开（本地 dev / 移动端跨域直连），生产可通过 CORS_ORIGINS 收紧（逗号分隔）
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount(
        "/uploads",
        StaticFiles(directory=str(uploads_dir), check_dir=False),
        name="uploads",
    )

    app.include_router(auth.router)
    app.include_router(species.router)
    app.include_router(bills.router)
    app.include_router(logs.router)
    app.include_router(stats.router)

    @app.middleware("http")
    async def app_middleware(request: Request, call_next):
        start = time.time()

        if request.url.path.startswith("/api/health"):
            response = await call_next(request)
        elif not _initialized:
            # 初始化失败后按间隔自动重试，避免该实例一直 503 到被回收
            if (
                not _init_in_progress
                and time.time() - _last_init_attempt > _INIT_RETRY_INTERVAL
            ):
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, init_app)
            response = JSONResponse(
                status_code=503,
                content={
                    # 初始化失败时给准确提示，避免用户误以为"服务器还在启动"
                    "detail": (
                        "服务暂时不可用：数据库连接失败，正在自动重试，请稍后刷新"
                        if _init_error
                        else "服务器正在启动，请稍后重试"
                    ),
                    "error": "初始化失败，请检查数据库连接配置" if _init_error else None,
                },
            )
        else:
            response = await call_next(request)

        elapsed = (time.time() - start) * 1000
        logger.info(
            "[%s] %s - %s - %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        if elapsed > 500:
            logger.warning(
                "SLOW %s %s took %.2fms",
                request.method,
                request.url.path,
                elapsed,
            )
        return response

    @app.get("/api/health")
    def health_check():
        # 健康检查对外只暴露状态，不泄露内部异常细节（error 只给一句笼统提示）
        if _initialized:
            status_text = "ok"
        elif _init_error:
            status_text = "error"
        else:
            status_text = "warming_up"
        return {
            "status": status_text,
            "initialized": _initialized,
            "error": "初始化失败，请检查数据库连接配置" if _init_error else None,
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        logger.error("Global exception: %s", exc)
        logger.error(traceback.format_exc())
        error_type = type(exc).__name__
        # 数据库瞬时异常（连接被回收/超时/冷启动）归为 503：前端 GET 会自动重试，避免用户看到"内部错误"
        if isinstance(exc, (SAOperationalError, SADBAPIError, SATimeoutError)):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "服务暂时不可用，请稍后重试",
                    "error": error_type,
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误，请稍后重试",
                "error": error_type,
            },
        )

    return app


app = create_app()
