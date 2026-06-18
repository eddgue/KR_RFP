"""The deterministic stub engine (ENG-PLAN §5, SPIKE_D2_engine).

D2 is in spike; per ADR-0003 the engine internals stay stubbed behind the frozen interface
until the spike resolves. This stub is a pure, deterministic placeholder that returns a
valid-shaped result so every consumer (Runner, API, tests) is unblocked with real-shaped data.

Placeholder semantics (NOT the real v3 brain):
  - cost-only `rec_score` (lower landed cost -> higher score), other factors zeroed;
  - a single Scenario A (lowest-cost reference);
  - single-winner awards: the cheapest eligible bid per (dc, lot, tf) cell, `volume_share = 1.0`.

The `engine_version` is tagged `stub` so no stubbed run is ever mistaken for a validated v3
run (ENG-PLAN §5 guardrail). When D2 finalizes (Option A), the real scorer + split allocator
replace this body; the interface and the records do not change.

PURITY: stdlib + the interface (pydantic) only. No db/http/clock/random.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.interface import (
    BidInput,
    BidScore,
    Engine,
    EngineInputs,
    EngineResult,
    Scenario,
    ScenarioAward,
    ScenarioCode,
)

STUB_VERSION = "stub"


class DeterministicStubEngine(Engine):
    """A pure, reproducible placeholder engine (cost-only, single-winner)."""

    version = STUB_VERSION

    def run(self, inputs: EngineInputs) -> EngineResult:
        eligible = [b for b in inputs.bids if b.eligible]

        scores = self._score(inputs.bids, eligible)
        awards = self._allocate(eligible)
        scenarios = (
            Scenario(
                code=ScenarioCode.A,
                label="Lowest-cost reference",
                description="Benchmark lens (stub): cheapest eligible bid per cell.",
            ),
        )
        return EngineResult(
            engine_version=STUB_VERSION,
            scores=tuple(scores),
            scenarios=scenarios,
            awards=tuple(awards),
        )

    def _score(
        self, all_bids: tuple[BidInput, ...], eligible: list[BidInput]
    ) -> list[BidScore]:
        """Cost-only price score: cheapest eligible bid -> 100, linear down to 0. Deterministic."""

        costs = [b.landed_cost_per_case for b in eligible]
        lo = min(costs) if costs else Decimal("0")
        hi = max(costs) if costs else Decimal("0")
        spread = hi - lo

        scores: list[BidScore] = []
        for bid in all_bids:
            if not bid.eligible:
                price = Decimal("0")
            elif spread == 0:
                price = Decimal("100")
            else:
                price = (Decimal("100") * (hi - bid.landed_cost_per_case) / spread).quantize(
                    Decimal("0.0001")
                )
            scores.append(
                BidScore(
                    bid_id=bid.bid_id,
                    price_score=price,
                    coverage_score=Decimal("0"),
                    hist_score=Decimal("0"),
                    zrisk_score=Decimal("0"),
                    continuity_score=Decimal("0"),
                    rec_score=price,  # cost-only placeholder
                    eligible=bid.eligible,
                    gate_flags=bid.gate_flags,
                )
            )
        # Stable ordering for reproducibility.
        scores.sort(key=lambda s: s.bid_id)
        return scores

    def _allocate(self, eligible: list[BidInput]) -> list[ScenarioAward]:
        """Single-winner: cheapest eligible bid per (dc, lot, tf) cell, full volume share."""

        best: dict[tuple[str, str, str], BidInput] = {}
        for bid in eligible:
            cell = (bid.dc_no, bid.lot_id, bid.tf_code)
            current = best.get(cell)
            if current is None or self._cheaper(bid, current):
                best[cell] = bid

        awards = [
            ScenarioAward(
                scenario_code=ScenarioCode.A,
                dc_no=bid.dc_no,
                lot_id=bid.lot_id,
                tf_code=bid.tf_code,
                supplier_id=bid.supplier_id,
                volume_share=Decimal("1.0"),
                awarded_price=bid.landed_cost_per_case,
                is_recommended=True,
                is_fallback=False,
                cap_breach_flag=False,
            )
            for bid in best.values()
        ]
        awards.sort(key=lambda a: (a.dc_no, a.lot_id, a.tf_code, a.supplier_id))
        return awards

    @staticmethod
    def _cheaper(candidate: BidInput, current: BidInput) -> bool:
        """Tie-break on bid_id so the choice is deterministic, not insertion-order dependent."""

        if candidate.landed_cost_per_case != current.landed_cost_per_case:
            return candidate.landed_cost_per_case < current.landed_cost_per_case
        return candidate.bid_id < current.bid_id
