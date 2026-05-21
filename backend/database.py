import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 默认本地 SQLite
SQLITE_URL = "sqlite:///./fish_price.db"

# 优先从环境变量读取 DATABASE_URL (支持 Supabase/PostgreSQL)
_raw_url = os.getenv("DATABASE_URL", "")

if _raw_url:
    # Supabase 提供的链接通常以 postgres:// 开头，SQLAlchemy 需要 postgresql://
    if _raw_url.startswith("postgres://"):
        DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = _raw_url
elif os.getenv("VERCEL"):
    # 如果在 Vercel 但没配置 DATABASE_URL，退回到临时 SQLite (不推荐)
    DATABASE_URL = "sqlite:////tmp/fish_price.db"
else:
    DATABASE_URL = SQLITE_URL

kwargs = {}
if "sqlite" in DATABASE_URL:
    kwargs["connect_args"] = {"check_same_thread": False}
else:
    # 针对 PostgreSQL (Supabase) 的连接优化
    kwargs["pool_pre_ping"] = True
    kwargs["pool_size"] = 5
    kwargs["max_overflow"] = 10
    # 增加连接超时设置
    kwargs["connect_args"] = {"connect_timeout": 10}

engine = create_engine(DATABASE_URL, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
