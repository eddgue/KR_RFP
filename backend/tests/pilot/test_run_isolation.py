"""Per-run data isolation (D30) — the compliance regression test.

Provisions TWO run databases and writes the SAME globally-unique reference code (`ref.dc` DC01) into
each. In a shared database that collides (`dc_code=DC01 already exists`); with a database per
run it must NOT — each run holds its own DC01 and can never see the other's. Integration test:
needs a reachable Postgres AND a role with CREATEDB (skips cleanly otherwise). Drops both DBs after.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.pilot.run_db import (
    drop_run_database,
    provision_run_database,
    run_db_name,
    run_unit_of_work,
)

_INSERT_DC01 = text(
    "INSERT INTO ref.dc (dc_id, dc_code, dc_name, region, division, active_flag) "
    "VALUES (:id, 'DC01', 'Atlanta DC', :region, 'Produce', true)"
)


@pytest.mark.integration
def test_two_runs_get_isolated_databases(database_url: str) -> None:  # database_url: skip if no DB
    slug_a = f"iso-test-{uuid.uuid4().hex[:8]}"
    slug_b = f"iso-test-{uuid.uuid4().hex[:8]}"
    try:
        try:
            provision_run_database(slug_a)
        except Exception as exc:  # noqa: BLE001 — most likely: role lacks CREATEDB
            if "permission denied to create database" in str(exc):
                pytest.skip("DB role lacks CREATEDB — per-run isolation needs it")
            raise
        provision_run_database(slug_b)

        # The SAME global code DC01 into BOTH runs — a hard collision in any shared store.
        with run_unit_of_work(slug_a) as s:
            s.execute(_INSERT_DC01, {"id": str(uuid.uuid4()), "region": "EAST"})
        with run_unit_of_work(slug_b) as s:
            s.execute(_INSERT_DC01, {"id": str(uuid.uuid4()), "region": "WEST"})

        # Separate databases, and each holds ONLY its own DC01 (no cross-contamination).
        assert run_db_name(slug_a) != run_db_name(slug_b)
        with run_unit_of_work(slug_a) as s:
            assert [r[0] for r in s.execute(text("SELECT region FROM ref.dc"))] == ["EAST"]
        with run_unit_of_work(slug_b) as s:
            assert [r[0] for r in s.execute(text("SELECT region FROM ref.dc"))] == ["WEST"]
    finally:
        drop_run_database(slug_a)
        drop_run_database(slug_b)
