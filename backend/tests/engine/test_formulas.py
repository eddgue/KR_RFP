"""Canonical price-construction formula (E-39): one definition shared by engine + ingester.

Pure unit tests for `app.engine.formulas.construct_price_from_parts` — the §7 price arithmetic the
engine scorer and the bid ingester now both route through (so the formula lives in one place).
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.formulas import (
    awarded_cases,
    construct_price_from_parts,
    coverage_ratio,
    delta_vs_historical,
    line_spend,
    premium_dollars,
    price_delta,
    savings_dollars,
    savings_fraction,
    weekly_impact,
    z_score,
)

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


def test_z_score() -> None:
    assert z_score(D("12.00"), D("10.00"), D("2.00")) == D("1")
    assert z_score(D("12.00"), D("10.00"), D("0")) is None  # no spread -> no z


def test_coverage_ratio() -> None:
    assert coverage_ratio(D("80"), D("100")) == D("0.8")
    assert coverage_ratio(None, D("100")) is None
    assert coverage_ratio(D("80"), None) is None
    assert coverage_ratio(D("80"), D("0")) is None


def test_delta_vs_historical() -> None:
    assert delta_vs_historical(D("11.00"), D("10.00")) == D("0.1")
    assert delta_vs_historical(D("11.00"), None) is None  # no baseline
    assert delta_vs_historical(D("11.00"), D("0")) is None


def test_spend_and_savings() -> None:
    assert awarded_cases(D("600"), D("0.5")) == D("300.0")
    assert line_spend(D("11.50"), D("300")) == D("3450.00")
    assert savings_dollars(D("1000"), D("900")) == D("100")
    assert savings_fraction(D("1000"), D("900")) == D("0.1")
    assert savings_fraction(D("0"), D("900")) == D("0")  # no baseline -> 0, not a division error


def test_premium_impact_and_price_delta() -> None:
    assert premium_dollars(D("11.50"), D("10.00")) == D("1.50")
    assert weekly_impact(D("1.50"), D("600")) == D("900.00")
    assert price_delta(D("9.75"), D("10.00")) == D("-0.25")
