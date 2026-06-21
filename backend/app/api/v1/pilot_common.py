"""Shared PilotService wiring for the console's run-scoped surfaces (runs + bids).

Both the runs router (file/setup/template) and the bids router (import/list) drive the SAME
`app.pilot.service.PilotService` — no domain logic is reimplemented in the API layer. The service
is built against the configured `vault_root` with `isolate_db=False` so it shares the request's
governed session (no per-run database is provisioned), exactly the way the MCP server wraps it.
These helpers are factored here so neither router duplicates the wiring; the test suite redirects
the vault by monkeypatching `_vault_root` on THIS module.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config.settings import get_settings
from app.core.errors.taxonomy import AppError, ErrorCode
from app.cycle.loader import load_cycle
from app.pilot.service import PilotService
from app.pilot.vault import RunPaths


@lru_cache
def _vault_root() -> Path:
    """The configured vault root, created on first use (so a fresh box just works)."""

    root = Path(get_settings().vault_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def service() -> PilotService:
    """A PilotService on the configured vault; `isolate_db=False` shares the request session.

    `db_runs=True` (ADR-0018 Slice 2): the console dual-writes run identity to `pilot.run` so the
    stateless web path can resolve/list runs from the DB. The MCP harness builds its own service
    (no `db_runs`) and keeps its file vault.
    """

    # isolate_db=False: the console shares the request's governed session, no per-run DB.
    return PilotService(_vault_root(), isolate_db=False, db_runs=True)


def resolve_paths(slug: str) -> RunPaths:
    """The `RunPaths` for an existing run, or 404 if the slug isn't a real run."""

    paths = service().run_paths(slug)
    if not paths.root.is_dir():
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No run named {slug!r}.",
            status_code=404,
        )
    return paths


def resolve_round_id(db: Session, paths: RunPaths, round_no: int) -> str:
    """The cycle `round_id` for a 1-based round on the run's cycle, with DISTINCT errors.

    `gate_required` (400) when the run has no cycle yet (setup not ingested); `validation_error`
    (400) when the round is beyond the cycle's round count. Shared by the bids endpoints AND the
    bid-template endpoint so an out-of-range round is never mislabeled as "no cycle yet".
    """

    cycle_id_value = (
        paths.cycle_id_file.read_text(encoding="utf-8").strip()
        if paths.cycle_id_file.exists()
        else ""
    )
    if not cycle_id_value:
        raise AppError(
            code=ErrorCode.GATE_REQUIRED,
            message=f"Run {paths.slug!r} has no cycle yet — ingest the setup workbook first.",
            status_code=400,
        )
    cycle = load_cycle(db, cycle_id_value)
    if round_no > len(cycle.rounds):
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=(
                f"Round {round_no} is out of range — the cycle has {len(cycle.rounds)} round(s)."
            ),
            status_code=400,
        )
    return cycle.rounds[round_no - 1].id
