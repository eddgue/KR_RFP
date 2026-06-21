"""Kroger fiscal calendar — period<->date, the 4-3-3-3 quarter split, leap weeks, timeframes.

Asserts the loaded reference table (`app/fiscal/data/kroger_fiscal_periods.csv`) against the
authoritative facts derived from the sponsor's conversion table, and the timeframe grouping +
intake fan-out that the flat-13 model relies on (INTAKE_TEMPLATE_DESIGN §1a).

PURE: no DB, no network — just the calendar library + its packaged data.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.fiscal.calendar import (
    PERIODS_PER_YEAR,
    QUARTER_OF_PERIOD,
    all_periods,
    expand_to_periods,
    fiscal_halves,
    fiscal_quarters,
    fiscal_year_timeframe,
    fiscal_years,
    get_period,
    group_periods,
    period_for_date,
    periods_in_year,
)


def test_calendar_covers_fy16_to_fy36_with_13_periods_each() -> None:
    assert fiscal_years()[0] == 2016
    assert fiscal_years()[-1] == 2036
    for fy in fiscal_years():
        ps = periods_in_year(fy)
        assert [p.period for p in ps] == list(range(1, PERIODS_PER_YEAR + 1))


def test_every_period_is_contiguous_no_gaps() -> None:
    rows = all_periods()
    for prev, nxt in zip(rows, rows[1:], strict=False):
        assert nxt.begin == prev.end + timedelta(days=1)


def test_quarter_split_is_4_3_3_3_and_matches_the_data() -> None:
    # The constant is the fixed 4-3-3-3 split...
    counts = [sum(1 for p in QUARTER_OF_PERIOD.values() if p == q) for q in (1, 2, 3, 4)]
    assert counts == [4, 3, 3, 3]
    # ...and every row in the reference table agrees with it.
    for p in all_periods():
        assert p.quarter == QUARTER_OF_PERIOD[p.period]


def test_today_resolves_to_fy26_period_5() -> None:
    p = period_for_date(date(2026, 6, 20))
    assert (p.fiscal_year, p.period, p.quarter) == (2026, 5, 2)
    assert p.label == "P05-26"
    assert p.begin == date(2026, 5, 24) and p.end == date(2026, 6, 20)


def test_period_boundaries_are_inclusive() -> None:
    p = get_period(2026, 1)
    assert p.begin == date(2026, 2, 1) and p.end == date(2026, 2, 28)
    assert period_for_date(p.begin).period == 1
    assert period_for_date(p.end).period == 1
    # the day after P1 ends belongs to P2
    assert period_for_date(p.end + timedelta(days=1)).period == 2


def test_leap_year_gives_period_13_a_fifth_week() -> None:
    assert get_period(2028, 13).weeks == 5  # FY28 is a 53-week year
    assert get_period(2028, 13).days == 35
    assert get_period(2026, 13).weeks == 4  # an ordinary 52-week year
    assert get_period(2026, 13).days == 28


def test_dates_outside_the_calendar_raise() -> None:
    with pytest.raises(ValueError):
        period_for_date(date(2015, 1, 1))
    with pytest.raises(ValueError):
        get_period(2099, 1)


def test_fiscal_quarter_timeframes_cover_the_year() -> None:
    qs = fiscal_quarters(2026)
    assert [t.label for t in qs] == ["Q1", "Q2", "Q3", "Q4"]
    assert [t.period_numbers for t in qs] == [(1, 2, 3, 4), (5, 6, 7), (8, 9, 10), (11, 12, 13)]
    # a timeframe's span runs from its first period's begin to its last period's end
    q1 = qs[0]
    assert q1.begin == get_period(2026, 1).begin
    assert q1.end == get_period(2026, 4).end


def test_halves_and_full_year_presets() -> None:
    h = fiscal_halves(2026)
    assert [t.period_numbers for t in h] == [(1, 2, 3, 4, 5, 6, 7), (8, 9, 10, 11, 12, 13)]
    fy = fiscal_year_timeframe(2026)
    assert len(fy) == 1 and fy[0].period_numbers == tuple(range(1, 14))


def test_group_periods_rejects_non_covering_spans() -> None:
    with pytest.raises(ValueError):
        group_periods(2026, [(1, 2), (4, 13)])  # gap at period 3
    with pytest.raises(ValueError):
        group_periods(2026, [(1, 13), (5, 7)])  # overlap


def test_intake_fans_a_timeframe_out_to_its_flat_periods() -> None:
    # The buyer's earlier example grouping: A=P1-2, B=P3-9, C=P10-13.
    tfs = group_periods(2026, [(1, 2), (3, 9), (10, 13)], ["A", "B", "C"])
    fanned = {t.label: [p.period for p in expand_to_periods(t)] for t in tfs}
    assert fanned == {"A": [1, 2], "B": [3, 4, 5, 6, 7, 8, 9], "C": [10, 11, 12, 13]}
    # every one of the 13 periods is written exactly once across the fan-out
    written = [p for periods in fanned.values() for p in periods]
    assert sorted(written) == list(range(1, 14))
