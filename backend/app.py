import logging
import traceback
import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import engine, Base, get_db
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
        if os.getenv("RESET_DATABASE") == "true":
            logger.warning("RESET_DATABASE is true. Dropping all tables...")
            Base.metadata.drop_all(bind=engine)
            logger.warning("All tables dropped.")
            
        Base.metadata.create_all(bind=engine)
        bootstrap.run()
        _initialized = True
        logger.info("Application initialized successfully.")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Initialization failed: {error_msg}")
        logger.error(traceback.format_exc())
        
        # 针对常见的 Supabase 连接错误提供友好的提示
        if "tenant/user" in error_msg and "not found" in error_msg:
            friendly_error = "数据库连接失败：Supabase 项目 ID 或区域配置错误。请检查 Vercel 中的 DATABASE_URL 是否使用了正确的项目专属地址（建议使用 5432 端口的直连地址）。"
            raise Exception(friendly_error)
        elif "password authentication failed" in error_msg:
            raise Exception("数据库连接失败：密码错误，请检查 Vercel 中的 DATABASE_URL 配置。")
        
        raise e # 抛出原异常或处理后的异常

def create_app() -> FastAPI:
    app = FastAPI(title="Fish Price Platform API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(species.router)
    app.include_router(bills.router)
    app.include_router(logs.router)
    app.include_router(stats.router)

    @app.middleware("http")
    async def ensure_initialized(request: Request, call_next):
        # 在处理请求前确保已初始化（针对 Vercel 等 Serverless 环境优化）
        if not _initialized and not request.url.path.startswith("/api/health"):
            try:
                init_app()
            except Exception as e:
                # 如果初始化失败，直接返回 500
                return JSONResponse(
                    status_code=500,
                    content={"detail": "服务器初始化失败", "error": str(e)},
                )
        return await call_next(request)

    @app.get("/api/health")
    def health_check(db: Session = Depends(get_db)):
        try:
            # 检查数据库连接
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
            
        return {
            "status": "ok", 
            "initialized": _initialized,
            "database": db_status
        }

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
