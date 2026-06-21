"""Backfill `pilot.run` rows for existing vault folders (ADR-0018 Slice 2 → 3 hand-off).

Before Slice 3 flips the console's run-identity reads from the filesystem to `pilot.run`, every run
that already exists ONLY as a `runs/<slug>/` vault folder needs a DB row so it doesn't vanish from
the console. This one-shot backfill walks the vault, derives each run's identity from its existing
files exactly as the console does today — commodity from RUN.md's header, label from NOTES.md's
title (`_label_from_notes`), the `.rehearsal` sentinel (`is_rehearsal`), and the cycle link from
`cycle_id.txt` — and upserts a `pilot.run` row (inserting the missing ones, refreshing the cycle
link on any already present). Idempotent: re-running it is safe.

Run it as: `python -m app.pilot.backfill_runs` (uses the configured vault + DATABASE_URL). The MCP
harness is untouched; this only seeds the console's DB-backed identity from the existing vault.
"""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config.settings import get_settings
from app.core.db.session import unit_of_work
from app.pilot.run_repo import create_run_record, get_run, set_run_cycle
from app.pilot.status import read_status
from app.pilot.vault import RunPaths, is_rehearsal, list_runs

_NOTES_TITLE_RE = re.compile(r"^#\s*NOTES\s*[—-]\s*(.+)$")


def _label_from_notes(paths: RunPaths) -> str:
    """The run's label from NOTES.md's title (`# NOTES — {label}`), else the slug.

    Mirrors `app.api.v1.runs._label_from_notes` (NOTES.md's header is written once at creation, so
    it is the stable human label — RUN.md's title is re-stamped to the commodity on each render).
    """

    if paths.notes_md.exists():
        for line in paths.notes_md.read_text(encoding="utf-8").splitlines():
            match = _NOTES_TITLE_RE.match(line.strip())
            if match:
                return match.group(1).strip()
    return paths.slug


def _cycle_id(paths: RunPaths) -> str | None:
    if not paths.cycle_id_file.exists():
        return None
    value = paths.cycle_id_file.read_text(encoding="utf-8").strip()
    return value or None


def backfill_run(session: Session, paths: RunPaths) -> bool:
    """Upsert one vault folder's `pilot.run` row from its files; True if a row was inserted.

    Inserts the row when missing (deriving commodity/label/rehearsal from the vault), and links the
    cycle when `cycle_id.txt` carries one (whether the row was just created or already existed).
    """

    commodity = read_status(paths).get("Commodity", "")
    label = _label_from_notes(paths)
    rehearsal = is_rehearsal(paths)
    cycle_id = _cycle_id(paths)

    inserted = False
    if get_run(session, paths.slug) is None:
        create_run_record(
            session,
            slug=paths.slug,
            commodity=commodity,
            label=label,
            rehearsal=rehearsal,
        )
        inserted = True
    if cycle_id is not None:
        set_run_cycle(session, paths.slug, cycle_id)
    return inserted


def backfill_all(vault_root: Path | None = None) -> tuple[int, int]:
    """Backfill every vault run into `pilot.run`; return (inserted, total) counts.

    Runs inside the standard unit of work (one transaction). `vault_root` defaults to the configured
    console vault.
    """

    root = Path(vault_root) if vault_root is not None else Path(get_settings().vault_root)
    inserted = 0
    total = 0
    with unit_of_work() as session:
        for paths in list_runs(root):
            total += 1
            if backfill_run(session, paths):
                inserted += 1
    return inserted, total


def main() -> int:
    inserted, total = backfill_all()
    print(f"backfilled pilot.run: {inserted} inserted, {total} vault run(s) seen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
