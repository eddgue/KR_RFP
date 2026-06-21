"""DB-backed run identity (NFS Slice 2) — the `pilot.run` repo, dual-write, and backfill.

The web console resolves run identity from `pilot.run` (ADR-0018), not the vault folder. This proves
the building blocks Slice 3 flips the reads onto:

  * the repo CRUD (`create_run_record`/`get_run`/`list_run_records`/`set_run_cycle`/
    `delete_run_record`) round-trips a row;
  * the console-mode service DUAL-WRITES — `start_run(session=...)` inserts the row and
    `ingest_setup` sets its `cycle_id` (while still writing the vault files);
  * the MCP-harness mode (`db_runs` off) writes NO `pilot.run` row (the harness is untouched);
  * `backfill_runs` seeds a row for a pre-existing vault folder that has no DB row yet, deriving
    commodity/label/rehearsal/cycle from the files exactly as the console does.

Synthetic only (clean-room, ADR-0001); integration (skips when no DB).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.pilot.backfill_runs import backfill_run
from app.pilot.run_repo import (
    create_run_record,
    delete_run_record,
    get_run,
    list_run_records,
    set_run_cycle,
)
from app.pilot.service import PilotService
from app.pilot.vault import stage_filename
from tests.pilot.test_pilot_cycle_e2e import _build_filled_setup

pytestmark = pytest.mark.integration


def test_repo_crud_round_trips(db_session) -> None:  # type: ignore[no-untyped-def]
    """create → get → list → set_cycle → delete, all on the rolled-back session."""

    slug = "tomato-20260621-abc123"
    created = create_run_record(
        db_session, slug=slug, commodity="Field Tomatoes", label="Repo Test", rehearsal=False
    )
    assert created.slug == slug
    assert created.cycle_id is None
    assert created.created_at is not None

    fetched = get_run(db_session, slug)
    assert fetched is not None
    assert fetched.commodity == "Field Tomatoes"
    assert fetched.label == "Repo Test"
    assert fetched.rehearsal is False

    assert slug in {r.slug for r in list_run_records(db_session)}

    set_run_cycle(db_session, slug, "cycle-xyz")
    assert get_run(db_session, slug).cycle_id == "cycle-xyz"

    # set_run_cycle on an unknown slug is a clean error, never a silent no-op.
    with pytest.raises(ValueError):
        set_run_cycle(db_session, "no-such-run", "cycle-xyz")

    delete_run_record(db_session, slug)
    assert get_run(db_session, slug) is None
    # Idempotent: deleting a missing row is a no-op.
    delete_run_record(db_session, slug)


def test_console_service_dual_writes_run_row(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """Console mode (db_runs=True): start_run inserts the row; ingest_setup sets its cycle_id."""

    service = PilotService(tmp_path, isolate_db=False, db_runs=True)
    paths = service.start_run(
        commodity="Field Tomatoes", label="Dual Write", rehearsal=False, session=db_session
    )

    row = get_run(db_session, paths.slug)
    assert row is not None
    assert row.commodity == "Field Tomatoes"
    assert row.label == "Dual Write"
    assert row.rehearsal is False
    assert row.cycle_id is None  # not linked until setup ingest

    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)

    # The dual-write linked the cycle on the row (and the vault cycle_id.txt still matches).
    assert get_run(db_session, paths.slug).cycle_id == cycle_id
    assert paths.cycle_id_file.read_text(encoding="utf-8").strip() == cycle_id


def test_harness_mode_writes_no_run_row(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """MCP-harness mode (db_runs off) writes NO pilot.run row — the harness is untouched."""

    service = PilotService(tmp_path, isolate_db=False)  # db_runs defaults to False
    paths = service.start_run(commodity="Field Tomatoes", label="Harness", session=db_session)
    assert get_run(db_session, paths.slug) is None


def test_console_start_run_scaffolds_no_folder(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """Console mode (persist_outputs off) writes only the DB row — NO vault folder (Slice 6)."""

    service = PilotService(tmp_path, isolate_db=False, db_runs=True, persist_outputs=False)
    paths = service.start_run(commodity="Field Tomatoes", label="No Folder", session=db_session)
    # The pilot.run row exists; the vault folder does not.
    assert get_run(db_session, paths.slug) is not None
    assert not paths.root.exists()


def test_console_delete_run_removes_row(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """Console close-out deletes the pilot.run row (Slice 6); idempotent."""

    service = PilotService(tmp_path, isolate_db=False, db_runs=True, persist_outputs=False)
    paths = service.start_run(commodity="Field Tomatoes", label="Closeout", session=db_session)
    assert get_run(db_session, paths.slug) is not None

    service.delete_run(db_session, paths.slug)
    assert get_run(db_session, paths.slug) is None
    # Idempotent: deleting an already-gone run is a no-op.
    service.delete_run(db_session, paths.slug)


def test_rehearsal_dual_write_flags_synthetic(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """A rehearsal run's dual-written row carries rehearsal=True."""

    service = PilotService(tmp_path, isolate_db=False, db_runs=True)
    paths = service.start_run(
        commodity="Test Greens", label="Practice", rehearsal=True, session=db_session
    )
    assert get_run(db_session, paths.slug).rehearsal is True


def test_backfill_seeds_existing_vault_folder(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """Backfill inserts a pilot.run row for a folder created without the DB-backed identity.

    A run created in harness mode (no DB row) is the pre-Slice-2 reality. The backfill walks the
    vault and seeds its row from the existing files — commodity/label/rehearsal/cycle — so Slice 3
    can read it from the DB without the folder vanishing from the console.
    """

    harness = PilotService(tmp_path, isolate_db=False)  # no db_runs → no row written
    paths = harness.start_run(commodity="Field Tomatoes", label="Legacy Folder")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = harness.ingest_setup(db_session, paths, setup_path)

    assert get_run(db_session, paths.slug) is None  # no DB identity yet

    inserted = backfill_run(db_session, paths)
    assert inserted is True

    row = get_run(db_session, paths.slug)
    assert row is not None
    assert row.commodity == "Field Tomatoes"
    assert row.label == "Legacy Folder"
    assert row.rehearsal is False
    assert row.cycle_id == cycle_id  # linked from cycle_id.txt

    # Idempotent: a second backfill inserts nothing and keeps the cycle link.
    assert backfill_run(db_session, paths) is False
    assert get_run(db_session, paths.slug).cycle_id == cycle_id
