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

from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.pilot_common import resolve_paths, resolve_round_id, service
from app.auth.deps import CurrentUser
from app.core.errors.taxonomy import AppError, ErrorCode
from app.domain.bid.models import BidLine
from app.pilot.flex_ingest import ColumnMapping, MappingProposal
from app.pilot.vault import SUBDIR_INPUTS, RunPaths, stage_filename, write_to_run

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
    """A completed import: how many bid lines persisted + the run's refreshed kanban."""

    ingested: int
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

    * `mode=strict` — save the file into inputs/ and ingest via the key-validated path
      (`ingest_bids`); returns `{ingested, kanban}`.
    * `mode=flexible`, `confirm=false` — infer the messy file's column mapping (`ingest_any`,
      confirm=False) and return `{proposal}`; NOTHING is written.
    * `mode=flexible`, `confirm=true` — apply the confirmed mapping + ingest (`ingest_any`,
      confirm=True); returns `{ingested, kanban}`.

    404 if the run doesn't exist; 400 if there's no cycle yet / the round is out of range.
    """

    svc = service()
    paths = resolve_paths(run)
    # Validate the round against the cycle up front so a bad round is a clean 400, not a 500 deep
    # in the service (so even flexible-propose, which writes nothing, rejects an impossible round).
    resolve_round_id(db, paths, round)
    data = file.file.read()

    if mode == "strict":
        uploaded = write_to_run(
            paths, SUBDIR_INPUTS, stage_filename(_stage(round), f"round{round}_bids_uploaded"), data
        )
        count = _ingest_bids(svc, db, paths, round, uploaded)
        return IngestedResponse(ingested=count, kanban=svc.status(db, paths))

    # flexible — write the bytes to a temp scratch path inside inputs/ so the service reads a file.
    scratch = write_to_run(paths, SUBDIR_INPUTS, f"round{round}_raw_supplier_drop.xlsx", data)
    if not confirm:
        proposal = svc.ingest_any(db, paths, round, scratch, confirm=False)
        # Propose writes nothing governed; drop the scratch upload so a rejected proposal is clean.
        scratch.unlink(missing_ok=True)
        assert isinstance(proposal, MappingProposal)  # noqa: S101 — confirm=False path returns one
        return ProposeImportResponse(proposal=_mapping_view(proposal))

    result = svc.ingest_any(db, paths, round, scratch, confirm=True)
    assert isinstance(result, int)  # noqa: S101 — confirm=True path returns the ingested count
    return IngestedResponse(ingested=result, kanban=svc.status(db, paths))


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

    paths = resolve_paths(run)
    round_id = resolve_round_id(db, paths, round)
    cycle_id = paths.cycle_id_file.read_text(encoding="utf-8").strip()
    rows = (
        db.execute(
            select(BidLine)
            .where(BidLine.cycle_id == cycle_id, BidLine.round_id == round_id)
            .order_by(
                BidLine.supplier_id,
                BidLine.dc_id,
                BidLine.lot_id,
                BidLine.tf_id,
            )
        )
        .scalars()
        .all()
    )
    return [_bid_line_view(row) for row in rows]


def _ingest_bids(svc: Any, db: Session, paths: RunPaths, round_no: int, uploaded: Path) -> int:
    """Run the strict key-validated ingest, mapping a malformed/mismatched file to a clean 400."""

    try:
        return int(svc.ingest_bids(db, paths, round_no, uploaded))
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Could not ingest the Round {round_no} bid file: {exc}",
            status_code=400,
        ) from exc


def _stage(round_no: int) -> int:
    """The normalized workflow stage number for a round's uploaded bids (mirrors PilotService)."""

    return 3 + (round_no - 1) * 3
