"""Migration round-trip (PLAN §7, SKELETON R8) — integration.

up -> down -> up must be clean. This kills the SQLite-ism risk and proves every migration is
reversible. Runs against the real Postgres service (Alembic's `command` API, programmatically).
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.core.db.base import SCHEMAS

pytestmark = pytest.mark.integration


def _alembic_config(database_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def test_migrations_roundtrip(engine, database_url: str) -> None:
    """upgrade head -> downgrade base -> upgrade head, asserting schema presence at each up."""

    cfg = _alembic_config(database_url)

    def schemas_present() -> set[str]:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT schema_name FROM information_schema.schemata")
            ).scalars()
            return set(rows)

    # Start from a known floor, then exercise the round-trip.
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    assert set(SCHEMAS).issubset(schemas_present())

    command.downgrade(cfg, "base")
    assert not (set(SCHEMAS) & schemas_present()), "schemas should be gone after downgrade base"

    command.upgrade(cfg, "head")
    assert set(SCHEMAS).issubset(schemas_present())
