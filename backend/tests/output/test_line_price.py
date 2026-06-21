"""Unit test for `_line_price` — the scenario workbook's canonical price reader (#2 fix).

Proves the workbook now constructs each bid's price the same way the engine scored it (E-39):
All-In if present, else FOB + surcharges − discount — so a component-basis bid is no longer
dropped from the price grids / market stats / coverage / FOB tabs.
"""

from __future__ import annotations

from decimal import Decimal

from app.output.scenario_workbook import _line_price

_D = Decimal


def test_all_in_present_is_taken_verbatim() -> None:
    # All-In wins; discounts are NOT re-subtracted (the §7 double-subtract guard).
    assert _line_price(_D("11.50"), _D("9.00"), _D("1.00"), _D("0.50"), _D("0.25")) == _D("11.50")


def test_component_basis_is_constructed() -> None:
    # No All-In -> FOB + delivery + vegcool − lot_discount = 9 + 1 + 0.5 − 0.25.
    assert _line_price(None, _D("9.00"), _D("1.00"), _D("0.50"), _D("0.25")) == _D("10.25")


def test_component_basis_none_surcharges_default_zero() -> None:
    assert _line_price(None, _D("9.00"), None, None, None) == _D("9.00")


def test_no_all_in_no_fob_is_none() -> None:
    assert _line_price(None, None, None, None, None) is None


def test_accepts_db_style_values() -> None:
    # DB numeric columns arrive as Decimal/None; the coercion must round-trip them.
    price = _line_price(_D("18.40"), _D("0.85"), _D("0.40"), _D("0.25"), _D("0"))
    assert price == _D("18.40")  # All-In present -> verbatim
    fallback = _line_price(None, _D("18.40"), _D("0.85"), _D("0.40"), _D("0.25"))
    assert fallback == _D("19.40")  # 18.40 + 0.85 + 0.40 − 0.25
