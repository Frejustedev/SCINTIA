"""Database engine and session management (SQLAlchemy 2.0).

The engine is created lazily so importing this module never requires a configured
database — Phase 0 and unit tests run without Postgres.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False)


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        url = get_settings().database_url
        if not url:
            raise RuntimeError("DATABASE_URL is not configured.")
        _engine = create_engine(url, pool_pre_ping=True, future=True)
    return _engine


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a transactional session (commit/rollback/close)."""
    session = SessionLocal(bind=get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
