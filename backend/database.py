import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLITE_URL = "sqlite:///./fish_price.db"

_raw_url = os.getenv("DATABASE_URL", "")
if _raw_url:
    DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)
elif os.getenv("VERCEL"):
    DATABASE_URL = "sqlite:////tmp/fish_price.db"
else:
    DATABASE_URL = SQLITE_URL

kwargs = {}
if "sqlite" in DATABASE_URL:
    kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
