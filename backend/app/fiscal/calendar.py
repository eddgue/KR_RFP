"""Kroger fiscal calendar — the authoritative 13-period reference (period <-> date, timeframes).

Kroger runs a **4-3-3-3** retail fiscal calendar: every fiscal year has EXACTLY 13 four-week
periods grouped into four quarters — Q1 = P1-4, Q2 = P5-7, Q3 = P8-10, Q4 = P11-13. Most years are
52 weeks (every period = 4 weeks); a 53-week "leap" year (~every 5-6 years) gives **Period 13 a 5th
week** to keep the year anchored near the start of February. Period spans are therefore NOT always
28 days, so this module never assumes a fixed length — the begin/end dates come from the sponsor's
authoritative conversion table (`data/kroger_fiscal_periods.csv`, FY16..FY36, fully contiguous).

This is the canonical grain the flat-13 intake model records against (INTAKE_TEMPLATE_DESIGN §1a):
every offer lands in exactly ONE of the 13 periods (`period_for_date`). A bid template groups the 13
periods into a handful of **timeframes** (e.g. the fiscal quarters) so a supplier prices a few spans
instead of 13 cells; intake then **fans out** each timeframe's price to every period it covers
(`expand_to_periods`) — keeping the storage flat and the supplier form easy at the same time.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent / "data" / "kroger_fiscal_periods.csv"

PERIODS_PER_YEAR = 13

# The fixed 4-3-3-3 quarter split (period -> quarter), verified across every FY in the table.
QUARTER_OF_PERIOD: dict[int, int] = {
    1: 1,
    2: 1,
    3: 1,
    4: 1,  # Q1 (4 periods)
    5: 2,
    6: 2,
    7: 2,  # Q2
    8: 3,
    9: 3,
    10: 3,  # Q3
    11: 4,
    12: 4,
    13: 4,  # Q4
}


@dataclass(frozen=True)
class FiscalPeriod:
    """One of the 13 periods of a Kroger fiscal year, with its authoritative calendar span."""

    fiscal_year: int  # the Kroger FY as a calendar year, e.g. 2026 == "FY 26"
    period: int  # 1..13
    quarter: int  # 1..4 (4-3-3-3)
    begin: date
    end: date
    weeks: int  # 4, or 5 for Period 13 of a 53-week year

    @property
    def days(self) -> int:
        return (self.end - self.begin).days + 1

    @property
    def label(self) -> str:
        """The sponsor's period label, e.g. 'P05-26' (Period 5 of FY 26)."""

        return f"P{self.period:02d}-{self.fiscal_year % 100:02d}"


@dataclass(frozen=True)
class Timeframe:
    """A contiguous span of periods the bid template groups together (the supplier prices ONE)."""

    label: str
    fiscal_year: int
    start_period: int
    end_period: int
    begin: date
    end: date

    @property
    def period_numbers(self) -> tuple[int, ...]:
        return tuple(range(self.start_period, self.end_period + 1))


@lru_cache(maxsize=1)
def _load() -> tuple[FiscalPeriod, ...]:
    rows: list[FiscalPeriod] = []
    with _DATA.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(
                FiscalPeriod(
                    fiscal_year=int(r["fiscal_year"]),
                    period=int(r["period"]),
                    quarter=int(r["quarter"]),
                    begin=date.fromisoformat(r["begin_date"]),
                    end=date.fromisoformat(r["end_date"]),
                    weeks=int(r["weeks"]),
                )
            )
    return tuple(rows)


# --------------------------------------------------------------------------- #
# lookups
# --------------------------------------------------------------------------- #
def all_periods() -> tuple[FiscalPeriod, ...]:
    """Every period in the calendar (FY16..FY36), ordered."""

    return _load()


def fiscal_years() -> tuple[int, ...]:
    """The fiscal years the calendar covers, ascending."""

    return tuple(sorted({p.fiscal_year for p in _load()}))


def periods_in_year(fiscal_year: int) -> tuple[FiscalPeriod, ...]:
    """The 13 periods of a fiscal year, in order (raises if the year is outside the table)."""

    ps = tuple(p for p in _load() if p.fiscal_year == fiscal_year)
    if not ps:
        lo, hi = fiscal_years()[0], fiscal_years()[-1]
        raise ValueError(f"fiscal year {fiscal_year} is outside the calendar (FY{lo}..FY{hi}).")
    return ps


def get_period(fiscal_year: int, period: int) -> FiscalPeriod:
    """The single FiscalPeriod for (fiscal_year, period); raises if the period is out of range."""

    for p in periods_in_year(fiscal_year):
        if p.period == period:
            return p
    raise ValueError(f"period {period} is out of range 1..{PERIODS_PER_YEAR}.")


def period_for_date(day: date) -> FiscalPeriod:
    """The fiscal period a calendar date falls in (raises if the date is outside the calendar)."""

    for p in _load():
        if p.begin <= day <= p.end:
            return p
    first, last = _load()[0], _load()[-1]
    raise ValueError(
        f"{day.isoformat()} is outside the calendar ({first.begin.isoformat()}.."
        f"{last.end.isoformat()})."
    )


# --------------------------------------------------------------------------- #
# timeframe grouping (period -> timeframe map) + intake fan-out
# --------------------------------------------------------------------------- #
def group_periods(
    fiscal_year: int,
    spans: list[tuple[int, int]],
    labels: list[str] | None = None,
) -> list[Timeframe]:
    """Group the year's 13 periods into contiguous timeframes from (start, end) period spans.

    `spans` must be contiguous and cover periods 1..13 exactly once (e.g. the buyer's earlier
    example `[(1, 2), (3, 9), (10, 13)]`). Each timeframe's begin/end come from its first/last
    period's authoritative dates. This is the per-cycle template grouping (INTAKE §1a).
    """

    if not spans:
        raise ValueError("at least one period span is required.")
    flat = [p for s, e in spans for p in range(s, e + 1)]
    if flat != list(range(1, PERIODS_PER_YEAR + 1)):
        raise ValueError(
            "spans must be contiguous and cover periods 1..13 exactly once; "
            f"got {spans} -> periods {flat}."
        )
    if labels is not None and len(labels) != len(spans):
        raise ValueError("labels must match the number of spans.")

    out: list[Timeframe] = []
    for i, (start, end) in enumerate(spans):
        first, last = get_period(fiscal_year, start), get_period(fiscal_year, end)
        label = labels[i] if labels else f"P{start:02d}-P{end:02d}"
        out.append(
            Timeframe(
                label=label,
                fiscal_year=fiscal_year,
                start_period=start,
                end_period=end,
                begin=first.begin,
                end=last.end,
            )
        )
    return out


def fiscal_quarters(fiscal_year: int) -> list[Timeframe]:
    """The four fiscal quarters as timeframes (4-3-3-3): Q1=P1-4, Q2=P5-7, Q3=P8-10, Q4=P11-13."""

    return group_periods(fiscal_year, [(1, 4), (5, 7), (8, 10), (11, 13)], ["Q1", "Q2", "Q3", "Q4"])


def fiscal_halves(fiscal_year: int) -> list[Timeframe]:
    """Two halves aligned to the quarter boundaries: H1=Q1+Q2 (P1-7), H2=Q3+Q4 (P8-13)."""

    return group_periods(fiscal_year, [(1, 7), (8, 13)], ["H1", "H2"])


def fiscal_year_timeframe(fiscal_year: int) -> list[Timeframe]:
    """A single timeframe over the whole year (a flat-year bid: one price for all 13 periods)."""

    return group_periods(fiscal_year, [(1, 13)], ["FY"])


def per_period(fiscal_year: int) -> list[Timeframe]:
    """The finest grouping — each period is its own timeframe (the supplier prices all 13)."""

    return group_periods(
        fiscal_year,
        [(p, p) for p in range(1, PERIODS_PER_YEAR + 1)],
        [f"P{p:02d}" for p in range(1, PERIODS_PER_YEAR + 1)],
    )


def expand_to_periods(timeframe: Timeframe) -> tuple[FiscalPeriod, ...]:
    """Fan a timeframe out to every fiscal period it covers — intake's flat-13 write (INTAKE §1a).

    A timeframe priced once is recorded against each of its periods, so the database stays flat at
    the 13-period grain while the supplier only filled a handful of timeframe cells.
    """

    return tuple(get_period(timeframe.fiscal_year, p) for p in timeframe.period_numbers)
