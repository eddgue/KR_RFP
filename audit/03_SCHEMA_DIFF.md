---
doc: Audit — Schema Diff
id: AUDIT-003
version: 1.0
status: Final
created: 2026-06-18
depends_on: AUDIT-002
audience: Backend dev, Architect, DBA
---

# Audit — Schema Diff (63 vs 36 tables)

Table-level diff of `specs/original-engine/BUILD_03_schema.sql` (**AS-BUILT, 63 tables**) against `specs/rfp-engine/BUILD_03_schema.sql` (**BRIEF, 36 tables**), organized by the shared eight-layer model. Use this as the crosswalk when authoring migrations.

Legend: **=** present and equivalent · **≈** present but materially different (note explains) · **＋** present here, absent in the other · **∅** absent.

---

## 0. Counts at a glance

| | AS-BUILT | BRIEF |
|---|---:|---:|
| Tables | **63** | **36** |
| CHECK clauses | **67** | 14 |
| Composite/identity FKs (multi-column) | **46** | **0** |
| Partial unique indexes | 5 | 0 |
| Native enum types / CHECK-enforced enums | ~55 enums | ~10 inline CHECKs |
| Physical naming | flat (`rfp_cycle`, `scenario_a_*`) | Postgres schemas (`cyc.cycle`, `eng.*`) |
| DB target actually exercised | SQLite (demo) despite PG header | PostgreSQL 15+ (unbuilt) |

The 27-table surplus in the AS-BUILT is **not** broader capability — it is **depth in the middle** (calc-run governance, eligibility, landed cost, commercial pricing, volume-scope prep, round lifecycle) plus identity machinery. The BRIEF's 36 are **broader but shallower**, and include the entire `awd`/scorecard surface the AS-BUILT lacks.

---

## 1. `ref` — reference / dimensions

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `ref.commodity` | `commodity_master_db` | = | |
| `ref.subcommodity` | `subcommodity_master` | ≈ | as-built lacks `is_organic`/`pack_type` parsed hints; brief lacks the composite `(subcom,commodity)` identity FK |
| `ref.dc` | `dc_master_db` | = | |
| `ref.supplier` | `supplier_master` | = | both auto-upsert; as-built also keeps an `aliases` text blob *and* a typed alias table |
| `ref.supplier_alias` | `supplier_alias` | ≈ | as-built: typed kinds, partial-unique-active index, deactivation lineage (richer) |
| `ref.item` | `item_master` | ≈ | as-built carries composite `(item,commodity)`/`(item,subcom)` identity pairs |
| `ref.item_alias` | `item_alias` | ≈ | as-built: typed, commodity/subcom-scoped partial unique index (richer) |
| `ref.fiscal_calendar` | `fiscal_date_conversion` | ≈ | both loaded lookups to ~2037; as-built has quarter/period/week labels + range CHECKs; brief is leaner |
| `ref.zip_centroid` | ∅ | ＋ | **GAP G7** — as-built has no centroid table, hence no distance calc |
| ∅ | `dc_alias` | ＋ | as-built resolves DC text too (brief folds DC into supplier-style aliasing) |
| ∅ | `loading_location` | ＋ | as-built models supplier shipping points as a table (brief uses `ship_from_zip` text) |
| ∅ | `master_data_quarantine` | ＋ | **KEEP** — as-built's "never guess" queue (domains + rejection reasons) |
| ∅ (net-new) | ∅ | — | **`client`/tenant** — named in Session 1, modeled by neither |

---

## 2. `norm` — normalization / lot store

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `norm.lot` | `cycle_lot` (≈) | ≈ | as-built's lot is **cycle-scoped** (`cycle_lot`), brief's is a **persistent cross-cycle** `norm.lot`. Different lifetime — reconcile. |
| `norm.attribute_def` | ∅ | ＋ | **GAP G8** — no taxonomy in as-built |
| `norm.lot_attribute` | ∅ | ＋ | **GAP G8** |
| `norm.item_lot_map` | (alias system) | ≈ | brief: explicit sticky UPC→lot, proposed→confirmed. as-built: the typed alias layer is the analogue but maps to master entities, not a persistent lot taxonomy |
| ∅ | `source_artifact` | ＋ | as-built: file lineage with sha256, provenance identity quads (**KEEP**) |
| ∅ | `normalization_run` / `normalization_run_source` | ＋ | as-built: which files fed a normalized load |

**Key reconciliation:** the as-built treats the lot as **cycle-local** (`cycle_lot` + `cycle_lot_item`, one lot per item per cycle), while the brief treats it as a **persistent, cross-cycle** normalization asset (`norm.lot` + sticky `item_lot_map`). The brief's stance is the one that delivers "next cycle the same UPC arrives already mapped." Adopt the brief's persistent lot, keep the as-built's per-cycle scoping tables as the in-cycle view over it.

---

## 3. `cyc` — cycle / setup (the keystone)

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `cyc.cycle` | `rfp_cycle` | ≈ | **GAP G5** — both thin vs the real kickoff. as-built adds `why_now`, `target_savings_amt`, `round_count` CHECK 2–6; brief adds `pricing_basis`, `objective`, `horizon` |
| `cyc.cycle_timeframe` | `cycle_tf` | = | both: timeframe as a dimension (agree) |
| `cyc.cycle_round` | `cycle_round` | ≈ | as-built: forward-only `round_status` enum + due-date columns; brief: `bid_type` + `is_final` flags |
| `cyc.cycle_dc` | (DC scope via `cycle_item_scope`) | ≈ | brief has explicit `cycle_dc`; as-built scopes items, not DCs directly |
| `cyc.cycle_lot` | `cycle_lot` | ≈ | see §2 lifetime note |
| `cyc.cycle_term` (PBA) | ∅ | ＋ | **GAP G5** — as-built has **no cycle-level PBA term table**; PBA lives only in onion bid intake |
| ∅ | `cycle_item_scope` | ＋ | as-built: explicit in/out scope with rationale |
| ∅ | `cycle_lot_item` | ＋ | as-built: lot×item combos, one lot per item per cycle |
| ∅ | `cycle_projected_volume` | ＋ | as-built: demand at DC×item×tf (brief uses `bid.volume_requirement`) |
| ∅ | `cycle_invited_supplier` | ＋ | as-built: the submitted-vs-missing denominator (**KEEP**) |
| ∅ (net-new, G5) | ∅ | — | `cycle_objective`, `cycle_pricing`+`cycle_safety`, `cycle_commercial_term` (working capital/KPM), `cycle_rfi_question`, `cycle_timeline_event`, `cycle_narrative` — modeled by neither |

---

## 4. `bid` — intake, eligibility, capacity, landed cost

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `bid.bid` | `bid_line` (+ `bid_submission`) | ≈ | as-built splits submission header from priced line; carries identity quads, `is_scoreable`/`is_awardable`, leverage signals (richer). **Brief's `grow_origin`/`ship_from_zip`/`distance_miles` are absent in as-built (G7).** |
| `bid.bid_price` | (columns on `bid_line` + `landed_cost_result`) | ≈ | as-built: components on the line *plus* a 5-mode `landed_cost_result` (**KEEP, richer**). Brief's `no_double_discount` CHECK ≈ as-built's reconciliation modes |
| `bid.bid_index_component` | (commercial layer) | ≈ | brief: simple key/value; as-built: full commercial index modeling (§7) |
| `bid.volume_requirement` | `cycle_projected_volume` (≈) + VSP | ≈ | as-built models demand via projected volume + normalized volume scope |
| `bid.volume_limit` | `capacity_statement` + `capacity_constraint` | ≈ | **as-built far richer** — 5 capacity scopes, scope/field-match CHECK. Brief's `volume_limit` **has no PK** (`[D-3]`). **KEEP as-built.** |
| ∅ | `supplier_capability` | ＋ | as-built: CONFIRMED_CAPABLE gate (only capable is awardable) |
| ∅ | `eligibility_result` | ＋ | **KEEP** — 7 gates, 12 reason codes |
| ∅ | `eligibility_gate_result` | ＋ | **KEEP** — per-gate outcome rows |
| ∅ | `eligibility_exception` | ＋ | **KEEP** — recorded overrides |
| ∅ | `landed_cost_result` | ＋ | **KEEP** — 5 modes, 8 blocking reasons (richer than brief's `bid_price`) |

---

## 5. `eng` — runs, scores, scenarios

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `eng.analysis_run` | `calculation_run` | ≈ | **as-built far richer** — hashed manifests, execution-contract, version pins, identity triples (**KEEP**) |
| ∅ | `calculation_run_input` | ＋ | **KEEP** — frozen inputs, one-per-type, hash |
| ∅ | `metric_definition_version` | ＋ | **KEEP** — formula version pin |
| ∅ | `engine_release` | ＋ | **KEEP** — engine version pin (git sha) |
| ∅ | `scenario_config_version` | ＋ | **KEEP** — config version pin |
| `eng.bid_score` | ∅ | ＋ | **GAP G2 (Critical)** — no scoring model in as-built |
| `eng.scenario` (A–G) | `scenario_a_result` | ≈ | **GAP G2** — as-built has **only Scenario A** (min-cost), brief has 7 lenses |
| `eng.scenario_award` (split) | `scenario_a_cell_assignment` | ≈ | **GAP G1 (Critical)** — as-built `UNIQUE(run,dc,lot,tf)` single-winner, no `volume_share` |
| ∅ | `scenario_a_line_detail` | ＋ | as-built: per-item cost detail under a cell |
| ∅ | `scenario_a_capacity_usage` | ＋ | as-built: capacity arithmetic CHECK (remaining = limit − assigned) |
| ∅ | `round_analysis_snapshot` | ＋ | as-built: one canonical run per round (anchors "open last cycle") |

**The crux of the build lives in this layer.** The as-built has a *deeper run/governance apparatus* but the *wrong and narrower brain* (single min-cost scenario, single-winner cells). The brief has the *right and broader brain* (scoring + 7 lenses + splits) but a *thinner run model*. Target = brief's `bid_score`/`scenario`/`scenario_award` semantics **on** the as-built's calc-run governance.

---

## 6. `awd` — selected awards, freeze/layer, outputs

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `awd.award` | ∅ | ＋ | **GAP G3 (Critical)** — no award object; selection = scenario + `decision_note` |
| `awd.award_layer` | ∅ | ＋ | **GAP G3** — no freeze-and-layer |
| `awd.signoff` | ∅ | ＋ | **GAP G3** — no out-gate object |
| `awd.generated_document` | ∅ | ＋ | **GAP G3** — Output Factory PARKED |

**The entire layer is greenfield in the as-built.** This is the largest single build by surface area and the brief specifies it well.

---

## 7. `perf` — history, scorecard, fiscal, pricing

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `perf.itrade_receipt` | `historical_award_assignment` (+ `_price_basis`) | ≈ | **GAP G6** — as-built has **awarded cost**, not receipt-level feed. Different grain. |
| ∅ | `historical_awarded_cost_ingestion_issue` | ＋ | as-built: persisted importer issues (**KEEP** the discipline) |
| `perf.kcms_movement` | ∅ | ＋ | **GAP G6** — no scan feed |
| `perf.supplier_scorecard` | ∅ | ＋ | **GAP G6** — no scorecard (two-snapshot derivation) |
| (fiscal in `ref`) | `fiscal_date_conversion` | ≈ | as-built puts fiscal in its own table (§1) |
| (volume in `bid`) | `volume_scope_source_row` | ＋ | **KEEP** — demand/capacity by CHECK |
| | `normalized_volume_scope` | ＋ | **KEEP** — validated demand-only output |
| | `volume_scope_override` | ＋ | **KEEP** — overrides with lineage |
| | `volume_scope_prep_issue` | ＋ | **KEEP** — ~24 issue codes |
| **Commercial pricing (10 tables):** | | | **brief folds pricing into `bid`; as-built makes it a layer** |
| (in `bid.bid_price`) | `commercial_pricing_model` | ＋ | three-value raw/derived/normalized rule (**KEEP, re-point to kickoff — G4**) |
| | `commercial_price_component` | ＋ | 20 component types |
| | `commercial_market_reference` | ＋ | **holds the safety parameters (reset/trigger/collar) — stored, never fired (G4)** |
| | `commercial_pricing_window` | ＋ | |
| | `commercial_market_kickoff_snapshot` | ＋ | |
| | `commercial_qdp` | ＋ | quantity-discount pricing |
| | `commercial_lot_market_delta` | ＋ | |
| | `commercial_market_proxy_basis` | ＋ | 5-level fallback proxy |
| | `commercial_pricing_formula_audit` | ＋ | **replayable audit (KEEP)** |
| | `commercial_pricing_validation_issue` | ＋ | 18 codes |

---

## 8. `audit` — event log

| BRIEF | AS-BUILT | State | Note |
|---|---|:---:|---|
| `audit.event_log` (live) | `audit_event` (SCAFFOLD) | ≈ | **GAP G11** — as-built's hash-chain design is **stronger** but unpopulated; make it live |
| (commentary via events) | `decision_note` | ＋ | as-built: append-only free-text note, 8-scope bindable (**KEEP**) |
| ∅ | `round_supplier_participation` | ＋ | as-built round lifecycle (**KEEP**) |
| ∅ | `round_feedback_issued` | ＋ | as-built: drafted-only feedback (**GAP G9** — add SENT) |
| ∅ | `round_field_reduction_decision` | ＋ | as-built: next-round invitation list |

---

## 9. Migration implications (for the target spec)

1. **The as-built schema is the migration baseline** (Decision D1), but must first be **regenerated/validated on real PostgreSQL** and have the SQLite-isms and the no-op CHECK removed (`[D-6]`).
2. **Additive, low-risk migrations** (no existing-data conflict): `norm.attribute_def`/`lot_attribute`; `ref.zip_centroid` + distance columns on the bid line; `perf.itrade_receipt`/`kcms_movement`/`supplier_scorecard`; the whole `awd.*` layer; `eng.bid_score`; the kickoff satellite tables (G5); `client`/tenant + RBAC.
3. **Breaking migrations** (touch the grain — sequence carefully, ship together per Ed's direction): relax `scenario_a_cell_assignment`'s single-cell uniqueness and add `volume_share` (G1); generalize `scenario_a_*` → `scenario`/`scenario_award` (G2). These two are the only genuinely destructive changes; everything else is additive.
4. **Re-point, don't rebuild, the commercial layer** (G4): keep the 10 tables, source their parameters from the kickoff declaration, and add the safety-execution path.
5. **Lot lifetime change** (§2): introduce persistent `norm.lot` and back-fill `cycle_lot` as a view/scope over it. Medium-risk; do it before normalization persistence matters (Phase B).
