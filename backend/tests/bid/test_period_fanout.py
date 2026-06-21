"""Pure tests for the intake fan-out (INTAKE §1a) — no DB, synthetic payloads only.

Asserts the flat-13 contract: a few timeframes priced once fan out to all 13 fiscal periods, each
period covered exactly once, payloads copied (not shared), and overlaps rejected.
"""

from __future__ import annotations

import pytest

from app.domain.bid.period_fanout import FannedPrice, fan_out, fan_out_all
from app.fiscal.calendar import (
    fiscal_quarters,
    fiscal_year_timeframe,
    group_periods,
)


def _periods(records: list[FannedPrice]) -> list[int]:
    return [r.fiscal_period.period for r in records]


def test_full_year_fans_to_all_thirteen_periods_with_identical_payload() -> None:
    timeframe = fiscal_year_timeframe(2026)[0]
    payload = {"all_in_case": 12.34, "volume": 1000}

    fanned = fan_out(timeframe, payload)

    assert _periods(fanned) == list(range(1, 14))
    assert all(r.fiscal_period.fiscal_year == 2026 for r in fanned)
    for record in fanned:
        assert record.payload == payload


def test_buyer_example_grouping_maps_each_span_to_its_payload() -> None:
    timeframes = group_periods(2026, [(1, 2), (3, 9), (10, 13)], ["A", "B", "C"])
    payload_a = {"price": "A"}
    payload_b = {"price": "B"}
    payload_c = {"price": "C"}

    fanned = fan_out_all(
        [
            (timeframes[0], payload_a),
            (timeframes[1], payload_b),
            (timeframes[2], payload_c),
        ]
    )

    by_period = {r.fiscal_period.period: r.payload for r in fanned}
    # Every one of the 13 periods appears exactly once.
    assert _periods(fanned) == list(range(1, 14))
    assert len(by_period) == 13
    # Periods 1-2 carry A, 3-9 carry B, 10-13 carry C.
    assert all(by_period[p] == payload_a for p in (1, 2))
    assert all(by_period[p] == payload_b for p in range(3, 10))
    assert all(by_period[p] == payload_c for p in (10, 11, 12, 13))


def test_fiscal_quarters_fan_to_4_3_3_3() -> None:
    quarters = fiscal_quarters(2026)
    payloads = [{"q": "Q1"}, {"q": "Q2"}, {"q": "Q3"}, {"q": "Q4"}]

    fanned = fan_out_all(list(zip(quarters, payloads, strict=True)))

    # 4 + 3 + 3 + 3 = 13 fanned rows covering every period once.
    assert len(fanned) == 13
    assert _periods(fanned) == list(range(1, 14))

    by_period = {r.fiscal_period.period: r for r in fanned}
    # Quarter membership matches the 4-3-3-3 split and the payload of that quarter.
    for period in (1, 2, 3, 4):
        assert by_period[period].fiscal_period.quarter == 1
        assert by_period[period].payload == {"q": "Q1"}
    for period in (5, 6, 7):
        assert by_period[period].fiscal_period.quarter == 2
        assert by_period[period].payload == {"q": "Q2"}
    for period in (8, 9, 10):
        assert by_period[period].fiscal_period.quarter == 3
        assert by_period[period].payload == {"q": "Q3"}
    for period in (11, 12, 13):
        assert by_period[period].fiscal_period.quarter == 4
        assert by_period[period].payload == {"q": "Q4"}


def test_fan_out_all_rejects_overlapping_timeframes() -> None:
    # Two timeframes that both cover period 5 (P5-7 and P5-7 again).
    overlapping = group_periods(2026, [(1, 4), (5, 7), (8, 13)])
    q2_again = group_periods(2026, [(1, 4), (5, 7), (8, 13)])[1]

    with pytest.raises(ValueError, match="more than one timeframe"):
        fan_out_all(
            [
                (overlapping[1], {"price": 1}),  # P5-7
                (q2_again, {"price": 2}),  # P5-7 again -> overlap on 5,6,7
            ]
        )


def test_payload_is_copied_not_shared() -> None:
    timeframe = fiscal_year_timeframe(2026)[0]
    payload: dict[str, object] = {"price": 1}

    fanned = fan_out(timeframe, payload)

    # Mutating one record's payload must not affect the others or the original.
    first = dict(fanned[0].payload)
    first["price"] = 999
    assert fanned[1].payload["price"] == 1
    assert payload["price"] == 1
