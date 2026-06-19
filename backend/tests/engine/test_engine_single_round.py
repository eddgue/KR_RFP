"""The single-round guard (TOMATO_RUN.md) — PURE, no DB.

v3 crashed in step 6 on a single-round (R1-only) cycle: the prior-round price lookup indexed
`prior_round['Round']` unconditionally, but CONFIG correctly sets `prior_round = None` for a
one-round cycle -> `None['Round']` -> TypeError. Our lifted engine MUST guard it: when
`config.prior_round_code is None` it skips the prior-round lookup and completes the run.

These tests run the full engine on a single-round configuration and assert it completes,
produces scores + scenarios + awards, and stays deterministic — the regression that v3 failed.
"""

from __future__ import annotations

from app.engine.interface import EngineConfig, EngineInputs
from app.engine.v3 import V3Engine
from tests.engine.golden_fixture import build_inputs


def test_single_round_cycle_completes_without_crash() -> None:
    """prior_round_code None (R1-only) -> the engine runs end-to-end, no TypeError."""

    inputs = build_inputs(single_round=True)
    assert inputs.config.prior_round_code is None  # the crashing condition in v3

    result = V3Engine().run(inputs)  # must NOT raise

    assert result.scores, "single-round run produced no scores"
    assert result.scenarios, "single-round run produced no scenarios"
    assert result.awards, "single-round run produced awards"
    assert result.engine_version == "v3-cleanroom"


def test_single_round_prior_price_map_is_empty() -> None:
    """The guarded prior-price lookup returns an EMPTY map (not None, no crash) when no prior."""

    inputs = build_inputs(single_round=True)
    prior = V3Engine._prior_round_prices(inputs)
    assert prior == {}


def test_single_round_matches_multiround_scoring_for_same_bids() -> None:
    """Scoring is unaffected by the prior-round guard (historical uses the incumbent baseline)."""

    single = V3Engine().run(build_inputs(single_round=True))
    multi = V3Engine().run(build_inputs(single_round=False))
    single_scores = {s.bid_id: s.rec_score for s in single.scores}
    multi_scores = {s.bid_id: s.rec_score for s in multi.scores}
    assert single_scores == multi_scores


def test_minimal_single_round_no_prior_no_incumbents_no_volumes() -> None:
    """A degenerate R1-only cycle (the Tomato shape: no incumbents/volumes) still completes."""

    cfg = EngineConfig(active_tf_codes=("TF1",), final_round_code="R1", prior_round_code=None)
    inputs = EngineInputs(cycle_id="cyc-r1", round_code="R1", config=cfg, bids=())
    result = V3Engine().run(inputs)
    assert result.engine_version == "v3-cleanroom"
    assert result.awards == ()
