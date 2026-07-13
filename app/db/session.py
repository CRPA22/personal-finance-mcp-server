"""Database session factory and dependency."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

# Use sync URL (replace asyncpg with psycopg2)
_sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(
    _sync_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"options": "-c statement_timeout=30000"},
    execution_options={"prepared_statement_cache_size": 0},
)

SessionLocal = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """Generator that yields a database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_context() -> Generator[Session, None, None]:
    """Context manager for manual session handling (e.g. in tools)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
