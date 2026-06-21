"""E-38 capacity-check evaluator (pure): allocation vs stated ceiling — period + weekly checks.

Unit-level proof of `evaluate_capacity` — the accuracy core's "never recommend beyond stated
capacity" flag. No DB: feed award cells + a capacity map; assert the over-capacity verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.output.capacity_check import StatedCapacity, evaluate_capacity

_D = Decimal
_WEEKS = 13  # WEEKS_PER_TF (the workbook convention): one timeframe = 13 weeks


@dataclass(frozen=True)
class _Cell:
    supplier_id: str
    dc_id: str
    lot_id: str
    tf_id: str
    volume_share: Decimal
    period_cases: Decimal


def _cell(sup: str, share: str, cases: str) -> _Cell:
    # Distinct dc/lot/tf per supplier so each cell has its own capacity key.
    return _Cell(sup, f"DC-{sup}", f"LOT-{sup}", "TF1", _D(share), _D(cases))


def test_over_period_when_allocation_exceeds_total_ceiling() -> None:
    cell = _cell("A", "1.0", "6500")  # allocated 6500 cases over the TF
    cap = {("A", "DC-A", "LOT-A", "TF1"): StatedCapacity(None, _D("6000"))}
    (row,) = evaluate_capacity([cell], cap, weeks_per_tf=_WEEKS)
    assert row.allocated_cases == _D("6500.0")
    assert row.has_statement is True
    assert row.over_period is True
    assert row.over_capacity is True
    assert row.status == "OVER CAPACITY"


def test_within_period_but_over_weekly() -> None:
    cell = _cell("B", "1.0", "6500")  # 6500 total -> 500/week
    cap = {("B", "DC-B", "LOT-B", "TF1"): StatedCapacity(_D("400"), _D("7000"))}
    (row,) = evaluate_capacity([cell], cap, weeks_per_tf=_WEEKS)
    assert row.over_period is False
    assert row.allocated_weekly_cases == _D("500")
    assert row.over_weekly is True
    assert row.over_capacity is True


def test_within_both_ceilings() -> None:
    cell = _cell("C", "1.0", "6500")  # 6500 total, 500/week
    cap = {("C", "DC-C", "LOT-C", "TF1"): StatedCapacity(_D("600"), _D("7000"))}
    (row,) = evaluate_capacity([cell], cap, weeks_per_tf=_WEEKS)
    assert row.over_capacity is False
    assert row.status == "Within capacity"


def test_volume_share_scales_allocation() -> None:
    cell = _cell("D", "0.5", "6500")  # half the cell -> 3250 cases
    cap = {("D", "DC-D", "LOT-D", "TF1"): StatedCapacity(None, _D("4000"))}
    (row,) = evaluate_capacity([cell], cap, weeks_per_tf=_WEEKS)
    assert row.allocated_cases == _D("3250.0")
    assert row.over_period is False


def test_no_statement_is_reported_not_flagged() -> None:
    cell = _cell("E", "1.0", "9999")
    (row,) = evaluate_capacity([cell], {}, weeks_per_tf=_WEEKS)
    assert row.has_statement is False
    assert row.over_capacity is False
    assert row.status == "No stated capacity"
    assert row.max_period_cases is None and row.max_weekly_cases is None


def test_only_period_stated_ignores_weekly_dimension() -> None:
    cell = _cell("F", "1.0", "6500")
    cap = {("F", "DC-F", "LOT-F", "TF1"): StatedCapacity(None, _D("6000"))}
    (row,) = evaluate_capacity([cell], cap, weeks_per_tf=_WEEKS)
    assert row.over_weekly is False  # no weekly ceiling -> weekly never flags
    assert row.over_period is True
