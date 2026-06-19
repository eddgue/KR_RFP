"""Golden-master reproduction + band-edge + invariant tests for the V3 engine (S2 exit gate).

The synthetic fixture (placeholders only) is engineered to hit every band/branch of
V3_ENGINE_LOGIC.md; `golden_expectations.json` holds the independently-derived expected values
(traced from the spec band tables, NOT from our engine and NOT from the quarantined v3 —
clean-room, ADR-0001). These tests assert the lifted engine reproduces them exactly.

PURE: no DB, no network — just the engine library + fixtures.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.engine.interface import BidScore, EngineConfig, ScenarioAward
from app.engine.scoring import resolve_weights
from app.engine.v3 import V3_VERSION, V3Engine
from tests.engine.golden_fixture import build_inputs

_EXPECT = json.loads(
    (Path(__file__).parent / "golden_expectations.json").read_text(encoding="utf-8")
)


def _scores_by_id() -> dict[str, BidScore]:
    res = V3Engine().run(build_inputs())
    return {s.bid_id: s for s in res.scores}


def _awards() -> tuple[ScenarioAward, ...]:
    return V3Engine().run(build_inputs()).awards


def _award(code: str, dc: str, lot: str) -> list[ScenarioAward]:
    return [
        a
        for a in _awards()
        if a.scenario_code.value == code and a.dc_no == dc and a.lot_id == lot
    ]


# ---------------------------------------------------------------------------
# 3.1 Scoring — band edges (the cascade boundaries)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("band", ["price_band", "coverage_band", "historical_band"])
def test_factor_band_edges(band: str) -> None:
    """Every price/coverage/historical band edge reproduces score + composite RecScore."""

    scores = _scores_by_id()
    for bid_id, exp in _EXPECT[band].items():
        if bid_id.startswith("_"):
            continue
        s = scores[bid_id]
        for field, value in exp.items():
            if field in {"_note", "gate"}:
                continue
            if field == "eligible":
                assert s.eligible is value, f"{bid_id}.eligible"
            else:
                assert getattr(s, field) == Decimal(value), f"{bid_id}.{field}"
        if "gate" in exp:
            assert exp["gate"] in s.gate_flags, f"{bid_id} missing gate {exp['gate']}"


def test_zrisk_band_edges() -> None:
    """Z-risk: tight-cluster 100, deep-low outlier 60 (+flag), high outlier 40 (+flag)."""

    scores = _scores_by_id()
    for bid_id, exp in _EXPECT["zrisk_band"].items():
        if bid_id.startswith("_"):
            continue
        s = scores[bid_id]
        assert s.zrisk_score == Decimal(exp["zrisk_score"]), bid_id
        if "gate" in exp:
            assert exp["gate"] in s.gate_flags, bid_id


def test_continuity_incumbent_vs_rival() -> None:
    """Continuity 100 for incumbent, 0 for the non-incumbent rival; composites match."""

    scores = _scores_by_id()
    for bid_id, exp in _EXPECT["continuity"].items():
        if bid_id.startswith("_"):
            continue
        s = scores[bid_id]
        assert s.continuity_score == Decimal(exp["continuity_score"]), bid_id
        assert s.rec_score == Decimal(exp["rec_score"]), bid_id


# ---------------------------------------------------------------------------
# 3.2 Eligibility — gate reason codes
# ---------------------------------------------------------------------------
def test_eligibility_gates_and_reason_codes() -> None:
    """Each hard gate flips eligibility and emits its exact reason-code string."""

    scores = _scores_by_id()
    # Premium ceiling (PremVsLow > threshold).
    assert scores["b_pe_LP07_e"].eligible is False
    assert "Price premium exceeds threshold" in scores["b_pe_LP07_e"].gate_flags
    # Coverage floor (<80%).
    assert scores["b_cov_LC01_e"].eligible is False
    assert "Insufficient volume (<80%)" in scores["b_cov_LC01_e"].gate_flags
    # No valid price (price <= 0).
    assert scores["b_zeroprice"].eligible is False
    assert "No valid price" in scores["b_zeroprice"].gate_flags
    # Advisory outlier flags do NOT by themselves flip eligibility off the hard gates.
    assert "Low price outlier: validate sustainability" in scores["b_zlow"].gate_flags
    assert scores["b_zlow"].eligible is True  # premium ok, coverage ok -> still eligible


def test_low_bidder_count_flag() -> None:
    """A group with <3 suppliers carries the advisory low-bidder flag on every member."""

    scores = _scores_by_id()
    # The 2-bid price-edge groups carry the advisory flag.
    assert "Low bidder count (<3): Z-score less reliable" in scores["b_pe_LP01_e"].gate_flags


# ---------------------------------------------------------------------------
# 3.3 Split allocation — Scenario D (top-N, fallback, cap-breach, concentration)
# ---------------------------------------------------------------------------
def test_scenario_d_split_and_fallback() -> None:
    """Scenario D: top-N suppliers per DC×TF, per-lot picks, fallback-flagged outside fill."""

    exp = _EXPECT["scenario_d_split"]
    got = {
        (a.lot_id, a.supplier_id): a.is_fallback
        for a in _awards()
        if a.scenario_code.value == "D" and a.dc_no == exp["dc_no"]
    }
    for row in exp["awards"]:
        key = (row["lot_id"], row["supplier_id"])
        assert key in got, f"missing D award {key}"
        assert got[key] is row["is_fallback"], f"fallback flag mismatch {key}"


def test_concentration_flag() -> None:
    """A supplier whose Scenario-B RecSpend >= conc_thresh of category spend is flagged."""

    flagged = V3Engine().concentration_flagged_suppliers(build_inputs())
    assert flagged == set(_EXPECT["concentration"]["flagged_suppliers"])


def test_cap_breach_surfaces() -> None:
    """A DC×TF whose Scenario-B awards span >max_sup_dc suppliers sets cap_breach_flag."""

    dc, tf = _EXPECT["cap_breach"]["breaching_dc_tf"]
    breach_awards = [
        a
        for a in _awards()
        if a.scenario_code.value == "B" and a.dc_no == dc and a.tf_code == tf
    ]
    assert breach_awards, "expected B awards in the breaching DC×TF"
    assert all(a.cap_breach_flag is True for a in breach_awards)


# ---------------------------------------------------------------------------
# 3.4 Scenarios A-G
# ---------------------------------------------------------------------------
def test_scenario_a_lowest_cost() -> None:
    """Scenario A awards the cheapest eligible bid per cell."""

    exp = _EXPECT["scenario_a_lowest_cost"]
    aw = _award("A", exp["dc_no"], exp["lot_id"])
    assert len(aw) == 1
    assert aw[0].supplier_id == exp["supplier_id"]
    assert aw[0].awarded_price == Decimal(exp["awarded_price"])


def test_scenario_b_differs_from_a_when_risk_adjusted() -> None:
    """B (risk-adjusted) can pick a different supplier than A (lowest cost) — incumbent boost."""

    c = _EXPECT["scenario_c_incumbent_defense"]
    a_aw = _award("A", c["dc_no"], c["lot_id"])
    b_aw = _award("B", c["dc_no"], c["lot_id"])
    assert a_aw[0].supplier_id == c["a_supplier"]
    assert b_aw[0].supplier_id == c["b_supplier"]
    assert a_aw[0].supplier_id != b_aw[0].supplier_id


def test_scenario_c_incumbent_defense() -> None:
    """C retains the incumbent within a comparable premium at coverage; else falls back to B."""

    c = _EXPECT["scenario_c_incumbent_defense"]
    c_aw = _award("C", c["dc_no"], c["lot_id"])
    assert c_aw[0].supplier_id == c["c_supplier"]


def test_scenario_e_exclusion() -> None:
    """Excluded supplier is dropped and B's selection re-runs over the remaining field."""

    exp = _EXPECT["scenario_e_exclusion"]
    e_aw = _award("E", exp["dc_no"], exp["lot_id"])
    assert e_aw[0].supplier_id == exp["supplier_id"]


def test_scenario_f_custom_override() -> None:
    """Custom override replaces B's pick with the named supplier where they have an eligible bid."""

    exp = _EXPECT["scenario_f_custom"]
    f_aw = _award("F", exp["dc_no"], exp["lot_id"])
    b_aw = _award("B", exp["dc_no"], exp["lot_id"])
    assert b_aw[0].supplier_id == exp["b_supplier"]
    assert f_aw[0].supplier_id == exp["f_supplier"]


def test_scenario_g_preferred_with_noeligible_exception() -> None:
    """Preferred rule forces the supplier where eligible; a no-bid rule keeps B's pick."""

    exp = _EXPECT["scenario_g_preferred"]
    g_aw = _award("G", exp["dc_no"], exp["lot_id"])
    assert g_aw[0].supplier_id == exp["g_supplier"]
    # The LT99/S_NONE preferred rule has no eligible bid -> no crash, no spurious award.
    assert not _award("G", "DCxx", "LT99")


# ---------------------------------------------------------------------------
# 3.5 Cost construction — All-In primary, fallback, double-subtract guard
# ---------------------------------------------------------------------------
def test_cost_fallback_and_double_subtract_guard() -> None:
    """All-In present -> verbatim (NOT re-discounted); All-In blank -> built from parts."""

    cc = _EXPECT["cost_construction"]
    fb = _award("A", "DC50", "LT01")
    ds = _award("A", "DC50", "LT02")
    assert fb[0].awarded_price == Decimal(cc["b_fallback"]["awarded_price"])
    # The guard: even though Lot_Discount=2 is populated, All-In 95 is NOT re-subtracted.
    assert ds[0].awarded_price == Decimal(cc["b_doublesub"]["awarded_price"])


# ---------------------------------------------------------------------------
# Weight renormalization (§2.6)
# ---------------------------------------------------------------------------
def test_weight_renormalization() -> None:
    """Weights off-sum by >1% renormalize to sum 1.0; within 1% are left untouched."""

    exp = _EXPECT["weight_renormalization"]
    raw = exp["raw"]
    cfg = EngineConfig(
        weight_price=Decimal(raw["price"]),
        weight_coverage=Decimal(raw["coverage"]),
        weight_historical=Decimal(raw["historical"]),
        weight_zrisk=Decimal(raw["zrisk"]),
        weight_continuity=Decimal(raw["continuity"]),
    )
    w = resolve_weights(cfg)
    norm = exp["normalized"]
    assert w.price == Decimal(norm["price"])
    assert w.coverage == Decimal(norm["coverage"])
    assert w.historical == Decimal(norm["historical"])
    assert w.zrisk == Decimal(norm["zrisk"])
    assert w.continuity == Decimal(norm["continuity"])
    assert (w.price + w.coverage + w.historical + w.zrisk + w.continuity) == Decimal("1.00")

    # Default (sums to 1.0) is unchanged.
    d = resolve_weights(EngineConfig())
    assert d.price == Decimal("0.35")


# ---------------------------------------------------------------------------
# Determinism + version tag
# ---------------------------------------------------------------------------
def test_engine_is_deterministic_and_versioned() -> None:
    """Same inputs -> identical result; the run is tagged with the real (non-stub) version."""

    first = V3Engine().run(build_inputs())
    second = V3Engine().run(build_inputs())
    assert first == second
    assert first.engine_version == V3_VERSION == "v3-cleanroom"
    assert first.engine_version != "stub"
