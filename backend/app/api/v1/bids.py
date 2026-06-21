"""Bids surface (`/api/v1/bids`): import a round's bids + list them at one grain (PLAN §5).

Wraps the existing `app.pilot.service.PilotService` (shared wiring in `app.api.v1.pilot_common`) —
NO new bid write path is introduced. Import drives the governed ingest methods: the STRICT
key-validated path (`ingest_bids`) for files returned on our owned template, and the FLEXIBLE
"take my file as-is" path (`ingest_any`) for a supplier's own messy sheet — propose-then-confirm,
so the buyer confirms the inferred column mapping before anything is written. The list endpoint
reads the run's persisted `bid.bid_line` rows for a round at the identity grain. Every route is
authenticated (`get_current_user`).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.pilot_common import resolve_round_id, resolve_run, service
from app.auth.deps import CurrentUser
from app.core.errors.taxonomy import AppError, ErrorCode
from app.domain.bid.models import BidLine
from app.pilot.flex_ingest import ColumnMapping, MappingProposal
from app.pilot.service import BidIngestResult
from app.pilot.status import kanban
from app.pilot.vault import RunPaths

router = APIRouter()


# --------------------------------------------------------------------------- #
# response models
# --------------------------------------------------------------------------- #
class ColumnMappingView(BaseModel):
    """One inferred column → field mapping inside a `MappingProposal` (JSON-safe)."""

    field: str = Field(description="The mapped bid field (supplier/dc/lot/all_in/fob/volume).")
    column_index: int = Field(description="1-based column position in the supplier's messy sheet.")
    source_header: str
    basis: str = Field(description="How it was decided: 'header', 'values', or 'header+values'.")
    confidence: Literal["high", "medium", "low"]


class MappingProposalView(BaseModel):
    """The inferred mapping the console SHOWS the buyer to confirm before a flexible ingest."""

    sheet_name: str
    header_row: int
    mappings: dict[str, ColumnMappingView]
    ambiguities: list[str]
    is_confident: bool = Field(
        description="True when every identity field + a price field mapped with nothing ambiguous."
    )
    summary: str = Field(description="A plain-language summary of the mapping for the buyer.")


class ProposeImportResponse(BaseModel):
    """Flexible import, confirm=false: the proposal to review; NOTHING is written to the run."""

    proposal: MappingProposalView


class IngestedResponse(BaseModel):
    """A completed import: how many bid lines persisted + the run's refreshed kanban.

    The quarantine/supersede/capacity counts are RETURNED here (ADR-0018 Slice 4) instead of being
    appended to NOTES.md — the web console surfaces them to the buyer and nothing hits disk.
    `superseded` is how many prior bid lines a re-send replaced; `capacity_loaded` is how many
    stated per-cell ceilings landed; `quarantined_bids`/`quarantined_capacity` are rows the strict
    path dropped (key mismatch / bad number), surfaced so they're never silently lost.
    """

    ingested: int
    superseded: int = 0
    capacity_loaded: int = 0
    quarantined_bids: int = 0
    quarantined_capacity: int = 0
    kanban: dict[str, list[str]]


class BidLineView(BaseModel):
    """A reviewer-friendly view of one persisted `bid.bid_line` row (identity + price + status)."""

    bid_line_id: str
    supplier_id: str
    dc_id: str
    lot_id: str
    item_id: str
    tf_id: str
    fiscal_period_id: str | None
    currency_code: str
    price_basis: str
    submitted_all_in_case: float | None
    fob_case: float | None
    price_basis_resolved: str | None
    volume_minimum_cases: float | None
    transit_days: int | None
    validity_status: str
    is_scoreable: bool
    is_awardable: bool
    incomplete_reason_code: str | None


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _mapping_view(proposal: MappingProposal) -> MappingProposalView:
    """Serialize a `MappingProposal` (a dataclass) into the JSON-safe response view."""

    return MappingProposalView(
        sheet_name=proposal.sheet_name,
        header_row=proposal.header_row,
        mappings={field: _column_view(m) for field, m in proposal.mappings.items()},
        ambiguities=list(proposal.ambiguities),
        is_confident=proposal.is_confident,
        summary=proposal.describe(),
    )


def _column_view(mapping: ColumnMapping) -> ColumnMappingView:
    return ColumnMappingView(
        field=mapping.field,
        column_index=mapping.column_index,
        source_header=mapping.source_header,
        basis=mapping.basis,
        confidence=_confidence(mapping.confidence),
    )


def _confidence(value: str) -> Literal["high", "medium", "low"]:
    if value in ("high", "medium", "low"):
        return value  # type: ignore[return-value]
    return "low"


def _bid_line_view(row: BidLine) -> BidLineView:
    return BidLineView(
        bid_line_id=row.bid_line_id,
        supplier_id=row.supplier_id,
        dc_id=row.dc_id,
        lot_id=row.lot_id,
        item_id=row.item_id,
        tf_id=row.tf_id,
        fiscal_period_id=row.fiscal_period_id,
        currency_code=row.currency_code,
        price_basis=row.price_basis,
        submitted_all_in_case=_num(row.submitted_all_in_case),
        fob_case=_num(row.fob_case),
        price_basis_resolved=row.price_basis_resolved,
        volume_minimum_cases=_num(row.volume_minimum_cases),
        transit_days=row.transit_days,
        validity_status=row.validity_status,
        is_scoreable=row.is_scoreable,
        is_awardable=row.is_awardable,
        incomplete_reason_code=row.incomplete_reason_code,
    )


def _num(value: Any) -> float | None:
    """Coerce a Numeric/Decimal column to a JSON float (None passes through)."""

    return None if value is None else float(value)


# --------------------------------------------------------------------------- #
# endpoints
# --------------------------------------------------------------------------- #
@router.post(
    "/import",
    response_model=ProposeImportResponse | IngestedResponse,
    summary="Import a round's bids (strict or flexible)",
)
def import_bids(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File(description="The returned bid file (.xlsx).")],
    run: Annotated[str, Form(description="The run slug the bids belong to.")],
    round: Annotated[int, Form(ge=1, description="The 1-based round number.")],
    mode: Annotated[Literal["strict", "flexible"], Form(description="Ingest mode.")],
    confirm: Annotated[
        bool, Form(description="Flexible only: apply the inferred mapping + ingest.")
    ] = False,
) -> ProposeImportResponse | IngestedResponse:
    """Import a round's bids, strict (owned template) or flexible (supplier's own sheet).

    The uploaded file is streamed straight into ingest and NEVER written to disk (ADR-0018 Slice 4):

    * `mode=strict` — ingest the owned-template bytes via the key-validated path
      (`ingest_bids_bytes`); returns `{ingested, …counts, kanban}`.
    * `mode=flexible`, `confirm=false` — infer the messy file's column mapping
      (`ingest_any_bytes`, confirm=False) and return `{proposal}`; NOTHING is written.
    * `mode=flexible`, `confirm=true` — apply the confirmed mapping + ingest
      (`ingest_any_bytes`, confirm=True); returns `{ingested, …counts, kanban}`.

    404 if the run doesn't exist; 400 if there's no cycle yet / the round is out of range.
    """

    svc = service()
    run_row = resolve_run(db, run)  # 404 if no such run (DB-resolved identity, Slice 3)
    paths = svc.run_paths(run)
    # Validate the round against the cycle up front so a bad round is a clean 400, not a 500 deep
    # in the service (so even flexible-propose, which writes nothing, rejects an impossible round).
    resolve_round_id(db, paths, round)
    data = file.file.read()

    if mode == "strict":
        strict_result = _ingest_bids_bytes(svc, db, paths, round, data, actor=user.username)
        return _ingested_response(strict_result, kanban(db, run_row.cycle_id, paths))

    if not confirm:
        # Propose: infer the mapping from the bytes in memory and return it — nothing is written,
        # nothing ever touched disk (no scratch file to clean up).
        proposal = svc.ingest_any_bytes(db, paths, round, data, confirm=False, actor=user.username)
        assert isinstance(proposal, MappingProposal)  # noqa: S101 — confirm=False path returns one
        return ProposeImportResponse(proposal=_mapping_view(proposal))

    flex_result = svc.ingest_any_bytes(db, paths, round, data, confirm=True, actor=user.username)
    assert isinstance(flex_result, BidIngestResult)  # noqa: S101 — confirm=True returns the result
    return _ingested_response(flex_result, kanban(db, run_row.cycle_id, paths))


@router.get("", response_model=list[BidLineView], summary="List a round's ingested bids")
def list_bids(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    run: Annotated[str, Query(description="The run slug.")],
    round: Annotated[int, Query(ge=1, description="The 1-based round number.")],
) -> list[BidLineView]:
    """The run's persisted `bid.bid_line` rows for a round, at the identity grain.

    Scopes to the run's cycle + the round's `round_id` (resolved from the cycle), so it returns
    exactly this run's ingested bids for that round. 404 if the run doesn't exist; 400 if there's no
    cycle yet / the round is out of range.
    """

    run_row = resolve_run(db, run)  # 404 if no such run (DB-resolved identity, Slice 3)
    paths = service().run_paths(run)
    round_id = resolve_round_id(db, paths, round)
    cycle_id = run_row.cycle_id or ""
    # OPTION B (INTAKE §1a): bids are STORED flat at the 13 fiscal periods (one row per period in a
    # timeframe's span). This list is the IDENTITY grain (one row per supplier × dc × lot × item ×
    # tf), so collapse the fanned period rows to ONE representative per cell with DISTINCT ON — the
    # fanned rows share an identical payload, so any one represents the cell (a tf-grain NULL-period
    # row is its own representative). Keeps the listing contract at the identity grain.
    # Only ACTIVE (`is_scoreable`) rows are listed — mirrors the engine's `_read_bid_lines` filter
    # so the listing shows the CURRENT submission per cell. A re-submission supersedes prior rows
    # (flips them non-scoreable, never hard-deletes); without this filter the DISTINCT ON could
    # surface a superseded row as the cell's representative.
    rows = (
        db.execute(
            select(BidLine)
            .where(
                BidLine.cycle_id == cycle_id,
                BidLine.round_id == round_id,
                BidLine.is_scoreable.is_(True),
            )
            .distinct(
                BidLine.supplier_id,
                BidLine.dc_id,
                BidLine.lot_id,
                BidLine.item_id,
                BidLine.tf_id,
            )
            .order_by(
                BidLine.supplier_id,
                BidLine.dc_id,
                BidLine.lot_id,
                BidLine.item_id,
                BidLine.tf_id,
                BidLine.fiscal_period_id.nulls_last(),
                BidLine.bid_line_id,
            )
        )
        .scalars()
        .all()
    )
    return [_bid_line_view(row) for row in rows]


def _ingest_bids_bytes(
    svc: Any, db: Session, paths: RunPaths, round_no: int, data: bytes, *, actor: str
) -> BidIngestResult:
    """Run the strict key-validated bytes ingest, mapping a malformed/mismatched file to a 400."""

    try:
        result = svc.ingest_bids_bytes(db, paths, round_no, data, actor=actor)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Could not ingest the Round {round_no} bid file: {exc}",
            status_code=400,
        ) from exc
    assert isinstance(result, BidIngestResult)  # noqa: S101
    return result


def _ingested_response(result: BidIngestResult, board: dict[str, list[str]]) -> IngestedResponse:
    """Shape a `BidIngestResult` + the refreshed kanban into the response (counts, no NOTES)."""

    return IngestedResponse(
        ingested=result.ingested,
        superseded=result.superseded,
        capacity_loaded=result.capacity_loaded,
        quarantined_bids=result.quarantined_bids,
        quarantined_capacity=result.quarantined_capacity,
        kanban=board,
    )
