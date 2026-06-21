"""Runs surface (`/api/v1/runs`): list, create, read, and drive the input chain of pilot runs.

Wraps the existing `app.pilot.service.PilotService` (the same way the MCP server does) — NO domain
logic is reimplemented here. The service is built against the configured `vault_root` with
`isolate_db=False` so it shares the request's governed session (no per-run database is provisioned).
Every route is authenticated (`get_current_user`). Responses are plain Pydantic views the console
renders; commodity/label/rehearsal come from each run's vault metadata and `stage` is a short
human label distilled from the kanban. The run-scoped file / setup / template endpoints expose the
front half of the cycle loop (list + download run files, ingest the setup workbook, generate a
round's bid template); the service wiring (`_vault_root` / `service` / `resolve_paths`) is shared
with the bids router via `app.api.v1.pilot_common`.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.pilot_common import resolve_paths, service
from app.auth.deps import CurrentUser
from app.core.errors.taxonomy import AppError, ErrorCode
from app.pilot.status import read_status
from app.pilot.vault import (
    SUBDIR_INPUTS,
    RunPaths,
    build_run_zip,
    is_rehearsal,
    stage_filename,
    write_to_run,
)

router = APIRouter()

# The .xlsx media type — every run file the console serves is a workbook (setup, template, output).
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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


class RunFile(BaseModel):
    """One file present in a run's inputs/ or outputs/ dir (what the console lists + downloads)."""

    name: str
    kind: Literal["input", "output"]
    size_bytes: int
    modified: str = Field(description="Last-modified timestamp, ISO-8601 UTC.")


class IngestSetupResponse(BaseModel):
    """The result of ingesting the setup workbook: the new cycle id + the recomputed kanban."""

    cycle_id: str
    kanban: dict[str, list[str]]


class GenerateTemplateResponse(BaseModel):
    """The generated bid template's filename (downloadable via the file endpoint) + the kanban."""

    filename: str
    kanban: dict[str, list[str]]


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


def _run_files(paths: RunPaths) -> list[RunFile]:
    """Every file in the run's inputs/ + outputs/ dirs (skipping the .gitkeep scaffold markers)."""

    files: list[RunFile] = []
    for directory, kind in ((paths.inputs, "input"), (paths.outputs, "output")):
        if not directory.is_dir():
            continue
        for entry in sorted(directory.iterdir()):
            if not entry.is_file() or entry.name == ".gitkeep":
                continue
            stat = entry.stat()
            files.append(
                RunFile(
                    name=entry.name,
                    kind="input" if kind == "input" else "output",
                    size_bytes=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                )
            )
    return files


def _resolve_run_file(paths: RunPaths, name: str) -> Path:
    """Resolve a plain filename to a real file inside the run's inputs/ or outputs/, or 404.

    Path-traversal guard: only a bare filename is accepted, and the resolved path must stay inside
    the run's inputs/ or outputs/ dir — anything that escapes (`..`, an absolute path, a nested
    segment) or that doesn't exist is a clean 404, never a read outside the run folder.
    """

    not_found = AppError(
        code=ErrorCode.NOT_FOUND,
        message=f"No file named {name!r} in run {paths.slug!r}.",
        status_code=404,
    )
    # A bare filename only — reject any path separators / parent refs before touching the fs.
    if name != Path(name).name or name in ("", ".", ".."):
        raise not_found
    for directory in (paths.inputs, paths.outputs):
        candidate = (directory / name).resolve()
        try:
            candidate.relative_to(directory.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    raise not_found


# --------------------------------------------------------------------------- #
# endpoints
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[RunSummary], summary="List runs")
def list_runs(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[RunSummary]:
    """Every run in the vault, each with a one-line stage label from its kanban."""

    svc = service()
    summaries: list[RunSummary] = []
    for paths in svc.list_runs():
        board = svc.status(db, paths)
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

    svc = service()
    paths = svc.start_run(commodity=body.commodity, label=body.label, rehearsal=body.rehearsal)
    board = svc.status(db, paths)
    summary = _summary(paths, board)
    return RunDetail(**summary.model_dump(), kanban=board)


@router.get("/{slug}", response_model=RunDetail, summary="Read one run")
def get_run(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunDetail:
    """One run's summary + its full kanban board, or 404 if the slug isn't a real run."""

    svc = service()
    paths = resolve_paths(slug)
    board = svc.status(db, paths)
    summary = _summary(paths, board)
    return RunDetail(**summary.model_dump(), kanban=board)


# --------------------------------------------------------------------------- #
# run-scoped files (list + download) — how the console fetches setup/template/output workbooks
# --------------------------------------------------------------------------- #
@router.get("/{slug}/files", response_model=list[RunFile], summary="List a run's files")
def list_run_files(
    slug: str,
    user: CurrentUser,
) -> list[RunFile]:
    """The files in the run's inputs/ + outputs/ dirs, or 404 if the slug isn't a real run."""

    paths = resolve_paths(slug)
    return _run_files(paths)


@router.get("/{slug}/files/{name}", summary="Download a run file")
def download_run_file(
    slug: str,
    name: str,
    user: CurrentUser,
) -> FileResponse:
    """Stream a run file as an attachment, or 404 if the run/file is missing.

    Path-traversal safe: only a plain filename that resolves inside the run's inputs/ or outputs/
    is served (see `_resolve_run_file`); the response is an xlsx attachment the browser downloads.
    """

    paths = resolve_paths(slug)
    target = _resolve_run_file(paths, name)
    return FileResponse(
        path=target,
        media_type=_XLSX_MEDIA_TYPE,
        filename=target.name,
        content_disposition_type="attachment",
    )


@router.get("/{slug}/archive", summary="Download the whole run folder as a zip")
def download_run_archive(
    slug: str,
    user: CurrentUser,
) -> Response:
    """Stream the run's full folder set (skeleton + files) as one zip, or 404 if the run is missing.

    The zip carries the inputs/outputs/memory folder skeleton plus the run's files + manifests, so
    the console user can unzip it locally and drop each downloaded output into the folder it belongs
    to (see `build_run_zip`).
    """

    paths = resolve_paths(slug)
    return Response(
        content=build_run_zip(paths),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{slug}.zip"'},
    )


# --------------------------------------------------------------------------- #
# input chain — ingest the setup workbook + generate a round's bid template
# --------------------------------------------------------------------------- #
@router.post(
    "/{slug}/setup",
    response_model=IngestSetupResponse,
    summary="Ingest the setup/kickoff workbook",
)
def ingest_setup(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File(description="The filled setup/kickoff workbook (.xlsx).")],
) -> IngestSetupResponse:
    """Save the uploaded setup workbook into inputs/ and ingest it into a governed cycle.

    The bytes are written into the run's inputs/ via the governed `write_to_run`, then handed to
    `PilotService.ingest_setup`, which creates the cycle, links cycle_id.txt, and recomputes the
    kanban. Returns the new cycle id + the refreshed kanban. 404 if the run doesn't exist.
    """

    svc = service()
    paths = resolve_paths(slug)
    data = file.file.read()
    uploaded = write_to_run(paths, SUBDIR_INPUTS, stage_filename(1, "setup_kickoff"), data)
    cycle_id = svc.ingest_setup(db, paths, uploaded)
    board = svc.status(db, paths)
    return IngestSetupResponse(cycle_id=cycle_id, kanban=board)


@router.post(
    "/{slug}/rounds/{round}/template",
    response_model=GenerateTemplateResponse,
    summary="Generate a round's bid template",
)
def generate_bid_template(
    slug: str,
    round: Annotated[int, PathParam(ge=1)],
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> GenerateTemplateResponse:
    """Generate the round's owned bid template into inputs/ (downloadable via the file endpoint).

    Wraps `PilotService.generate_bid_template`; the run must already have a cycle (setup ingested
    first) — if it doesn't, a clean 400 (`gate_required`) is surfaced rather than a 500. Returns the
    generated filename + the refreshed kanban. 404 if the run doesn't exist.
    """

    svc = service()
    paths = resolve_paths(slug)
    try:
        generated = svc.generate_bid_template(db, paths, round)
    except ValueError as exc:
        raise _no_cycle_yet(slug, exc) from exc
    board = svc.status(db, paths)
    return GenerateTemplateResponse(filename=generated.name, kanban=board)


def _no_cycle_yet(slug: str, exc: Exception) -> AppError:
    """A clean 400 for the 'no cycle yet' gate (service raises ValueError before setup ingest)."""

    return AppError(
        code=ErrorCode.GATE_REQUIRED,
        message=f"Run {slug!r} has no cycle yet — ingest the setup workbook first.",
        status_code=400,
    )
