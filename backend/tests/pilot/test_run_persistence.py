"""Vault-carried DB persistence — a run's governed DB survives a wiped (ephemeral) container.

The web environment is reclaimed between sessions, so a run's isolated Postgres DB is gone next
time. The vault git repo carries a per-run SQL dump; on session start the DB is rehydrated from it.
This proves the round trip end to end: provision → write → dump → DROP (the wipe) → restore → the
data is intact, so the run resumes exactly where it was.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from app.pilot.run_db import (
    drop_run_database,
    dump_run_database,
    provision_run_database,
    restore_run_database,
    run_db_name,
    run_unit_of_work,
)


@pytest.mark.integration
def test_run_db_dump_drop_restore_round_trips(tmp_path: Path) -> None:
    slug = f"persist-test-{uuid.uuid4().hex[:8]}"
    marker = uuid.uuid4().hex
    try:
        provision_run_database(slug)  # fresh migrated isolated DB

        # Write a sentinel into a migrated table (ref.client exists after migrate-to-head).
        with run_unit_of_work(slug) as session:
            session.execute(
                text(
                    "INSERT INTO ref.client (id, client_code, client_name, is_active) "
                    "VALUES (gen_random_uuid(), :code, :name, true)"
                ),
                {"code": f"C-{marker[:6]}", "name": marker},
            )

        # Dump to a vault-like path, then DROP the DB — the ephemeral container being reclaimed.
        dump = tmp_path / "runs" / slug / "db" / "run_db.sql"
        dump_run_database(slug, dump)
        assert dump.is_file() and dump.stat().st_size > 0
        drop_run_database(slug)

        # Fresh container: the DB is gone. Rehydrate from the vault dump.
        restore_run_database(slug, dump)

        # The sentinel survived the wipe — the run resumes with its governed data intact.
        with run_unit_of_work(slug) as session:
            got = session.execute(
                text("SELECT client_name FROM ref.client WHERE client_name = :m"),
                {"m": marker},
            ).scalar()
        assert got == marker
        assert run_db_name(slug).startswith("kr_rfp_run_")
    finally:
        drop_run_database(slug)
