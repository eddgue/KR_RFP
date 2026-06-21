"""Runs surface (`/api/v1/runs`): list, create, and read pilot runs for the web console.

Wraps the existing `app.pilot.service.PilotService` (the same way the MCP server does) — NO domain
logic is reimplemented here. The service is built against the configured `vault_root` with
`isolate_db=False` so it shares the request's governed session (no per-run database is provisioned).
Every route is authenticated (`get_current_user`). Responses are plain Pydantic views the console
renders; commodity/label/rehearsal come from each run's vault metadata and `stage` is a short
human label distilled from the kanban.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.deps import CurrentUser
from app.core.config.settings import get_settings
from app.core.errors.taxonomy import AppError, ErrorCode
from app.pilot.service import PilotService
from app.pilot.status import read_status
from app.pilot.vault import RunPaths, is_rehearsal

router = APIRouter()


# --------------------------------------------------------------------------- #
# response models
# --------------------------------------------------------------------------- #
class RunSummary(BaseModel):
    """A run as it appears in the list — identity + a one-line stage label."""

    slug: str
    commodity: str
    label: str
    rehearsal: bool
    stage: str = Field(description="A short human label for where the run is (from the kanban).")


class RunDetail(RunSummary):
    """A single run with its full kanban board (Done / Doing / Next / Waiting on you)."""

    kanban: dict[str, list[str]]


class CreateRunRequest(BaseModel):
    commodity: str
    label: str
    rehearsal: bool = False


# --------------------------------------------------------------------------- #
# service wiring (vault root from settings; share the request DB session)
# --------------------------------------------------------------------------- #
@lru_cache
def _vault_root() -> Path:
    """The configured vault root, created on first use (so a fresh box just works)."""

    root = Path(get_settings().vault_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _service() -> PilotService:
    # isolate_db=False: the console shares the request's governed session, no per-run DB.
    return PilotService(_vault_root(), isolate_db=False)


# --------------------------------------------------------------------------- #
# metadata helpers (commodity / label / stage from the run's vault files)
# --------------------------------------------------------------------------- #
_NOTES_TITLE_RE = re.compile(r"^#\s*NOTES\s*[—-]\s*(.+)$")


def _label_from_notes(paths: RunPaths) -> str:
    """The run's label — read from the NOTES.md title (`# NOTES — {label}`), never re-stamped.

    RUN.md's title gets rewritten to the commodity on each kanban render, so NOTES.md (whose header
    is written once at creation) is the stable source for the human label. Falls back to the slug.
    """

    if paths.notes_md.exists():
        for line in paths.notes_md.read_text(encoding="utf-8").splitlines():
            match = _NOTES_TITLE_RE.match(line.strip())
            if match:
                return match.group(1).strip()
    return paths.slug


def _stage_label(board: dict[str, list[str]]) -> str:
    """A short human stage label: the first in-flight/next item, else the last Done, else Setup."""

    for bucket in ("Doing", "Next", "Waiting on you"):
        entries = board.get(bucket, [])
        if entries:
            return entries[0]
    done = board.get("Done", [])
    if done:
        return done[-1]
    return "Setup"


def _summary(paths: RunPaths, board: dict[str, list[str]]) -> RunSummary:
    header = read_status(paths)
    return RunSummary(
        slug=paths.slug,
        commodity=header.get("Commodity", ""),
        label=_label_from_notes(paths),
        rehearsal=is_rehearsal(paths),
        stage=_stage_label(board),
    )


def _resolve_paths(slug: str) -> RunPaths:
    """The RunPaths for an existing run, or 404 if the slug isn't a real run."""

    paths = _service().run_paths(slug)
    if not paths.root.is_dir():
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No run named {slug!r}.",
            status_code=404,
        )
    return paths


# --------------------------------------------------------------------------- #
# endpoints
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[RunSummary], summary="List runs")
def list_runs(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[RunSummary]:
    """Every run in the vault, each with a one-line stage label from its kanban."""

    service = _service()
    summaries: list[RunSummary] = []
    for paths in service.list_runs():
        board = service.status(db, paths)
        summaries.append(_summary(paths, board))
    return summaries


@router.post(
    "",
    response_model=RunDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new run",
)
def create_run(
    body: CreateRunRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunDetail:
    """Start a new RFP run (vault scaffold + Setup/Kickoff workbook) and return its detail.

    With `isolate_db=False` no per-run database is provisioned; the run rides the governed store.
    """

    service = _service()
    paths = service.start_run(commodity=body.commodity, label=body.label, rehearsal=body.rehearsal)
    board = service.status(db, paths)
    summary = _summary(paths, board)
    return RunDetail(**summary.model_dump(), kanban=board)


@router.get("/{slug}", response_model=RunDetail, summary="Read one run")
def get_run(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunDetail:
    """One run's summary + its full kanban board, or 404 if the slug isn't a real run."""

    service = _service()
    paths = _resolve_paths(slug)
    board = service.status(db, paths)
    summary = _summary(paths, board)
    return RunDetail(**summary.model_dump(), kanban=board)
