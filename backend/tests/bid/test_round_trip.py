"""D20 round-trip proof: generate a template -> fill (synthetic) -> ingest -> grain round-trips.

The system owns BOTH ends (generate + ingest) of ONE owned schema (D20). This asserts that a
template generated for a synthetic cycle scope, filled with synthetic bids, ingests back to the
SAME supplier x DC x lot x item x TF x round grain, with the cost COMPONENTS preserved exactly.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from openpyxl import load_workbook

from app.domain.bid.bid_ingester import (
    PRICE_BASIS_ALL_IN,
    PRICE_BASIS_FALLBACK,
    Completeness,
    ingest_template,
)
from app.domain.bid.template_generator import (
    build_template_workbook,
    generate_template_bytes,
)
from app.domain.bid.template_schema import (
    BID_HEADERS,
    HEADER_ROW,
    SHEET_BIDS,
    SHEET_CAPACITY,
    SHEET_INSTRUCTIONS,
    BidColumn,
)
from tests.bid.synthetic import build_resolver, build_scope

_D = Decimal


def _fill_bids(template_bytes: bytes) -> bytes:
    """Fill the generated template's blank price cells with synthetic bids (the supplier step).

    Row 0 -> All-In bid. Row 1 -> component-fallback bid. The rest -> All-In with volume.
    """

    wb = load_workbook(BytesIO(template_bytes))
    ws = wb[SHEET_BIDS]
    col = {h: i for i, h in enumerate(BID_HEADERS, start=1)}

    def put(row: int, column: BidColumn, value: object) -> None:
        ws.cell(row=row, column=col[column.value], value=value)

    body_rows = list(range(HEADER_ROW + 1, ws.max_row + 1))
    for offset, row in enumerate(body_rows):
        if offset == 0:
            # All-In bid (price basis ALL_IN), with volume.
            put(row, BidColumn.ALL_IN, "100.00")
            put(row, BidColumn.TOTAL_VOL_OFFERED, "500")
            put(row, BidColumn.WEEKLY_VOL_OFFERED, "50")
            put(row, BidColumn.PRICING_COMMENTS, "firm")
        elif offset == 1:
            # Component-fallback bid: FOB 90 + Delivery 5 + VegCool 3 - LotDisc 2 = 96.00.
            put(row, BidColumn.FOB, "90.00")
            put(row, BidColumn.DELIVERY_SURCHARGE, "5.00")
            put(row, BidColumn.VEGCOOL_SURCHARGE, "3.00")
            put(row, BidColumn.LOT_DISCOUNT, "2.00")
            put(row, BidColumn.TOTAL_VOL_OFFERED, "300")
        else:
            put(row, BidColumn.ALL_IN, "101.50")
            put(row, BidColumn.TOTAL_VOL_OFFERED, "200")

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_generated_template_has_owned_sheets_and_grain() -> None:
    scope = build_scope()
    wb = build_template_workbook(scope)
    assert wb.sheetnames == [SHEET_INSTRUCTIONS, SHEET_BIDS, SHEET_CAPACITY]
    ws = wb[SHEET_BIDS]
    headers = [ws.cell(row=HEADER_ROW, column=c).value for c in range(1, len(BID_HEADERS) + 1)]
    assert headers == list(BID_HEADERS)
    # One Bids body row per scope cell.
    assert ws.max_row - HEADER_ROW == len(scope.rows)


def test_round_trip_grain_and_components_exact() -> None:
    scope = build_scope()
    resolver = build_resolver()

    template_bytes = generate_template_bytes(scope)
    filled_bytes = _fill_bids(template_bytes)
    result = ingest_template(filled_bytes, resolver)

    # Nothing quarantined — a clean self-generated round-trip.
    assert result.quarantined == []
    # Same number of lines as scope rows (grain count round-trips).
    assert len(result.lines) == len(scope.rows)

    # The ingested identity grain matches the scope's identity grain EXACTLY (the D20 proof).
    ingested_grain = {
        (
            line.round_code,
            line.identity.supplier_id,
            line.identity.dc_id,
            line.identity.lot_id,
            line.identity.item_id,
            line.identity.tf_code,
        )
        for line in result.lines
    }
    scope_grain = {
        (r.round_code, r.supplier_id, r.dc_id, r.lot_id, r.item_id, r.tf_code) for r in scope.rows
    }
    assert ingested_grain == scope_grain

    by_row = {line.source_row_number: line for line in result.lines}
    first_row = min(by_row)

    # Row 0 — All-In basis, price verbatim, components carried.
    all_in_line = by_row[first_row]
    assert all_in_line.price_basis == PRICE_BASIS_ALL_IN
    assert all_in_line.landed_cost_per_case == _D("100.00")
    assert all_in_line.components.all_in == _D("100.00")
    assert all_in_line.completeness is Completeness.BID
    assert all_in_line.total_vol_offered == _D("500")
    assert all_in_line.weekly_vol_offered == _D("50")
    assert all_in_line.pricing_comments == "firm"

    # Row 1 — component fallback, §7 sum, components preserved exactly.
    fb_line = by_row[first_row + 1]
    assert fb_line.price_basis == PRICE_BASIS_FALLBACK
    assert fb_line.landed_cost_per_case == _D("96.00")  # 90 + 5 + 3 - 2
    assert fb_line.components.fob == _D("90.00")
    assert fb_line.components.delivery_surcharge == _D("5.00")
    assert fb_line.components.vegcool_surcharge == _D("3.00")
    assert fb_line.components.lot_discount == _D("2.00")
    assert fb_line.completeness is Completeness.BID

    # All lines flagged BID; counts reconcile.
    assert result.bid_count == len(scope.rows)
    assert result.no_bid_count == 0
    assert result.incomplete_count == 0
