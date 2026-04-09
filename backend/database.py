import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def _default_database_url() -> str:
    # Prefer Postgres, but allow local SQLite for quick starts.
    return "sqlite:///./ecotrack.db"


DATABASE_URL = os.getenv("DATABASE_URL", _default_database_url())

# For PostgreSQL, recommended format:
# postgresql+psycopg2://user:password@localhost:5432/ecotrack
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@contextmanager
def session_scope() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
