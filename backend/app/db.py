"""SQLAlchemy database setup."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import DATABASE_URL


def _database_url(value: str) -> str:
    """Use psycopg 3 for Vercel Marketplace PostgreSQL URLs."""
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value.removeprefix("postgres://")
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value.removeprefix("postgresql://")
    return value


RESOLVED_DATABASE_URL = _database_url(DATABASE_URL)
engine_options = {"connect_args": {"check_same_thread": False}} if RESOLVED_DATABASE_URL.startswith("sqlite") else {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
if RESOLVED_DATABASE_URL.endswith(":memory:"):
    engine_options["poolclass"] = StaticPool
engine = create_engine(RESOLVED_DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
