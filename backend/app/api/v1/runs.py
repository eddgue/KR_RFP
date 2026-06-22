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

import zipfile
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi import Path as PathParam
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.pilot_common import resolve_paths, resolve_round_id, resolve_run, service
from app.auth.deps import CurrentUser
from app.comms.resolvers import SupplierEmailDraft
from app.core.errors.taxonomy import AppError, ErrorCode
from app.domain.awd.read import AwardDetail, AwardSummary
from app.domain.eng.read import (
    AnalysisSummary,
    ScenarioComparisonRow,
    ScenarioDetail,
)
from app.pilot.deliverables import Deliverable, enumerate_deliverables
from app.pilot.models import Run
from app.pilot.run_repo import list_run_records
from app.pilot.status import kanban
from app.pilot.vault import RunPaths

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


class StrategyResponse(BaseModel):
    """The run's EFFECTIVE engine strategy — the resolved weights + the four safeties the next
    analysis will use (read straight off the cycle config the engine reads, never a copy)."""

    weight_preset: str
    weight_price: Decimal
    weight_coverage: Decimal
    weight_historical: Decimal
    weight_zrisk: Decimal
    weight_continuity: Decimal
    premium_ceiling: Decimal
    coverage_floor: Decimal
    conc_thresh: Decimal
    max_sup_dc: int


class UpdateStrategyRequest(BaseModel):
    """Set the run's engine strategy (persisted onto the cycle; the next analysis picks it up)."""

    weight_preset: str = Field(
        description="balanced | price_focus | coverage_focus | risk_averse | custom"
    )
    premium_ceiling: Decimal = Field(gt=0, le=1, description="Eligibility premium ceiling (0–1).")
    coverage_floor: Decimal = Field(gt=0, le=1, description="Eligibility coverage floor (0–1).")
    conc_thresh: Decimal = Field(gt=0, le=1, description="Concentration flag threshold (0–1).")
    max_sup_dc: int = Field(ge=1, description="Max suppliers per DC.")


class FreezeAwardRequest(BaseModel):
    """Promote a human-selected lens to a FROZEN award (the governed decision)."""

    analysis_run_id: str
    scenario_code: str = Field(default="B", description="The lens to freeze (default B).")
    award_code: str = Field(description="The buyer's award identifier (e.g. AWD-2026-TOMATO-1).")


class FreezeAwardResponse(BaseModel):
    """The frozen award's id + the scenario it was frozen from."""

    award_id: str
    scenario_code: str


class FinalizeRunResponse(BaseModel):
    """The result of finalizing (closing out) a run — closed flag + the closing deliverables.

    `closed` is True once the governed CLOSED event has landed; `award_id` is the FROZEN award the
    run is closed against; `won_suppliers` / `not_won_suppliers` count the award (won) + rejection
    (not-won) notices now available (render-on-request, nothing persisted).
    """

    closed: bool
    award_id: str
    won_suppliers: int = Field(description="Awarded suppliers — award notices available.")
    not_won_suppliers: int = Field(
        description="Participants with a lost lot — rejection notices available."
    )


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
# metadata helpers (commodity / label / stage / cycle from the pilot.run row, Slice 3)
# --------------------------------------------------------------------------- #
def _board_for(db: Session, run: Run, paths: RunPaths) -> dict[str, list[str]]:
    """The kanban board for a run, with the cycle link resolved from the DB row (not files).

    Run identity (and the cycle link) is DB-resolved (Slice 3): the kanban reads the governed cycle
    state for `run.cycle_id` and the file-presence signal (setup_present) from the vault folder
    while the dual-write era keeps the folder around. A run with no cycle yields a files-only board.
    """

    return kanban(db, run.cycle_id, paths)


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


def _has_cycle(db: Session, slug: str) -> bool:
    """True once setup has been ingested — the run row carries a cycle_id (DB-resolved, Slice 3).

    A durable, file-generation-independent signal: a returning user who ingested setup but hasn't
    generated a template yet still has the post-setup steps unlocked. Resolves the `pilot.run` row
    (404 if the run doesn't exist), so the award/comms routes that gate on a cycle stay DB-backed.
    """

    return bool(resolve_run(db, slug).cycle_id)


def _summary(run: Run, board: dict[str, list[str]]) -> RunSummary:
    return RunSummary(
        slug=run.slug,
        commodity=run.commodity,
        label=run.label,
        rehearsal=run.rehearsal,
        stage=_stage_label(board),
        has_cycle=bool(run.cycle_id),
    )


def _run_files(db: Session, run: Run) -> list[RunFile]:
    """Every deliverable the run can produce, projected from the DB (ADR-0018 Slice 5).

    The console's file list is `enumerate_deliverables` rendered on request — NOT a scan of the
    vault `inputs/`/`outputs/` dirs. Each item's `size_bytes` is the rendered byte length (the
    workbooks are deterministic DB-renders, E-39); `modified` is the request time (a render has no
    on-disk mtime). Names match exactly what the harness writes today.
    """

    now = datetime.now(UTC).isoformat()
    files: list[RunFile] = []
    for d in enumerate_deliverables(
        db, cycle_id=run.cycle_id, slug=run.slug, rehearsal=run.rehearsal
    ):
        files.append(
            RunFile(
                name=d.name,
                kind=d.kind,
                size_bytes=len(d.render(db)),
                modified=now,
            )
        )
    return files


def _resolve_deliverable(db: Session, run: Run, name: str) -> Deliverable:
    """Resolve a plain filename to the matching DB deliverable, or 404 (ADR-0018 Slice 5).

    The console serves a render, never a file off disk, so there is no path-traversal surface: only
    an exact match against an enumerated deliverable name is served (anything else is a clean 404).
    """

    for d in enumerate_deliverables(
        db, cycle_id=run.cycle_id, slug=run.slug, rehearsal=run.rehearsal
    ):
        if d.name == name:
            return d
    raise AppError(
        code=ErrorCode.NOT_FOUND,
        message=f"No file named {name!r} in run {run.slug!r}.",
        status_code=404,
    )


def _run_archive_zip(db: Session, run: Run) -> bytes:
    """An in-memory zip of every DB-rendered deliverable, under the run slug (ADR-0018 Slice 5).

    Replaces the on-disk `build_run_zip` dir-scan: each deliverable is rendered from the DB and
    written into the zip at `<slug>/<name>` so the buyer unzips a complete, self-describing folder.
    """

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in enumerate_deliverables(
            db, cycle_id=run.cycle_id, slug=run.slug, rehearsal=run.rehearsal
        ):
            zf.writestr(f"{run.slug}/{d.name}", d.render(db))
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# endpoints
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[RunSummary], summary="List runs")
def list_runs(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[RunSummary]:
    """Every run, from the `pilot.run` table (Slice 3 — DB-resolved, not a vault scan).

    Each run's stage label comes from its kanban (the governed cycle state + the vault folder's
    file-presence signal while the dual-write era keeps the folder around).
    """

    svc = service()
    summaries: list[RunSummary] = []
    for run in list_run_records(db):
        paths = svc.run_paths(run.slug)
        board = _board_for(db, run, paths)
        summaries.append(_summary(run, board))
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
    paths = svc.start_run(
        commodity=body.commodity, label=body.label, rehearsal=body.rehearsal, session=db
    )
    run = resolve_run(db, paths.slug)  # the just-dual-written pilot.run row
    board = _board_for(db, run, paths)
    summary = _summary(run, board)
    return RunDetail(**summary.model_dump(), kanban=board)


@router.get("/{slug}", response_model=RunDetail, summary="Read one run")
def get_run(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunDetail:
    """One run's summary + its full kanban board, or 404 if the slug isn't a real run."""

    svc = service()
    run = resolve_run(db, slug)
    paths = svc.run_paths(slug)
    board = _board_for(db, run, paths)
    summary = _summary(run, board)
    return RunDetail(**summary.model_dump(), kanban=board)


# --------------------------------------------------------------------------- #
# run-scoped files (list + download) — how the console fetches setup/template/output workbooks
# --------------------------------------------------------------------------- #
@router.get("/{slug}/files", response_model=list[RunFile], summary="List a run's files")
def list_run_files(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[RunFile]:
    """The run's deliverables, projected from the DB (Slice 5), or 404 if the run doesn't exist.

    Not a vault dir-scan: each item is what the run CAN produce (setup template, bid templates,
    sealed-analysis alignment workbooks, frozen-award guides, post-award docs), rendered on request.
    """

    run = resolve_run(db, slug)
    return _run_files(db, run)


@router.get("/{slug}/files/{name}", summary="Download a run file")
def download_run_file(
    slug: str,
    name: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Render the named deliverable from the DB and stream it as an attachment (Slice 5).

    The bytes are generated on request from the governed records (never read off disk); only an
    exact match against an enumerated deliverable name is served, so an unknown name is a clean 404.
    """

    run = resolve_run(db, slug)
    deliverable = _resolve_deliverable(db, run, name)
    return Response(
        content=deliverable.render(db),
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{deliverable.name}"'},
    )


@router.get("/{slug}/archive", summary="Download all the run's deliverables as a zip")
def download_run_archive(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Stream every deliverable as one in-memory zip (Slice 5), or 404 if the run doesn't exist.

    Each deliverable is rendered from the DB and written into the zip at `<slug>/<name>` — a
    complete, self-describing folder the buyer unzips locally. Nothing is read off disk.
    """

    run = resolve_run(db, slug)
    return Response(
        content=_run_archive_zip(db, run),
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
    """Stream the uploaded setup workbook straight into ingest — no file is written (Slice 4).

    The bytes are read into memory and handed to `PilotService.ingest_setup_bytes`, which creates
    the governed cycle and links it on the run's `pilot.run` row — the uploaded workbook is NEVER
    persisted to disk (ADR-0018). Returns the new cycle id + the refreshed kanban. 404 if the run
    doesn't exist; 409 (conflict) if the run already has a cycle (setup is once-per-run — a second
    ingest would orphan the prior cycle).
    """

    svc = service()
    paths = resolve_paths(db, slug)
    cycle_id = svc.ingest_setup_bytes(db, paths, file.file.read())
    board = _board_for(db, resolve_run(db, slug), paths)
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
    paths = resolve_paths(db, slug)
    resolve_round_id(db, paths, round)  # gate_required (no cycle) vs validation_error (bad round)
    generated = svc.generate_bid_template(db, paths, round)
    board = _board_for(db, resolve_run(db, slug), paths)
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
    paths = resolve_paths(db, slug)
    resolve_round_id(db, paths, round)  # gate_required (no cycle) vs validation_error (bad round)
    out_path = svc.run_round(db, paths, round, actor=user.username)

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
    "/{slug}/strategy",
    response_model=StrategyResponse,
    summary="Read the run's engine strategy (resolved weights + safeties)",
)
def get_strategy(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> StrategyResponse:
    """The EFFECTIVE strategy the next analysis will use. 400 `gate_required` if no cycle yet."""

    svc = service()
    paths = resolve_paths(db, slug)
    if not _has_cycle(db, slug):
        raise AppError(
            code=ErrorCode.GATE_REQUIRED,
            message="No cycle yet — ingest the setup workbook first.",
            status_code=400,
        )
    return StrategyResponse(**svc.get_strategy(db, paths))


@router.put(
    "/{slug}/strategy",
    response_model=StrategyResponse,
    summary="Set the run's engine strategy (persisted onto the cycle)",
)
def set_strategy(
    slug: str,
    body: UpdateStrategyRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> StrategyResponse:
    """Persist the weights preset + the four safeties onto the cycle; the next analysis uses them.

    400 `gate_required` if no cycle yet, `validation_error` on an unknown preset / out-of-range
    safety. The change is config (pre-decision); the sealed analysis tamper-seals the effective
    config it actually ran under (C2).
    """

    svc = service()
    paths = resolve_paths(db, slug)
    if not _has_cycle(db, slug):
        raise AppError(
            code=ErrorCode.GATE_REQUIRED,
            message="No cycle yet — ingest the setup workbook first.",
            status_code=400,
        )
    try:
        updated = svc.set_strategy(
            db,
            paths,
            weight_preset=body.weight_preset,
            premium_ceiling=body.premium_ceiling,
            coverage_floor=body.coverage_floor,
            conc_thresh=body.conc_thresh,
            max_sup_dc=body.max_sup_dc,
            actor=user.username,
        )
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR, message=str(exc), status_code=400
        ) from exc
    return StrategyResponse(**updated)


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
    paths = resolve_paths(db, slug)
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
    paths = resolve_paths(db, slug)
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
    paths = resolve_paths(db, slug)
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
    paths = resolve_paths(db, slug)
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


@router.post(
    "/{slug}/finalize",
    response_model=FinalizeRunResponse,
    summary="Finalize & close out a run (governed terminal action)",
)
def finalize_run(
    slug: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> FinalizeRunResponse:
    """Terminal governed close-out of a run (`PilotService.finalize_run`) — the design's "Finalize
    & close run" step.

    After an award is FROZEN, the buyer takes this terminal action: the run is locked CLOSED (a
    governed `CLOSED` audit event lands, entity = the cycle, actor = the authenticated user) and the
    closing deliverables — the award notices (won) + rejection notices (not-won) — become available
    (render-on-request; nothing is persisted, ADR-0018/E-42). This is NOT a delete (the run + its
    governed records remain). 404 if the run doesn't exist; 409 (conflict) if it has no frozen award
    yet (an un-awarded run can't be closed out). Idempotent: re-finalizing a closed run returns the
    same summary and emits no second CLOSED event.
    """

    svc = service()
    paths = resolve_paths(db, slug)
    summary = svc.finalize_run(db, paths, actor=user.username)
    return FinalizeRunResponse(
        closed=summary.closed,
        award_id=summary.award_id,
        won_suppliers=summary.won_suppliers,
        not_won_suppliers=summary.not_won_suppliers,
    )


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
    paths = resolve_paths(db, slug)
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

    paths = resolve_paths(db, slug)
    # An award can't exist before a cycle does — treat "no cycle" as "no such award" (404).
    if not _has_cycle(db, slug):
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
    paths = resolve_paths(db, slug)
    # Scope to THIS run's cycle (another run's award / no cycle is a 404) and fetch the award's real
    # cells in one shot — `award_detail` raises ValueError when the id isn't ours.
    if not _has_cycle(db, slug):
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

    paths = resolve_paths(db, slug)
    if not _has_cycle(db, slug):
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

    paths = resolve_paths(db, slug)
    if not _has_cycle(db, slug):
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

    paths = resolve_paths(db, slug)
    _ensure_analysis(db, paths, slug, analysis_run_id)
    return service().feedback_email_drafts(db, paths, analysis_run_id, buyer_name=user.username)


def _ensure_analysis(db: Session, paths: RunPaths, slug: str, analysis_run_id: str) -> None:
    """Guard the scenario/award reads: a cycle must exist (400) and the run must be one of its
    SEALED analyses (404) — so an unknown / other-run analysis id is never silently served.
    """

    if not _has_cycle(db, slug):
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
