"""Canonical formula reuse (E-37 / Codex PR #18): comms computes prices/premia like the engine.

Pure unit tests — no DB. They lock the two behaviours Codex flagged: (1) a component-basis bid
(FOB only, no All-In) still yields a price via the engine's §7 `construct_price`, and (2) an
ineligible bid that breaches BOTH hard gates produces a hard-ask row for EACH.
"""

from __future__ import annotations

from decimal import Decimal

from app.comms.resolvers import _constructed_price, _hard_ask_rows
from app.engine.formulas import construct_price, premium_vs_low
from app.engine.interface import BidComponents, BidInput
from app.engine.scoring import GATE_COVERAGE, GATE_PREMIUM

D = Decimal


def test_constructed_price_primary_all_in() -> None:
    """All-In present -> taken verbatim (discounts are NOT re-subtracted)."""

    assert _constructed_price(D("11.50"), D("9.00"), D("1.00"), D("0.50"), D("0.25")) == D("11.50")


def test_constructed_price_fallback_from_components() -> None:
    """No All-In -> FOB + delivery + vegcool − lot_discount (the §7 fallback), not dropped."""

    assert _constructed_price(None, D("9.00"), D("1.00"), D("0.50"), D("0.25")) == D("10.25")


def test_constructed_price_none_without_price() -> None:
    """Neither All-In nor FOB -> no constructed price (row contributes nothing)."""

    assert _constructed_price(None, None, None, None, None) is None


def test_constructed_price_matches_engine_construct_price() -> None:
    """The comms wrapper is the engine's canonical formula — same number, by construction."""

    comp = BidComponents(
        all_in=None,
        fob=D("9.00"),
        delivery_surcharge=D("1.00"),
        vegcool_surcharge=D("0.50"),
        lot_discount=D("0.25"),
    )
    engine_price = construct_price(
        BidInput(
            bid_id="b",
            supplier_id="s",
            dc_no="d",
            lot_id="l",
            tf_code="t",
            landed_cost_per_case=D("9.00"),
            components=comp,
        )
    )
    assert _constructed_price(None, D("9.00"), D("1.00"), D("0.50"), D("0.25")) == engine_price


def test_premium_vs_low() -> None:
    assert premium_vs_low(D("11.00"), D("10.00")) == D("0.1")
    assert premium_vs_low(D("10.00"), D("0")) is None  # no benchmark -> undefined


def test_hard_ask_rows_reports_every_breached_gate() -> None:
    """Both gates set -> a row for each; a supplier sees price AND coverage must change."""

    rows = _hard_ask_rows(f"{GATE_PREMIUM};{GATE_COVERAGE}", D("0.18"), D("0.12"), D("0.80"))
    issues = [r[0] for r in rows]
    assert "Price premium exceeds threshold" in issues
    assert "Insufficient volume offered" in issues
    assert len(rows) == 2


def test_hard_ask_rows_single_and_fallback() -> None:
    assert len(_hard_ask_rows(GATE_PREMIUM, D("0.18"), D("0.12"), D("0.80"))) == 1
    assert len(_hard_ask_rows(GATE_COVERAGE, D("0.05"), D("0.12"), D("0.80"))) == 1
    fallback = _hard_ask_rows("", D("0.05"), D("0.12"), D("0.80"))
    assert len(fallback) == 1 and fallback[0][0] == "Not eligible for award"
