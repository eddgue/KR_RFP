"""Ingest a returned bid template back to `bid.bid_line` (+ components) rows (D20 ingest-end).

This is the INGEST end of the round-trip. It reads OUR owned template (`template_schema.py`) —
NOT arbitrary legacy layouts (D20: "no universal-format guessing for the live product"). It:

  1. Reads the `Bids` sheet by HEADER NAME (never by column index — the reference's trailing-
     width inflation taught us not to trust `max_column`; CYCLE_FIELDTOMATO_STRUCTURE.md §2).
  2. Resolves supplier / DC / item / lot / TF identity via the ref/alias layer (stubbed here as
     a pluggable `IdentityResolver`; the real one queries `ref.*_alias`).
  3. Constructs the per-line cost via the engine's §7 rule (All-In primary; fallback =
     FOB + Delivery + VegCool - Lot Discount) WITH the double-subtract guard.
  4. Flags completeness: `bid` (priced), `no_bid` (all price cells blank), `incomplete` (partial).
  5. Quarantines rows it cannot resolve — it does NOT guess.

Output is an in-memory `IngestResult` of parsed lines + quarantined rows; persisting to the DB
(`bid.bid_line` / the component columns added by migration 0007) is the caller's unit of work.
The parsed line carries exactly the columns the engine's cost construction needs, so a generated
template round-trips to the same `bid_line` grain it was built from (the D20 proof).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from io import BytesIO
from typing import Protocol

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from app.domain.bid.template_schema import (
    HEADER_ROW,
    SHEET_BIDS,
    BidColumn,
)


class Completeness(StrEnum):
    """Per-line completeness flag (CYCLE_FIELDTOMATO_STRUCTURE.md §4 No-Bid handling)."""

    BID = "bid"  # a usable price is present (All-In, or enough components for the fallback)
    NO_BID = "no_bid"  # every price/volume cell blank — a declined cell, NOT a zero price
    INCOMPLETE = "incomplete"  # partial: some price intent but not enough to construct a price


class QuarantineReason(StrEnum):
    """Why a row could not become a resolved, costed bid line (we quarantine, never guess)."""

    UNRESOLVED_SUPPLIER = "unresolved_supplier"
    UNRESOLVED_DC = "unresolved_dc"
    UNRESOLVED_LOT = "unresolved_lot"
    UNRESOLVED_ITEM = "unresolved_item"
    UNRESOLVED_TF = "unresolved_tf"
    MISSING_IDENTITY = "missing_identity"  # a required scope cell was blank
    DOUBLE_SUBTRACT = "double_subtract"  # All-In AND a discount both populated (§7 footgun)
    BAD_NUMERIC = "bad_numeric"  # a price cell held a non-numeric value


@dataclass(frozen=True)
class ResolvedIdentity:
    """The store-canonical ids a parsed row resolved to."""

    supplier_id: str
    dc_id: str
    lot_id: str
    item_id: str
    tf_code: str


class IdentityResolver(Protocol):
    """Resolves the human labels in a template back to canonical store ids.

    The real implementation queries `ref.supplier_alias` / `ref.dc_alias` / `ref.item_alias`
    (KEEP #6, the alias layer) and the cycle's `cyc.cycle_lot` / `cyc.cycle_timeframe` scope.
    Each method returns the canonical id, or None when the label cannot be resolved (-> quarantine,
    never a guess).
    """

    def resolve_supplier(self, label: str) -> str | None: ...
    def resolve_dc(self, label: str) -> str | None: ...
    def resolve_lot(self, label: str) -> str | None: ...
    def resolve_item(self, label: str) -> str | None: ...
    def resolve_tf(self, code: str) -> str | None: ...


@dataclass
class StubIdentityResolver:
    """A simple dict-backed resolver (stub) — maps normalized labels to canonical ids.

    Stands in for the ref/alias layer for the prototype and tests. Normalization is the same
    case/space-folding the alias layer applies (`normalized_alias_text`), so an exact or
    alias-style label resolves and an unknown one returns None (-> quarantine).
    """

    suppliers: dict[str, str] = field(default_factory=dict)
    dcs: dict[str, str] = field(default_factory=dict)
    lots: dict[str, str] = field(default_factory=dict)
    items: dict[str, str] = field(default_factory=dict)
    tfs: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _norm(text: str) -> str:
        return " ".join(text.strip().lower().split())

    def resolve_supplier(self, label: str) -> str | None:
        return self.suppliers.get(self._norm(label))

    def resolve_dc(self, label: str) -> str | None:
        return self.dcs.get(self._norm(label))

    def resolve_lot(self, label: str) -> str | None:
        return self.lots.get(self._norm(label))

    def resolve_item(self, label: str) -> str | None:
        return self.items.get(self._norm(label))

    def resolve_tf(self, code: str) -> str | None:
        return self.tfs.get(self._norm(code))


@dataclass(frozen=True)
class ParsedComponents:
    """The cost components parsed from one bid row (maps 1:1 to the engine's BidComponents / §7)."""

    all_in: Decimal | None
    fob: Decimal | None
    delivery_surcharge: Decimal
    vegcool_surcharge: Decimal
    lot_discount: Decimal


@dataclass(frozen=True)
class ParsedBidLine:
    """One resolved, costed bid line — the round-trip target (maps onto bid.bid_line + components).

    `landed_cost_per_case` is the §7-constructed price (the engine's Price); `components` are the
    raw parts persisted to the bid_line component columns (migration 0007). `price_basis` records
    which §7 branch produced the price (ALL_IN vs COMPONENT_FALLBACK), so the store is honest about
    provenance and the no-double-discount CHECK has a basis to key on.
    """

    round_code: str
    bid_type: str
    identity: ResolvedIdentity
    components: ParsedComponents
    landed_cost_per_case: Decimal | None
    price_basis: str
    weekly_vol_offered: Decimal | None
    total_vol_offered: Decimal | None
    invested_r1: bool | None
    pricing_comments: str | None
    completeness: Completeness
    source_row_number: int


@dataclass(frozen=True)
class QuarantinedRow:
    """A row that could not be ingested — kept verbatim with its reason (we do not guess)."""

    source_row_number: int
    reason: QuarantineReason
    detail: str
    raw: dict[str, str]


@dataclass
class IngestResult:
    """The outcome of ingesting one returned template."""

    lines: list[ParsedBidLine] = field(default_factory=list)
    quarantined: list[QuarantinedRow] = field(default_factory=list)

    @property
    def bid_count(self) -> int:
        return sum(1 for line in self.lines if line.completeness is Completeness.BID)

    @property
    def no_bid_count(self) -> int:
        return sum(1 for line in self.lines if line.completeness is Completeness.NO_BID)

    @property
    def incomplete_count(self) -> int:
        return sum(1 for line in self.lines if line.completeness is Completeness.INCOMPLETE)


# Price basis labels (mirror the bid_line.price_basis vocabulary).
PRICE_BASIS_ALL_IN = "ALL_IN"
PRICE_BASIS_FALLBACK = "COMPONENT_FALLBACK"


def _to_decimal(value: object) -> Decimal | None:
    """Coerce a cell to Decimal; None/blank -> None; non-numeric -> raises ValueError."""

    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return Decimal(stripped)
        except InvalidOperation as exc:
            raise ValueError(f"non-numeric price cell: {value!r}") from exc
    if isinstance(value, bool):  # guard: bool is an int subclass, never a price
        raise ValueError(f"non-numeric price cell: {value!r}")
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    raise ValueError(f"non-numeric price cell: {value!r}")


def _to_bool(value: object) -> bool | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"", "-"}:
        return None
    return text in {"y", "yes", "true", "1", "invested"}


def _header_index(ws: Worksheet) -> dict[str, int]:
    """Map header text -> 1-based column index from the template's header row (by NAME, §2 rule)."""

    index: dict[str, int] = {}
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=HEADER_ROW, column=col).value
        if cell is not None:
            index[str(cell).strip()] = col
    return index


def construct_price(components: ParsedComponents) -> tuple[Decimal | None, str | None, str | None]:
    """Apply the engine's §7 cost construction + double-subtract guard.

    Returns (price, basis, error). Price = All-In if present; else
    FOB + Delivery + VegCool - Lot Discount. The guard: if All-In is present AND a discount is
    also populated, that is the double-subtract footgun (V3 §7) — we do NOT recompute and do NOT
    silently drop the discount; we surface it for quarantine (the store's `no_double_discount`
    CHECK is the persistence-side backstop).
    """

    if components.all_in is not None:
        # All-In is taken verbatim (already net of discounts). A populated Lot Discount alongside
        # it is the ambiguous double-subtract case — block it rather than guess which is canonical.
        if components.lot_discount != Decimal("0"):
            return None, None, "All-In present together with a Lot Discount (double-subtract risk)"
        return components.all_in, PRICE_BASIS_ALL_IN, None

    if components.fob is not None:
        price = (
            components.fob
            + components.delivery_surcharge
            + components.vegcool_surcharge
            - components.lot_discount
        )
        return price, PRICE_BASIS_FALLBACK, None

    # No All-In and no FOB -> nothing to construct (a no-bid or incomplete row).
    return None, None, None


def _classify(
    components: ParsedComponents,
    price: Decimal | None,
    weekly: Decimal | None,
    total: Decimal | None,
) -> Completeness:
    """bid / no_bid / incomplete classification (§4 No-Bid handling)."""

    zero = Decimal("0")
    has_any_price_intent = (
        components.all_in is not None
        or components.fob is not None
        or components.delivery_surcharge != zero
        or components.vegcool_surcharge != zero
        or components.lot_discount != zero
    )
    has_vol = weekly is not None or total is not None
    if price is not None and price > 0:
        return Completeness.BID
    if not has_any_price_intent and not has_vol:
        return Completeness.NO_BID
    return Completeness.INCOMPLETE


def ingest_template(data: bytes, resolver: IdentityResolver) -> IngestResult:
    """Parse a returned template (xlsx bytes) into resolved, costed bid lines + quarantined rows."""

    wb = load_workbook(BytesIO(data), data_only=True, read_only=True)
    if SHEET_BIDS not in wb.sheetnames:
        wb.close()
        raise ValueError(f"template missing required sheet {SHEET_BIDS!r}")
    ws = wb[SHEET_BIDS]
    headers = _header_index(ws)

    result = IngestResult()
    # Iterate body rows (row 1 = title, row 2 = headers, row 3+ = body).
    for row_number, row_cells in enumerate(
        ws.iter_rows(min_row=HEADER_ROW + 1, values_only=False), start=HEADER_ROW + 1
    ):
        raw = _row_to_dict(row_cells, headers)
        if not any(raw.values()):
            continue  # skip fully blank rows
        parsed = _parse_row(raw, row_number, resolver)
        if isinstance(parsed, QuarantinedRow):
            result.quarantined.append(parsed)
        else:
            result.lines.append(parsed)
    wb.close()
    return result


def _row_to_dict(row_cells: object, headers: dict[str, int]) -> dict[str, str]:
    """Build {header: stringified value} for a row, keyed by the template's header names."""

    # row_cells is a tuple of cells; index by (col - 1).
    cells = list(row_cells)  # type: ignore[call-overload]
    out: dict[str, str] = {}
    for header, col_index in headers.items():
        idx = col_index - 1
        value = cells[idx].value if 0 <= idx < len(cells) else None
        out[header] = "" if value is None else str(value).strip()
    return out


def _cell(raw: dict[str, str], column: BidColumn) -> str:
    return raw.get(column.value, "").strip()


def _parse_row(
    raw: dict[str, str], row_number: int, resolver: IdentityResolver
) -> ParsedBidLine | QuarantinedRow:
    """Resolve identity, construct price, classify completeness — or quarantine (never guess)."""

    supplier_label = _cell(raw, BidColumn.SUPPLIER)
    dc_label = _cell(raw, BidColumn.DC)
    lot_label = _cell(raw, BidColumn.LOT)
    item_label = _cell(raw, BidColumn.ITEM)
    tf_code = _cell(raw, BidColumn.TF)
    round_code = _cell(raw, BidColumn.ROUND)
    bid_type = _cell(raw, BidColumn.BID_TYPE)

    # A required scope cell missing -> cannot place the row in the grain.
    for label in (supplier_label, dc_label, lot_label, item_label, tf_code):
        if not label:
            return QuarantinedRow(
                row_number, QuarantineReason.MISSING_IDENTITY, "blank scope cell", raw
            )

    supplier_id = resolver.resolve_supplier(supplier_label)
    if supplier_id is None:
        return QuarantinedRow(
            row_number, QuarantineReason.UNRESOLVED_SUPPLIER, supplier_label, raw
        )
    dc_id = resolver.resolve_dc(dc_label)
    if dc_id is None:
        return QuarantinedRow(row_number, QuarantineReason.UNRESOLVED_DC, dc_label, raw)
    lot_id = resolver.resolve_lot(lot_label)
    if lot_id is None:
        return QuarantinedRow(row_number, QuarantineReason.UNRESOLVED_LOT, lot_label, raw)
    item_id = resolver.resolve_item(item_label)
    if item_id is None:
        return QuarantinedRow(row_number, QuarantineReason.UNRESOLVED_ITEM, item_label, raw)
    resolved_tf = resolver.resolve_tf(tf_code)
    if resolved_tf is None:
        return QuarantinedRow(row_number, QuarantineReason.UNRESOLVED_TF, tf_code, raw)

    try:
        components = ParsedComponents(
            all_in=_to_decimal(raw.get(BidColumn.ALL_IN.value)),
            fob=_to_decimal(raw.get(BidColumn.FOB.value)),
            delivery_surcharge=_to_decimal(raw.get(BidColumn.DELIVERY_SURCHARGE.value))
            or Decimal("0"),
            vegcool_surcharge=_to_decimal(raw.get(BidColumn.VEGCOOL_SURCHARGE.value))
            or Decimal("0"),
            lot_discount=_to_decimal(raw.get(BidColumn.LOT_DISCOUNT.value)) or Decimal("0"),
        )
        weekly = _to_decimal(raw.get(BidColumn.WEEKLY_VOL_OFFERED.value))
        total = _to_decimal(raw.get(BidColumn.TOTAL_VOL_OFFERED.value))
    except ValueError as exc:
        return QuarantinedRow(row_number, QuarantineReason.BAD_NUMERIC, str(exc), raw)

    price, basis, price_error = construct_price(components)
    if price_error is not None:
        return QuarantinedRow(row_number, QuarantineReason.DOUBLE_SUBTRACT, price_error, raw)

    completeness = _classify(components, price, weekly, total)
    identity = ResolvedIdentity(
        supplier_id=supplier_id, dc_id=dc_id, lot_id=lot_id, item_id=item_id, tf_code=resolved_tf
    )
    comments = _cell(raw, BidColumn.PRICING_COMMENTS) or None
    return ParsedBidLine(
        round_code=round_code,
        bid_type=bid_type,
        identity=identity,
        components=components,
        landed_cost_per_case=price,
        price_basis=basis or "",
        weekly_vol_offered=weekly,
        total_vol_offered=total,
        invested_r1=_to_bool(raw.get(BidColumn.INVESTED_R1.value)),
        pricing_comments=comments,
        completeness=completeness,
        source_row_number=row_number,
    )
