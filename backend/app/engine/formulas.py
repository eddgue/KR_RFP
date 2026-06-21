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


def construct_price(bid: BidInput) -> Decimal | None:
    """Derive Price for a bid (V3 §7). All-In primary; fallback sums components net of discounts.

    The double-subtract guard: when All-In is present it is taken verbatim (already net of
    discounts) — Lot/AllLot discounts are NOT re-subtracted. Discounts apply ONLY on the fallback
    branch. Rows with Price NaN/<=0 return None (dropped downstream).
    """

    comp = bid.components
    if comp is None:
        price = bid.landed_cost_per_case
    elif comp.all_in is not None:
        # PRIMARY: take All-In verbatim. Do NOT subtract discounts again (the footgun).
        price = comp.all_in
    elif comp.fob is not None:
        # FALLBACK: build from parts; discounts applied here and ONLY here.
        price = (
            comp.fob
            + comp.delivery_surcharge
            + comp.vegcool_surcharge
            - comp.lot_discount
            - comp.all_lot_discount
        )
    else:
        return None
    if price <= _ZERO:
        return None
    return price


def premium_vs_low(price: Decimal, market_low: Decimal) -> Decimal | None:
    """Price premium over the cell's market low, as a fraction: (price − low) / low (V3 §2.4).

    None when the benchmark is non-positive (no defined premium). This is the ratio the scorer gates
    on (GATE_PREMIUM) and the comms feedback/rejection drafts quote — defined once, referenced
    everywhere.
    """

    return (price - market_low) / market_low if market_low > _ZERO else None
