"""JSON-serializable READ layer over the sealed engine records (the web alignment slice).

Lives in the `eng` PERSISTENCE domain (NOT `app.engine`, which is the PURE clean-room engine —
stdlib + pydantic only, no sqlalchemy): this is a read over the sealed `eng.*` rows, so it belongs
with the other db-touching `eng` code.

Today the engine's scenario / award / score data is only readable INSIDE the Excel writer
(`app.output.scenario_workbook`). This module exposes the same numbers as plain Pydantic views a
web screen can consume — list the sealed analyses, compare the seven lenses side by side, and
inspect one lens cell-by-cell — WITHOUT touching openpyxl.

NUMBERS MATCH THE WORKBOOK BY CONSTRUCTION. The per-lens spend / Δ / savings come from the SAME
pure gather the workbook uses (`_gather_scenario_rollups`); the per-cell competitive grid comes
from the SAME `_gather_cells`; the chosen scenario's award split comes from the SAME
`PilotService._scenario_award_view`. We RESHAPE those outputs into JSON, we do not recompute them,
so the web can never diverge from the Excel (a consistency test asserts this against the gather
directly).

Decision-support only (ADR-0006): a lens RECOMMENDS, it never asserts. B is the default
recommendation (the only lens carrying `is_recommended` / `rec_type`); A is the lowest-cost Δ
baseline.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.eng.models import AnalysisScenario
from app.engine.formulas import savings_dollars
from app.output.scenario_workbook import (
    CellInfo,
    _gather_cells,
    _gather_scenario_rollups,
)
from app.output.types import CycleView

# B is the default recommendation lens (the only one carrying is_recommended / rec_type).
RECOMMENDED_SCENARIO_CODE = "B"


# --------------------------------------------------------------------------- #
# response views (JSON-safe — plain Pydantic, NOT openpyxl-bound)
# --------------------------------------------------------------------------- #
class AnalysisSummary(BaseModel):
    """One sealed `eng.analysis_run`, surfaced for the "which analysis" picker."""

    version: int = Field(description="1-based ordinal among the cycle's sealed runs (oldest=1).")
    analysis_run_id: str
    round_number: int = Field(description="The 1-based cycle round this analysis scored.")
    engine_version: str
    sealed_at: datetime = Field(description="When the run finished + sealed (UTC).")


class ScenarioComparisonRow(BaseModel):
    """One lens rolled up for the side-by-side comparison (which lens to pick)."""

    code: str = Field(description="The lens code A-G.")
    label: str
    description: str
    total_spend: float = Field(description="Lens spend = Σ price × cases × share over all cells.")
    delta_vs_a: float = Field(description="Spend Δ vs lens A (the lowest-cost benchmark).")
    savings_vs_incumbent_pct: float = Field(
        description="Fraction saved vs the incumbent-routing baseline (0.05 = 5%)."
    )
    savings_vs_stly_pct: float = Field(
        description="Fraction saved vs the SYNTHETIC prior-year baseline (incumbent × 1.04)."
    )
    supplier_count: int
    cell_count: int
    cap_breach_count: int
    is_recommended: bool = Field(description="True for lens B (the default recommendation).")


class SupplierCell(BaseModel):
    """One supplier's competitive line within a cell (price + flags + this lens's share)."""

    name: str
    price_per_case: float | None = Field(
        description="The supplier's final-round all-in $/case for this cell (None if no bid)."
    )
    is_min: bool = Field(description="True if this is the lowest priced bid in the cell.")
    is_incumbent: bool = Field(description="True if this supplier is the cell's incumbent.")
    is_recommended: bool = Field(description="True if this lens awarded this supplier the cell.")
    rec_score: float | None = Field(description="The supplier's RecScore (0-100) for this cell.")
    volume_share: float = Field(
        description="This lens's awarded volume share to this supplier (0 if not awarded)."
    )


class SupplierCellRef(BaseModel):
    """The supplier a lens awarded a cell — supplier + price + (B-only) reason label."""

    supplier: str
    rec_type: str = Field(description="The B reason label (Lowest cost / …); '' for other lenses.")
    price: float | None


class ScenarioDetailCell(BaseModel):
    """One (DC × lot × item × TF) cell, resolved to names + the competitive picture for a lens."""

    dc: str
    lot: str
    item: str
    tf: str
    volume: float = Field(description="Projected period cases for the cell.")
    baseline_price: float = Field(description="Incumbent-routing baseline $/case.")
    min_price: float | None = Field(description="The lowest bid $/case in the cell (None if none).")
    incumbent_supplier: str
    suppliers: list[SupplierCell]
    recommended: SupplierCellRef | None = Field(
        description="The supplier this lens awarded the cell (B carries a rec_type reason)."
    )


class ScenarioSavingsSummary(BaseModel):
    """The chosen lens's spend + savings headline (matches the comparison row for this lens)."""

    total_spend: float
    savings_vs_incumbent: float = Field(description="Dollars saved vs the incumbent baseline.")
    savings_vs_incumbent_pct: float
    savings_vs_stly: float = Field(description="Dollars saved vs the SYNTHETIC prior-year proxy.")
    savings_vs_stly_pct: float


class ScenarioDetail(BaseModel):
    """One lens inspected cell-by-cell — the per-cell grid + the savings headline."""

    code: str
    label: str
    description: str
    is_recommended: bool
    savings: ScenarioSavingsSummary
    cells: list[ScenarioDetailCell]


# --------------------------------------------------------------------------- #
# read functions
# --------------------------------------------------------------------------- #
def list_analyses(session: Session, cycle_id: str) -> list[AnalysisSummary]:
    """The cycle's SEALED analysis runs, oldest first, each with its 1-based version ordinal.

    Mirrors the `history` shape (ordered by `run_started_at`, the round number joined from
    `cyc.cycle_round`) but returns typed views the web renders directly. Unsealed runs are omitted.
    """

    rows = session.execute(
        text(
            "SELECT r.analysis_run_id, r.engine_version, r.run_finished_at, "
            "       COALESCE(cr.round_number, 0) AS round_number "
            "FROM eng.analysis_run r "
            "LEFT JOIN cyc.cycle_round cr ON cr.round_id = r.round_id "
            "WHERE r.cycle_id = :cyc AND r.is_sealed = true "
            "ORDER BY r.run_started_at"
        ),
        {"cyc": cycle_id},
    ).all()
    return [
        AnalysisSummary(
            version=seq,
            analysis_run_id=run_id,
            round_number=int(round_number),
            engine_version=engine_version,
            sealed_at=sealed_at,
        )
        for seq, (run_id, engine_version, sealed_at, round_number) in enumerate(rows, start=1)
    ]


def _scenarios(session: Session, analysis_run_id: str) -> list[AnalysisScenario]:
    """The run's A-G lens headers, ordered by code (the order the workbook gathers them in)."""

    return list(
        session.query(AnalysisScenario)
        .filter(AnalysisScenario.analysis_run_id == analysis_run_id)
        .order_by(AnalysisScenario.scenario_code)
        .all()
    )


def scenario_comparison(
    session: Session, cycle_view: CycleView, analysis_run_id: str
) -> list[ScenarioComparisonRow]:
    """The seven lenses side by side: spend, Δ vs A, savings, counts, breaches (which lens).

    Reuses the workbook's `_gather_scenario_rollups` verbatim, so every number is identical to the
    alignment workbook's Scenario Comparison tab for the same run. B is flagged `is_recommended`.
    """

    scenarios = _scenarios(session, analysis_run_id)
    rollups, _baseline_total, _stly_total = _gather_scenario_rollups(
        session, cycle_view, scenarios, analysis_run_id
    )
    desc_by_code = {s.scenario_code: (s.description or "") for s in scenarios}
    return [
        ScenarioComparisonRow(
            code=r.code,
            label=r.label,
            description=desc_by_code.get(r.code, ""),
            total_spend=float(r.total_spend),
            delta_vs_a=float(r.delta_vs_a),
            savings_vs_incumbent_pct=float(r.savings_vs_baseline_frac),
            savings_vs_stly_pct=float(r.savings_vs_stly_frac),
            supplier_count=r.n_suppliers,
            cell_count=r.n_cells,
            cap_breach_count=r.n_cap_breaches,
            is_recommended=r.code == RECOMMENDED_SCENARIO_CODE,
        )
        for r in rollups
    ]


def scenario_detail(
    session: Session,
    cycle_view: CycleView,
    analysis_run_id: str,
    scenario_code: str,
    *,
    final_round_id: str,
    award_view: object,
) -> ScenarioDetail:
    """One lens cell-by-cell: the competitive supplier grid + this lens's award + the savings.

    The competitive picture (every supplier's $/case, min, incumbent, RecScore) comes from the
    workbook's `_gather_cells`; THIS lens's awarded supplier + volume share per cell comes from the
    passed `award_view` (built by `PilotService._scenario_award_view(scenario_code)`), so the
    "recommended" supplier + share reflect the CHOSEN lens, not always B. The savings headline is
    the chosen lens's row from `_gather_scenario_rollups` — identical to the comparison endpoint.
    """

    scenarios = _scenarios(session, analysis_run_id)
    header = next((s for s in scenarios if s.scenario_code == scenario_code), None)
    if header is None:
        raise ValueError(f"scenario {scenario_code!r} not found on run {analysis_run_id!r}")

    sup_name = {sup.id: sup.name for sup in cycle_view.suppliers}

    # The competitive grid per cell (prices / scores / incumbent / min) — shared with the workbook.
    # A split lens (D) has >1 award row per (dc, lot, tf), so `_gather_cells` emits one `CellInfo`
    # per row; dedupe to ONE cell per (dc, lot, tf) (the competitive grid is share-independent).
    gathered = _gather_cells(session, cycle_view, analysis_run_id, final_round_id, award_view)  # type: ignore[arg-type]
    cells: list[CellInfo] = []
    seen: set[tuple[str, str, str]] = set()
    for cell in gathered:
        key_t = (cell.dc_id, cell.lot_id, cell.tf_id)
        if key_t in seen:
            continue
        seen.add(key_t)
        cells.append(cell)

    # This lens's award split per (dc, lot, tf): {supplier_name -> volume_share} + the picked price.
    award_cells = getattr(award_view, "cells", [])
    share_by_cell: dict[tuple[str, str, str], dict[str, Decimal]] = {}
    price_by_award_cell: dict[tuple[str, str, str], dict[str, Decimal]] = {}
    for c in award_cells:
        key = (c.dc_id, c.lot_id, c.tf_id)
        name = sup_name.get(c.supplier_id, c.supplier_id[:6])
        share_by_cell.setdefault(key, {})[name] = Decimal(str(c.volume_share))
        price_by_award_cell.setdefault(key, {})[name] = Decimal(str(c.awarded_price))

    detail_cells = [
        _detail_cell(cell, share_by_cell, price_by_award_cell, scenario_code) for cell in cells
    ]

    # Savings headline = this lens's comparison row (same gather → same numbers).
    rollups, baseline_total, stly_total = _gather_scenario_rollups(
        session, cycle_view, scenarios, analysis_run_id
    )
    row = next((r for r in rollups if r.code == scenario_code), None)
    spend = row.total_spend if row is not None else Decimal("0")
    savings = ScenarioSavingsSummary(
        total_spend=float(spend),
        savings_vs_incumbent=float(savings_dollars(baseline_total, spend)),
        savings_vs_incumbent_pct=float(row.savings_vs_baseline_frac) if row is not None else 0.0,
        savings_vs_stly=float(savings_dollars(stly_total, spend)),
        savings_vs_stly_pct=float(row.savings_vs_stly_frac) if row is not None else 0.0,
    )

    return ScenarioDetail(
        code=scenario_code,
        label=header.label,
        description=header.description or "",
        is_recommended=scenario_code == RECOMMENDED_SCENARIO_CODE,
        savings=savings,
        cells=detail_cells,
    )


def _detail_cell(
    cell: CellInfo,
    share_by_cell: dict[tuple[str, str, str], dict[str, Decimal]],
    price_by_award_cell: dict[tuple[str, str, str], dict[str, Decimal]],
    scenario_code: str,
) -> ScenarioDetailCell:
    """Reshape one gathered `CellInfo` + this lens's award split into the JSON cell view."""

    key = (cell.dc_id, cell.lot_id, cell.tf_id)
    shares = share_by_cell.get(key, {})
    awarded_prices = price_by_award_cell.get(key, {})
    min_price = min(cell.price_by_supplier.values()) if cell.price_by_supplier else None

    suppliers: list[SupplierCell] = []
    for name in cell.eligible_suppliers:
        price = cell.price_by_supplier.get(name)
        score = cell.score_by_supplier.get(name)
        suppliers.append(
            SupplierCell(
                name=name,
                price_per_case=float(price) if price is not None else None,
                is_min=price is not None and min_price is not None and price == min_price,
                is_incumbent=name == cell.incumbent_name,
                is_recommended=shares.get(name, Decimal("0")) > 0,
                rec_score=float(score) if score is not None else None,
                volume_share=float(shares.get(name, Decimal("0"))),
            )
        )

    # The lens's awarded supplier for the cell — the single-winner pick (or the largest share for a
    # split lens like D). B carries the engine's rec_type reason; other lenses leave it blank.
    recommended: SupplierCellRef | None = None
    if shares:
        top = max(shares.items(), key=lambda kv: kv[1])[0]
        awarded_price = awarded_prices.get(top)
        recommended = SupplierCellRef(
            supplier=top,
            rec_type=cell.rec_type if scenario_code == RECOMMENDED_SCENARIO_CODE else "",
            price=float(awarded_price) if awarded_price is not None else None,
        )

    return ScenarioDetailCell(
        dc=cell.dc_name,
        lot=cell.lot_name,
        item=cell.item_name,
        tf=cell.tf_name,
        volume=float(cell.volume),
        baseline_price=float(cell.baseline_price),
        min_price=float(min_price) if min_price is not None else None,
        incumbent_supplier=cell.incumbent_name,
        suppliers=suppliers,
        recommended=recommended,
    )
