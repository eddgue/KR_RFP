# ADR-0006 — Engine brain: adopt v3's five-factor scoring + split allocation

- **Status:** Accepted (sponsor-ratified 2026-06-18 — "D2 Spike ok!")
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Engine lead
- **Relates:** Decision D2, the spike `project/squads/engine-domain/SPIKE_D2_engine.md`, gaps G1/G2, ADR-0001
- **Supersedes:** the as-built's exact min-cost single-winner solver as *the* engine

## Context

The two original codebases carried different brains. The as-built repository implemented an **exact minimum-cost, single-winner solver** (Scenario A). The verified `rfp_analysis_engine_v3.py` implements **decision-support**: five banded factors (Price 0.35, Coverage 0.25, Historical 0.20, Z-Risk 0.10, Continuity 0.10) → a recommendation score, with split (allocation) awards via `max_two_per_dc`. The real evidence — the leadership sign-off deck splitting DCs across suppliers, and cost being only 35% of the decision — backs the v3 model. The Engine squad's spike recommended adopting v3 (Option A); the sponsor ratified it.

## Decision

**Adopt the v3 engine logic as the system's brain**, lifted clean into a library behind the frozen `run(cycle_id, round_code, config) -> run_id` interface (ADR-0001: logic only, no Excel-formatting code, never imported from the isolated repo):

1. **Scoring** — `eng.bid_score` with the five banded factors and the weighted composite. Cost is 35%, not 100%.
2. **Scenarios** — the seven lenses A–G. **Scenario A becomes the "lowest-cost reference" lens** (a benchmark shown for context), not the award mechanism. The old min-cost solver is retired into this lens.
3. **Split allocation** — `eng.scenario_award` carries one row per awarded supplier per cell, each with `volume_share` and a `cap_breach_flag`; `max_two_per_dc` is the default cap, permit-not-force (a cell defaults to one supplier but may split when its per-DC/per-lot splittable flag is set), capacity-constrained.
4. **Decision-support only** — the engine computes, scores, compares, and proposes; a human selects. It never auto-asserts an award; the `BANNED_DECISION_WORDS` guard stays on the recommendation surface.

## Consequences

- **G1 (split) and G2 (scoring) ship together** as one engine increment (they both touch the solver core), **after** the Phase-B real-data pilot, behind the `split_award` / `scenario_lenses` feature flags (DevOps plan).
- The frozen engine **interface does not change** — only the implementation behind the deterministic stub is replaced — so the store, API contract, and tests already built remain valid.
- Validation is by **golden-master reproduction** (QA plan): the new engine must reproduce v3's verified scoring + split on a known input/output pair (the top sponsor ask).
- The as-built's eligibility (7 gates) and landed-cost (5 modes) layers are **kept** and feed the scorer as inputs.

## Status

Ratified. Phase D engine work is now unblocked in principle; it executes after Phase B (the pilot proves the feeds) and Phase C (the cycle config drives the run).
