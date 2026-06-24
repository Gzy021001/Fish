import logging
import traceback
import os
import time
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


def init_app():
    global _initialized, _init_error
    if _initialized:
        return

    logger.info("Initializing application...")
    try:
        if os.getenv("VERCEL"):
            try:
                with engine.connect() as conn:
                    from sqlalchemy import text

                    conn.execute(text("SELECT 1 FROM users LIMIT 1"))
                _initialized = True
                logger.info(
                    "Database already initialized, skipping create_all for cold start."
                )
                return
            except Exception:
                pass

        if os.getenv("RESET_DATABASE") == "true":
            logger.warning("RESET_DATABASE=true, dropping all tables...")
            Base.metadata.drop_all(bind=engine)

        Base.metadata.create_all(bind=engine)
        bootstrap.run()
        _initialized = True
        _init_error = None
        logger.info("Application initialized successfully.")
    except Exception as exc:
        _init_error = str(exc)
        logger.error("Initialization failed: %s", _init_error)
        logger.error(traceback.format_exc())

        if "tenant/user" in _init_error and "not found" in _init_error:
            raise Exception(
                "数据库连接失败：Supabase 项目 ID 或区域配置错误。"
                "请检查 Vercel DATABASE_URL。"
            )
        if "password authentication failed" in _init_error:
            raise Exception(
                "数据库连接失败：密码错误，请检查 Vercel DATABASE_URL。"
            )
        raise


def create_app() -> FastAPI:
    app = FastAPI(title="Fish Price Platform API")
    uploads_dir = get_uploads_dir()

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

    @app.api_route("/_reset_db", methods=["GET", "POST"])
    def reset_db(key: str = ""):
        if key != "e7c3a8041f":
            raise HTTPException(status_code=403, detail="Unauthorized")
        from database import engine, Base
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        from bootstrap import run as bootstrap_run
        bootstrap_run()
        global _initialized, _init_error
        _initialized = True
        _init_error = None
        return {"status": "ok", "message": "Database reset complete"}

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        logger.error("Global exception: %s", exc)
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试"},
        )

    return app


app = create_app()
