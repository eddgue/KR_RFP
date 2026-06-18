---
doc: System Overview & Architecture Decisions
id: DOC-001
version: 1.0
status: Draft
created: 2026-06-17
last_updated: 2026-06-17
depends_on: None
---

# System Overview & Architecture Decisions

The first document. Everything downstream references it. It says what the system is and records the decisions that the data model and tech spec implement. The decisions are not opinions; each one resolves a finding verified across the intake.

---

## System Overview

**What it is.** A governed system of record for running Kroger produce sourcing cycles (RFPs) end to end: set up a cycle, send bids, take them back, normalize them, score and allocate, choose awards, and generate the booking guide, sign-off, and supplier letters — with every cycle, bid, and award stored so any past cycle reopens as a query.

**The three problems it kills.**
1. **Historical blindness.** Today, "look back" means hunting a shared drive with non-standard naming. The store makes "open last cycle" a button.
2. **Non-standard process.** Everyone runs RFPs their own way, recorded nowhere. The setup file defines the rail; the store records the run.
3. **Manual dependence.** The booking guide, letters, and sign-off are hand-built today. They become generated outputs.

**What already exists (and this is the key context).** The scoring/allocation engine is **built and good** — `rfp_analysis_engine_v3.py`, verified: five-factor weighted scoring (cost is 35%), eligibility gates with reasons, split-award allocation capped per DC, seven scenario lenses, config-driven and commodity-agnostic. Around it sits a ten-script workflow package (cycle init, bid templates, intake, reconcile, distance, scoring, feedback letters, award letters, booking sheet, event log) and a deployed Streamlit app.

**What is missing (the build).** A persistent, governed **store** under the workflow. The engine is stateless — file in, file out — so it does not, by itself, cure historical blindness. The work is not building the brain. It is giving the brain a spine: the data layer in `BUILD_03_schema.sql`, with the engine plugged in as a library and outputs generated from records.

**⚠️ Verify before greenfield.** The deployed Streamlit app and the `_event_log` utility may already persist some state. Confirm whether the live app writes to a database or hands back a zip *before* building this store from scratch. If a store exists, reconcile it to this schema. If it is file-in/file-out, this is the greenfield backend. (Open item carried from the intake.)

**Scale assumptions.** Tens of categories, dozens of DCs, hundreds of lots, single-digit thousands of bids per cycle, a handful of rounds. This is a system-of-record workload, not a high-throughput one. Postgres is ample.

---

## ADR-001 — Store first, engine as a library, UI last

**Status:** Accepted
**Context.** The engine is finished; the UI is bad; there is no store. The deployed notebook/Streamlit UX is poor for a structural reason: a stateless engine can only have a bad UI, because every good front-end feature (remember my data, open last cycle, adjust live) needs state the engine lacks.
**Decision.** Build the persistent data layer first. Wrap the v3 engine as a callable library that reads bids from the store and writes runs/scenarios back. Generate outputs from records. Build the UI last, as a view onto the store.
**Consequences.** Backend-first sequencing (see tech spec). The UI work is deferred but becomes straightforward once the store exists. The engine's monolithic Excel-formatting code (~2/3 of it) is dropped; only its logic (~1/3) is lifted.
**Rejected.** Polishing the UI now — yields a nicer way to run a stateless script that still forgets everything each run.

---

## ADR-002 — Lot is the grain; normalization is a first-class store

**Status:** Accepted
**Context.** Bids and receipts arrive at UPC. The engine compares them via a `product&DC` string-concat key that silently misaligns when descriptions differ. Ed already built the UPC→lot decomposition by hand (the Norm sheet) but it is per-file and not sticky.
**Decision.** Make the lot (parent product) the bid/award grain. Persist the normalization: raw item, decomposed attributes, and a sticky `item_lot_map` (propose → human-confirm → reuse). Join on lot, never on a concatenated string.
**Consequences.** A normalization layer (`norm.*`) and a confirm workflow. One-time attribute-taxonomy confirmation per commodity at onboarding.
**Rejected.** Keeping the string key — it is the root cause of comparison drift.

---

## ADR-003 — Awards are split (supplier shares per cell)

**Status:** Accepted
**Context.** The original spec locked "one supplier wins one DC × lot × timeframe cell" as foundational. The leadership sign-off deck disproves it on every slide ("Onions52, Owyhee"). The engine's `max_two_per_dc` confirms it in code. They are called *Allocation* models because they allocate volume across suppliers.
**Decision.** A cell is awarded as a **set of supplier shares**, capacity-constrained, human-decided. One row per awarded supplier per cell, each carrying a `volume_share`.
**Consequences.** `eng.scenario_award` and `awd.award` are multi-row per cell. Capacity (`volume_limit`) is load-bearing. Any consumer that assumed single-winner must change.
**Rejected.** Single-winner grain — it is wrong at the root, and anything built on it inherits the flaw.

---

## ADR-004 — Immutable runs; freeze-and-layer; nothing deleted

**Status:** Accepted
**Context.** The Excel tooling recomputes live (SUMIFS/MINIFS/LET); a deleted sheet silently breaks numbers with no audit. The process needs proof: any RFP must reopen with the full story.
**Decision.** Analysis runs are sealed with a `config_json` snapshot; corrections are new runs, never edits. Awarded terms freeze (`frozen_at`); later changes layer on top (`award_layer`), date-stamped; raw is never overwritten. No hard deletes anywhere. An append-only `event_log` records every state change.
**Consequences.** More storage, deliberate immutability rules (app-level + DB constraints/triggers). "Open last cycle" and audit become trivial queries.
**Rejected.** In-place edits / live recompute — the fragility the system exists to remove.

---

## ADR-005 — Decision-support, not auto-award

**Status:** Accepted
**Context.** The original spec built an "exact minimum-cost solver" that picks the winner. Ed's real engine scores five weighted factors (cost 35%) and surfaces the minimum as a *reference*; the human picks, because the real choice is cost + supply security + quality + incumbent + risk.
**Decision.** The engine computes scores, eligibility, and scenarios, and proposes a recommendation. A human selects the scenario and promotes it to awards. The minimum is shown, never auto-applied.
**Consequences.** The selection step is explicit (`scenario` → `award`). The UI must support comparing lenses and overriding per cell.
**Rejected.** Auto-award by lowest cost — it automates the one judgment Ed deliberately keeps.

---

## ADR-006 — Two origins kept separate

**Status:** Accepted
**Context.** Ship-from (from iTrade/PO, loose) and grow-origin (supplier-stated per period) are different facts and are conflated in naive models.
**Decision.** Store `grow_origin` and `ship_from_zip` separately on bids and receipts. Never auto-derive one from the other. Distance (freight proxy) derives from ship-from via `zip_centroid`.
**Consequences.** Two columns, one distance calc. Honest origin data.
**Rejected.** A single "origin" field.

---

## ADR-007 — One feed (iTrade) powers cost and the scorecard

**Status:** Accepted
**Context.** iTrade is every PO receipt with cost components, fiscal stamping, and quality/quantity fields. Both historical awarded cost and the supplier scorecard derive from it. KCMS (scan movement) is a separate feed.
**Decision.** Land iTrade once (`perf.itrade_receipt`); derive both the cost baseline and the scorecard from it. Keep KCMS distinct. Trust the feed's own flags first; reject impossible date spans.
**Consequences.** No duplicate cost feed. The scorecard is a derivation, captured as two frozen snapshots (kickoff, sign-off).
**Rejected.** Separate cost and scorecard feeds — they are the same source.

---

## ADR-008 — Timeframe is a dimension, not a fork

**Status:** Accepted
**Context.** The Colored-Potato model clones the entire engine per timeframe (Data cube TF1/TF2, Scenario TF1/TF2…), doubling the workbook by hand. The v3 engine already takes TFs as active config.
**Decision.** Timeframe is a dimension on cycles, bids, scores, and awards. One engine run handles N timeframes.
**Consequences.** No per-TF duplication. The single largest efficiency gain in the build.
**Rejected.** Per-timeframe forks.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-17 | Session | Initial draft; 8 ADRs from intake sessions 1–6 |
