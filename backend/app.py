import logging
import traceback
import os
import time
import json
import urllib.request
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from database import engine, Base
import bootstrap

from routers import auth, species, bills, logs, stats
from services.image_storage import get_uploads_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_initialized = False
_init_error = None


def _tables_exist():
    """快速检查：users 表存在说明 DB 已初始化，跳过 create_all"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        return "users" in inspector.get_table_names()
    except Exception:
        return False


def init_app():
    global _initialized, _init_error
    if _initialized:
        return

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
        logger.info("Application initialized successfully.")
    except Exception as exc:
        _init_error = str(exc)
        logger.error("Initialization failed: %s", _init_error)
        logger.error(traceback.format_exc())


import asyncio

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
            response = JSONResponse(
                status_code=503,
                content={
                    "detail": "服务器正在启动，请稍后重试",
                    "error": _init_error if _init_error else None,
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
        return {
            "status": "ok" if _initialized else ("error" if _init_error else "warming_up"),
            "initialized": _initialized,
            "error": _init_error,
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        logger.error("Global exception: %s", exc)
        logger.error(traceback.format_exc())
        error_type = type(exc).__name__
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误，请稍后重试",
                "error": error_type,
            },
        )

    return app


app = create_app()
