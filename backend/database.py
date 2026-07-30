import os
from sqlalchemy import create_engine
from pathlib import Path
from sqlalchemy.orm import declarative_base, sessionmaker
import logging
from urllib.parse import urlparse, quote_plus, unquote_plus

logger = logging.getLogger(__name__)

def _read_local_env_url() -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env.local"
    if not env_path.exists():
        return ""
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key == "DATABASE_URL":
                return value.strip().strip('"').strip("'")
    except Exception as exc:
        logger.warning("Failed to read .env.local: %s", exc)
    return ""

def _normalize_database_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

    try:
        parsed = urlparse(raw_url)
        if parsed.password:
            decoded_pwd = unquote_plus(parsed.password)
            needs_encode = decoded_pwd == parsed.password and any(
                c in parsed.password for c in ["@", ":", "/", "?", "&", "=", "+", " "]
            )
            if needs_encode:
                encoded_pwd = quote_plus(parsed.password)
                raw_url = raw_url.replace(f":{parsed.password}@", f":{encoded_pwd}@", 1)
    except Exception as exc:
        logger.warning("Failed to normalize database URL: %s", exc)

    return raw_url

_raw_url = os.getenv("DATABASE_URL") or _read_local_env_url()

if not _raw_url:
    raise ValueError("DATABASE_URL environment variable is not set. Please configure it in .env.local.")

DATABASE_URL = _normalize_database_url(_raw_url)

try:
    parsed = urlparse(DATABASE_URL)
    logger.info(
        "Connecting to Neon database at %s:%s/%s",
        parsed.hostname,
        parsed.port or 5432,
        parsed.path.lstrip("/"),
    )
except Exception:
    pass

kwargs = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10,
    "connect_args": {
        "connect_timeout": 10,
        "sslmode": "require",
    }
}

engine = create_engine(DATABASE_URL, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
