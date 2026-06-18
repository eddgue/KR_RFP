---
doc: Audit — Gap Analysis (the "gaps" deliverable)
id: AUDIT-002
version: 1.0
status: Final
created: 2026-06-18
depends_on: AUDIT-000, AUDIT-001
audience: Architect, Build lead, Sponsor
---

# Audit — Gap Analysis

The exhaustive diff between the **AS-BUILT** (`specs/original-engine/`, the inherited code) and the **BRIEF** (`specs/rfp-engine/`, the intake-derived target). This is the "full analysis on gaps" deliverable.

**Reading frame.** The BRIEF is ground truth on *what the system should do* (it was written from real artifacts; the AS-BUILT's own README concedes "where the two disagree, the brief is ground truth"). The AS-BUILT is ground truth on *what exists and how rigorously it is built*. A "gap" is therefore a place where the as-built code must **change, build, relax, or be kept** to reach the brief's intent at enterprise quality. Each gap gets a **disposition**:

- **KEEP** — as-built is right (sometimes more right than the brief); carry it forward unchanged.
- **RELAX** — as-built is over-constrained; loosen a rule the brief needs loosened.
- **CHANGE** — as-built implements the wrong model; replace or re-point it.
- **BUILD** — neither side has it built; net-new.
- **MERGE** — both have a partial; combine the as-built's storage with the brief's placement/semantics.

Severity: **Critical** (foundational, blocks the brief's core value) · **High** · **Medium** · **Low**.

---

## 1. Capability matrix (the one-screen diff)

| Capability | BRIEF (target) | AS-BUILT (today) | Disposition | Sev |
|---|---|---|---|:---:|
| Lot grain via sticky normalization | `norm.item_lot_map` (propose→confirm) | typed alias system + quarantine (richer) | **KEEP** (as-built) | — |
| Lot **attribute taxonomy** | `attribute_def` + `lot_attribute` | absent | **BUILD** | Med |
| Award grain | **split** (`scenario_award`/`award`, `volume_share`) | **single-winner** (`UNIQUE(run,dc,lot,tf)`) | **CHANGE/RELAX** | **Crit** |
| Decision logic | **5-factor scoring** + 7 lenses A–G | exact **min-cost** solver, Scenario A only | **CHANGE** | **Crit** |
| Eligibility gating | `bid_score.eligible` + `gate_flags` | 7 gates · 12 codes · gate-result rows | **KEEP** (as-built) | — |
| Landed-cost standardization | `bid_price` components + 1 CHECK | 5 modes · 8 blocking reasons · tolerance | **KEEP** (as-built) | — |
| Immutable runs | `analysis_run` + `config_json` | sealed `calculation_run` + hashed manifests + version pins | **KEEP** (as-built) | — |
| Pricing model placement | at **kickoff** (`cyc.cycle`) | at commercial/bid grain | **MERGE** (lift up) | High |
| Five pricing **safeties** | named, not modeled | parameters stored, **never executed** | **MERGE/BUILD** | High |
| Award object → **freeze → layer** | `award.frozen_at` + `award_layer` | none | **BUILD** | **Crit** |
| Sign-off gate (out) | `awd.signoff` (portfolio) | none | **BUILD** | **Crit** |
| Generated outputs | booking guide, deck, letters, email | none (Output Factory PARKED) | **BUILD** | **Crit** |
| Stage-0 governance gate (in) | kickoff as in-gate | not implemented | **BUILD** | Med |
| "Sent" governance gate | draft→sent = official | drafts only ("never sends") | **CHANGE** | Med |
| Supplier scorecard | 2 frozen snapshots from iTrade | absent | **BUILD** | High |
| iTrade receipt feed | every PO receipt (`itrade_receipt`) | only `historical_award_assignment` (awarded cost) | **BUILD** | High |
| KCMS scan feed | `kcms_movement` (distinct) | absent | **BUILD** | High |
| Two origins + distance | `grow_origin`/`ship_from_zip` + `zip_centroid` | principle only; no distance calc | **BUILD** | Med |
| Fiscal calendar / STLY | `ref.fiscal_calendar` (to 2037) | `fiscal_date_conversion` (loaded lookup, not seeded) | **KEEP** (as-built) | Low |
| Demand vs capacity | two simple tables | separated by DB CHECK + VSP maturity | **KEEP** (as-built) | — |
| Timeframe as a dimension | `cycle_timeframe` | `cycle_tf` | **KEEP** (both agree) | — |
| Process rail | generated from cycle timeline | hardcoded 10 stages | **CHANGE** | Med |
| Live event log | `audit.event_log` (live) | `audit_event` hash-chain **SCAFFOLD** | **CHANGE/FINISH** | Med |
| Referential identity integrity | single-col FKs (0 composite) | 46 composite-identity FKs | **KEEP** (as-built) | — |
| Tenancy / client | named, not modeled | not modeled | **BUILD** (net-new) | High |
| Security / RBAC / NFRs | absent | absent | **BUILD** (net-new) | High |

---

## 2. ADR-by-ADR reconciliation

The two packages each carry eight ADRs in the same numbering. They agree on five and diverge on three — and the divergences are the program.

| ADR | BRIEF position | AS-BUILT position | Verdict |
|---|---|---|---|
| 001 Store-first, engine as library, UI last | Accepted | Implemented (console is a read-only view) | **Agree.** As-built is further along; keep. |
| 002 Lot is the grain; normalization is first-class | Accepted (`item_lot_map`) | Implemented (alias layer) **minus the attribute taxonomy** | **Agree on grain; gap on taxonomy** (→ G8). |
| 003 Award grain | **Split** | **Single-winner (forbidden to split)** | **Diverge — Critical** (→ G1). |
| 004 Immutable runs; freeze-and-layer; nothing deleted | Accepted (incl. `award.frozen_at` + `award_layer`) | Implemented for **runs**; freeze-and-layer of **awards NOT built** | **Agree on runs; gap on award freeze** (→ G3). |
| 005 Decision-support, not auto-award | Accepted (5-factor scoring) | **Partial** — has the restraint, not the scoring model | **Diverge — Critical** (→ G2). |
| 006 Two origins kept separate | Accepted (+ `zip_centroid` distance) | "Agreed in spirit," **no distance calc, not two-field** | **Diverge — Medium** (→ G7). *(Note: the two packages number this differently — see §5.)* |
| 007 One feed (iTrade) powers cost + scorecard | Accepted | **Historical cost only; no scorecard, no receipt feed** | **Diverge — High** (→ G6). |
| 008 Timeframe is a dimension; demand≠capacity | Accepted | Implemented (+ DB CHECK) | **Agree.** Keep; as-built is stronger. |

> **ADR numbering caveat.** The two packages do not map ADR↔ADR one-to-one. The AS-BUILT's ADR-005 is *landed-cost standardization* and its ADR-007 is *pricing-at-commercial-layer*; the BRIEF's ADR-005 is *decision-support* and ADR-006 is *two-origins*. The table above aligns them by **topic**, not by number. The target spec should renumber once, canonically.

---

## 3. The gaps in detail

### G1 — Award grain: single-winner → split allocation · **CHANGE/RELAX · Critical**

**Evidence.** Sign-off deck awards single DCs to *multiple* suppliers ("Onions52, Owyhee"; "Keystone, Onions52, Owyhee"). The v3 engine's `max_two_per_dc` consolidates to the strongest N per DC and splits lots between them. The models are literally called *Allocation* models.

**As-built reality.** `scenario_a_cell_assignment` carries `UNIQUE (scenario_run_id, dc_id, lot_id, tf_id)` and a single nullable `supplier_id` — the database **physically forbids** more than one supplier per cell. There is no `volume_share` column anywhere. The solver is structurally single-winner.

**Target.** The BRIEF's `eng.scenario_award` / `awd.award` carry **one row per awarded supplier per cell**, each with `volume_share`, `awarded_price`, `cap_breach_flag`.

**Disposition.** Drop the single-cell uniqueness; re-grain to (run, dc, lot, tf, **supplier**); add `volume_share`. Per Ed's 2026-06-17 direction this is a *permit-not-force* change: the auto scenario still defaults to one supplier per DC, but a cell may split when a **per-DC/per-lot splittable flag** is set, with capacity (`volume_limit` / `capacity_constraint`) as the binding constraint. This is one of the two changes Ed explicitly wants shipped **together** (with G2) because both touch the solver core.

**Blast radius.** `scenario_a_cell_assignment`, `scenario_a_line_detail`, `scenario_a_capacity_usage`, the Scenario A service, the presenter, every read that assumed one winner, and the (to-be-built) award tables.

---

### G2 — Decision logic: min-cost solver → five-factor decision-support · **CHANGE · Critical**

**Evidence.** `rfp_analysis_engine_v3.py` (verified, 4,198 lines) scores five **banded** factors, config-weighted: Price 0.35 (premium-vs-low bands ≤3→100/≤7→80/≤12→50/>12→20), Coverage 0.25, Historical 0.20, Z-Risk 0.10, Continuity 0.10 → composite `RecScore`. Cost is **35%**, not 100%. Plus seven scenario lenses A–G and eligibility gates with reason codes.

**As-built reality.** Scenario A is an **exact minimum-cost solver** (`scenario_a_result.objective_total_spend`, picks the lowest feasible benchmark). There is **no `bid_score` table, no weighted factors, no banding, and only Scenario A.** The as-built *does* have the right restraint — a `BANNED_DECISION_WORDS` guard stops the presenter from asserting an award — but restraint is not a scoring model.

**Target.** Add `eng.bid_score` (5 factors + composite + eligibility + gate_flags). Make the min-cost result **Scenario A = "lowest-cost reference"** (one of the lenses, shown as a benchmark, never auto-applied) and add lenses **B–G** (recommendation, incumbent-defense, max-N, exclusion, custom, preferred).

**Disposition.** This is where the BRIEF's brain replaces the AS-BUILT's brain. The cleanest path (Decision D2): **lift v3's scoring/allocation as the engine library** and let the existing min-cost solver become Scenario A. The as-built's eligibility and landed-cost layers feed the scorer as inputs — they are **kept** (they are richer than the brief's).

**Blast radius.** New `bid_score`; Scenario tables generalize from `scenario_a_*` to `scenario` + `scenario_award`; the engine runner; the calc-run contract types.

---

### G3 — The entire `awd` layer: award → freeze → layer → sign-off → outputs · **BUILD · Critical**

**As-built reality.** No `award` table, no `award_layer`, no `signoff`, no `generated_document`. Selection today = choosing a scenario + attaching a free-text `decision_note`. Stages 8–9 are NOT BUILT; the "Output Factory" is PARKED.

**Target.** The BRIEF specifies the whole layer: `awd.award` (promoted from a scenario_award, multi-row per cell, `frozen_at` seals at sign-off), `awd.award_layer` (post-freeze changes layer on top, date-stamped, raw recoverable), `awd.signoff` (portfolio-level, savings-vs-STLY headline), `awd.generated_document` (booking guide, sign-off deck, award/no-award/feedback letters, confirmation email — generated from records).

**Disposition.** Net-new build, and the largest single gap by surface area. The brief specifies it well; the v1.4 workflow package already contains generators (`generate_booking_sheet`, `generate_final_letters`, `generate_feedback_letters`) that can be lifted to render *from records* instead of from a fresh Excel. Sequence the booking guide first (Decision D4) — it is the award table + execution logistics and is the most-used artifact.

**Dependency.** Requires G1 (split award rows) and G2 (a real selection to promote) to exist first.

---

### G4 — Pricing model: lift to kickoff + make the five safeties executable · **MERGE · High**

This gap cuts **both ways**, which is why it is a merge, not a one-directional fix.

**The BRIEF** puts the pricing decision in the right place — `cyc.cycle.pricing_basis` + cadence + the five safeties declared at kickoff (Discrepancy #3/#11 prove the real docs declare it there) — but **models it thinly**: `bid_price` + `bid_index_component` only, with the safeties named in prose and **absent from the schema** (`[D-2]`).

**The AS-BUILT** models pricing **richly but in the wrong place and inert**: a ten-table commercial layer (`commercial_pricing_model` with a three-value raw/derived/normalized rule, `commercial_price_component` 20 types, `commercial_market_reference` carrying `reset_cadence`/`trigger_band_pct`/`collar_floor`/`collar_cap`, a replayable `commercial_pricing_formula_audit`, 18 validation codes) — declared per **priced offer below the cycle**, with the safety parameters **stored but never executed**.

**Target (merge).**
1. **Lift the declaration to kickoff**: pricing basis, duration/cadence, baseline-then-negotiate, volume-split rule, and each safety become cycle-level setup (the brief's placement).
2. **Keep the as-built's component storage and formula audit** (the brief has nothing this good) — but re-point it to read its parameters from the kickoff declaration.
3. **Make the safeties executable/visualizable** — disaster trigger, inverse trigger + collar (floor/cap), rolling midpoint (window/reevaluation cadence), tolerance band (band%/hold-weeks/re-review), period-by-period. Ed's direction (2026-06-17): the safeties "live somewhere in the RFP details and are visualizable as calcs when necessary."

This is the only gap where both packages are simultaneously ahead of and behind each other.

---

### G5 — Kickoff keystone is thin in both, vs the real kickoff docs · **MERGE/BUILD · High**

Session 2 extracted the real kickoff schema from four real docs. It is far richer than either package's cycle table.

| Kickoff element (Session 2) | In BRIEF `cyc.cycle`? | In AS-BUILT `rfp_cycle`? |
|---|:---:|:---:|
| `annual_spend` (size of the prize) | no | no |
| `objective` (multi, with a primary) | single text, no enum | `target_savings_amt` only |
| `subcommodities_in_scope` (list) | via `cycle`/scope | via `cycle_item_scope`/subcom |
| pricing basis + cadence + baseline-then-negotiate | partial (`pricing_basis`) | no (lives at commercial layer) |
| the five safeties | no (`[D-2]`) | parameters at commercial layer, inert |
| PBA governance (metric thresholds, enforcement, tariff clauses) | `cycle_term` (topic/penalty/reward/accepted) | `cycle_term`? **no** — as-built has no cycle_term; PBA lives only in bid intake |
| working-capital terms (NET 30; quantified benefit) | no | no |
| KPM funding (84.51°) | no | no |
| configurable RFI question set | no | no |
| timeline / rail (ordered `{event,date}`) | no (rail implied) | no (rail hardcoded) |
| narrative blocks (prose: background, strategy, industry, data dive) | no | no |

**Disposition.** The kickoff is the **keystone** of the brief's whole thesis ("declare structure once, store it, render from it"), yet both schemas under-model it. Build a proper `cyc.cycle` + satellite tables: `cycle_objective`, `cycle_pricing` (+ `cycle_safety`), `cycle_pba_term`, `cycle_commercial_term` (working capital, KPM), `cycle_rfi_question`, `cycle_timeline_event`, `cycle_narrative` (versioned rich text). Rule from Session 2 to honor: **structured fields drive the system; narrative blocks carry the why and stay prose** — never force narrative into fields.

---

### G6 — Supplier scorecard + iTrade receipt feed + KCMS · **BUILD · High**

**As-built reality.** Has `historical_award_assignment` (parent: last cycle's awards, volume on the parent) + `historical_awarded_price_basis` (child: one row per routing basis) + an ingestion-issue table. That is **awarded cost only** — *not* the receipt-level feed. There is **no `supplier_scorecard` and no `kcms_movement`.**

**Target.** The brief's `perf.itrade_receipt` is **every PO receipt** with cost components, fiscal stamp, quality/quantity fields and dirty-data flags — "one feed, two jobs": it powers both historical cost *and* the scorecard. `perf.supplier_scorecard` is two frozen snapshots per cycle (kickoff + sign-off). `perf.kcms_movement` is the distinct scan/margin feed.

**Disposition.** Build the receipt-grain `itrade_receipt` (the as-built's `historical_award_assignment` becomes a *derivation* over it, not the source), build the scorecard as a derivation (two frozen snapshots), and add KCMS. Keep the as-built's strong importer discipline (flag-first validation, impossible-date-span rejection, key-off-codes-not-filename) — Session 3 and the as-built ingestion-issue table agree on these rules.

---

### G7 — Two origins + zip-centroid distance · **BUILD · Medium**

**As-built reality.** `bid_line` has a `loading_location_id` (FK to a supplier loading location) but **no `grow_origin` / `ship_from_zip` pair and no `distance_miles`.** There is **no `zip_centroid` table and no distance calc anywhere** — the brief's freight proxy does not exist.

**Target.** `bid.grow_origin` (supplier-stated, per period) and `bid.ship_from_zip` (from PO, loose) kept **separate, never auto-derived from each other** (ADR-006); `ref.zip_centroid`; `distance_miles` derived ship-from → DC. The v1.4 workflow package already ships `calculate_distances` + `us_zip_centroids.csv` to lift.

---

### G8 — Lot attribute taxonomy · **BUILD · Medium**

**As-built reality.** Resolves items→lots via the alias system but has **no `attribute_def` / `lot_attribute`** decomposition. You cannot regroup "all organic" or "all field-process" without re-mapping.

**Why it matters.** The **Conventional/Organic split runs through every sign-off recommendation** (Session 4) and drives the financial split — it is load-bearing, not cosmetic. Without the taxonomy that grouping has no queryable home.

**Target.** `norm.attribute_def` (universal core ORGANIC/COLOR/SIZE/PACK + per-commodity extensions) + `norm.lot_attribute`. One confirmation pass per commodity at onboarding (Open item carried by both). **Keep** the as-built's superior alias+quarantine machinery underneath.

---

### G9 — "Sent" governance gate · **CHANGE · Medium**

**As-built reality.** Treats "never sends" as a virtue: `round_feedback_issued` is draft-status only; the presenter has a `BANNED_DECISION_WORDS` guard. No SENT state exists.

**Target.** Draft→sent is a **governance gate, not a channel** (Discrepancy #2, Session 1): "sent" means official, it left the building, recorded with approver and timestamp. The confirmation email after live negotiation is the official record.

**Disposition.** Add a `sent` lifecycle state with approver + timestamp to feedback, awards, and generated documents. Keep the `BANNED_DECISION_WORDS` guard for the *recommendation* surface (the system still must not auto-assert an award) — the two are compatible: the engine never asserts, but a human can promote a draft to sent.

---

### G10 — Process rail: hardcoded → generated from the cycle · **CHANGE · Medium**

**As-built reality.** The 10-stage rail is **hardcoded** in `app_scenario_a_preview.py`. (A second older doc hardcoded 13 stages — both wrong per Discrepancy #4.)

**Target.** "Process shape is per-cycle, not hardcoded" (Locked truth #8). The kickoff timeline (Session 2 §G, an ordered `{event,date}` list) **defines the rail; the app renders the rail from the file.** Rounds vary (3 default, more if there is juice; R4 seen).

**Disposition.** Build `cycle_timeline_event` (from G5) and drive the console from it. This is the concrete fix for the "non-standard process" problem the whole system exists to kill.

---

### G11 — Audit event log: scaffold → live · **CHANGE/FINISH · Medium**

**As-built reality.** `audit_event` is a sophisticated hash-chain design but **SCAFFOLD** — unpopulated, no write-only enforcement (`[D-7]`). The functional trail is the calc-run ledger + append-only bookkeeping.

**Target.** `audit.event_log` is **live and append-only** — "the line between a system of record and a pile of file generators." "Open last cycle" is a query across cycle→rounds→bids→runs→scenarios→awards joined through the event trail.

**Disposition.** Finish the as-built's design (its hash-chain is *better* than the brief's simpler jsonb log) — wire population on every state change and enforce write-only. Do **not** rebuild it as the brief's simpler table; promote the brief's "must be live" requirement onto the as-built's stronger structure.

---

### G12 — Stage-0 governance in-gate · **BUILD · Medium**

**As-built reality.** "A real cycle on real data requires a Stage-0 governance sign-off that is **not implemented.**" Everything is synthetic-only.

**Target.** The kickoff *is* the in-gate (the BRIEF's two-gate frame: kickoff in, sign-off out). Build the in-gate as a real approval object so a cycle cannot open against real data without it.

---

### Net-new (neither package) — tenancy, security, NFRs · **BUILD · High**

Carried from `01 [D-4]`/`[X-1]`. Not a "gap between the two" but a gap in **both**, and mandatory for enterprise:
- **Tenancy / `client`** as a first-class reference entity (Session 1 names it); the sign-off gate is portfolio-level across categories/clients (Session 4).
- **Actor/role model + RBAC**, PII/data-classification, retention, API auth/authz.
- **NFRs**: sizing (the stated workload — tens of categories, dozens of DCs, hundreds of lots, single-digit-thousand bids/cycle, a handful of rounds — is modest; design accordingly), performance targets, backup/DR, observability.
- **Real-data pilot** — one full cycle end-to-end on a real iTrade pull + real bids. This is the top program risk on both sides.

---

## 4. What the AS-BUILT gets right and the BRIEF should adopt (the "keep" list)

These are *reverse gaps* — places the as-built is **more** enterprise-ready than the brief. The target must inherit them rather than regress to the brief's thinner model.

1. **Composite-identity referential integrity** — 46 multi-column FKs guaranteeing lot∈cycle, item∈lot, tf∈cycle, loading-location∈supplier, submission identity quad, calc-run identity. The brief has **zero**. *Keep the as-built discipline; it is the difference between a schema and a system of record.*
2. **Sealed calc-run governance** — hashed input/output manifests, execution-contract enum, required-inputs-by-contract, version pins (`metric_definition_version`, `engine_release`, `scenario_config_version`), `calculation_run_input` freeze. The brief's single `analysis_run` + `config_json` is a thinner version of the same idea.
3. **Five-mode landed-cost standardization** (`landed_cost_result`: DIRECT_ALL_IN / RECONCILED_ALL_IN / RECONSTRUCTED_APPROVED / MISMATCH_BLOCKED / FOB_PREVIEW_ONLY; 8 blocking reasons; tolerance; awardable/non-awardable shape CHECKs). The brief's `bid_price` is just components + one CHECK.
4. **Seven-gate eligibility** (`eligibility_result` + `eligibility_gate_result` + `eligibility_exception` + `supplier_capability` + `capacity_statement` + `capacity_constraint`; 12 reason codes). The brief reduces this to `bid_score.eligible` + a `gate_flags` string.
5. **Demand≠capacity enforced by DB CHECK** (`ck_vsp_capacity_never_active_demand`) plus the whole Volume-&-Scope-Prep maturity (precedence ranks, ~24 issue codes, overrides with lineage). The brief has two simple tables.
6. **Typed-alias + quarantine identity system** (typed alias kinds, partial unique indexes for one-active-alias-per-normalized-form, deactivation lineage, a shared quarantine queue with domains and rejection reasons). Richer than the brief's `item_lot_map`/`supplier_alias`.
7. **The audit hash-chain *design*** (before/after state hashes, prev/this event hash) — superior structure to the brief's jsonb log; just needs to be made live (G11).

---

## 5. Reconciliation map (where each target capability comes from)

| Target capability | Source of the **shape/intent** | Source of the **rigor/storage** |
|---|---|---|
| Lot grain + normalization | BRIEF (taxonomy) | AS-BUILT (alias + quarantine) |
| Split allocation awards | BRIEF | net-new grain change to AS-BUILT solver |
| 5-factor scoring + lenses A–G | BRIEF / v3 engine | net-new `bid_score`; AS-BUILT eligibility+landed-cost as inputs |
| Immutable runs | both | AS-BUILT (sealed runs + manifests) |
| Pricing at kickoff + executable safeties | BRIEF (placement) | AS-BUILT (commercial component storage) |
| Award / freeze / layer / sign-off / outputs | BRIEF | net-new build; lift v1.4 generators |
| Scorecard / iTrade receipts / KCMS | BRIEF | net-new; AS-BUILT importer discipline |
| Two origins + distance | BRIEF | net-new; lift `calculate_distances` |
| Event log (live) | BRIEF (must be live) | AS-BUILT (hash-chain design) |
| Referential integrity, CHECKs, calc-run governance | — | AS-BUILT (keep wholesale) |
| Tenancy, security, NFRs, real-data pilot | net-new (neither) | net-new |

**One-line synthesis:** *Build the brief's brain and outward-facing half on the as-built's spine, lifting pricing to kickoff and the v1.4 generators onto records — then add the enterprise layer (tenancy/security/NFRs) and prove it on one real cycle.*
