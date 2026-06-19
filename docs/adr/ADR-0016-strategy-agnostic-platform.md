# ADR-0016 — Strategy-agnostic platform: strategies are first-class, developed and run

- **Status:** Accepted (sponsor-stated 2026-06-18) — foundational
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Engine lead
- **Relates:** D18; D17 (reference is AS-IS, not target); ADR-0006 (engine as library); D9/D12/D13 (cycle config, pricing, safeties); intake locked-truth #8 (process per-cycle); the engine's commodity-agnostic CONFIG + weight presets; the as-built `scenario_config_version` / `metric_definition_version` / `engine_release` version pins.

## Context

The uploaded reference files are each a **single-strategy mold** — one RFP's particular approach (its weights, lenses, pricing, constraints, steps) baked into a spreadsheet. The risk is building the *system* as a hardcode of one such mold. The sponsor's principle: **we are building a strategy-agnostic platform on which strategies are developed and run** — not a tool wired to any one strategy. The v3 engine already points this way ("commodity-agnostic," CONFIG-driven, "change Active Weights and re-run"); we generalize from *commodity*-agnostic to *strategy*-agnostic. **Commodity-agnostic ⊆ strategy-agnostic.**

## Decision

**A `Strategy` is a first-class, named, versioned, reusable configuration object** that parameterizes how a cycle is set up, analyzed, and awarded. Nothing strategy-specific is hardcoded in the engine, store, or UI — they operate on the strategy config.

A strategy comprises the configurable levers:
- **Objective(s)** (savings / continuity / quality / diversification / strategic; multi with a primary).
- **Pricing model** — basis, cadence, baseline-then-negotiate, volume split (D9/D12) + the **safeties** (collar, rolling midpoint, tolerance band, disaster/inverse — D13), all per-RFP.
- **Scoring** — weights/preset (Balanced / Price Focus / Coverage Focus / Risk Averse / Custom) or fully custom weights.
- **Award constraints** — max-suppliers-per-DC, single-supplier-per-lot, global/per-lot premium thresholds, coverage eligibility floor.
- **Scenario lenses to run** — A–G plus custom / preferred / exclusions.
- **Process rail / steps** — the per-cycle timeline (rail from the setup file; locked-truth #8), not a fixed 10/13-stage hardcode.
- **Preferences / exclusions** — preferred or excluded suppliers, etc.

Strategies are:
- **Developed** — composed, configured, **saved as reusable templates/presets**, and **versioned** (so a strategy can be refined over time and a past cycle still reproduces under the exact strategy version it ran — pairs with immutable runs and "same render live or historic," D12).
- **Run** — bound to a cycle and executed; the same cycle's bids can be **re-run under different strategies** (different weights/lenses/constraints) to compare outcomes (the engine already supports re-run-with-new-weights).

The reference corpus informs the **primitives** strategies are built from (the contract, the data, the levers). It is never the system.

## Consequences

- Elevate the as-built version pins (`scenario_config_version`, `metric_definition_version`, `engine_release`) and the engine's CONFIG presets into a first-class **`strategy` (template) + per-cycle strategy binding** in the model.
- The platform must let users **define, save, version, and apply** strategies, and A/B them on the same cycle data.
- Reusable **strategy templates/presets** (e.g. a house "Balanced savings" strategy, a "supply-assurance" strategy) are a product feature, not a one-off config.
- Every analysis run records the **strategy version** it used → reproducibility + "open last cycle" renders the historic strategy faithfully.
- Guards against the #1 failure mode (digitizing one strategy's spreadsheets); reinforces D17.

## Rejected

- Hardcoding any single strategy's weights/lenses/steps/pricing into the engine or UI (a single-strategy tool, which is what the reference molds are).
