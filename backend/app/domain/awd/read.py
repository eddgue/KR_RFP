"""JSON-serializable READ layer over the FROZEN award + its versioned adjustment layers.

Lives in the `awd` PERSISTENCE domain (db-touching), mirroring `app.domain.eng.read` for the
alignment slice. Exposes the post-award records the web console renders: list a cycle's frozen
awards, and inspect one award — its baseline lines, the EFFECTIVE price per cell (the frozen
baseline overlaid by every layer), and the full version history (v0 frozen → vN).

NUMBERS COME FROM THE SAME SERVICE the post-award workbook uses — `effective_award` (per-cell
effective price) + `award_versions` (the version history) — reshaped into JSON, never recomputed,
so the web can't diverge from the generated post-award document.

Freeze-and-layer (ADR-0014): the award is the immutable frozen baseline; every post-award move is
an append-only, date-stamped layer on top — the baseline is never edited.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.awd.models import Award, AwardAdjustment, AwardLine
from app.domain.awd.service import award_versions, effective_award
from app.output.types import CycleView


# --------------------------------------------------------------------------- #
# response views (JSON-safe — plain Pydantic)
# --------------------------------------------------------------------------- #
class AwardSummary(BaseModel):
    """One frozen award in the cycle — identity + line count + the latest layer version."""

    award_id: str
    award_code: str
    scenario_code: str
    frozen_at: datetime
    frozen_by: str
    line_count: int
    latest_version: int = Field(description="The highest adjustment version (0 = baseline only).")


class AwardLineView(BaseModel):
    """One awarded cell — names (D23) + frozen baseline, effective price, and the delta."""

    dc: str
    lot: str
    tf: str
    supplier: str
    volume_share: float
    frozen_price: float
    effective_price: float = Field(
        description="The frozen baseline overlaid by every layer (latest version)."
    )
    delta: float = Field(description="effective_price − frozen_price (0 if never adjusted).")


class AwardVersionView(BaseModel):
    """One row of the award's version history (v0 frozen baseline → vN layers)."""

    version_no: int
    adjustment_type: str
    effective_date: date
    reason: str
    created_at: datetime
    created_by: str
    n_lines: int = Field(
        description="Cells in this version (baseline cells for v0; changed cells for a layer)."
    )


class AwardDetail(BaseModel):
    """One frozen award inspected — baseline + effective lines + the full version history."""

    award_id: str
    award_code: str
    scenario_code: str
    frozen_at: datetime
    frozen_by: str
    latest_version: int
    lines: list[AwardLineView]
    versions: list[AwardVersionView]


# --------------------------------------------------------------------------- #
# read functions
# --------------------------------------------------------------------------- #
def list_awards(session: Session, cycle_id: str) -> list[AwardSummary]:
    """The cycle's FROZEN awards, oldest first, each with its line count + latest layer version."""

    awards = list(
        session.execute(select(Award).where(Award.cycle_id == cycle_id).order_by(Award.frozen_at))
        .scalars()
        .all()
    )
    out: list[AwardSummary] = []
    for award in awards:
        line_count = session.execute(
            select(func.count()).select_from(AwardLine).where(AwardLine.award_id == award.award_id)
        ).scalar_one()
        latest = session.execute(
            select(func.coalesce(func.max(AwardAdjustment.version_no), 0)).where(
                AwardAdjustment.award_id == award.award_id
            )
        ).scalar_one()
        out.append(
            AwardSummary(
                award_id=award.award_id,
                award_code=award.award_code,
                scenario_code=award.scenario_code,
                frozen_at=award.frozen_at,
                frozen_by=award.frozen_by,
                line_count=int(line_count),
                latest_version=int(latest),
            )
        )
    return out


def award_detail(session: Session, cycle_view: CycleView, award_id: str) -> AwardDetail:
    """One frozen award: baseline lines + effective prices + the full version history.

    The effective price per cell is the frozen baseline overlaid by every layer (`effective_award`);
    the history is `award_versions` (v0 FROZEN → vN). Cells are resolved to names (D23). Raises
    ValueError if the id is not a frozen award OF THIS RUN'S CYCLE (mapped to a clean 404 by the
    router) — the lookup is scoped to `cycle_view.cycle_id`, so a run-scoped endpoint can never
    return another run's award prices/history (and never resolves names against the wrong cycle).
    """

    award = session.execute(
        select(Award).where(
            Award.award_id == award_id,
            Award.cycle_id == cycle_view.cycle_id,
        )
    ).scalar_one_or_none()
    if award is None:
        raise ValueError(f"award {award_id!r} not found")

    dc_name = {dc.id: dc.name for dc in cycle_view.dcs}
    lot_name = {lot.id: lot.name for lot in cycle_view.lots}
    tf_name = {tf.id: tf.name for tf in cycle_view.tfs}
    sup_name = {sup.id: sup.name for sup in cycle_view.suppliers}

    # The effective price per cell at the latest version (baseline overlaid by all layers).
    effective = effective_award(session, award_id=award_id)

    base_rows = session.execute(
        select(
            AwardLine.dc_id,
            AwardLine.lot_id,
            AwardLine.tf_id,
            AwardLine.supplier_id,
            AwardLine.volume_share,
            AwardLine.frozen_price,
        ).where(AwardLine.award_id == award_id)
    ).all()

    lines: list[AwardLineView] = []
    for dc_id, lot_id, tf_id, supplier_id, volume_share, frozen_price in base_rows:
        eff = effective.get((dc_id, lot_id, tf_id, supplier_id), frozen_price)
        lines.append(
            AwardLineView(
                dc=dc_name.get(dc_id, dc_id[:6]),
                lot=lot_name.get(lot_id, lot_id[:6]),
                tf=tf_name.get(tf_id, tf_id[:6]),
                supplier=sup_name.get(supplier_id, supplier_id[:6]),
                volume_share=float(volume_share),
                frozen_price=float(frozen_price),
                effective_price=float(eff),
                delta=float(eff - frozen_price),
            )
        )
    lines.sort(key=lambda line: (line.dc, line.lot, line.tf, line.supplier))

    versions = [
        AwardVersionView(
            version_no=v["version_no"],
            adjustment_type=v["adjustment_type"],
            effective_date=v["effective_date"],
            reason=v["reason"],
            created_at=v["created_at"],
            created_by=v["created_by"],
            n_lines=v["n_lines"],
        )
        for v in award_versions(session, award_id=award_id)
    ]
    latest_version = max((v.version_no for v in versions), default=0)

    return AwardDetail(
        award_id=award.award_id,
        award_code=award.award_code,
        scenario_code=award.scenario_code,
        frozen_at=award.frozen_at,
        frozen_by=award.frozen_by,
        latest_version=latest_version,
        lines=lines,
        versions=versions,
    )
