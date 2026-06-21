"""ref.fiscal_period seed fidelity — the governed period dimension mirrors the calendar library.

Migration 0014 creates ref.fiscal_period and seeds it from the authoritative CSV
(app/fiscal/data/kroger_fiscal_periods.csv, the same source app.fiscal.calendar loads). This test
provisions a freshly migrated isolated DB and proves the table round-trips that calendar: the full
273-row FY16..FY36 set landed, the fiscal-year span is 2016..2036, and a sampled row matches the
typed library exactly (so the database dimension and the in-process library never diverge).
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import text

from app.fiscal.calendar import get_period
from app.pilot.run_db import drop_run_database, provision_run_database, run_unit_of_work


@pytest.mark.integration
def test_ref_fiscal_period_seeded_from_calendar() -> None:
    slug = f"fiscal-period-test-{uuid.uuid4().hex[:8]}"
    try:
        provision_run_database(slug)  # fresh migrated isolated DB (includes 0014)

        with run_unit_of_work(slug) as session:
            # (a) the full FY16..FY36 calendar landed — 273 rows.
            count = session.execute(text("SELECT count(*) FROM ref.fiscal_period")).scalar()
            assert count == 273

            # (b) the fiscal-year span is 2016..2036 inclusive.
            lo, hi = session.execute(
                text("SELECT min(fiscal_year), max(fiscal_year) FROM ref.fiscal_period")
            ).one()
            assert (lo, hi) == (2016, 2036)

            # (c) a sampled row matches the typed calendar library exactly.
            row = session.execute(
                text(
                    "SELECT quarter, begin_date, end_date, weeks FROM ref.fiscal_period "
                    "WHERE fiscal_year = :fy AND period = :p"
                ),
                {"fy": 2026, "p": 5},
            ).one()
            assert row.quarter == 2
            assert row.begin_date == date(2026, 5, 24)
            assert row.end_date == date(2026, 6, 20)

            expected = get_period(2026, 5)
            assert row.quarter == expected.quarter
            assert row.begin_date == expected.begin
            assert row.end_date == expected.end
            assert row.weeks == expected.weeks
    finally:
        drop_run_database(slug)
