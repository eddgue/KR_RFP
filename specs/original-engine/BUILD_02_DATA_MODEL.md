---
doc: Data Model (As-Built)
id: ORIG-002
version: 1.0
status: As-Built
created: 2026-06-18
last_updated: 2026-06-18
depends_on: ORIG-001 (System Overview & ADRs)
---

# Data Model (As-Built)

The companion to `BUILD_03_schema.sql` (63 real tables, generated from the SQLAlchemy models). This explains *why* each table exists and how the grain holds. It is deliberately mapped onto the **same eight-layer shape** the brief's `BUILD_02` uses (`ref / norm / cyc / bid / eng / awd / perf / audit`), so the two can be diffed layer by layer. The code does not literally use Postgres schemas; these are logical layers.

Read the as-built ADRs (`ORIG-001`) first.

---

## Conventions (real, in code)

- Primary keys are 36-char string UUIDs (`String(36)`).
- Money is `Numeric(18,6)`; case volumes `Numeric(18,3)`/`(18,6)`; rates/percents `Numeric(9,6)`.
- Enums are real database `CHECK` constraints in most tables — an out-of-list value is rejected by the database.
- "Append-only" = corrections insert a superseding row; never edit/delete. Enforced at the service layer, and for calculation outputs by database guard listeners.
- Services never own a transaction: they `add` + `flush`, never `commit`.

---

## The grain, stated once

Every priced fact resolves to: **supplier × lot/item × DC × timeframe × round × price.**

- **DC × lot/item × supplier** is the bid and award grain. Region / National / Local / growing-region are **tags**, never a grain level.
- **One supplier wins one cell** today (single-winner). The brief permits a split; the code does not. (ADR-003 — the headline gap.)
- **Timeframe** is a dimension, never a forked workbook.
- **Round** is a first-class record (R1..Rn) with a forward-only status machine.
- **Price** standardizes to one landed number via five modes; the commercial layer additionally normalizes six pricing *models* to one comparable value.

---

## Layer 1 — `ref` equivalent: master data + aliases (BUILT)

The reference entities every cycle hangs off, plus the alias machinery.

| Table | Holds | Note |
|---|---|---|
| `supplier_master` | Canonical supplier | |
| `dc_master_db` | Distribution center | |
| `commodity_master_db` | Commodity | |
| `subcommodity_master` | Sub-commodity | Optional cycle scoping; trigger enforces scope consistency |
| `item_master` | Physical case SKU + UPC/identity | |
| `loading_location` | Supplier → physical shipping point | |
| `supplier_alias` / `item_alias` / `dc_alias` | Alias text → master id | Append-only except `active_flag`; one active alias per normalized form (partial unique index); typed alias kinds |
| `master_data_quarantine` | The shared "couldn't resolve" queue | Domain DC/ITEM/SUPPLIER; 5 rejection reasons; resolve per row |

**Gap vs brief's `ref`:** the code has no `fiscal_calendar` *here* (it lives in its own table — see Layer 7), no `zip_centroid` (so **no distance/freight-proxy calc exists at all**), and the supplier scorecard reference is absent.

---

## Layer 2 — `norm` equivalent: the lot/alias store (BUILT, partial)

This is the layer that makes the lot grain sticky.

| Table | Holds | Note |
|---|---|---|
| `item_alias` (+ supplier/dc) | UPC/text → master, **sticky** | The brief's `item_lot_map` analogue |
| `source_artifact` | Uploaded-file lineage | |
| `normalization_run` / `normalization_run_source` | Which files fed a normalized load | Import lineage |

**Gap vs brief's `norm`:** the brief has a first-class **`lot`**, **`attribute_def`** (a real taxonomy), and **`lot_attribute`** (decomposition, so you can regroup "all organic" without re-mapping). The code resolves items to lots/master entities but **does not decompose attributes into a queryable taxonomy.** Eduardo deferred the taxonomy design to the brief ("E7 — defer to zip").

---

## Layer 3 — `cyc` equivalent: cycle structure (BUILT)

The keystone, declared at setup.

| Table | Holds | Note |
|---|---|---|
| `rfp_cycle` | Commodity, objective, dates, status (12 states) | Optional subcommodity; scope-consistency trigger |
| `cycle_round` | R1..Rn, round status | Composite FK; forward-only status machine (8 states) |
| `cycle_tf` | Active timeframes | **Dimension, not a fork** |
| `cycle_lot` | Lot grouping | |
| `cycle_item_scope` / `cycle_lot_item` | In-scope items, lot×item combos | |
| `cycle_projected_volume` | Demand at DC × lot × item | What the scenario engine must cover |
| `cycle_invited_supplier` | Composite PK (cycle, supplier) | The denominator for submitted-vs-missing |

**Gap vs brief's `cyc`:** the brief declares the **pricing basis and the five safeties at the cycle** (`cycle_term` for PBA/program terms). The code has no `cycle_term` and declares pricing at the commercial layer (ADR-007). No per-cycle pricing-model / safety declaration exists at kickoff.

---

## Layer 4 — `bid` equivalent: intake, eligibility, capacity (BUILT)

Multiple intake templates collapse to one destination grain.

| Table | Holds | Note |
|---|---|---|
| `bid_submission` | One supplier's submission for a round | 8 top-level statuses |
| `bid_line` | One priced line at the locked grain | 7 line statuses, 9 incomplete reasons, 5 leverage reasons; price basis ALL_IN / FOB_PLUS_COMPONENTS / FOB_ONLY_PREVIEW |
| `supplier_capability` | Can this supplier serve this scope? | Only CONFIRMED_CAPABLE is awardable |
| `eligibility_exception` | Recorded overrides | |
| `capacity_statement` / `capacity_constraint` | How much a supplier can supply | 5 scopes: CELL / DC_TF / LOT_TF / SUPPLIER_TF / TOTAL_CYCLE |
| `eligibility_result` / `eligibility_gate_result` | Gate outcomes | 7 gates, 4 statuses, 12 reason codes |
| `landed_cost_result` | Standardized cost per supplier×cell | 5 modes, 8 blocking reasons |

**The double-subtraction guard** lives in the commercial layer (Layer 7-commercial), not here. `grow_origin` vs `ship_from_zip` — **honesty note:** the brief's two-origins-separate principle is *agreed in spirit*, but the code does **not** have a `zip_centroid`/distance calc, and origin columns are not the two-field model the brief specifies. This is a build item, not a done item.

---

## Layer 5 — `eng` equivalent: runs, scores, scenarios (BUILT — single-winner)

| Table | Holds | Note |
|---|---|---|
| `calculation_run` | One sealed run + hashed manifests | 6 run types, 5 statuses, execution-contract marker. A correction is a NEW run. |
| `calculation_run_input` | Frozen inputs to a run | 9 input types; required-inputs-by-contract |
| `metric_definition_version` / `engine_release` / `scenario_config_version` | Version pins | Which metric/engine/config a run used |
| `scenario_a_result` | Scenario A header | Solve status, total cost, feasibility |
| `scenario_a_cell_assignment` | Which supplier won each cell | **One supplier per cell — single-winner** |
| `scenario_a_line_detail` | Per cell×item cost detail | Cases, landed cost/case, line spend; CHECK all > 0 |
| `scenario_a_capacity_usage` | One row per applicable constraint | Limit, used, remaining, satisfied; CHECK remaining = limit − assigned |

**Gap vs brief's `eng` — the big one.** The brief's `bid_score` (5 banded factors → rec_score, eligibility + gate_flags) **does not exist** — there is no scoring model, only an exact min-cost solver. The brief's `scenario` (lenses **A–G**) is **only A** here. The brief's `scenario_award` is **split** (one row per awarded supplier per cell, each with `volume_share`); the code's `scenario_a_cell_assignment` is **single-winner with no volume_share**. This layer is where the two largest changes land.

---

## Layer 6 — `awd` equivalent: selected awards, freeze/layer, outputs (MOSTLY NOT BUILT)

| Table | Status | Note |
|---|---|---|
| (no `award` table) | **NOT BUILT** | Selection today = a scenario choice + a `decision_note`. No frozen award object. |
| (no `award_layer`) | **NOT BUILT** | Freeze-and-layer of awarded terms does not exist. |
| (no `signoff`) | **NOT BUILT** | No out-gate approval object. |
| (no `generated_document`) | **NOT BUILT** | Output Factory / booking guide / letters are PARKED. |

**Gap vs brief's `awd`:** essentially the whole layer. The code asserts **no final award**, has **no freeze**, and **generates no documents**. The brief makes "Sent" a governance gate and generates the booking guide, sign-off deck, and letters from records. This is the outward-facing half of the brief, and it is the thinnest part of the code.

---

## Layer 7 — `perf` equivalent: history, fiscal calendar, pricing (BUILT — partial)

The code splits what the brief groups as `perf`, and adds a commercial pricing layer the brief folds into `bid`.

**Historical Awarded Cost (the brief's `itrade_receipt` analogue):**

| Table | Holds | Note |
|---|---|---|
| `historical_award_assignment` (PARENT) | Last cycle's awards: cycle × DC × item × supplier × window | Volume lives **only** on the parent; tags (NAT/LOCAL, CONV/ORG), incumbent flag |
| `historical_awarded_price_basis` (CHILD) | One row per routing basis (FOB/DLVD/XDOCK/CBS_FREIGHT) | Price never volume; spend computed at read time; no spend column |
| `historical_awarded_cost_ingestion_issue` | 8 importer-validation codes, persisted | severity HARD_REJECT / WARN_ACCEPT / DEDUPE |

**Fiscal calendar (the brief's `fiscal_calendar`):**

| Table | Holds | Note |
|---|---|---|
| `fiscal_date_conversion` | One row per calendar_date → FY/Q/period/week | A **loaded lookup, never a formula**. 2020–2037 validated CLEAN but not seeded. |

**Volume + Scope Prep (the brief's volume tables):**

| Table | Holds | Note |
|---|---|---|
| `volume_scope_source_row` | Every governed volume/capacity input row | DEMAND vs CAPACITY; CHECK forbids capacity-as-active-demand |
| `normalized_volume_scope` | Validated demand-only output | One row per single fiscal period; no allocation math ever |
| `volume_scope_override` / `volume_scope_prep_issue` | Overrides with lineage; ~24 issue codes | |

**Commercial pricing (the brief folds pricing into `bid`; the code makes it a layer):**

10 `commercial_*` tables — `commercial_pricing_model` (6 models, 4 lanes, three-value rule), `commercial_price_component` (20 component types), `commercial_market_reference` (reset cadence + trigger band + collar — **stored, never executed**), `commercial_pricing_window`, `commercial_market_kickoff_snapshot`, `commercial_qdp`, `commercial_lot_market_delta`, `commercial_market_proxy_basis`, `commercial_pricing_formula_audit` (replayable), `commercial_pricing_validation_issue` (18 codes).

**Gap vs brief's `perf`:** the code has **historical cost** but **no supplier scorecard** (the brief derives two frozen snapshots, kickoff + sign-off, from the one feed) and **no KCMS movement feed**. The five pricing **safeties** are stored as inert parameters — the engine never fires them.

---

## Layer 8 — `audit` equivalent: the event log (SCAFFOLD)

| Table | Status | Note |
|---|---|---|
| `audit_event` | **SCAFFOLD** | Hash-chained log (event type, entity, actor, before/after hashes, prev/this event hash). Population + write-only enforcement deferred. |
| `decision_note` | **BUILT** | Append-only free-text note bindable to cycle/round/scenario/supplier/DC/lot/TF |

**Gap vs brief's `audit`:** the brief's `event_log` is *the* line between a system of record and a pile of generators, and is meant to be live. Here it is a scaffold; the **functional** audit trail today is the calculation-run ledger (Layer 5) plus append-only round bookkeeping, which together already answer "open last cycle." A `decision_note` carries human commentary; a structured **NoteThread** (8-scope) is CONTRACT-ONLY.

---

## What this model already fixes (agrees with brief)

| Brief gap | Fixed in code by |
|---|---|
| String-concat match key | The alias layer (sticky resolution) |
| Stateless, no history | The whole persistent store + calc-run ledger + historical cost |
| Live-formula fragility / silent overwrite | Immutable `calculation_run` + DB guard listeners |
| Timeframe forked per workbook | `cycle_tf` dimension + Volume+Scope Prep |
| Cost double-subtraction | Commercial-layer validation |
| Demand polluted by capacity | `ck_vsp_capacity_never_active_demand` CHECK |

## What this model does NOT yet fix (the gap)

| Brief requirement | As-built reality |
|---|---|
| Split awards (`volume_share`, multi-supplier cell) | Single-winner only (ADR-003) |
| Decision-support scoring (5 banded factors) | Exact min-cost solver only |
| Seven scenario lenses A–G | Only Scenario A |
| Awards: select → freeze → layer | No award object, no freeze, no layer |
| Generated outputs (booking guide, deck, letters) | None — Output Factory PARKED |
| Supplier scorecard (two frozen snapshots) | Not built |
| KCMS movement feed | Not built |
| Two origins + zip-centroid distance | Principle agreed; no distance calc, no zip_centroid |
| Lot attribute taxonomy | Lots/items resolved, no attribute decomposition |
| Pricing model + five safeties at kickoff | Pricing at commercial layer; safeties inert |
| "Sent" governance gate | Drafts only; no SENT state |

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-18 | Session | As-built data model across 63 tables, mapped to the brief's 8 layers for diffing. |
