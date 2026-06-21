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

    # The non-spine schemas hand-written migrations add (auth identity, pilot run identity) must
    # round-trip cleanly too — created at head, gone at base (ADR-0018 Slice 2: pilot.run).
    non_spine = {"auth", "pilot"}

    # Start from a known floor, then exercise the round-trip.
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    present = schemas_present()
    assert set(SCHEMAS).issubset(present)
    assert non_spine.issubset(present)

    command.downgrade(cfg, "base")
    present = schemas_present()
    assert not (set(SCHEMAS) & present), "schemas should be gone after downgrade base"
    assert not (non_spine & present), "auth/pilot schemas should be gone after downgrade base"

    command.upgrade(cfg, "head")
    present = schemas_present()
    assert set(SCHEMAS).issubset(present)
    assert non_spine.issubset(present)
