"""Generate the owned bid-template xlsx from a cycle scope (D20 generate-end, D17 our design).

Given a `CycleScope` (synthetic for now — in production it is read from `cyc.*`: the lots, DCs,
items, TFs, and rounds in scope), produce a multi-sheet workbook:
  * `Instructions` — cycle identity + window + the supplier rules + the template-version token.
  * `Bids`         — one pre-filled scope row per cell, with blank price/volume cells.
  * `Capacity`     — one pre-filled row per supplier x DC x item x TF, blank capacity cells.

This is the GENERATE end of the round-trip; `bid_ingester.py` is the INGEST end. Both share
`template_schema.py`, so they cannot drift (D20). File IO via openpyxl is fine here — this is a
service, not the pure engine.
"""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from app.domain.bid.template_schema import (
    BID_HEADERS,
    BODY_START_ROW,
    CAPACITY_HEADERS,
    HEADER_ROW,
    SHEET_BIDS,
    SHEET_CAPACITY,
    SHEET_INSTRUCTIONS,
    TITLE_ROW,
    BidColumn,
    CapacityColumn,
    CycleScope,
    ScopeRow,
)

# The supplier rules written onto the Instructions sheet (label, value) — our wording, D17.
_INSTRUCTION_RULES: tuple[tuple[str, str], ...] = (
    ("Template version", ""),  # filled from scope at build time
    ("Cycle", ""),
    ("Window", ""),
    (
        "Pricing",
        "Enter EITHER an All-In $/case (already net of all discounts) OR the components "
        "(FOB + Delivery Surcharge + VegCool Surcharge - Lot Discount). Do not enter both an "
        "All-In and a Lot Discount on the same row.",
    ),
    (
        "No Bid",
        "Leave ALL price cells blank on a row you decline. Do not enter 0 for a no-bid.",
    ),
    (
        "Volume",
        "Enter Weekly and/or Total Vol Offered in cases for rows you bid.",
    ),
    (
        "Grain",
        "One row per DC x Lot x Item x TF. Prices are per period (TF) — fill each row you serve.",
    ),
)


def _write_headers(ws: Worksheet, title: str, headers: tuple[str, ...]) -> None:
    """Write the row-1 title band and the row-2 header row."""

    ws.cell(row=TITLE_ROW, column=1, value=title)
    for col_index, header in enumerate(headers, start=1):
        ws.cell(row=HEADER_ROW, column=col_index, value=header)


def _build_instructions(ws: Worksheet, scope: CycleScope) -> None:
    ws.cell(row=1, column=1, value="Kroger Produce RFP — Bid Template")
    rows: list[tuple[str, str]] = []
    for label, value in _INSTRUCTION_RULES:
        if label == "Template version":
            value = scope.template_version
        elif label == "Cycle":
            value = f"{scope.cycle_code} — {scope.cycle_name}"
        elif label == "Window":
            value = scope.window_label
        rows.append((label, value))
    for offset, (label, value) in enumerate(rows, start=3):
        ws.cell(row=offset, column=1, value=label)
        ws.cell(row=offset, column=2, value=value)


def _scope_cell_values(row: ScopeRow, cycle_id: str) -> dict[BidColumn, str]:
    """The system-owned scope cells written into a `Bids` row.

    D21: the KEY-ID columns carry the system-owned surrogate UUIDs (the join identity); the display
    columns carry the human names (attributes only). Both are system-owned/locked — a supplier
    never edits them — but only the keys are the identity the ingester validates against the scope.
    """

    return {
        # --- Key IDs (D21) — the join identity (validated, never resolved, on ingest). ---
        BidColumn.CYCLE_ID: cycle_id,
        BidColumn.ROUND_ID: row.round_id,
        BidColumn.TF_ID: row.tf_id,
        BidColumn.LOT_ID: row.lot_id,
        BidColumn.ITEM_ID: row.item_id,
        BidColumn.DC_ID: row.dc_id,
        BidColumn.SUPPLIER_ID: row.supplier_id,
        # --- Display names (attributes only; a mismatch warns, never re-resolves). ---
        BidColumn.ROUND: row.round_code,
        BidColumn.BID_TYPE: row.bid_type,
        BidColumn.SUPPLIER: row.supplier_label,
        BidColumn.DC: row.dc_label,
        BidColumn.LOT: row.lot_label,
        BidColumn.ITEM: row.item_label,
        BidColumn.TF: row.tf_code,
    }


def _build_bids(ws: Worksheet, scope: CycleScope) -> None:
    _write_headers(ws, f"Bids — {scope.cycle_name}", BID_HEADERS)
    header_index = {header: i for i, header in enumerate(BID_HEADERS, start=1)}
    for offset, scope_row in enumerate(scope.rows, start=BODY_START_ROW):
        for column, value in _scope_cell_values(scope_row, scope.cycle_id).items():
            ws.cell(row=offset, column=header_index[column.value], value=value)
        # Price/volume cells are intentionally left blank for the supplier to fill.


def _build_capacity(ws: Worksheet, scope: CycleScope) -> None:
    _write_headers(ws, f"Capacity — {scope.cycle_name}", CAPACITY_HEADERS)
    header_index = {header: i for i, header in enumerate(CAPACITY_HEADERS, start=1)}
    # Capacity grain is supplier x DC x item x TF (round-independent) — dedupe the bid scope.
    seen: set[tuple[str, str, str, str]] = set()
    offset = BODY_START_ROW
    for scope_row in scope.rows:
        key = (
            scope_row.supplier_label,
            scope_row.dc_label,
            scope_row.item_label,
            scope_row.tf_code,
        )
        if key in seen:
            continue
        seen.add(key)
        ws.cell(row=offset, column=header_index[CapacityColumn.SUPPLIER.value], value=key[0])
        ws.cell(row=offset, column=header_index[CapacityColumn.DC.value], value=key[1])
        ws.cell(row=offset, column=header_index[CapacityColumn.ITEM.value], value=key[2])
        ws.cell(row=offset, column=header_index[CapacityColumn.TF.value], value=key[3])
        offset += 1


def build_template_workbook(scope: CycleScope) -> Workbook:
    """Build the in-memory multi-sheet template workbook for a cycle scope."""

    wb = Workbook()
    # openpyxl seeds a default sheet; repurpose it as Instructions.
    instructions = wb.active
    assert instructions is not None  # noqa: S101 — Workbook() always has an active sheet
    instructions.title = SHEET_INSTRUCTIONS
    _build_instructions(instructions, scope)

    bids = wb.create_sheet(SHEET_BIDS)
    _build_bids(bids, scope)

    capacity = wb.create_sheet(SHEET_CAPACITY)
    _build_capacity(capacity, scope)

    return wb


def generate_template_bytes(scope: CycleScope) -> bytes:
    """Generate the template and return it as xlsx bytes (the artifact the system releases)."""

    wb = build_template_workbook(scope)
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
