"""Import timeframe-structured bids (with the full column set) INTO the by-period schema (§1a).

End-to-end proof of the flat-13 storage path on a real Postgres:
  1. stand up a real cycle (valid FK parents) and INGEST a bid template filled with the **potato
     sample's** prices across the full column set (All-In / FOB / surcharges / discount / volume) —
     these are the timeframe-grain rows (one per cell × TF, `fiscal_period_id` NULL);
  2. derive the cycle timeframe's PERIOD SPAN from its calendar dates (`period_for_date`);
  3. FAN each timeframe row out to every fiscal period in that span (`period_fanout.fan_out`) and
     write the by-period rows (`fiscal_period_id` set) — this is the "import into the by-period
     schema";
  4. assert every column survives the fan-out verbatim on each period, each by-period row links to a
     real `ref.fiscal_period`, the whole span is covered, and the period-grain uniqueness (migration
     0016) actually permits the fan-out.

Uses the potato sample when present (real prices); falls back to synthetic prices when it is absent
(the sample is git-ignored), so the test is CI-safe. Integration (needs a live Postgres at head).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy import text

from app.domain.bid.models import BidLine
from app.domain.bid.period_fanout import fan_out
from app.domain.bid.template_schema import BODY_START_ROW, HEADER_ROW, SHEET_BIDS, BidColumn
from app.fiscal.calendar import Timeframe, get_period, period_for_date
from app.pilot.service import PilotService
from app.pilot.vault import stage_filename
from tests.pilot.test_pilot_cycle_e2e import _build_filled_setup

_POTATO_SAMPLE = (
    Path(__file__).resolve().parents[2].parent
    / "reference"
    / "samples"
    / ("potato_2026_rfp_input.xlsx")
)

# The price/volume columns we copy through the fan-out and assert survive verbatim per period.
_CARRIED_COLUMNS = (
    "submitted_all_in_case",
    "fob_case",
    "delivery_surcharge_case",
    "vegcool_surcharge_case",
    "lot_discount_case",
    "volume_minimum_cases",
    "transit_days",
    "currency_code",
    "price_basis",
)


def _potato_price_pool() -> list[tuple[float, float]]:
    """Real (all-in, FOB) pairs from the potato sample; empty when that file is absent (CI)."""

    if not _POTATO_SAMPLE.is_file():
        return []
    wb = load_workbook(_POTATO_SAMPLE, read_only=True, data_only=True)
    pool: list[tuple[float, float]] = []
    for row in wb["IN_Bids"].iter_rows(min_row=5, values_only=True):
        if not row or row[0] is None:
            continue
        all_in, fob = row[7], row[8]
        if isinstance(all_in, int | float) and isinstance(fob, int | float):
            pool.append((float(all_in), float(fob)))
        if len(pool) >= 64:
            break
    return pool


def _header_map(ws: Worksheet) -> dict[str, int]:
    return {
        str(ws.cell(row=HEADER_ROW, column=c).value).strip(): c
        for c in range(1, ws.max_column + 1)
        if ws.cell(row=HEADER_ROW, column=c).value is not None
    }


def _fill_template_full_columns(template_bytes: bytes, pool: list[tuple[float, float]]) -> bytes:
    """Fill every scope row across the full column set, ALTERNATING the two valid price bases.

    A bid is either All-In basis OR component basis (FOB + surcharges) — never both on one row. To
    exercise the WHOLE column set with valid bids: even rows take the potato All-In/FOB (+ transit),
    odd rows take FOB + the three surcharge/discount components. Volume is set on every row.
    """

    wb = load_workbook(BytesIO(template_bytes))
    ws = wb[SHEET_BIDS]
    headers = _header_map(ws)

    def put(row: int, bid_col: BidColumn, value: object) -> None:
        c = headers.get(bid_col.value)
        if c is not None:
            ws.cell(row=row, column=c, value=value)

    fallback = [(18.40, 17.40), (24.75, 23.75), (31.41, 30.41), (26.50, 25.50)]
    prices = pool or fallback
    idx = 0
    for row in range(BODY_START_ROW, ws.max_row + 1):
        sup = str(ws.cell(row=row, column=headers[BidColumn.SUPPLIER.value]).value or "").strip()
        lot = str(ws.cell(row=row, column=headers[BidColumn.LOT.value]).value or "").strip()
        if not sup or not lot:
            continue
        all_in, fob = prices[idx % len(prices)]
        if idx % 2 == 0:  # All-In basis (real potato price) + transit
            put(row, BidColumn.ALL_IN, all_in)
            put(row, BidColumn.FOB, fob)
            put(row, BidColumn.TRANSIT_DAYS, 3)
        else:  # component basis: FOB + surcharges/discount (no All-In)
            put(row, BidColumn.FOB, fob)
            put(row, BidColumn.DELIVERY_SURCHARGE, 0.85)
            put(row, BidColumn.VEGCOOL_SURCHARGE, 0.40)
            put(row, BidColumn.LOT_DISCOUNT, 0.25)
        put(row, BidColumn.WEEKLY_VOL_OFFERED, 600)
        put(row, BidColumn.TOTAL_VOL_OFFERED, 7800)
        idx += 1

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.mark.integration
def test_timeframe_bids_import_into_by_period_schema(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    pool = _potato_price_pool()
    service = PilotService(tmp_path, isolate_db=False)
    paths = service.start_run(commodity="Colored Potatoes", label="Period Import")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)

    template_path = service.generate_bid_template(db_session, paths, 1)
    template_path.write_bytes(_fill_template_full_columns(template_path.read_bytes(), pool))
    n_lines = service.ingest_bids(db_session, paths, 1, template_path)
    assert n_lines > 0

    # The timeframe-grain rows just imported (one per cell × TF, no period yet).
    tf_rows = (
        db_session.query(BidLine)
        .filter(BidLine.cycle_id == cycle_id, BidLine.fiscal_period_id.is_(None))
        .all()
    )
    assert len(tf_rows) == n_lines

    # Derive each timeframe's PERIOD SPAN from its real calendar dates (date -> fiscal period).
    tf_dates = {
        tf_id: (start, end)
        for tf_id, start, end in db_session.execute(
            text("SELECT tf_id, start_date, end_date FROM cyc.cycle_timeframe WHERE cycle_id = :c"),
            {"c": cycle_id},
        ).all()
    }
    # ref.fiscal_period id lookup for FY2026, by period number.
    fp_id_by_period = dict(
        db_session.execute(
            text("SELECT period, id FROM ref.fiscal_period WHERE fiscal_year = 2026")
        ).all()
    )

    # FAN OUT each timeframe row into the by-period schema, carrying its full column payload.
    expected_span: list[int] | None = None
    for src in tf_rows:
        start, end = tf_dates[src.tf_id]
        first, last = period_for_date(start), period_for_date(end)
        assert first.fiscal_year == last.fiscal_year == 2026
        timeframe = Timeframe(
            label="cycle-tf",
            fiscal_year=2026,
            start_period=first.period,
            end_period=last.period,
            begin=get_period(2026, first.period).begin,
            end=get_period(2026, last.period).end,
        )
        span = list(range(first.period, last.period + 1))
        assert len(span) > 1, "the timeframe must cover several periods for a real fan-out"
        expected_span = span

        payload = {c: getattr(src, c) for c in _CARRIED_COLUMNS}
        for fanned in fan_out(timeframe, payload):
            period = fanned.fiscal_period.period
            db_session.add(
                BidLine(
                    bid_line_id=str(uuid.uuid4()),
                    submission_id=src.submission_id,
                    cycle_id=src.cycle_id,
                    round_id=src.round_id,
                    supplier_id=src.supplier_id,
                    dc_id=src.dc_id,
                    lot_id=src.lot_id,
                    item_id=src.item_id,
                    tf_id=src.tf_id,
                    fiscal_period_id=str(fp_id_by_period[period]),
                    exclusivity_required_flag=src.exclusivity_required_flag,
                    validity_status=src.validity_status,
                    created_at=datetime.now(UTC).replace(tzinfo=None),
                    is_scoreable=src.is_scoreable,
                    is_awardable=src.is_awardable,
                    **{c: fanned.payload[c] for c in _CARRIED_COLUMNS},
                )
            )
    db_session.flush()  # the period-grain uniqueness (migration 0016) must permit this

    assert expected_span is not None
    n_periods = len(expected_span)

    # (a) the by-period rows landed: one per (timeframe row × period in its span).
    by_period = (
        db_session.query(BidLine)
        .filter(BidLine.cycle_id == cycle_id, BidLine.fiscal_period_id.is_not(None))
        .all()
    )
    assert len(by_period) == n_lines * n_periods

    # (b) every by-period row links to a real ref.fiscal_period, and the whole span is covered once.
    linked = db_session.execute(
        text(
            "SELECT fp.fiscal_year, fp.period, count(*) "
            "FROM bid.bid_line bl JOIN ref.fiscal_period fp ON bl.fiscal_period_id = fp.id::text "
            "WHERE bl.cycle_id = :c AND bl.fiscal_period_id IS NOT NULL "
            "GROUP BY fp.fiscal_year, fp.period ORDER BY fp.period"
        ),
        {"c": cycle_id},
    ).all()
    assert [(fy, p) for fy, p, _ in linked] == [(2026, p) for p in expected_span]
    assert all(cnt == n_lines for _, _, cnt in linked)  # each period got every cell's price

    # (c) every COLUMN survives the fan-out verbatim — for EVERY source row vs. its period rows.
    for sample in tf_rows:
        period_rows = (
            db_session.query(BidLine)
            .filter(
                BidLine.cycle_id == cycle_id,
                BidLine.submission_id == sample.submission_id,
                BidLine.dc_id == sample.dc_id,
                BidLine.lot_id == sample.lot_id,
                BidLine.item_id == sample.item_id,
                BidLine.tf_id == sample.tf_id,
                BidLine.fiscal_period_id.is_not(None),
            )
            .all()
        )
        assert len(period_rows) == n_periods
        for pr in period_rows:
            for column in _CARRIED_COLUMNS:
                assert getattr(pr, column) == getattr(sample, column), f"{column} not preserved"

    # (d) the full column set was genuinely exercised: some cells priced All-In (real potato value,
    # a Decimal), others carried the surcharge components — both survived into the by-period rows.
    all_in_vals = [r.submitted_all_in_case for r in tf_rows if r.submitted_all_in_case is not None]
    surcharge_vals = [r.delivery_surcharge_case for r in tf_rows if r.delivery_surcharge_case]
    assert all_in_vals and all(isinstance(v, Decimal) for v in all_in_vals)
    assert surcharge_vals, "the surcharge/component columns were exercised and carried through"
