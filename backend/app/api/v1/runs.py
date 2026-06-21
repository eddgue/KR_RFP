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
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi import Path as PathParam
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.pilot_common import resolve_paths, resolve_round_id, service
from app.auth.deps import CurrentUser
from app.comms.resolvers import SupplierEmailDraft
from app.core.errors.taxonomy import AppError, ErrorCode
from app.domain.awd.read import AwardDetail, AwardSummary
from app.domain.eng.read import (
    AnalysisSummary,
    ScenarioComparisonRow,
    ScenarioDetail,
)
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
    has_cycle: bool = Field(
        description="True once setup has been ingested (a cycle exists) — the durable signal the "
        "console uses to unlock the post-setup steps, independent of any generated file."
    )


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


class RunAnalysisResponse(BaseModel):
    """The result of running a round's alignment analysis: the sealed run summary + scenario count.

    `version` is the 1-based ordinal of this sealed run among the cycle's runs; `analysis_run_id` is
    the handle the web threads through the scenario reads + the freeze; `scenario_count` is the
    number of lenses sealed (A-G, normally 7).
    """

    version: int
    analysis_run_id: str
    round_number: int
    sealed_at: datetime
    scenario_count: int
    filename: str = Field(description="The versioned alignment workbook written into outputs/.")


class FreezeAwardRequest(BaseModel):
    """Promote a human-selected lens to a FROZEN award (the governed decision)."""

    analysis_run_id: str
    scenario_code: str = Field(default="B", description="The lens to freeze (default B).")
    award_code: str = Field(description="The buyer's award identifier (e.g. AWD-2026-TOMATO-1).")


class FreezeAwardResponse(BaseModel):
    """The frozen award's id + the scenario it was frozen from."""

    award_id: str
    scenario_code: str


class AdjustmentLineChange(BaseModel):
    """One cell repriced by a post-award adjustment — the cell key + its new $/case."""

    dc_id: str
    lot_id: str
    tf_id: str
    supplier_id: str
    new_price: float = Field(gt=0, description="The cell's new all-in $/case (must be > 0).")


class RecordAdjustmentRequest(BaseModel):
    """Append an append-only post-award adjustment layer to a frozen award (governed decision)."""

    adjustment_type: str = Field(min_length=1, description="The layer's type (e.g. MARKET_HIKE).")
    effective_date: date = Field(description="The business date the new prices take effect.")
    reason: str = Field(min_length=1, description="Why the layer was applied (stored verbatim).")
    changes: list[AdjustmentLineChange] = Field(
        min_length=1, description="The cells repriced (at least one)."
    )


class RecordAdjustmentResponse(BaseModel):
    """The recorded layer's new version + the regenerated post-award document filename."""

    award_id: str
    version_no: int
    filename: str


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


def _has_cycle(paths: RunPaths) -> bool:
    """True once setup has been ingested — the run's cycle_id.txt exists and is non-empty.

    A durable, file-generation-independent signal: a returning user who ingested setup but hasn't
    generated a template yet should still have the post-setup steps unlocked (re-uploading setup
    would re-create the cycle).
    """

    return paths.cycle_id_file.exists() and bool(
        paths.cycle_id_file.read_text(encoding="utf-8").strip()
    )


def _summary(paths: RunPaths, board: dict[str, list[str]]) -> RunSummary:
    header = read_status(paths)
    return RunSummary(
        slug=paths.slug,
        commodity=header.get("Commodity", ""),
        label=_label_from_notes(paths),
        rehearsal=is_rehearsal(paths),
        stage=_stage_label(board),
        has_cycle=_has_cycle(paths),
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

    Wraps `PilotService.generate_bid_template`. The round is pre-validated (shared with the bids
    endpoints) so the two failure modes are DISTINCT clean 400s: `gate_required` when there's no
    cycle yet (setup not ingested), `validation_error` when the round is out of range — never a 500,
    and an out-of-range round is never mislabeled "no cycle yet". Returns the generated filename +
    the refreshed kanban. 404 if the run doesn't exist.
    """

    svc = service()
    paths = resolve_paths(slug)
    resolve_round_id(db, paths, round)  # gate_required (no cycle) vs validation_error (bad round)
    generated = svc.generate_bid_template(db, paths, round)
    board = svc.status(db, paths)
    return GenerateTemplateResponse(filename=generated.name, kanban=board)


# --------------------------------------------------------------------------- #
# web alignment / scenario slice — run a round's analysis, list it, compare the
# seven lenses, inspect one lens cell-by-cell, and freeze a chosen lens. Every
# route reuses PilotService (isolate_db=False) — no engine logic is reimplemented.
# --------------------------------------------------------------------------- #
@router.post(
    "/{slug}/rounds/{round}/analysis",
    response_model=RunAnalysisResponse,
    summary="Run a round's alignment analysis (seals eng.* + writes the workbook)",
)
def run_analysis(
    slug: str,
    round: Annotated[int, PathParam(ge=1)],
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunAnalysisResponse:
    """Run the engine on a round → a sealed `eng.analysis_run` (+ the versioned alignment workbook).

    Wraps `PilotService.run_round`. The round is pre-validated (`resolve_round_id`) so the two
    failure modes are DISTINCT clean 400s: `gate_required` when there's no cycle yet (setup not
    ingested), `validation_error` when the round is out of range. Returns the sealed run summary
    (version ordinal, analysis_run_id, sealed time, lens count) the web threads into the scenario
    reads + the freeze. 404 if the run doesn't exist.
    """

    svc = service()
    paths = resolve_paths(slug)
    resolve_round_id(db, paths, round)  # gate_required (no cycle) vs validation_error (bad round)
    out_path = svc.run_round(db, paths, round)

    # The just-sealed run is the cycle's latest; surface its typed summary + the lens count.
    analyses = svc.list_analyses(db, paths)
    if not analyses:  # pragma: no cover — run_round always seals one
        raise AppError(
            code=ErrorCode.INTERNAL,
            message="Analysis ran but no sealed run was found.",
            status_code=500,
        )
    latest = analyses[-1]
    scenario_count = len(svc.scenario_comparison(db, paths, latest.analysis_run_id))
    return RunAnalysisResponse(
        version=latest.version,
        analysis_run_id=latest.analysis_run_id,
        round_number=latest.round_number,
        sealed_at=latest.sealed_at,
        scenario_count=scenario_count,
        filename=out_path.name,
    )


@router.get(
    "/{slug}/analysis",
    response_model=list[AnalysisSummary],
    summary="List a run's sealed analyses",
)
def list_run_analyses(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[AnalysisSummary]:
    """The run's SEALED analysis runs (oldest first, each with its version ordinal + round).

    Empty list when the run has no cycle / no sealed run yet (a list endpoint, never a gate). 404 if
    the run doesn't exist.
    """

    svc = service()
    paths = resolve_paths(slug)
    return svc.list_analyses(db, paths)


@router.get(
    "/{slug}/analysis/{analysis_run_id}/scenarios",
    response_model=list[ScenarioComparisonRow],
    summary="Compare the seven lenses for a sealed analysis",
)
def get_scenario_comparison(
    slug: str,
    analysis_run_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[ScenarioComparisonRow]:
    """The seven lenses A-G side by side — spend, Δ vs A, savings, counts, breaches (which lens).

    Numbers are identical to the alignment workbook's Scenario Comparison tab (shared computation).
    400 (`gate_required`) before any cycle; 404 for an unknown run / analysis run.
    """

    svc = service()
    paths = resolve_paths(slug)
    _ensure_analysis(db, paths, slug, analysis_run_id)
    return svc.scenario_comparison(db, paths, analysis_run_id)


@router.get(
    "/{slug}/analysis/{analysis_run_id}/scenarios/{scenario_code}",
    response_model=ScenarioDetail,
    summary="Inspect one lens cell-by-cell",
)
def get_scenario_detail(
    slug: str,
    analysis_run_id: str,
    scenario_code: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ScenarioDetail:
    """One lens's per-cell competitive grid (every supplier's $/case, min, incumbent, awarded share)
    plus the savings headline. 400 (`gate_required`) before any cycle; 404 unknown run / analysis;
    `validation_error` (400) for an unknown scenario code on the run.
    """

    svc = service()
    paths = resolve_paths(slug)
    _ensure_analysis(db, paths, slug, analysis_run_id)
    try:
        return svc.scenario_detail(db, paths, analysis_run_id, scenario_code)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Scenario {scenario_code!r} is not a lens on analysis {analysis_run_id!r}.",
            status_code=400,
        ) from exc


@router.post(
    "/{slug}/awards/freeze",
    response_model=FreezeAwardResponse,
    summary="Freeze a chosen lens into an award (governed decision)",
)
def freeze_award(
    slug: str,
    body: FreezeAwardRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> FreezeAwardResponse:
    """Promote the human-selected lens to a FROZEN award (`PilotService.freeze_award`).

    A governed decision (ADR-0006: the human asserts the award) — the FROZEN audit event fires
    inside the award domain on this path. 400 (`gate_required`) before any cycle; 404 unknown run;
    `validation_error` (400) for an unknown analysis run / scenario. Idempotent: re-freezing the
    same (run, scenario) returns the existing award_id. Returns `{award_id, scenario_code}`.
    """

    svc = service()
    paths = resolve_paths(slug)
    _ensure_analysis(db, paths, slug, body.analysis_run_id)
    try:
        award_id = svc.freeze_award(
            db,
            paths,
            analysis_run_id=body.analysis_run_id,
            scenario_code=body.scenario_code,
            award_code=body.award_code,
            actor=user.username,
        )
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Could not freeze award: {exc}",
            status_code=400,
        ) from exc
    return FreezeAwardResponse(award_id=award_id, scenario_code=body.scenario_code)


@router.get(
    "/{slug}/awards",
    response_model=list[AwardSummary],
    summary="List a run's frozen awards",
)
def list_run_awards(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[AwardSummary]:
    """The run's FROZEN awards (oldest first, each with its line count + latest layer version).

    Empty list when the run has no cycle / no frozen award yet (a list endpoint, never a gate). 404
    if the run doesn't exist.
    """

    svc = service()
    paths = resolve_paths(slug)
    return svc.list_awards(db, paths)


@router.get(
    "/{slug}/awards/{award_id}",
    response_model=AwardDetail,
    summary="Inspect one frozen award (baseline + effective + version history)",
)
def get_run_award(
    slug: str,
    award_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AwardDetail:
    """One frozen award: baseline lines, the EFFECTIVE price per cell (baseline overlaid by every
    layer), and the full version history (v0 FROZEN → vN). 404 if the run / award doesn't exist.
    """

    paths = resolve_paths(slug)
    # An award can't exist before a cycle does — treat "no cycle" as "no such award" (404).
    if not _has_cycle(paths):
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        )
    try:
        return service().award_detail(db, paths, award_id)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        ) from exc


@router.post(
    "/{slug}/awards/{award_id}/adjustments",
    response_model=RecordAdjustmentResponse,
    summary="Record a post-award adjustment layer (governed)",
)
def record_award_adjustment(
    slug: str,
    award_id: str,
    body: RecordAdjustmentRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RecordAdjustmentResponse:
    """Append an append-only, date-stamped post-award adjustment LAYER to a frozen award.

    A governed decision (ADR-0014: the baseline is never edited; a price move is a new versioned
    layer) — the `CREATED` audit event fires inside the award domain on this path. The award is
    scoped to THIS run's cycle and every change must reference a cell that exists on the award, so a
    cross-run id is a 404 and an off-award cell is a clean 400 (never a phantom layer). Returns the
    new `version_no` + the regenerated post-award document filename. 404 if the run / award is
    unknown; 400 (`validation_error`) for an off-award cell or a service rejection.
    """

    svc = service()
    paths = resolve_paths(slug)
    # Scope to THIS run's cycle (another run's award / no cycle is a 404) and fetch the award's real
    # cells in one shot — `award_detail` raises ValueError when the id isn't ours.
    if not _has_cycle(paths):
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        )
    try:
        detail = svc.award_detail(db, paths, award_id)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        ) from exc

    valid_cells = {(line.dc_id, line.lot_id, line.tf_id, line.supplier_id) for line in detail.lines}
    keys = [(c.dc_id, c.lot_id, c.tf_id, c.supplier_id) for c in body.changes]
    unknown = [key for key in keys if key not in valid_cells]
    if unknown:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"{len(unknown)} change(s) reference a cell not on award {award_id!r}.",
            status_code=400,
        )
    # One price per cell per layer: the DB has a unique (adjustment, cell) index, so a repeated cell
    # would 500 on insert — reject it as a clean 400 up front (which new_price would even win?).
    if len(set(keys)) != len(keys):
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="A cell is repeated in changes; adjust each cell at most once per layer.",
            status_code=400,
        )

    line_changes = [
        (c.dc_id, c.lot_id, c.tf_id, c.supplier_id, Decimal(str(c.new_price))) for c in body.changes
    ]
    try:
        out_path = svc.record_adjustment(
            db,
            paths,
            award_id=award_id,
            adjustment_type=body.adjustment_type,
            effective_date=body.effective_date,
            reason=body.reason,
            line_changes=line_changes,
            actor=user.username,
        )
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Could not record the adjustment: {exc}",
            status_code=400,
        ) from exc

    updated = svc.award_detail(db, paths, award_id)
    return RecordAdjustmentResponse(
        award_id=award_id, version_no=updated.latest_version, filename=out_path.name
    )


@router.get(
    "/{slug}/awards/{award_id}/comms/award",
    response_model=list[SupplierEmailDraft],
    summary="Award-notification email drafts (one per awarded supplier)",
)
def get_award_comms_drafts(
    slug: str,
    award_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[SupplierEmailDraft]:
    """One template-merge award-notification DRAFT per awarded supplier (E-37) — draft-only.

    Fills the authored award template from governed data; the authenticated user is the draft's
    `[#BuyerName]`. 404 if the run / award is unknown (scoped to the run's cycle).
    """

    paths = resolve_paths(slug)
    if not _has_cycle(paths):
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        )
    try:
        return service().award_email_drafts(db, paths, award_id, buyer_name=user.username)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        ) from exc


@router.get(
    "/{slug}/awards/{award_id}/comms/rejection",
    response_model=list[SupplierEmailDraft],
    summary="Non-selection email drafts (one per supplier with a lost lot)",
)
def get_rejection_comms_drafts(
    slug: str,
    award_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[SupplierEmailDraft]:
    """One template-merge non-selection ("RFP Results") DRAFT per supplier with a lost lot (E-37).

    Keyed on the frozen award; each lost lot is itemized with the supplier's price, the market-low
    benchmark, the % gap, and a data-centered reason. The authenticated user is the draft's
    `[#BuyerName]`. 404 if the run / award is unknown (scoped to the run's cycle).
    """

    paths = resolve_paths(slug)
    if not _has_cycle(paths):
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        )
    try:
        return service().rejection_email_drafts(db, paths, award_id, buyer_name=user.username)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No frozen award {award_id!r} on run {slug!r}.",
            status_code=404,
        ) from exc


@router.get(
    "/{slug}/analysis/{analysis_run_id}/comms/feedback",
    response_model=list[SupplierEmailDraft],
    summary="Round-feedback email drafts (one per above-benchmark supplier)",
)
def get_feedback_comms_drafts(
    slug: str,
    analysis_run_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[SupplierEmailDraft]:
    """One template-merge round-feedback DRAFT per supplier above the market-low benchmark (E-37).

    Splits hard asks (ineligible — fix to keep participating) from soft asks (eligible but above the
    benchmark) over the sealed analysis's scored round; the authenticated user is the draft's
    `[#BuyerName]`. 400 (`gate_required`) before any cycle; 404 for an unknown run / analysis run.
    """

    paths = resolve_paths(slug)
    _ensure_analysis(db, paths, slug, analysis_run_id)
    return service().feedback_email_drafts(db, paths, analysis_run_id, buyer_name=user.username)


def _ensure_analysis(db: Session, paths: RunPaths, slug: str, analysis_run_id: str) -> None:
    """Guard the scenario/award reads: a cycle must exist (400) and the run must be one of its
    SEALED analyses (404) — so an unknown / other-run analysis id is never silently served.
    """

    if not _has_cycle(paths):
        raise AppError(
            code=ErrorCode.GATE_REQUIRED,
            message=f"Run {slug!r} has no sealed analysis yet — run a round's analysis first.",
            status_code=400,
        )
    known = {a.analysis_run_id for a in service().list_analyses(db, paths)}
    if analysis_run_id not in known:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No sealed analysis {analysis_run_id!r} on run {slug!r}.",
            status_code=404,
        )
