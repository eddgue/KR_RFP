"""The OWNED bid-template schema — the single contract shared by both ends of the round-trip.

D20 (round-trip ingest) + D17 (our own multi-sheet template, not a copy of the reference).
This module is the *one* place the template's shape is declared; `template_generator.py` writes
it and `bid_ingester.py` reads it back. There is exactly one owned schema, two ends — so the two
can never drift (the whole point of D20: "the engine ingests the files it itself creates").

Design (D17 — our design, not the reference's 14-tab supplier workbook):
  * `Instructions`  — a cover/instructions sheet: cycle identity, window, template version, the
    rules a supplier must follow (No Bid handling, All-In vs component pricing, one-discount-path).
  * `Bids`          — the priced grain: ONE row per supplier x DC x lot x item x TF x round,
    carrying the engine's IN_Bids contract columns (CYCLE_FIELDTOMATO_STRUCTURE.md §1.2):
    Round, Bid Type, Supplier, DC, Lot, Item, TF, All-In $/case, FOB $/case, Delivery Surcharge,
    VegCool Surcharge, Lot Discount, Pricing Comments, Weekly/Total Vol Offered, Invested?(R1).
    Cost components are period-grain (D12): TF is on the row, so each period carries its own
    component set.
  * `Capacity`      — supplier capacity/volume offered per DC x item x TF (the coverage feed).

The generator pre-fills the scope columns (the cells the SYSTEM owns: identity + scope) and
leaves the price/volume cells blank for the supplier to fill. The ingester reads the same
columns back by header name (never by position — the reference's trailing-width inflation, §2 of
the structural map, taught us not to trust `max_column`).

D21 — explicit key IDs at every grain. Each `Bids` row carries the system-owned surrogate KEY
IDs (cycle / round / tf / lot / item / dc — UUID strings) alongside the human-readable names.
The key IDs are the JOIN identity; the names are DISPLAY-ONLY attributes. Because the template
embeds the keys, ingesting OUR template is a KEY-VALIDATED LOAD (read the embedded key, check it
against the cycle scope's known key set, accept or quarantine) — never a text/name guess. The
key columns are marked system-owned/locked (a convention here — `KEY_ID_COLUMNS`; no real Excel
cell-locking needed) so a supplier is never expected (or permitted) to touch them. Name resolution
survives ONLY in the legacy path (`legacy_adapter`), where inputs predate embedded keys.

NO real data here — pure structure (sheet names, headers, the version token). ADR-0001 §4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# The version token stamped into every generated template and asserted on ingest. Bump on any
# header/grain change so an old file ingested against a new reader is caught, not silently mapped.
TEMPLATE_VERSION = "kr-bid-template/v1"

# Soft "form" protection password for the supplier-facing sheets. Only the entry cells are unlocked;
# everything else is locked so a supplier fills a TRUE FORM, not a free spreadsheet. Excel sheet
# protection is a usability guard (not security) — the keyed re-ingest remains the real check (D21).
TEMPLATE_PROTECT_PASSWORD = "kr-rfp-bid"

# Header text of the generator-added per-row readiness traffic light (Not bid / Incomplete /
# Complete). It is a LOCKED, generator-owned formula column — NOT part of the ingested contract, so
# it is appended after BID_HEADERS and the ingester never reads it.
BID_STATUS_HEADER = "Bid Status"

# Sheet names (our design — D17). Stable identifiers the generator writes and the ingester reads.
SHEET_INSTRUCTIONS = "Instructions"
SHEET_BIDS = "Bids"
SHEET_CAPACITY = "Capacity"

# The header row index (1-based, openpyxl convention) for the data sheets. Row 1 is a title band;
# headers live on row 2; body starts row 3. (Our own layout — NOT the reference's row-4/row-17.)
TITLE_ROW = 1
HEADER_ROW = 2
BODY_START_ROW = 3


class BidColumn(StrEnum):
    """Canonical header strings for the `Bids` sheet — the IN_Bids contract, our wording.

    The string VALUE is the literal cell text the generator writes and the ingester matches on.
    Resolving by these names (not column index) is what makes the round-trip robust (D20).
    """

    # --- Key IDs (D21): system-owned surrogate UUIDs — THE join identity. Locked; never edited
    #     by a supplier, never the basis for a text guess. Validated, not resolved, on ingest. ---
    CYCLE_ID = "Cycle ID"
    ROUND_ID = "Round ID"
    TF_ID = "TF ID"
    LOT_ID = "Lot ID"
    ITEM_ID = "Item ID"
    DC_ID = "DC ID"
    SUPPLIER_ID = "Supplier ID"
    # --- Display names (system-owned attributes; human-readable, NOT the join key). A name that
    #     disagrees with the keyed identity is a WARNING/cross-check, never a re-resolve. ---
    ROUND = "Round"
    BID_TYPE = "Bid Type"
    SUPPLIER = "Supplier"
    DC = "DC Name"
    LOT = "Lot"
    ITEM = "Item Description"
    TF = "TF"
    # --- Pricing components (supplier-owned; left blank by the generator). D12 period-grain. ---
    ALL_IN = "All-In $/case"
    FOB = "FOB $/case"
    DELIVERY_SURCHARGE = "Delivery Surcharge"
    VEGCOOL_SURCHARGE = "VegCool Surcharge"
    LOT_DISCOUNT = "Lot Discount"
    # Supplier-stated lane transit (origin→DC), a hidden cost surfaced in the analysis. Always part
    # of the column SET; not every cycle/process populates it (blank -> no transit shown, no proxy).
    TRANSIT_DAYS = "Transit Days"
    PRICING_COMMENTS = "Pricing Comments"
    # --- Volume offered (supplier-owned; drives coverage). ---
    WEEKLY_VOL_OFFERED = "Weekly Vol Offered"
    TOTAL_VOL_OFFERED = "Total Vol Offered"
    INVESTED_R1 = "Invested? (R1)"


# The KEY-ID columns (D21): system-owned surrogate UUIDs, LOCKED. These are the join identity the
# ingester validates against the cycle scope's known key set; a supplier must never touch them. The
# ordering here is also the grain tuple order used by the key validator + the round-trip assertion.
KEY_ID_COLUMNS: tuple[BidColumn, ...] = (
    BidColumn.CYCLE_ID,
    BidColumn.ROUND_ID,
    BidColumn.TF_ID,
    BidColumn.LOT_ID,
    BidColumn.ITEM_ID,
    BidColumn.DC_ID,
    BidColumn.SUPPLIER_ID,
)

# The human DISPLAY columns the generator pre-fills (system-owned attributes; NOT the join key).
DISPLAY_SCOPE_COLUMNS: tuple[BidColumn, ...] = (
    BidColumn.ROUND,
    BidColumn.BID_TYPE,
    BidColumn.SUPPLIER,
    BidColumn.DC,
    BidColumn.LOT,
    BidColumn.ITEM,
    BidColumn.TF,
)

# All system-owned (key + display) scope columns the generator pre-fills.
SCOPE_COLUMNS: tuple[BidColumn, ...] = (*KEY_ID_COLUMNS, *DISPLAY_SCOPE_COLUMNS)

# The supplier-owned price/volume columns (blank in a fresh template).
PRICE_COLUMNS: tuple[BidColumn, ...] = (
    BidColumn.ALL_IN,
    BidColumn.FOB,
    BidColumn.DELIVERY_SURCHARGE,
    BidColumn.VEGCOOL_SURCHARGE,
    BidColumn.LOT_DISCOUNT,
    BidColumn.TRANSIT_DAYS,
    BidColumn.PRICING_COMMENTS,
    BidColumn.WEEKLY_VOL_OFFERED,
    BidColumn.TOTAL_VOL_OFFERED,
    BidColumn.INVESTED_R1,
)

# Full ordered header list for the `Bids` sheet (scope first, then pricing).
BID_HEADERS: tuple[str, ...] = tuple(c.value for c in (*SCOPE_COLUMNS, *PRICE_COLUMNS))


class CapacityColumn(StrEnum):
    """Canonical header strings for the `Capacity` sheet (supplier volume capability)."""

    SUPPLIER = "Supplier"
    DC = "DC Name"
    ITEM = "Item Description"
    TF = "TF"
    MAX_WEEKLY_CASES = "Max Weekly Cases"
    MAX_TOTAL_CASES = "Max Total Cases"
    CAPACITY_NOTES = "Capacity Notes"


CAPACITY_HEADERS: tuple[str, ...] = tuple(c.value for c in CapacityColumn)

# The supplier-owned entry columns on the Capacity sheet (the only cells unlocked on the form).
CAPACITY_ENTRY_COLUMNS: tuple[CapacityColumn, ...] = (
    CapacityColumn.MAX_WEEKLY_CASES,
    CapacityColumn.MAX_TOTAL_CASES,
    CapacityColumn.CAPACITY_NOTES,
)


# --- The scope contract: what the generator needs from a cycle to build the template. ---


@dataclass(frozen=True)
class ScopeRow:
    """One supplier x DC x lot x item x TF x round cell — the template's pre-filled grain.

    The generator emits one `Bids` row per ScopeRow, embedding the system-owned KEY IDs (D21) as
    the join identity and the *_label fields as display-only attributes. On ingest of OUR template
    the keys are VALIDATED against the cycle scope (never resolved from the labels); the labels are
    at most a cross-check that can warn.

    IDs are the store's system-owned surrogate UUIDs; the *_label fields are the human strings
    written into the sheet for the supplier to read.
    """

    round_code: str
    bid_type: str
    # --- System-owned surrogate KEY IDs (D21) — the join identity. ---
    round_id: str
    tf_id: str
    supplier_id: str
    dc_id: str
    lot_id: str
    item_id: str
    # --- Display-only attributes (human-readable; NOT the join key). ---
    supplier_label: str
    dc_label: str
    lot_label: str
    item_label: str
    tf_code: str

    def key_grain(self, cycle_id: str) -> tuple[str, str, str, str, str, str, str]:
        """The full embedded key tuple for this row, in KEY_ID_COLUMNS order.

        (cycle_id, round_id, tf_id, lot_id, item_id, dc_id, supplier_id) — the exact identity the
        ingester reconstructs from the embedded cells and validates against the scope key set.
        """

        return (
            cycle_id,
            self.round_id,
            self.tf_id,
            self.lot_id,
            self.item_id,
            self.dc_id,
            self.supplier_id,
        )


@dataclass(frozen=True)
class CycleScope:
    """A cycle's scope (synthetic for now) — the strategy/cycle-driven generator input (D18/D20).

    Strategy-agnostic: the generator reads whatever lots/DCs/items/TFs/rounds are in scope and
    builds the template from them; nothing commodity- or strategy-specific is hardcoded.
    """

    cycle_id: str
    cycle_code: str
    cycle_name: str
    window_label: str
    template_version: str = TEMPLATE_VERSION
    rows: tuple[ScopeRow, ...] = field(default_factory=tuple)

    def key_set(self) -> frozenset[tuple[str, str, str, str, str, str, str]]:
        """The scope's KNOWN key grain set (D21) — the allow-list the ingester validates against.

        Each entry is one row's full embedded key tuple (KEY_ID_COLUMNS order). An ingested row
        whose embedded keys are not in this set is quarantined (KEY_MISMATCH/UNKNOWN_KEY), never
        guessed back to an identity by its display names.
        """

        return frozenset(row.key_grain(self.cycle_id) for row in self.rows)
