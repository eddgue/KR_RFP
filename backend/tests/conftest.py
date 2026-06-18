"""Shared test fixtures.

The PURE guards (clean-room import, engine stub) need nothing here. The integration fixtures
below require a real Postgres (PLAN §7: service tests run against a real DB, never SQLite).
DB-touching tests are marked `@pytest.mark.integration` so the pure suite runs standalone:

    pytest -m "not integration"   # PURE — no DB
    pytest                        # full — requires DATABASE_URL pointing at a live Postgres

Integration fixtures `skip` (not error) when no database is reachable, so a dev box without
Postgres still gets a green pure run.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest


@pytest.fixture(scope="session")
def database_url() -> str:
    """The DATABASE_URL the integration suite runs against (from settings/env)."""

    from app.core.config.settings import get_settings

    return get_settings().database_url


@pytest.fixture(scope="session")
def engine(database_url: str):  # type: ignore[no-untyped-def]
    """A SQLAlchemy engine; skips the integration suite if Postgres is unreachable."""

    from sqlalchemy import create_engine, text

    eng = create_engine(database_url, future=True, pool_pre_ping=True)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — any connection failure means "skip integration"
        pytest.skip(f"No reachable Postgres for integration tests: {exc}")
    return eng


@pytest.fixture
def db_session(engine) -> Iterator:  # type: ignore[no-untyped-def]
    """A session bound to a transaction that is rolled back after each test (isolation)."""

    from sqlalchemy.orm import Session

    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def seed_tenants(db_session):  # type: ignore[no-untyped-def]
    """Insert two tenants (A, B) for tenant-isolation tests; returns their ids."""

    from app.domain.ref.models import Client

    tenant_a = Client(
        id=uuid.uuid4(), client_code=f"A-{uuid.uuid4().hex[:8]}", client_name="Tenant A"
    )
    tenant_b = Client(
        id=uuid.uuid4(), client_code=f"B-{uuid.uuid4().hex[:8]}", client_name="Tenant B"
    )
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()
    return {"a": tenant_a.id, "b": tenant_b.id}
