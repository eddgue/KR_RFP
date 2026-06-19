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

NO real data here — pure structure (sheet names, headers, the version token). ADR-0001 §4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# The version token stamped into every generated template and asserted on ingest. Bump on any
# header/grain change so an old file ingested against a new reader is caught, not silently mapped.
TEMPLATE_VERSION = "kr-bid-template/v1"

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

    # --- Scope / identity (system-owned; the generator pre-fills these). ---
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
    PRICING_COMMENTS = "Pricing Comments"
    # --- Volume offered (supplier-owned; drives coverage). ---
    WEEKLY_VOL_OFFERED = "Weekly Vol Offered"
    TOTAL_VOL_OFFERED = "Total Vol Offered"
    INVESTED_R1 = "Invested? (R1)"


# The scope columns the generator pre-fills (the cells the system owns).
SCOPE_COLUMNS: tuple[BidColumn, ...] = (
    BidColumn.ROUND,
    BidColumn.BID_TYPE,
    BidColumn.SUPPLIER,
    BidColumn.DC,
    BidColumn.LOT,
    BidColumn.ITEM,
    BidColumn.TF,
)

# The supplier-owned price/volume columns (blank in a fresh template).
PRICE_COLUMNS: tuple[BidColumn, ...] = (
    BidColumn.ALL_IN,
    BidColumn.FOB,
    BidColumn.DELIVERY_SURCHARGE,
    BidColumn.VEGCOOL_SURCHARGE,
    BidColumn.LOT_DISCOUNT,
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


# --- The scope contract: what the generator needs from a cycle to build the template. ---


@dataclass(frozen=True)
class ScopeRow:
    """One supplier x DC x lot x item x TF x round cell — the template's pre-filled grain.

    The generator emits one `Bids` row per ScopeRow; the ingester resolves each parsed row back
    to this identity. IDs are the store's canonical ids; the *_label fields are the human strings
    written into the sheet (and matched on ingest via the ref alias layer).
    """

    round_code: str
    bid_type: str
    supplier_id: str
    supplier_label: str
    dc_id: str
    dc_label: str
    lot_id: str
    lot_label: str
    item_id: str
    item_label: str
    tf_code: str


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
