import os
from sqlalchemy import create_engine
from pathlib import Path
from sqlalchemy.orm import declarative_base, sessionmaker
import logging
logger = logging.getLogger(__name__)

# 默认本地 SQLite
SQLITE_URL = f"sqlite:///{(Path(__file__).resolve().parent / 'fish_price.db').as_posix()}"

# 优先从环境变量读取 POSTGRES_URL (Supabase Vercel Integration)，其次读取 DATABASE_URL
_raw_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL", "")

if _raw_url:
    # 移除可能存在的空格
    _raw_url = _raw_url.strip()
    
    # 自动处理密码中的特殊字符（例如密码中的 .. 导致解析失败的问题）
    from urllib.parse import urlparse, quote_plus, unquote_plus, urlencode, parse_qs
    try:
        parsed = urlparse(_raw_url)
        
        # 移除 psycopg2 不支持的 supa 参数
        if parsed.query:
            qs = parse_qs(parsed.query)
            if 'supa' in qs:
                del qs['supa']
            # 重建 URL
            parsed = parsed._replace(query=urlencode(qs, doseq=True))
            _raw_url = parsed.geturl()

        if parsed.password:
            # 只有当密码没有被 URL 编码时，才进行编码
            decoded_pwd = unquote_plus(parsed.password)
            if decoded_pwd == parsed.password and any(c in parsed.password for c in ['@', ':', '/', '?', '&', '=', '+', '.', '-']):
                encoded_pwd = quote_plus(parsed.password)
                _raw_url = _raw_url.replace(f":{parsed.password}@", f":{encoded_pwd}@")
    except Exception as e:
        logger.warning(f"Failed to auto-encode password: {e}")

    # Supabase 提供的链接通常以 postgres:// 开头，SQLAlchemy 需要 postgresql://
    if _raw_url.startswith("postgres://"):
        DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URL = _raw_url

    # 强制将 Supabase 直连地址 (IPv6) 转换为池化地址 (IPv4) 以兼容 Vercel
    if "db.kntqzmldrvvonhbggysa.supabase.co" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("db.kntqzmldrvvonhbggysa.supabase.co", "aws-0-ap-southeast-1.pooler.supabase.com")
        DATABASE_URL = DATABASE_URL.replace(":5432", ":6543")
        # Supabase Pooler (6543) 需要在用户名中包含 project ID 作为 tenant identifier
        if "postgres:" in DATABASE_URL and "postgres.kntqzmldrvvonhbggysa:" not in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("postgres:", "postgres.kntqzmldrvvonhbggysa:", 1)
    
    # 针对 Supabase Pooler (6543端口) 经常出现的区域错误进行检测
    if "pooler.supabase.com:6543" in DATABASE_URL and "aws-0-ap-southeast-1" in DATABASE_URL:
        logger.warning("检测到正在使用新加坡节点的池化连接，如果连接失败，请检查您的 Supabase 项目区域。")
    
    # 记录安全的连接日志
    try:
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        logger.info(f"Connecting to database at {parsed.hostname}:{parsed.port or 5432}/{parsed.path.lstrip('/')}")
    except:
        pass
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
