---
doc: System Overview & Architecture Decisions (As-Built)
id: ORIG-001
version: 1.0
status: As-Built
created: 2026-06-18
last_updated: 2026-06-18
depends_on: None
---

# System Overview & Architecture Decisions (As-Built)

The first document. It says what the system **is today** and records the decisions the running code already embodies. These are not proposals; each one is implemented in `models.py`, the services, and the migrations, and is covered by tests. This is the counterpart to the brief's `BUILD_01`, written so the two can be diffed.

---

## System Overview

**What it is.** A **governed RFP Process Console** for running Kroger produce sourcing cycles, built backend-first. A persistent store (63 tables under Alembic) sits under a 10-stage Streamlit console. The store holds master data, cycle structure, bids, eligibility, standardized landed cost, an immutable calculation-run ledger, a benchmark scenario optimizer, round lifecycle bookkeeping, historical awarded cost, a governed fiscal calendar, demand/scope prep, and a commercial pricing-model layer.

**What is BUILT and good.** The **store and the governed calculation spine.** The system already does the hard, unglamorous things the brief says are the whole job: it persists every cycle, bid, and run; it seals calculation runs with hashed input/output manifests and enforces their immutability *at the database layer*; it standardizes every bid to one comparable landed cost across five pricing bases; it keeps a sticky alias map so messy spreadsheet text resolves to master entities; it separates demand from capacity by a database CHECK; and it drafts feedback without ever sending it.

**What is the heart, and where it diverges.** **Scenario A** — an exact minimum-cost award optimizer that respects capacity at five scopes and itemizes its output. It is the most heavily built calculator. It is *also* the single largest divergence from the brief: it is a **single-winner, lowest-cost solver**, where the brief calls for **decision-support scoring with split awards and seven lenses**. The brain is real, but it is a different brain than the brief describes.

**What is thin or missing.** The outward-facing half: Stage 8 (Execution Prep — leadership deck, booking guide, award/rejection comms) and Stage 9 (Closeout) are **NOT BUILT**. The five pricing safeties the brief calls "the real product" are, at best, stored inert. The supplier scorecard, KCMS feed, freeze-and-layer of awards, and "Sent" governance state do not exist. The audit hash-chain is a scaffold.

**Scale assumptions.** Tens of categories, dozens of DCs, hundreds of lots, single-digit-thousands of bids per cycle, a handful of rounds. A system-of-record workload. The code runs on synthetic SQLite for the demo; the model is Postgres-shaped (real CHECK constraints, partial unique indexes, triggers).

**⚠️ Governance gate.** A real cycle on real data requires a **Stage 0 governance sign-off** that is **not implemented**. Everything in the repo is synthetic-only.

---

## ADR-001 — Store-first, governed spine, console on top

**Status:** Implemented
**Context.** The work that matters is the persistent governed store, not another stateless script. A console is only as trustworthy as the records under it.
**Decision.** Build the data layer first (63 tables under Alembic), wrap every computation as a sealed calculation run, and put a thin Streamlit console on top that is **read-only over governed output** plus a session-state overlay for what-ifs.
**Consequences.** Backend-first sequencing (Stages 2.5 → 2.9E). The scenario views never recompute or mutate sealed numbers — the only thing that layer writes back is a decision note.
**Divergence from brief:** none in spirit. The brief's ADR-001 is the same instinct (store first, UI last). The console here is further along than "UI last" implies, but it is correctly a *view*, not a source of truth.

---

## ADR-002 — Lot is the grain; aliases make it sticky

**Status:** Implemented
**Context.** Bids and receipts arrive at UPC/raw text. Comparing them needs a stable parent grain and a way to absorb naming drift.
**Decision.** The bid/award grain is **DC × lot/item × supplier × timeframe**. A four-table alias system (`dc_alias`, `item_alias`, `supplier_alias`, plus a shared `master_data_quarantine`) maps messy text → master ids, append-only except a soft `active_flag`, one active alias per normalized form (partial unique index). Unresolvable text is **quarantined**, never guessed.
**Consequences.** A resolver service (`master_data_alias.py`, 1,145 lines) with EXACT/ALIAS/FUZZY/AMBIGUOUS/UNRESOLVED outcomes. Stage 0 import depends on it.
**Divergence from brief:** agrees. The brief's `norm.item_lot_map` (sticky UPC→lot) is this alias layer by another name. **Gap:** the brief models an explicit `lot` + `lot_attribute` + `attribute_def` taxonomy; the code has lots and items but no first-class attribute decomposition table.

---

## ADR-003 — One supplier per cell (single-winner) — KNOWN DIVERGENCE

**Status:** Implemented — and flagged for change
**Context.** The older spec locked "one supplier wins one DC × lot × timeframe cell."
**Decision (as-built).** Scenario A **forbids** more than one winner per cell. `ScenarioACellAssignment` is one supplier per (DC, lot, TF).
**Consequences.** `volume_share` does not exist. The solver is structurally single-winner.
**Divergence from brief — MEDIUM.** The brief proves splits happen as an **edge case** (organics; the sign-off deck's "Onions52, Owyhee"; the real engine's `max_two_per_dc` = *allow up to two when warranted*). Per Eduardo (2026-06-17): the auto scenario should keep defaulting to **one supplier per DC**, but a cell must be *permitted* to split into multiple suppliers each carrying a `volume_share`. The split trigger is a **per-DC / per-lot setup flag** (which DCs/lots are splittable), not auto-keyed off an attribute. **This is one of the two biggest planned changes.**

---

## ADR-004 — Immutable calculation runs; append-only everywhere

**Status:** Implemented
**Context.** A system of record must be able to prove what produced any number, and must never silently overwrite.
**Decision.** Every computation is a **`CalculationRun`** with hashed input/output manifests (sha256) and an execution-contract marker. Once a run is SUCCEEDED, its outputs (`LandedCostResult`, eligibility results, the four Scenario A tables) are **append-only, enforced by database guard listeners** (`controls/calc_run_guards.py`), not just by convention. Corrections are new runs. Round bookkeeping, notes, and feedback are all append-only via superseding rows.
**Consequences.** Reproducibility and audit are structural. "Open last cycle" is a join across cycle → rounds → bids → runs → scenarios.
**Divergence from brief:** agrees strongly. The brief's ADR-004 (immutable runs, no deletes, event log) is exactly this — **except** the brief's *freeze-and-layer of awarded terms* (`award.frozen_at` + `award_layer`) is **not built**, because awards-as-a-frozen-object don't exist yet (see ADR-006).

---

## ADR-005 — Standardize landed cost across five bases; block, never guess

**Status:** Implemented
**Context.** Suppliers quote on different bases (FOB, delivered, cross-dock, all-in, components). They must collapse to one comparable number, and a number that can't be trusted must be *blocked*, not silently zeroed.
**Decision.** Each eligible bid resolves to a landed cost via one of **5 modes**: DIRECT_ALL_IN, RECONCILED_ALL_IN, RECONSTRUCTED_APPROVED (`fob + freight + fuel + accessorial + shrink − item_discount`), MISMATCH_BLOCKED, FOB_PREVIEW_ONLY. A bid that can't be costed gets one of **8 explicit blocking reasons**. Eligibility runs first: **7 gates**, 12 reason codes; only **CONFIRMED_CAPABLE** is awardable.
**Consequences.** `landed_cost.py` (545 lines), `eligibility.py` (677 lines). FOB-only bids are visible but not awardable — the scoreable-vs-awardable line, made explicit.
**Divergence from brief:** agrees, and is in fact richer than the brief's price model. The brief's no-double-discount guard is present in the commercial layer.

---

## ADR-006 — Decision-support is PARTIAL; no final award is asserted — KNOWN DIVERGENCE

**Status:** Partial — and flagged for change
**Context.** The choice is not purely cost; a human picks. The system should support that, not pre-empt it.
**Decision (as-built).** Scenario A surfaces an exact **minimum-cost benchmark**; a business presenter renders it in plain English with a `BANNED_DECISION_WORDS` guard so it **never asserts an award**. A human selects a scenario and attaches a decision note. There is **no "final award" object** and no decision-justification taxonomy (free-text only).
**Consequences.** Stage 7 (Decision Support) is PARTIAL; Stage 8 (Execution Prep) is NOT BUILT.
**Divergence from brief — LARGE.** The brief's engine is **decision-support by construction**: 5 banded factors (Price .35, Coverage .25, Historical .20, Z-Risk .10, Continuity .10) → a recommendation score, with the minimum shown only as a reference. The code has the *restraint* (it won't auto-assert an award) but not the *scoring model*, and it has only Scenario A where the brief has **seven lenses A–G** (benchmark, recommendation, incumbent-defense, max-N, exclusion, custom, preferred). **This is the second of the two biggest planned changes.**

---

## ADR-007 — Pricing model lives at the commercial/bid layer (not kickoff) — KNOWN DIVERGENCE

**Status:** Implemented (at the wrong layer, per the brief)
**Context.** An RFP awards a **pricing model, not just a price** — fixed, market/index ± spread, QDP, market-proxy.
**Decision (as-built).** A 10-table commercial layer standardizes any of **6 pricing models** into one comparable value with a fully **replayable formula audit**, governed by a **three-value rule** (raw / system-derived / normalized are three separate stored values; raw is append-only and never overwritten). 18 validation codes. The model is declared per priced offer at the commercial grain.
**Consequences.** `commercial_pricing.py` (1,036 lines); the pricing decision currently sits *below* the cycle.
**Divergence from brief — MEDIUM.** The brief declares the pricing model **at kickoff** (`cyc.cycle`), including cadence and the **five safeties** (disaster trigger, inverse + collar, rolling midpoint, tolerance band, period-by-period). The code stores reset/trigger/collar **parameters** but **never executes them** — the safeties are inert. The change is to lift the pricing decision up to kickoff and keep the component storage already built. Eduardo's direction (2026-06-17): the safeties "live somewhere in the RFP details and are visualizable as calcs when necessary."

---

## ADR-008 — Timeframe is a dimension; demand and capacity are separated by a CHECK

**Status:** Implemented
**Context.** Forking a workbook per timeframe is the failure mode. And demand volume must never be polluted by supplier capacity.
**Decision.** **Timeframe** is a dimension on cycles, bids, scope, and scenario output — never a fork. **Volume + Scope Prep** lands every governed volume/capacity row, tags each as DEMAND or CAPACITY, and a database CHECK (`ck_vsp_capacity_never_active_demand`) makes it **impossible for a capacity row to be marked active demand**. No allocation math is ever performed; multi-period rows are held as ALLOCATION_REQUIRED.
**Consequences.** `volume_scope_prep.py` (747 lines). A clean, period-aware, demand-only scope feeds the engine.
**Divergence from brief:** agrees on both points (the brief's ADR-008 timeframe-as-dimension, and its demand/capacity separation).

---

## The two-line summary for the gap analysis

- **Agrees with the brief:** store-first governed spine, lot-grain via sticky aliases, immutable runs, landed-cost standardization, timeframe-as-dimension, demand≠capacity, three-value pricing, drafts-don't-auto-send.
- **Diverges from the brief (the work):** single-winner → permit splits (ADR-003); min-cost solver → decision-support scoring + 7 lenses (ADR-006); pricing model at bid-layer → at kickoff + execute the five safeties (ADR-007); no "Sent" / no frozen award / no scorecard / no KCMS / no Output Factory → build the outward-facing half.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-18 | Session | As-built ADRs harvested from the running code + SYSTEM_SPEC for gap analysis. |
