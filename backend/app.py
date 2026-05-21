import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from database import engine, Base
from utils import UPLOAD_DIR, SPECIES_UPLOAD_DIR
import bootstrap

from routers import auth, species, bills, logs, stats

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 启动初始化标记
_initialized = False

def init_app():
    global _initialized
    if _initialized:
        return
    
    logger.info("Initializing application...")
    try:
        Base.metadata.create_all(bind=engine)
        bootstrap.run()
        _initialized = True
        logger.info("Application initialized successfully.")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        logger.error(traceback.format_exc())

def create_app() -> FastAPI:
    app = FastAPI(title="Fish Price Platform API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    UPLOAD_DIR.mkdir(exist_ok=True)
    SPECIES_UPLOAD_DIR.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    app.include_router(auth.router)
    app.include_router(species.router)
    app.include_router(bills.router)
    app.include_router(logs.router)
    app.include_router(stats.router)

    @app.middleware("http")
    async def ensure_initialized(request: Request, call_next):
        # 在处理请求前确保已初始化（针对 Vercel 等 Serverless 环境优化）
        if not _initialized and not request.url.path.startswith("/api/health"):
            init_app()
        return await call_next(request)

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "initialized": _initialized}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试", "error": str(exc)},
        )

    return app


app = create_app()
