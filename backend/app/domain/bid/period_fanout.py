"""Intake fan-out — realize the flat-13 model by fanning timeframe prices out to periods (§1a).

INTAKE_TEMPLATE_DESIGN §1a: storage stays **flat at the 13 periods**, but a supplier only prices a
handful of **timeframes** (contiguous spans of fiscal periods grouped by the bid template). Intake
then **fans out** each timeframe's price to EVERY fiscal period the timeframe covers, so each of the
13 periods carries the timeframe's payload verbatim while the supplier filled only a few cells.

This module is PURE logic — no database, no ORM, no `app.domain.*` imports. It builds on the
authoritative calendar (`app.fiscal.calendar.expand_to_periods`) and emits plain `FannedPrice`
records. The ORM / ingest wiring (turning these records into `bid.bid_line` rows) is a SEPARATE step
layered on top later; keeping the fan-out pure lets it be unit-tested in isolation.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.fiscal.calendar import FiscalPeriod, Timeframe, expand_to_periods


@dataclass(frozen=True)
class FannedPrice:
    """A timeframe's payload landed on ONE fiscal period — the flat-13 grain (INTAKE §1a).

    `payload` is opaque: whatever price/volume/component dict the caller priced the timeframe with,
    copied verbatim onto each period. This module never inspects or hardcodes bid column names.
    """

    fiscal_period: FiscalPeriod
    payload: Mapping[str, object]

    @property
    def period_key(self) -> tuple[int, int]:
        """An id-able key for the landed period — `(fiscal_year, period)`, unique within a year."""

        return (self.fiscal_period.fiscal_year, self.fiscal_period.period)


def fan_out(timeframe: Timeframe, payload: Mapping[str, object]) -> list[FannedPrice]:
    """Fan one timeframe's payload out to every fiscal period it covers (INTAKE §1a).

    Each period gets its own SHALLOW COPY of `payload`, so callers cannot mutate shared state across
    the returned records. Returns one `FannedPrice` per period, in period order.
    """

    return [
        FannedPrice(fiscal_period=period, payload=copy.copy(payload))
        for period in expand_to_periods(timeframe)
    ]


def fan_out_all(
    groups: Sequence[tuple[Timeframe, Mapping[str, object]]],
) -> list[FannedPrice]:
    """Fan out several (timeframe, payload) pairs, flattened and ordered by period (INTAKE §1a).

    Validates that across all timeframes each fiscal period is covered AT MOST once — a period must
    not receive two prices. Raises `ValueError` on any overlap.
    """

    fanned: list[FannedPrice] = []
    seen: set[tuple[int, int]] = set()
    for timeframe, payload in groups:
        for record in fan_out(timeframe, payload):
            key = record.period_key
            if key in seen:
                fy, period = key
                raise ValueError(
                    f"period {period} of FY{fy} is covered by more than one timeframe; "
                    "each period must get at most one price."
                )
            seen.add(key)
            fanned.append(record)

    fanned.sort(key=lambda r: r.period_key)
    return fanned
