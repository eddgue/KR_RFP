"""Canonical numeric formulas — the single "table of calcs" for the platform (pure).

Every cross-layer calculation is defined ONCE here and imported wherever it is needed (the engine
scorer, the alignment/scenario views, the supplier-comms drafts, the generated documents) so no
layer re-derives a value inline and drifts from another. Add a formula here — with its spec
citation — and reference it; never copy a calculation into a call site.

Engine purity boundary: stdlib + `Decimal` only (no float, no I/O, no ORM), so the frozen engine
can depend on this module.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.interface import BidInput

_ZERO = Decimal("0")


def construct_price_from_parts(
    all_in: Decimal | None,
    fob: Decimal | None,
    delivery_surcharge: Decimal = _ZERO,
    vegcool_surcharge: Decimal = _ZERO,
    lot_discount: Decimal = _ZERO,
    all_lot_discount: Decimal = _ZERO,
) -> Decimal | None:
    """The RAW V3 §7 price from component parts — the single definition of the price arithmetic.

    All-In verbatim if present (already net of discounts — the double-subtract guard); else
    FOB + delivery + vegcool − lot_discount − all_lot_discount; None if neither All-In nor FOB.
    No `<= 0` filtering and no quarantine here — those are CALLER policies (the engine drops a
    non-positive price; the bid ingester quarantines an All-In-with-discount row). Shared by the
    engine scorer and the bid ingester so the formula lives in exactly one place.
    """

    if all_in is not None:
        return all_in
    if fob is not None:
        return fob + delivery_surcharge + vegcool_surcharge - lot_discount - all_lot_discount
    return None


def construct_price(bid: BidInput) -> Decimal | None:
    """Derive Price for a SCORED bid (V3 §7) via `construct_price_from_parts`.

    All-In primary, else the component fallback; with no components, the precomputed
    `landed_cost_per_case` is used. A non-positive or unconstructable price is dropped (None).
    """

    comp = bid.components
    if comp is None:
        price: Decimal | None = bid.landed_cost_per_case
    else:
        price = construct_price_from_parts(
            comp.all_in,
            comp.fob,
            comp.delivery_surcharge,
            comp.vegcool_surcharge,
            comp.lot_discount,
            comp.all_lot_discount,
        )
    if price is None or price <= _ZERO:
        return None
    return price


def premium_vs_low(price: Decimal, market_low: Decimal) -> Decimal | None:
    """Price premium over the cell's market low, as a fraction: (price − low) / low (V3 §2.4).

    None when the benchmark is non-positive (no defined premium). This is the ratio the scorer gates
    on (GATE_PREMIUM) and the comms feedback/rejection drafts quote — defined once, referenced
    everywhere.
    """

    return (price - market_low) / market_low if market_low > _ZERO else None
