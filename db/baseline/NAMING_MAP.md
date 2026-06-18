# NAMING_MAP.md — as-built (flat) → target (schema-qualified) crosswalk

The canonical decision (Platform & Data `PLAN.md` §3, audit `01 [X-3]`/`03 §3`): **schema-qualified,
brief-style names are canonical** (`cyc.cycle`, `eng.scenario_award`, `perf.itrade_receipt`). The
eight logical layers become real PostgreSQL schemas (`ref norm cyc bid eng awd perf audit`) — grants,
`search_path`, RLS, and the "open last cycle" joins all read better. The as-built's flat physical
names (`rfp_cycle`, `scenario_a_*`) are the **crosswalk source, not the target**.

## The rule

1. **Schema placement.** Map each as-built table to its layer (via `audit/03`) → that becomes its schema.
2. **Strip prefix/suffix noise.** `rfp_cycle` → `cyc.cycle`; `*_master`/`*_master_db` → drop the suffix
   (`dc_master_db` → `ref.dc`, `commodity_master_db` → `ref.commodity`).
3. **Flatten the `_a_` lens.** `scenario_a_*` → `eng.scenario*`, with the single-scenario `_a_` lens
   replaced by a `scenario_code` column (carried by the G2 breaking migration).
4. **Tables + schema canonicalize; columns do NOT.** Adopted tables **keep their as-built column
   names** (renaming is needless churn and breaks the KEEP rigor mapping). Only the **table** name and
   **schema** placement change.
5. **PK convention.** New tables standardize on `id`; adopted tables retain their `*_id` text-UUID PKs
   for composite-FK fidelity (documented in `schema.sql` / `CROSSWALK.md`).

## Key mappings

| As-built (flat) | Target (schema-qualified) | Disp. | Note |
|---|---|:--:|---|
| `rfp_cycle` | `cyc.cycle` | CLEAN | merge brief's pricing_basis/objective/horizon onto why_now/target_savings/round_count |
| `cycle_tf` | `cyc.cycle_timeframe` | ADOPT | keep `(tf_id, cycle_id)` composite identity |
| `cycle_round` | `cyc.cycle_round` | ADOPT | forward-only `round_status` |
| `cycle_item_scope` | `cyc.cycle_item_scope` | ADOPT | scope-with-rationale |
| `cycle_invited_supplier` | `cyc.cycle_invited_supplier` | ADOPT | submitted-vs-missing denominator |
| `commodity_master_db` | `ref.commodity` | ADOPT | drop `_master_db` |
| `dc_master_db` | `ref.dc` | ADOPT | drop `_master_db` |
| `supplier_master` | `ref.supplier` | ADOPT | drop `_master` |
| `item_master` | `ref.item` | ADOPT | drop `_master` |
| `subcommodity_master` | `ref.subcommodity` | CLEAN | add is_organic/pack_type hints; keep `(subcom,commodity)` FK |
| `loading_location` | `ref.loading_location` | ADOPT | composite `(location_id, supplier_id)` |
| `fiscal_date_conversion` | `ref.fiscal_calendar` | CLEAN | seed 2020–2037 lookup |
| `supplier_alias` / `item_alias` / `dc_alias` | `ref.supplier_alias` / `ref.item_alias` / `ref.dc_alias` | ADOPT | typed kinds, partial-unique-active |
| `master_data_quarantine` | `ref.master_data_quarantine` | ADOPT | quarantine queue |
| `cycle_lot` | `cyc.cycle_lot` | CLEAN | becomes scope over persistent `norm.lot` (G8) |
| `cycle_lot_item` | `cyc.cycle_lot_item` | CLEAN | cycle-scoped projection of `norm.item_lot_map` (G8) |
| `source_artifact` | `norm.source_artifact` | ADOPT | sha256 lineage |
| `normalization_run` / `normalization_run_source` | `norm.normalization_run` / `norm.normalization_run_source` | ADOPT | provenance quads |
| `bid_submission` | `bid.bid_submission` | ADOPT | header, identity quad |
| `bid_line` | `bid.bid_line` | CLEAN | add grow_origin/ship_from_zip/distance_miles (G7) |
| `landed_cost_result` | `bid.landed_cost_result` | ADOPT | 5 modes, 8 blocking reasons (KEEP #3) |
| `eligibility_result` / `_gate_result` / `_exception` | `bid.eligibility_result` / `bid.eligibility_gate_result` / `bid.eligibility_exception` | ADOPT | 7 gates, 12 codes (KEEP #4) |
| `supplier_capability` / `capacity_statement` / `capacity_constraint` | `bid.supplier_capability` / `bid.capacity_statement` / `bid.capacity_constraint` | ADOPT | 5 capacity scopes |
| `volume_scope_source_row` / `normalized_volume_scope` / `volume_scope_override` / `_prep_issue` | `bid.*` | ADOPT | demand≠capacity CHECK, VSP (KEEP #5) |
| `calculation_run` / `calculation_run_input` | `eng.calculation_run` / `eng.calculation_run_input` | ADOPT | sealed run spine (KEEP #2) |
| `metric_definition_version` / `engine_release` / `scenario_config_version` | `eng.*` | ADOPT | hashed manifests, version pins |
| `round_analysis_snapshot` | `eng.round_analysis_snapshot` | ADOPT | one canonical run/round — anchors "open last cycle" |
| `scenario_a_result` | `eng.scenario` | CLEAN→BREAK | generalize via `scenario_code` (G2); add `volume_share` (G1) |
| `scenario_a_cell_assignment` | `eng.scenario_award` | CLEAN→BREAK | re-grain to `(run, dc, lot, tf, supplier)` (G1) |
| `scenario_a_line_detail` | `eng.scenario_line_detail` | CLEAN | line under generalized scenario |
| `scenario_a_capacity_usage` | `eng.scenario_capacity_usage` | CLEAN | capacity-arithmetic CHECK summed across split suppliers (G1) |
| — (net-new) | `eng.bid_score` | ADD | 5 banded factors → composite + eligible + gate_flags |
| `historical_award_assignment` (+`_price_basis`, `_ingestion_issue`) | `perf.historical_award_assignment` (derivation) + `perf.itrade_receipt` | CLEAN/ADD | becomes a derivation over `perf.itrade_receipt` (G6) |
| — (net-new) | `perf.kcms_movement` | ADD | scan/margin, distinct feed |
| — (net-new) | `perf.supplier_scorecard` | ADD | two frozen snapshots (kickoff/signoff) |
| `commercial_*` (10 tables) | `perf.commercial_*` | ADOPT | re-point parameters to kickoff (G4) |
| `audit_event` | `audit.event_log` | ADOPT→FINISH | keep hash-chain; make live + write-only (G11) |
| `decision_note` | `audit.decision_note` | ADOPT | |
| `round_supplier_participation` / `round_feedback_issued` / `round_field_reduction_decision` | `audit.*` | ADOPT | round lifecycle; add `sent` state (G9) |
| — (net-new) | `awd.award` / `awd.award_layer` / `awd.signoff` / `awd.generated_document` | ADD | whole greenfield layer (G3) |
| — (net-new) | `ref.client` | ADD | tenant root; `client_id` FK columns (Security owns RLS policy) |
| — (net-new) | `ref.zip_centroid` | ADD | G7/E-12 distance |
| — (net-new) | `norm.lot` / `norm.attribute_def` / `norm.lot_attribute` / `norm.item_lot_map` | ADD | persistent-lot taxonomy (G8/E-11) |

> This is the **key-mappings seed**. The complete physical→canonical table for all 63 as-built tables
> is published as `db/baseline/CROSSWALK.md` at M0 (Platform & Data `PLAN.md` §3 step 5), so no read
> re-litigates a name.
