"""The real decision-support engine (ADR-0006) — clean-room re-implementation of v3 steps 1-7.

Lifted from our own spec `project/squads/engine-domain/V3_ENGINE_LOGIC.md` (never from the
quarantined source; `backend/` never imports `reference/`, ADR-0001). Replaces the deterministic
stub *body* behind the FROZEN `Engine.run(inputs) -> EngineResult` interface.

What it does (full-fidelity prototype, sponsor rule D19 — no stubs/MVP):
  * §7 cost construction (All-In primary + fallback) with the double-subtract guard;
  * §2 the five banded factors -> RecScore, weights resolved + renormalized from config;
  * §3 eligibility gates + reason codes;
  * §4 the max_two_per_dc split allocator (top-N per DC×TF, fallback-flagged fill, cap-breach);
  * §4.5 the 0.40 category-concentration flag;
  * §5 the seven lenses A-G;
  * the single-round guard: prior_round_code None -> skip the prior-round price lookup
    (TOMATO_RUN.md) instead of crashing.

Decision-support only (ADR-0006): scenario labels are screened by BANNED_DECISION_WORDS; the
engine proposes, a human decides. Strategy-agnostic (ADR-0016): every knob comes from config.

Pure: stdlib + the interface (pydantic) only. No db/http/clock/random.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.engine.allocation import (
    concentration_flags,
    rec_type,
    scenario_a,
    scenario_b,
    scenario_c,
    scenario_d,
    scenario_e,
    scenario_f,
    scenario_g,
)
from app.engine.guards import assert_decision_support
from app.engine.interface import (
    BidScore,
    Engine,
    EngineConfig,
    EngineInputs,
    EngineResult,
    Scenario,
    ScenarioAward,
    ScenarioCode,
)
from app.engine.scoring import ScoredBid, score_bids

V3_VERSION = "v3-cleanroom"

Cell = tuple[str, str, str]
_ONE = Decimal("1")
_ZERO = Decimal("0")

# Lens headers (decision-support phrasing — screened by the BANNED guard at construction).
_LENS_META: dict[ScenarioCode, tuple[str, str]] = {
    ScenarioCode.A: ("Lowest-cost reference", "Benchmark: cheapest eligible bid per cell."),
    ScenarioCode.B: ("Risk-adjusted recommendation", "Highest RecScore per cell (default lens)."),
    ScenarioCode.C: ("Incumbent defense", "Retain incumbent within a comparable premium at cover."),
    ScenarioCode.D: ("Max-N per DC", "Split: top-N strongest suppliers per DC, flagged fallback."),
    ScenarioCode.E: ("Exclusion applied", "Re-run the risk-adjusted lens minus exclusions."),
    ScenarioCode.F: ("Custom override", "Risk-adjusted lens with named-supplier overrides."),
    ScenarioCode.G: ("Preferred supplier", "Risk-adjusted lens favouring preferred suppliers."),
}


class V3Engine(Engine):
    """The lifted v3 decision-support engine (pure, reproducible)."""

    version = V3_VERSION

    def run(self, inputs: EngineInputs) -> EngineResult:
        config = inputs.config

        # --- SINGLE-ROUND GUARD (TOMATO_RUN.md): prior_round None -> skip prior-round lookup. ---
        # The latent v3 defect crashed on an R1-only cycle because the prior-round price lookup
        # indexed `prior_round['Round']` unconditionally (None['Round'] -> TypeError). We guard
        # it: when there is no prior round we build an EMPTY prior-price map and emit no
        # round-over-round deltas, instead of crashing. (The historical factor uses the
        # incumbent baseline, not the prior round, so scoring is unaffected either way.)
        prior_round_prices = self._prior_round_prices(inputs)

        # --- Demand + incumbent lookups (None-safe). ---
        volumes_by_cell: dict[Cell, Decimal | None] = {
            (v.dc_no, v.lot_id, v.tf_code): v.total_volume for v in inputs.volumes
        }
        incumbent_routing: dict[tuple[str, str], Decimal | None] = {
            (i.dc_no, i.lot_id): i.routing_cost_per_case for i in inputs.incumbents
        }

        # The prior-price map participates in no scoring math here (round deltas are an output
        # caveat, §7); referencing it keeps the guard live and prevents accidental indexing.
        assert prior_round_prices is not None  # always a dict (possibly empty), never None

        # --- §2/§3 scoring over all bids. ---
        scored = score_bids(inputs.bids, volumes_by_cell, incumbent_routing, config)
        eligible = [sb for sb in scored if sb.eligible and sb.price is not None]

        scores = self._build_scores(scored)
        scenarios = self._build_scenarios(config)
        awards = self._build_awards(eligible, volumes_by_cell, config)

        return EngineResult(
            engine_version=V3_VERSION,
            scores=scores,
            scenarios=scenarios,
            awards=awards,
        )

    def concentration_flagged_suppliers(self, inputs: EngineInputs) -> set[str]:
        """Suppliers whose Scenario-B RecSpend >= conc_thresh of category spend (§4.5).

        A category-spend concentration (supply-risk) signal, DISTINCT from the per-DC supplier
        cap (`cap_breach_flag`). The frozen `ScenarioAward` carries only the per-DC cap flag, so
        this concentration set is surfaced here for the runner's Share-of-Business view and for
        the golden-fixture assertion — neither flag auto-rejects (decision-support only).
        """

        config = inputs.config
        volumes_by_cell: dict[Cell, Decimal | None] = {
            (v.dc_no, v.lot_id, v.tf_code): v.total_volume for v in inputs.volumes
        }
        incumbent_routing: dict[tuple[str, str], Decimal | None] = {
            (i.dc_no, i.lot_id): i.routing_cost_per_case for i in inputs.incumbents
        }
        scored = score_bids(inputs.bids, volumes_by_cell, incumbent_routing, config)
        eligible = [sb for sb in scored if sb.eligible and sb.price is not None]
        b_pick = scenario_b(eligible)
        return concentration_flags(b_pick, volumes_by_cell, config)

    # ------------------------------------------------------------- prior round
    @staticmethod
    def _prior_round_prices(inputs: EngineInputs) -> dict[tuple[str, str, str], Decimal]:
        """Prior-round price map keyed (lot, tf, supplier) — NO DC (§7 caveat).

        THE GUARD (TOMATO_RUN.md): if `config.prior_round_code is None` (a single-round, R1-only
        cycle) return an empty map and never subscript the absent prior round. Only when a prior
        round is configured do we collect prior-round bid prices. The bundle here carries the
        final round; prior-round bids, when present, would arrive tagged with their round_code.
        """

        prior = inputs.config.prior_round_code
        if prior is None:
            return {}  # single-round cycle: skip the prior-round lookup entirely (no crash)
        out: dict[tuple[str, str, str], Decimal] = {}
        for bid in inputs.bids:
            # Lot-level only (no DC), per the §7 caveat; final-round bids carry the round_code.
            if bid.tf_code and inputs.round_code == prior:
                key = (bid.lot_id, bid.tf_code, bid.supplier_id)
                out[key] = bid.landed_cost_per_case
        return out

    # ------------------------------------------------------------------ scores
    @staticmethod
    def _build_scores(scored: list[ScoredBid]) -> tuple[BidScore, ...]:
        out = [
            BidScore(
                bid_id=sb.bid.bid_id,
                price_score=sb.price_score,
                coverage_score=sb.coverage_score,
                hist_score=sb.hist_score,
                zrisk_score=sb.zrisk_score,
                continuity_score=sb.continuity_score,
                rec_score=sb.rec_score,
                eligible=sb.eligible,
                gate_flags=sb.gate_flags,
            )
            for sb in scored
        ]
        out.sort(key=lambda s: s.bid_id)
        return tuple(out)

    # --------------------------------------------------------------- scenarios
    def _build_scenarios(self, config: EngineConfig) -> tuple[Scenario, ...]:
        out: list[Scenario] = []
        for code in config.lenses:
            label, desc = _LENS_META[code]
            # Decision-support restraint: screen every human-facing label.
            out.append(
                Scenario(
                    code=code,
                    label=assert_decision_support(label),
                    description=assert_decision_support(desc),
                )
            )
        return tuple(out)

    # ------------------------------------------------------------------ awards
    def _build_awards(
        self,
        eligible: list[ScoredBid],
        volumes_by_cell: dict[Cell, Decimal | None],
        config: EngineConfig,
    ) -> tuple[ScenarioAward, ...]:
        lenses = set(config.lenses)
        awards: list[ScenarioAward] = []

        # B is the reference C/E/F/G build their picks from.
        b_pick = scenario_b(eligible)

        if ScenarioCode.A in lenses:
            a_picks = scenario_a(eligible)
            breach_a = self._breach_set(a_picks, config)
            for sb in a_picks:
                awards.append(
                    self._mk(
                        sb,
                        ScenarioCode.A,
                        cap_breach=(sb.bid.dc_no, sb.bid.tf_code) in breach_a,
                    )
                )

        if ScenarioCode.B in lenses:
            breach_b = self._breach_set(b_pick.values(), config)
            for sb in b_pick.values():
                awards.append(
                    self._mk(
                        sb,
                        ScenarioCode.B,
                        is_recommended=True,
                        cap_breach=(sb.bid.dc_no, sb.bid.tf_code) in breach_b,
                        # §5 — the authoritative per-cell reason the recommendation rests on
                        # (single source of truth; the output renders it, never re-derives it).
                        rec_type_label=rec_type(sb, config),
                    )
                )

        if ScenarioCode.C in lenses:
            c_picks = scenario_c(eligible, b_pick, config)
            breach_c = self._breach_set(c_picks.values(), config)
            for sb in c_picks.values():
                awards.append(
                    self._mk(
                        sb, ScenarioCode.C, cap_breach=(sb.bid.dc_no, sb.bid.tf_code) in breach_c
                    )
                )

        if ScenarioCode.D in lenses:
            for award in scenario_d(eligible, config):
                awards.append(award)  # D builds its own ScenarioAward (split + fallback)

        if ScenarioCode.E in lenses:
            e_picks = scenario_e(eligible, config)
            breach_e = self._breach_set(e_picks.values(), config)
            for sb in e_picks.values():
                awards.append(
                    self._mk(
                        sb, ScenarioCode.E, cap_breach=(sb.bid.dc_no, sb.bid.tf_code) in breach_e
                    )
                )

        if ScenarioCode.F in lenses:
            f_picks = scenario_f(eligible, b_pick, config)
            breach_f = self._breach_set(f_picks.values(), config)
            for sb in f_picks.values():
                awards.append(
                    self._mk(
                        sb, ScenarioCode.F, cap_breach=(sb.bid.dc_no, sb.bid.tf_code) in breach_f
                    )
                )

        if ScenarioCode.G in lenses:
            g_picks = scenario_g(eligible, b_pick, config)
            breach_g = self._breach_set(g_picks.values(), config)
            for sb in g_picks.values():
                awards.append(
                    self._mk(
                        sb, ScenarioCode.G, cap_breach=(sb.bid.dc_no, sb.bid.tf_code) in breach_g
                    )
                )

        awards.sort(
            key=lambda a: (a.scenario_code.value, a.dc_no, a.lot_id, a.tf_code, a.supplier_id)
        )
        return tuple(awards)

    @staticmethod
    def _breach_set(bids: Iterable[ScoredBid], config: EngineConfig) -> set[tuple[str, str]]:
        """Per (dc, tf): an award seating >max_sup_dc distinct suppliers is a cap-breach (§4.4).

        Computed from EACH scenario's own awards (not just B), so the flag is a property of the
        award, not of the lens that produced it — two scenarios with the identical split carry the
        identical breach flags.
        """

        by_dctf: dict[tuple[str, str], set[str]] = {}
        for sb in bids:
            by_dctf.setdefault((sb.bid.dc_no, sb.bid.tf_code), set()).add(sb.bid.supplier_id)
        return {k for k, sups in by_dctf.items() if len(sups) > config.max_sup_dc}

    @staticmethod
    def _mk(
        sb: ScoredBid,
        code: ScenarioCode,
        *,
        is_recommended: bool = False,
        cap_breach: bool = False,
        rec_type_label: str | None = None,
    ) -> ScenarioAward:
        return ScenarioAward(
            scenario_code=code,
            dc_no=sb.bid.dc_no,
            lot_id=sb.bid.lot_id,
            tf_code=sb.bid.tf_code,
            supplier_id=sb.bid.supplier_id,
            volume_share=_ONE,
            awarded_price=sb.price if sb.price is not None else _ZERO,
            is_recommended=is_recommended,
            is_fallback=False,
            cap_breach_flag=cap_breach,
            rec_type=rec_type_label,
        )
