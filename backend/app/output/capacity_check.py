"""E-38 capacity check: does a scenario's allocation exceed a supplier's STATED capacity?

The accuracy core's safety question — "never recommend an award beyond stated capacity." A pure
evaluator (`evaluate_capacity`) compares each awarded cell's allocation (period cases × volume
share) against the supplier's stated CELL ceiling, plus a sealed-record reader (`load_active_
capacity`) that pulls those ceilings from the ACTIVE `bid.capacity_statement` / `bid.capacity_
constraint` rows (E-38 slice 1). Decision-support only: it FLAGS over-capacity so the buyer never
books a supplier beyond what they said they can supply — it never changes an award (ADR-0006).

Grain: capacity is per supplier x dc x lot x tf (the engine award's grain). Two comparisons:
  * PERIOD — allocated total over the timeframe vs `max_period_cases` ("Max Total Cases"). Exact,
    apples-to-apples (both are totals over the TF).
  * WEEKLY — allocated/weeks vs `max_weekly_cases`. The week count is the workbook's `WEEKS_PER_TF`
    convention (one timeframe's weeks); a cell flags if EITHER ceiling is exceeded.
When a (supplier, cell) has more than one stated constraint (e.g. multiple items under one lot), the
TIGHTEST (minimum) ceiling is used — conservative, so the check never understates an overage.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.engine.formulas import awarded_cases

# (supplier_id, dc_id, lot_id, tf_id) — the per-supplier cell grain capacity is stated/checked at.
CellKey = tuple[str, str, str, str]


class _AllocatedCell(Protocol):
    """The award-cell shape the evaluator needs (the workbook's AwardCellView satisfies it)."""

    @property
    def dc_id(self) -> str: ...
    @property
    def lot_id(self) -> str: ...
    @property
    def tf_id(self) -> str: ...
    @property
    def supplier_id(self) -> str: ...
    @property
    def volume_share(self) -> Decimal: ...
    @property
    def period_cases(self) -> Decimal: ...


@dataclass(frozen=True)
class StatedCapacity:
    """A supplier's stated ceiling for one cell (either/both may be None — at least one is set)."""

    max_weekly_cases: Decimal | None
    max_period_cases: Decimal | None


@dataclass(frozen=True)
class CapacityCheckRow:
    """One awarded cell checked against the supplier's stated ceiling (decision-support flag)."""

    supplier_id: str
    dc_id: str
    lot_id: str
    tf_id: str
    allocated_cases: Decimal  # period total = period_cases × volume_share
    allocated_weekly_cases: Decimal | None  # allocated / weeks_per_tf (None if weeks not positive)
    max_weekly_cases: Decimal | None
    max_period_cases: Decimal | None
    has_statement: bool  # did the supplier state ANY ceiling for this cell?
    over_period: bool
    over_weekly: bool

    @property
    def over_capacity(self) -> bool:
        return self.over_period or self.over_weekly

    @property
    def status(self) -> str:
        if not self.has_statement:
            return "No stated capacity"
        return "OVER CAPACITY" if self.over_capacity else "Within capacity"


def evaluate_capacity(
    award_cells: Iterable[_AllocatedCell],
    capacity_by_cell: dict[CellKey, StatedCapacity],
    *,
    weeks_per_tf: int,
) -> list[CapacityCheckRow]:
    """Compare each awarded cell's allocation to the supplier's stated ceiling; flag over-capacity.

    `award_cells` are the chosen scenario's allocation cells (supplier/dc/lot/tf + period_cases +
    volume_share); `capacity_by_cell` maps the (supplier, dc, lot, tf) cell to its stated ceiling.
    A cell with no stated ceiling is reported (has_statement=False), never flagged. Pure — no IO.
    """

    rows: list[CapacityCheckRow] = []
    for c in award_cells:
        key: CellKey = (c.supplier_id, c.dc_id, c.lot_id, c.tf_id)
        allocated = awarded_cases(c.period_cases, c.volume_share)
        weekly = (allocated / weeks_per_tf) if weeks_per_tf and weeks_per_tf > 0 else None
        cap = capacity_by_cell.get(key)
        if cap is None:
            rows.append(
                CapacityCheckRow(
                    supplier_id=c.supplier_id,
                    dc_id=c.dc_id,
                    lot_id=c.lot_id,
                    tf_id=c.tf_id,
                    allocated_cases=allocated,
                    allocated_weekly_cases=weekly,
                    max_weekly_cases=None,
                    max_period_cases=None,
                    has_statement=False,
                    over_period=False,
                    over_weekly=False,
                )
            )
            continue
        over_period = cap.max_period_cases is not None and allocated > cap.max_period_cases
        over_weekly = (
            cap.max_weekly_cases is not None
            and weekly is not None
            and weekly > cap.max_weekly_cases
        )
        rows.append(
            CapacityCheckRow(
                supplier_id=c.supplier_id,
                dc_id=c.dc_id,
                lot_id=c.lot_id,
                tf_id=c.tf_id,
                allocated_cases=allocated,
                allocated_weekly_cases=weekly,
                max_weekly_cases=cap.max_weekly_cases,
                max_period_cases=cap.max_period_cases,
                has_statement=True,
                over_period=over_period,
                over_weekly=over_weekly,
            )
        )
    return rows


def load_active_capacity(session: Session, cycle_id: str) -> dict[CellKey, StatedCapacity]:
    """Read the cycle's ACTIVE stated capacity ceilings as {(supplier,dc,lot,tf): StatedCapacity}.

    Reads only CELL-scoped constraints under a non-SUPERSEDED statement (E-38 slice 1 persists CELL
    rows; a re-submission supersedes its predecessor, so the latest ceilings win). When a cell has
    more than one constraint, the TIGHTEST (MIN) of each ceiling is taken — conservative.
    """

    rows = session.execute(
        text(
            "SELECT cs.supplier_id, cc.dc_id, cc.lot_id, cc.tf_id, "
            "MIN(cc.max_weekly_cases) AS w, MIN(cc.max_period_cases) AS p "
            "FROM bid.capacity_constraint cc "
            "JOIN bid.capacity_statement cs "
            "  ON cs.capacity_statement_id = cc.capacity_statement_id "
            "WHERE cc.cycle_id = :c AND cs.status <> 'SUPERSEDED' AND cc.scope_type = 'CELL' "
            "GROUP BY cs.supplier_id, cc.dc_id, cc.lot_id, cc.tf_id"
        ),
        {"c": cycle_id},
    ).all()
    out: dict[CellKey, StatedCapacity] = {}
    for sup, dc, lot, tf, weekly, period in rows:
        out[(sup, dc, lot, tf)] = StatedCapacity(
            max_weekly_cases=Decimal(str(weekly)) if weekly is not None else None,
            max_period_cases=Decimal(str(period)) if period is not None else None,
        )
    return out
