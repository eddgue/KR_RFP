"""Canonical price-construction formula (E-39): one definition shared by engine + ingester.

Pure unit tests for `app.engine.formulas.construct_price_from_parts` — the §7 price arithmetic the
engine scorer and the bid ingester now both route through (so the formula lives in one place).
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.formulas import construct_price_from_parts

D = Decimal


def test_all_in_taken_verbatim() -> None:
    """All-In present -> verbatim; discounts are NOT re-subtracted (the double-subtract guard)."""

    price = construct_price_from_parts(D("11.50"), D("9.00"), D("1.00"), D("0.50"), D("0.25"))
    assert price == D("11.50")


def test_fallback_sums_components_net_of_discounts() -> None:
    """No All-In -> FOB + delivery + vegcool − lot_discount − all_lot_discount."""

    fallback = construct_price_from_parts(None, D("9.00"), D("1.00"), D("0.50"), D("0.25"))
    assert fallback == D("10.25")
    with_all_lot = construct_price_from_parts(
        None, D("9.00"), D("1.00"), D("0.50"), D("0.25"), D("0.10")
    )
    assert with_all_lot == D("10.15")


def test_no_all_in_no_fob_is_none() -> None:
    assert construct_price_from_parts(None, None) is None


def test_raw_result_is_not_clamped() -> None:
    """The raw formula does NOT filter non-positive prices — that is a caller policy."""

    assert construct_price_from_parts(None, D("1.00"), lot_discount=D("3.00")) == D("-2.00")
