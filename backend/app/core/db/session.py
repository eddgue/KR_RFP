"""Engine, sessionmaker, and the request-scoped unit of work.

Transaction discipline (PLAN §7): **services `add` + `flush`, never `commit`.** The unit of
work owns the transaction boundary and commits exactly once per request (or worker task), so
multi-service operations are atomic and the audit write lands in the same transaction as the
change it records. On any exception the unit of work rolls back.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.settings import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )


engine: Engine = _build_engine()

# Note: services never call commit; the unit of work below owns it.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


@contextmanager
def unit_of_work() -> Iterator[Session]:
    """Request-scoped unit of work that OWNS the commit.

    Yields a session inside a transaction; commits on success, rolls back on any exception,
    and always closes. Services add+flush within this boundary and must not commit.
    """

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a unit-of-work-managed session for the request."""

    with unit_of_work() as session:
        yield session
