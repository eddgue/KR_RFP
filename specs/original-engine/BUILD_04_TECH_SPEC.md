---
doc: Technical Specification (As-Built)
id: ORIG-003
version: 1.0
status: As-Built
created: 2026-06-18
last_updated: 2026-06-18
depends_on: ORIG-001 (System Overview & ADRs), ORIG-002 (Data Model)
---

# Technical Specification (As-Built)

The counterpart to the brief's `BUILD_04`. It describes the components that **exist and run today**, how data moves through them, the Streamlit surface, and the order in which the system was actually built. Mirrors the brief's structure for diffing.

---

## Stack (real)

| Layer | Choice | Note |
|---|---|---|
| Database | SQLAlchemy 2.0 ORM, modeled Postgres-shaped | Demo runs on synthetic **SQLite**; DDL emits clean for PostgreSQL (see `BUILD_03_schema.sql`). Override via `DATABASE_URL`. |
| Migrations | Alembic | 14 migrations, single head `j29e0cpm01`, roundtrip-clean (upgrade→downgrade→upgrade tested). |
| Engine | Hand-built services in `services/*.py` (17 files) | The real `rfp_analysis_engine_v3.py` is **not** lifted in; the code re-implements the spine. |
| Ingestion | pandas / openpyxl importers + a 7-step column-mapping wizard | "Forms for humans, imports for scale, column-mapping for messy reality." |
| Output rendering | **None** | Output Factory / booking guide / letters are NOT BUILT. |
| Frontend | Streamlit Process Console | `streamlit_app.py → app_scenario_a_preview.py`. Read-only over governed output + session-state overlay. |
| Dependencies | **stdlib + sqlalchemy only** | No new third-party deps. |

---

## Component map (what exists)

| Component | Type | Responsibility | Status |
|---|---|---|---|
| Schema / migrations | DB | The 63-table store under Alembic | BUILT |
| Master-data alias resolver | service | Resolve messy text → master ids; quarantine the unresolvable | BUILT |
| Bid intake + classifier | service | Map bid files to `bid_line`; 7 statuses, incomplete/leverage reasons | BUILT |
| Eligibility | service | 7 gates → awardable/blocked/deferred | BUILT |
| Landed cost | service | 5 modes → one comparable cost; 8 blocking reasons | BUILT |
| Calc-run ledger + freeze | service | Seal runs, hash manifests, enforce immutability | BUILT |
| Run-input freeze | service | Freeze the 8 input types into a run | BUILT |
| Round lifecycle | service | Append-only participation / feedback / field-reduction | BUILT |
| Round analysis orchestrator | service | `execute_round_candidate_analysis` | BUILT |
| Scenario A (the optimizer) | service | Exact min-cost award, capacity at 5 scopes, itemized | BUILT (single-winner) |
| Scenario A views + presenter | service | Read-only dataclasses; plain-English; `BANNED_DECISION_WORDS` guard | BUILT |
| Historical Awarded Cost ingestion | service | Parent/child, routing-basis coalesce, 12 rejection codes | BUILT |
| Fiscal calendar | service | `map_to_fiscal_periods` over a loaded lookup | BUILT |
| Volume + Scope Prep | service | Demand/capacity split, precedence, fiscal classification | BUILT |
| Commercial pricing | service | Normalize 6 models → one value + replayable audit + 18-code validation | BUILT |
| **iTrade loader** | service | Land PO receipts | **NOT BUILT** (historical cost ingestion is the nearest thing) |
| **KCMS loader** | service | Land scan movement | **NOT BUILT** |
| **Scorecard builder** | service | Two frozen snapshots from one feed | **NOT BUILT** |
| **Distance calc** | service | Ship-from zip → DC distance | **NOT BUILT** (no `zip_centroid`) |
| **Decision-support scorer** | service | 5 banded factors → rec_score | **NOT BUILT** |
| **Scenario lenses B–G** | service | Recommendation / incumbent / max-N / exclusion / custom / preferred | **NOT BUILT** (only A) |
| **Selection → freeze → layer** | service | Promote, freeze, layer awards | **NOT BUILT** (no award object) |
| **Document generator** | service | Booking guide / deck / letters | **NOT BUILT** (PARKED) |
| **Event logger** | cross-cutting | Populate the hash-chain | **SCAFFOLD** |
| Streamlit Process Console | frontend | The 10-stage rail | BUILT (hardcoded rail) |

---

## Data flow (as it runs today)

1. **Reference + alias load.** Master entities + aliases land; unresolved text → `master_data_quarantine`. (BUILT)
2. **History load.** Last cycle's awards → `historical_award_assignment` (parent) + price bases (child). *No iTrade/KCMS feed.* (BUILT, partial)
3. **Fiscal + volume prep.** Fiscal calendar lookup classifies dates; Volume+Scope Prep produces a demand-only, period-aware scope, capacity kept separate by CHECK. (BUILT)
4. **Cycle setup.** Kickoff declares cycle → rounds, timeframes, lots, item scope, projected volume, invited suppliers, via the 6-section Setup UI + 7-step import wizard. *Pricing model is NOT declared here.* (BUILT)
5. **Bid round.** Suppliers' files → `bid_submission` / `bid_line`; classifier assigns statuses + incomplete/leverage reasons; commercial layer normalizes the pricing model to one comparable value. (BUILT)
6. **Eligibility + landed cost.** 7 gates, then 5-mode landed-cost standardization; uncostable bids blocked with a reason. (BUILT)
7. **Run.** A sealed `calculation_run` with hashed manifests → Scenario A writes `scenario_a_result` + cell assignments + line detail + capacity usage. *Single-winner, exact min cost. No scoring, no lenses B–G.* (BUILT)
8. **Review + select.** Human compares Scenario A vs a session-state custom overlay; attaches a `decision_note`. *No final-award object is created.* (PARTIAL)
9. **Loop.** Rounds repeat under a forward-only status machine; feedback is **drafted only** (no SENT). (BUILT)
10. **Sign-off / generate.** **NOT BUILT** — no signoff object, no document generation.
11. **Audit.** The calc-run ledger + append-only bookkeeping carry the trail; the `audit_event` hash-chain is a scaffold.

**Failure modes (real):** unresolved identity → quarantine, not a guess. Uncostable bid → blocked with one of 8 reasons, not a silent zero. Capacity row → can never be marked active demand (DB CHECK). Bad volume row → kept for audit with an issue code, not dropped.

---

## Governance model (as-built)

- **Immutable runs.** `calculation_run` + hashed manifests; outputs append-only, enforced by `controls/calc_run_guards.py` listeners. Re-run to correct.
- **No deletes.** Supersede via new rows everywhere.
- **Drafts, never sends.** No SENT state for feedback; a `BANNED_DECISION_WORDS` guard stops the presenter asserting an award.
- **Open last cycle.** A read over cycle → rounds → bids → runs → Scenario A, anchored by `round_analysis_snapshot` (one canonical per round).
- **NOT yet governed:** the `audit_event` hash-chain (scaffold), the Stage 0 sign-off gate (not built), and award freeze (no award object).

---

## The Streamlit surface (the 10-stage console)

The deployed entrypoint is `streamlit_app.py` (never-blank wrapper, fatal-error guards, sidebar build info), which calls `app_scenario_a_preview.py::_run()`. A task-first home screen (4 action cards + a "Where am I?" strip) lands the synthetic demo at **Round Analysis**.

| # | Stage | Status |
|---|---|---|
| 0 | Setup / Kickoff | BUILT (data + UI form) |
| 1 | Supplier Field | BUILT |
| 2 | Intake / Validation | BUILT |
| 3 | Round Analysis (engine core) | BUILT — most built |
| 4 | Cat Man Alignment | BUILT (notes) |
| 5 | Feedback / Next Round | BUILT (no SENT) |
| 6 | Scenario Review | BUILT (Scenario A + custom overlay) |
| 7 | Decision Support | PARTIAL |
| 8 | Execution Prep | NOT BUILT |
| 9 | Closeout | NOT BUILT |

The rail is **hardcoded** in `app_scenario_a_preview.py`. The brief wants it **generated from the cycle's declared timeline** (process shape is per-cycle variable). That is a known divergence.

> **Note:** a separate `app.py` (Phase-1a Charter form) exists but is **not** the deployed entrypoint. Don't confuse the two. A removed "aggregator" upload tool is **not** part of the product.

---

## Tests

54 test files; last full run **796 passed / 1 skipped**. Coverage: the engine (eligibility, landed cost, calc-run immutability, Scenario A solver), the 2.9x stages (alias resolver, historical cost, fiscal mapping, volume/scope prep, commercial pricing), and UI render contracts (never-blank guards, panel error isolation). Migration roundtrip tested. All fixtures **synthetic** — no real supplier names, no real commercial values.

---

## Build sequence (as it actually happened)

The code was built backend-first, stage by stage. Roughly:

- **2.5–2.6** — Calc-run ledger + governed execution contract; Scenario A outputs (the four tables); required lot/item.
- **2.8** — Setup redesign (6 sections + import wizard); invited suppliers; the Process Console IA; never-blank hardening.
- **2.9A** — Master-data alias system + resolver.
- **2.9B** — Historical Awarded Cost ingestion (parent/child).
- **2.9C** — Fiscal calendar (lookup, not formula).
- **2.9D** — Volume + Scope Prep (demand/capacity split).
- **2.9E** — Commercial Pricing Model (6 models, three-value rule, replayable audit).

**Dependencies honored:** store → reference/alias → history/fiscal/volume → cycle/bids → eligibility/landed cost → run/Scenario A → review. The outward-facing half (Stages 8–9, Output Factory) was never started.

---

## The build that remains (the gap, as a sequence)

Stated here so the gap analysis has a spine. Each maps to a divergence in `ORIG-001`/`ORIG-002`:

1. **Decision-support scoring** — 5 banded factors → rec_score, eligibility/gate output as score inputs (ADR-006). *Large; touches Scenario A core.*
2. **Split awards** — permit (not force) multiple suppliers per cell with `volume_share`, gated by a per-DC/per-lot splittable flag (ADR-003). *Medium; touches Scenario A core.*
3. **Scenario lenses B–G** — recommendation, incumbent-defense, max-N, exclusion, custom, preferred.
4. **Pricing model + five safeties at kickoff** — lift the pricing decision to the cycle; make the safeties executable/visualizable (ADR-007).
5. **Awards: select → freeze → layer**, plus a **"Sent" governance gate**.
6. **Outward-facing half** — supplier scorecard, generated booking guide / deck / letters (Output Factory), Closeout archive.
7. **Supporting gaps** — KCMS feed, zip-centroid distance calc, lot attribute taxonomy, live `audit_event` hash-chain, Stage 0 governance sign-off.

Per Eduardo's reconciliation (2026-06-17), the **first two** (decision-support scoring and split awards) are the deliberate reconciliation stage, planned together because both touch Scenario A at its core.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-18 | Session | As-built tech spec: real components, data flow, Streamlit surface, build sequence + remaining gap. |
