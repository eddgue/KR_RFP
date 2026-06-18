---
doc: Audit — Document Audit
id: AUDIT-001
version: 1.0
status: Final
created: 2026-06-18
depends_on: AUDIT-000
audience: Architect, QA, Build lead
---

# Audit — Document Audit

Assesses the two packages **as engineering artifacts** — structure, completeness, internal consistency, traceability, and enterprise-readiness — independent of the gap analysis (`02`). Every finding cites the artifact it came from so it can be checked.

Conventions: **BRIEF** = `specs/rfp-engine/`; **AS-BUILT** = `specs/original-engine/`. Defects are tagged `[D-n]` and severity-rated **Blocker / Major / Minor**.

---

## 1. Inventory and provenance

| | BRIEF | AS-BUILT |
|---|---|---|
| Core docs | `BUILD_00_README` · `01_SYSTEM_OVERVIEW_AND_ADRS` · `02_DATA_MODEL` · `03_schema.sql` · `04_TECH_SPEC` | identical five-doc shape |
| Evidence base | `intake/00_INDEX` + `SESSION-01..06` (7 files) + a 20-row discrepancy log | none included in-package |
| Schema size | 521 lines · **36 tables** · 8 logical schemas | 1,336 lines · **63 tables** · 8 logical layers |
| Constraint density | 14 CHECK clauses · **0** composite/identity FKs | 67 CHECK clauses · **46** composite/identity FKs |
| Headers / changelog | yes (`doc/id/version/status/depends_on` + changelog) | yes (same convention) |
| Declared status | **Draft** v1.0 (2026-06-17) | **As-Built** v1.0 (2026-06-18) |
| Stated authority on conflict | itself ("the brief is ground truth") | `docs/RFP_ENGINE_CONTROL_LAYER_SPEC_v1_0.md` (the "ECLS"), **not included** |

**Provenance quality.** The BRIEF is exceptionally well-sourced: each decision traces to a dated session and a named real artifact (kickoff docs, iTrade pulls, the Norm sheet, eight supplier bids, the `20260528_P&O_Leadership_Sign-Off.pptx`, and `rfp_analysis_engine_v3.py` read at 4,198 lines). The AS-BUILT is a faithful, self-aware map of a codebase but is **unverifiable from within its own package** — see `[D-5]`.

---

## 2. BRIEF — findings

### Strengths
- **Best-in-class requirements traceability.** The discrepancy log (`intake/00_INDEX.md`, 20 rows) pairs every "the doc says X / reality is Y" with a defect type. This is the single most valuable asset in either package and should survive into the target spec.
- **Decisions are justified, not asserted.** Each of the 8 ADRs names the finding it resolves and the alternative it rejects. ADR-003 (splits) and ADR-005 (decision-support) cite the specific real artifacts that disprove the old spec.
- **Honest about its own seams.** It flags the unverified-real-data risk, the persistence open question, and the paused fork rather than papering over them.
- **Right altitude for a handoff.** `BUILD_04` gives a component map, data flow, the v3 `run()` integration contract, a representative REST surface, and a phased A–F build sequence with explicit exit criteria.

### Defects

**`[D-1] Blocker — the foundational architecture decision is left open.`** The README, System Overview, and `BUILD_04` Open Item #1 all defer the greenfield-vs-reconcile question, and `intake/00_INDEX` records the "v3 brain on a new spine" fork as **"paused pending"** sight of the workflow package and the live app's persistence layer (Session 6, Addendum 3). A build package whose first instruction is "verify before you build" has not finished its own job. The AS-BUILT package resolves this (a real store exists), but the BRIEF never incorporates that. *Fix: fold the as-built reality in and close the decision (see `04` D1).*

**`[D-2] Major — the five pricing "safeties" are the named core of the product but are not modeled.`** Sessions 1 and 2 call the safeties "the real product" and Discrepancy #6 explicitly faults the old spec for storing them inert. Yet `BUILD_03_schema.sql` models pricing only as `bid.bid_price` (component columns + the `no_double_discount` CHECK) and `bid.bid_index_component` (key/value text). There is **no table or field** for disaster trigger, inverse trigger + collar, rolling midpoint, tolerance band, or period-by-period parameters, and nothing executable. The brief reproduces the exact failure it indicts. *(Ironically, the AS-BUILT *does* model these — `commercial_market_reference.reset_cadence/trigger_band_pct/collar_floor/collar_cap` — but also leaves them inert. See `02 §3 G4`.)*

**`[D-3] Major — the schema is under-constrained for an enterprise system of record.`** Specifics:
- **Zero composite/identity foreign keys.** The AS-BUILT uses 46 of them to guarantee, e.g., that a bid's lot belongs to the bid's cycle and its item belongs to that lot. The BRIEF's single-column FKs permit cross-cycle and cross-lot leakage that the data model's own prose forbids.
- **`bid.volume_limit` has no primary key** — it is a heap. Duplicate or contradictory capacity rows for the same (cycle, supplier, dc, lot, tf) can be inserted silently, and capacity is described as "load-bearing" for the split allocation (ADR-003). *Blocker-adjacent for the engine.*
- **Enums declared in prose, not enforced.** `cycle.objective`, `cycle_round.bid_type`, `cycle_term.topic`, `generated_document` consumers, and `award_layer.field` carry their allowed values only in comments. Compare the AS-BUILT, where these are DB `CHECK ... IN (...)` constraints or native enum types.
- **No immutability mechanism specified.** ADR-004 promises "no hard deletes … app-level + DB constraints/triggers," but no trigger, rule, or guard is written. The AS-BUILT ships `controls/calc_run_guards.py` listeners that enforce append-only at the DB layer.
- **Sparse indexing.** Only a handful of indexes; none on the high-cardinality `bid.bid` lookup paths beyond the natural unique key.

**`[D-4] Major — no non-functional, security, or tenancy layer.`** Session 1 names "Clients" as a first-class reference entity with "its own home," and the sign-off gate is described as **portfolio-level across multiple categories/clients** (Session 4) — yet there is no `client`/tenant table, no actor/role model, no RBAC, no PII/data-classification note, no retention policy, no auth on the REST surface, no performance or sizing targets beyond "Postgres is ample," and no backup/DR/observability. For an enterprise system of record holding commercial bid and award data, this is a whole missing layer.

**`[D-11] Minor — status never advanced past Draft, and there is no approval record.`** All five docs are `status: Draft, v1.0`. There is no sign-off, reviewer, or acceptance artifact, and the changelogs have a single row each. Acceptable for an intake deliverable; not acceptable as the thing you build an enterprise system from without a gate.

**`[D-12] Minor — some evidence is second-hand.`** Session 1 notes the iTrade export was "seen via a prior conversation, not opened live," and Session 5's engine run **errored at step 3** (the test never produced output). The conclusions are sound and later corroborated (Session 6 read the engine in full), but the data-shape claims that rest only on recalled artifacts should be re-validated against a live pull before they harden into schema.

---

## 3. AS-BUILT — findings

### Strengths
- **Radical honesty.** The status legend (BUILT / SCAFFOLD / CONTRACT-ONLY / PARKED / NOT BUILT) is applied consistently, and "honesty notes" call out removed features (the "aggregator"/Cycle Setup tool), the two Streamlit entrypoints, and the scaffold-only audit chain. Absence is made *legible* rather than hidden.
- **Genuinely enterprise-grade modeling.** 67 CHECKs and 46 composite-identity FKs encode business rules in the database: landed-cost awardable/non-awardable *shape* checks, capacity scope/field-match, scenario capacity arithmetic (`remaining = limit − assigned`), eligibility reason/submission consistency, alias deactivation consistency, fiscal-range bounds. This is the discipline the target needs.
- **A real governance spine.** Sealed `calculation_run` with hashed input/output manifests, an execution-contract enum, required-inputs-by-contract, and version pins (`metric_definition_version`, `engine_release`, `scenario_config_version`) — reproducibility and audit are structural, not aspirational.
- **Maturity in the unglamorous middle.** Five-mode landed-cost standardization (8 blocking reasons), seven-gate eligibility (12 reason codes), demand≠capacity by CHECK, typed aliases + quarantine, and a ten-table commercial-pricing layer with a replayable formula audit.

### Defects

**`[D-5] Major — the package is not self-verifiable, and its stated source of truth is absent.`** The README names the **ECLS** (`docs/RFP_ENGINE_CONTROL_LAYER_SPEC_v1_0.md`) as authoritative on any conflict and `docs/SYSTEM_SPEC.md` as the as-built narrative — **neither is included.** Nor are `models.py`, the migrations, or the tests. So claims like "63 tables generated from the models," "14 migrations, roundtrip-clean," and "796 passed / 1 skipped" **cannot be checked from the artifact set.** For an audit, this is a traceability hole; for a handoff, it means the most authoritative document is missing.

**`[D-6] Major — the schema is SQLite-shaped despite a PostgreSQL header, and several CHECKs are no-ops.`** `BUILD_03_schema.sql` says "dialect: PostgreSQL," but:
- Booleans are written/compared as `0/1` (`DEFAULT 0`, `is_eligible = 0`, `active_flag = 1`) — SQLite idiom, not Postgres `boolean`.
- `ck_calcrun_failed_has_errorlog` contains the branch `... OR (status != 'FAILED' AND (error_log IS NULL OR length(error_log) >= 0))` — `length(x) >= 0` is **always true**, so that half of the constraint enforces nothing. At least one shipped CHECK is vacuous.
- These betray the "synthetic SQLite for the demo" origin and mean the DDL has **not** been exercised on the Postgres semantics the target will run on. *Fix: regenerate and validate against real Postgres before it becomes the migration baseline.*

**`[D-7] Major — the audit hash-chain is a control that looks present but is not operative.`** `audit_event` carries a sophisticated tamper-evident design (`before_state_hash`, `after_state_hash`, `prev_event_hash`, `event_hash`), but the data model marks it **SCAFFOLD** — "population + write-only enforcement deferred." An auditor reading only the schema would conclude the system has a cryptographic audit trail; it does not. The *functional* trail today is the calc-run ledger plus append-only bookkeeping. This is an enterprise risk (false assurance) and must be either finished or relabeled.

**`[D-8] Major — the outward-facing half is absent, so the documented "process" stops at Stage 7.`** `BUILD_02 Layer 6` lists `award`, `award_layer`, `signoff`, `generated_document` as **NOT BUILT**; `BUILD_04` marks Stages 8–9 NOT BUILT. The as-built therefore documents a system that can analyze and recommend but cannot *award, freeze, sign off, or produce a single outward artifact* — exactly the half the BRIEF says is the whole point of a system of record.

**`[D-9] Minor — over-engineering at the edges, thin at the center of value.`** The intake's own characterization ("over-built at the edges, thin at the governance ends," Session 5) is visible in the schema: ten commercial-pricing tables and a six-table calc-run governance apparatus exist while the award object does not. The commercial layer normalizes six pricing models with a replayable audit, yet the pricing *decision* sits below the cycle and the safeties never fire. Effort was spent where the older spec pointed, not where the real workflow needed it.

**`[D-10] Minor — descriptive only; it resolves nothing.`** By design the package describes and does not recommend. Correct for an as-built, but it means every divergence is named and none is closed — the reconciliation layer (this audit and the target spec) is genuinely net-new.

---

## 4. Cross-cutting findings (both packages)

**`[X-1] Blocker (program) — nothing has run on real data.`** AS-BUILT: "Everything in the repo is synthetic-only"; "every BUILT means passes tests its own author designed." BRIEF: Discrepancy #10, "Synthetic data only, no real cycle run — biggest risk in the build." Two independently-produced packages converge on the same top risk. Until one full cycle runs end-to-end on a real iTrade pull and real bids, every capability claim on both sides is unproven against the mess it exists to absorb.

**`[X-2] Major — the two packages never reference each other, so each is missing what the other supplies.`** They were produced a day apart (BRIEF 06-17, AS-BUILT 06-18) and are explicitly meant to be diffed, but neither cites the other. The BRIEF asks "does a store exist?" and the AS-BUILT *is* that store's documentation; the AS-BUILT asks for nothing but lacks the brief's process truth. The reconciliation has to be done by a third artifact — this audit.

**`[X-3] Minor — naming and layer mapping are parallel but not identical.`** Both use the eight-layer mental model (`ref/norm/cyc/bid/eng/awd/perf/audit`), but the AS-BUILT uses physical table names (`rfp_cycle`, `cycle_tf`, `scenario_a_*`) and the BRIEF uses Postgres schemas (`cyc.cycle`, `cyc.cycle_timeframe`, `eng.scenario_award`). The target must pick one canonical naming and publish a crosswalk (started in `03`).

---

## 5. Enterprise-readiness scorecard (rubric)

Each dimension scored 1–5. Rubric: **1** absent · **2** gestured at · **3** adequate for a pilot · **4** strong · **5** exemplary.

| Dimension | What "strong" means here | BRIEF | AS-BUILT |
|---|---|:---:|:---:|
| Requirements traceability | Every decision → evidence → artifact | 5 | 3 |
| Business-process fidelity | Matches how the cycle is really run | 5 | 2 |
| Engine / decision logic | Scoring, lenses, allocation correct & justified | 4 | 2 |
| Data-model rigor | Identity integrity, CHECKs, immutability | 2 | 5 |
| Governance & audit | Sealed runs, append-only, live event log | 3 | 4 |
| Outward-facing half | Award, freeze, sign-off, generated outputs | 4 | 1 |
| Pricing & safeties | Right layer + executable safeties | 3 | 3 |
| Non-functional / security / tenancy | RBAC, PII, retention, NFRs, DR | 1 | 2 |
| Verified against real data | One real cycle, end to end | 1 | 1 |
| Self-verifiability of the package | Can the claims be checked from the artifact? | 4 | 2 |
| **Mean** | | **3.2** | **2.7** |

Read the means with care: the BRIEF scores higher on *intent and traceability*, the AS-BUILT on *engineering rigor*. The target must inherit the **max of each row**, not the average of either column — and must lift the two shared 1-2 rows (real-data validation, NFR/security) that neither package addresses.

---

## 6. Document-level recommendations

1. **Promote the BRIEF's `BUILD_01/02/04` to the structural template** for the reconciled target spec; it is ground truth on process and intent.
2. **Attach the missing authoritative documents** before relying on the AS-BUILT: the ECLS, `SYSTEM_SPEC.md`, `models.py`, the migration chain, and the test report. Until then, treat its quantitative claims (63 tables, 14 migrations, 796 tests) as asserted, not verified.
3. **Carry the discrepancy log forward** as a living register; it is the audit trail from old-spec error → corrected requirement.
4. **Re-baseline the schema on real PostgreSQL** and fix the SQLite-isms and no-op CHECK (`[D-6]`) — this DDL will become the migration baseline, so it must be clean.
5. **Open the two net-new sections** that neither package has: (a) the non-functional/security/tenancy spec (`[D-4]`), and (b) the real-data pilot plan (`[X-1]`).
6. **Resolve, then record, the build-path decision** (`[D-1]`) at the top of the target spec so no one re-litigates greenfield-vs-reconcile mid-build.
