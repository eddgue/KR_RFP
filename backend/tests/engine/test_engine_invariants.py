"""Decision-support invariants (ADR-0006) — PURE, no DB.

The engine PROPOSES; a human decides. These tests pin the non-negotiables:
  * the BANNED_DECISION_WORDS list is non-empty and enforced;
  * the guard RAISES on an asserted award verb and PASSES benign substrings;
  * no scenario label the engine emits trips the guard (the engine never auto-asserts);
  * the engine never reports a single supplier as "the winner" of a cell — it surfaces shares.
"""

from __future__ import annotations

import pytest

from app.engine.guards import (
    BANNED_DECISION_WORDS,
    BannedDecisionWordError,
    assert_decision_support,
)
from app.engine.v3 import V3Engine
from tests.engine.golden_fixture import build_inputs


def test_banned_list_is_nonempty() -> None:
    """The guard's banned-word list must be non-empty (S3)."""

    assert BANNED_DECISION_WORDS
    assert all(isinstance(w, str) and w for w in BANNED_DECISION_WORDS)


@pytest.mark.parametrize(
    "label",
    [
        "Supplier S01 is awarded the contract",
        "Award to S01",
        "S01 is the winner",
        "S01 selected for the lot",
        "Final decision: S01",
    ],
)
def test_guard_raises_on_asserted_award(label: str) -> None:
    """Any human-facing label asserting an award decision RAISES."""

    with pytest.raises(BannedDecisionWordError):
        assert_decision_support(label)


@pytest.mark.parametrize(
    "label",
    [
        "Risk-adjusted recommendation",
        "Lowest-cost reference",
        "Reward program note",  # 'reward' must NOT match 'award'
        "Lawn maintenance lot",  # benign substring guard
        "Proposed split across two suppliers",
    ],
)
def test_guard_passes_decision_support_phrasing(label: str) -> None:
    """Decision-support phrasing (and benign substrings) pass unchanged."""

    assert assert_decision_support(label) == label


def test_engine_scenario_labels_never_assert() -> None:
    """Every scenario label/description the engine emits passes the BANNED guard."""

    result = V3Engine().run(build_inputs())
    for scenario in result.scenarios:
        # Re-screening must not raise (the engine screened them at construction).
        assert assert_decision_support(scenario.label) == scenario.label
        assert assert_decision_support(scenario.description) == scenario.description


def test_engine_never_auto_asserts_a_single_winner() -> None:
    """Awards are split shares, not a winner verdict: no award is flagged as a final decision.

    `is_recommended` marks the risk-adjusted *proposal* (Scenario B), never an asserted award;
    every award carries a volume_share (a share, not a verdict) and the engine emits the
    benchmark Scenario A alongside it so cost is shown as context, not the decision.
    """

    result = V3Engine().run(build_inputs())
    # B awards are 'recommended' (a proposal); all other lenses are not.
    for a in result.awards:
        if a.scenario_code.value != "B":
            assert a.is_recommended is False
        # Every award is a share in [0, 1] — a proposed allocation, not a verdict.
        assert 0 <= a.volume_share <= 1
    # Scenario A (lowest-cost reference) is always present as the benchmark lens.
    assert any(s.code.value == "A" for s in result.scenarios)


def test_b_awards_carry_the_engine_rec_type() -> None:
    """D28: every Scenario-B pick carries the engine's authoritative RecType; other lenses don't.

    The per-cell reason is computed ONCE in the engine and travels on the award (the runner seals
    it, outputs render it — never re-derive it). RecType is the recommendation's 'why', so it is
    B-only; non-B lenses leave it None.
    """

    allowed = {
        "Lowest cost",
        "Coverage advantage",
        "Comparable premium",
        "Defensible premium",
        "Risk-adjusted",
    }
    result = V3Engine().run(build_inputs())
    b_awards = [a for a in result.awards if a.scenario_code.value == "B"]
    assert b_awards, "expected Scenario B (recommendation) awards"
    for a in b_awards:
        assert a.rec_type in allowed, f"B award missing/invalid rec_type: {a.rec_type!r}"
    for a in result.awards:
        if a.scenario_code.value != "B":
            assert a.rec_type is None, f"non-B {a.scenario_code.value} carried a rec_type"
