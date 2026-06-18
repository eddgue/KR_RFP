---
doc: Platform & Data Squad Plan
id: SQUAD-PLATDATA-001
version: 1.0
status: Draft
created: 2026-06-18
owner: Platform & Data squad lead
depends_on: audit/03_SCHEMA_DIFF, audit/02_GAP_ANALYSIS, audit/01_DOCUMENT_AUDIT, ADR-0001, project/04_PROGRAM_BACKLOG, project/05_MILESTONE_ROADMAP
epics: E-01, E-05, E-06, E-08, E-09, E-10, E-11, E-12, E-14(support), E-20(support), E-21(support)
---

# Platform & Data — Squad Plan

We own the governed PostgreSQL system of record: the clean baseline, the Alembic chain,
naming canonicalization, the data feeds (iTrade / KCMS / scorecard), and the persistent-lot
change. We re-express the as-built's rigor cleanly (ADR-0001 clean-room), keep the seven KEEP
capabilities, and ship exactly two breaking migrations (G1, G2) isolated behind a flag.
Everything else is additive. We do **not** own the engine brain (E-18/E-19/E-20 solver logic),
the awd output generators, or RBAC policy — we provide the tables those squads write to.

---

## 1. Baseline assessment

Keyed to the `audit/03` crosswalk. Three dispositions: **ADOPT** (carry the as-built table
forward verbatim, only re-expressed as clean PG), **CLEAN** (carry forward but fix a defect),
**ADD** (net-new, from the brief or net-new enterprise layer).

| Layer | As-built table(s) | Disposition | What we do |
|---|---|:--:|---|
| ref | `commodity_master_db`, `dc_master_db`, `supplier_master`, `item_master`, `loading_location` | ADOPT | rename to `ref.commodity/dc/supplier/item/loading_location`; keep composite identity pairs |
| ref | `subcommodity_master` | CLEAN | add `is_organic`/`pack_type` parsed-hint columns (brief), keep the `(subcom,commodity)` identity FK |
| ref | `supplier_alias`/`item_alias`/`dc_alias`, `master_data_quarantine` | ADOPT (KEEP #6) | typed kinds, partial-unique-active index, deactivation lineage, quarantine queue — verbatim |
| ref | `fiscal_date_conversion` | CLEAN | → `ref.fiscal_calendar`; **seed** the 2020–2037 lookup (today loaded-but-unseeded) |
| ref | — | ADD | `ref.zip_centroid` (G7/E-12); `client`/tenant FK column on cycle (net-new, Security owns policy) |
| norm | `cycle_lot`, `cycle_lot_item`, alias system | CLEAN | persistent `norm.lot` becomes the asset; `cyc.cycle_lot` back-fills as scope (§5, G8) |
| norm | — | ADD | `norm.attribute_def` + `norm.lot_attribute` taxonomy; `norm.item_lot_map` sticky propose→confirm (G8/E-11) |
| norm | `source_artifact`, `normalization_run(_source)` | ADOPT (KEEP) | sha256 lineage + provenance identity quads — verbatim |
| cyc | `rfp_cycle` | CLEAN | → `cyc.cycle`; merge brief's `pricing_basis`/`objective`/`horizon` onto as-built's `why_now`/`target_savings_amt`/`round_count` CHECK 2–6 |
| cyc | `cycle_tf`, `cycle_round`, `cycle_item_scope`, `cycle_projected_volume`, `cycle_invited_supplier` | ADOPT (KEEP) | keep forward-only `round_status`, scope-with-rationale, the submitted-vs-missing denominator |
| cyc | — | ADD (G5/E-14) | kickoff satellites — `cyc.cycle_term`(PBA), `cycle_objective`, `cycle_pricing`+`cycle_safety`, `cycle_commercial_term`, `cycle_rfi_question`, `cycle_timeline_event`, `cycle_narrative` |
| bid | `bid_submission` + `bid_line` | ADOPT + CLEAN | keep the split header/line, identity quads, `is_scoreable`/`is_awardable`; ADD `grow_origin`/`ship_from_zip`/`distance_miles` (G7) |
| bid | `landed_cost_result` (5 mode) | ADOPT (KEEP #3) | 5 modes, 8 blocking reasons, awardable-shape CHECKs — verbatim |
| bid | `eligibility_result`/`_gate_result`/`_exception`, `supplier_capability`, `capacity_statement`/`_constraint` | ADOPT (KEEP #4) | 7 gates, 12 codes, 5 capacity scopes — verbatim |
| bid | `volume_scope_source_row`, `normalized_volume_scope`, `volume_scope_override`/`_prep_issue` | ADOPT (KEEP #5) | demand≠capacity CHECK + VSP maturity — verbatim |
| eng | `calculation_run`, `calculation_run_input`, `metric_definition_version`, `engine_release`, `scenario_config_version` | ADOPT (KEEP #2) | sealed run spine, hashed manifests, version pins — verbatim |
| eng | `scenario_a_result`, `scenario_a_cell_assignment`, `scenario_a_line_detail`, `scenario_a_capacity_usage` | CLEAN→BREAK | generalize to `eng.scenario`/`scenario_award` (G2) + relax single-winner + add `volume_share` (G1). §2 M-G1/M-G2 |
| eng | `round_analysis_snapshot` | ADOPT (KEEP) | one canonical run per round — anchors "open last cycle" |
| eng | — | ADD | `eng.bid_score` (5 banded factors → composite + eligible + gate_flags) — Engine writes, we model (G2/E-18) |
| awd | — | ADD (G3) | whole layer greenfield: `awd.award`/`award_layer`/`signoff`/`generated_document` — Engine/Experience own logic, we model grain + freeze constraints |
| perf | `historical_award_assignment`(+`_price_basis`, `_ingestion_issue`) | CLEAN | becomes a **derivation** over the new `perf.itrade_receipt`, not the source (G6/§4) |
| perf | — | ADD (G6) | `perf.itrade_receipt` (receipt grain), `perf.kcms_movement`, `perf.supplier_scorecard` (two frozen snapshots) |
| perf | `commercial_*` (10 tables) | ADOPT (KEEP) | re-point parameters to kickoff (G4 — Engine drives the safety execution; we keep storage + formula audit) |
| audit | `audit_event` (hash-chain), `decision_note` | ADOPT→FINISH | keep the stronger hash-chain design; make it live + write-only (G11/E-05, with Security) |
| audit | `round_supplier_participation`, `round_feedback_issued`, `round_field_reduction_decision` | ADOPT (KEEP) | round lifecycle; ADD `sent` state to feedback (G9, Security/Engine drive) |

**Net:** of 63 as-built tables we ADOPT ~42 near-verbatim (the KEEP spine + reference + cyc/bid/eng
governance), CLEAN ~9 (defect fixes + merges + the two G1/G2 breaks), and ADD ~18 net-new
(taxonomy, zip, three feeds, awd layer, bid_score, kickoff satellites, client/tenant).

---

## 2. Migration strategy (the Alembic chain)

Alembic on PostgreSQL 15. The baseline is **our own** clean artifact under `db/baseline/` (ADR-0001) —
not an import of the old project. Migrations are grouped by epic; the two breaking ones are isolated
and feature-flagged. **Every migration carries a roundtrip test**: `alembic upgrade head` →
`alembic downgrade base` → `upgrade head` again must be byte-identical on the schema dump, and
`alembic check` must report no model drift (closes the as-built's unverifiable "roundtrip-clean" claim, `01 [D-5]`).

**M0 — Clean baseline (E-01, Phase 0, P0).** The as-built 63 tables re-expressed as clean PG.
This is the single largest task and is **planned here, authored in Phase 0** (not in this doc).
Fixes the `[D-6]` SQLite-isms, confirmed at:
- boolean `DEFAULT 0`/`DEFAULT 1` → native `boolean DEFAULT false/true` (e.g. `bid_line.is_scoreable/is_awardable/leverage_signal_flag` line 55–61);
- comparisons `is_eligible = 0`, `constraint_satisfied = 1/0` → `is_eligible IS false`, `constraint_satisfied`;
- delete the no-op branch `length(error_log) >= 0` in `ck_calcrun_failed_has_errorlog` (line 119) — keep only `(status='FAILED' AND error_log IS NOT NULL) OR (status<>'FAILED' AND error_log IS NULL)`;
- prose-only enums → native `CREATE TYPE ... AS ENUM` (or `CHECK ... IN`), consistently;
- `VARCHAR(36)` UUID PKs reviewed — keep as text-UUID for fidelity, or move to native `uuid` (decide in Phase 0, document the call).
M0 ships the full KEEP spine and all 46 composite-identity FKs intact. Roundtrip + `alembic check` green is the E-01 exit gate.

**Additive migrations (Phase A→C, no existing-data conflict — order within phase flexible):**

| Mig | Epic | Adds |
|---|:--:|---|
| M1 audit-live | E-05 | populate triggers + write-only enforcement on `audit.event_log` (hash-chain finish) |
| M2 attribute-taxonomy | E-11 | `norm.attribute_def`, `norm.lot_attribute`, persistent `norm.lot`, `norm.item_lot_map` |
| M3 zip-distance | E-12 | `ref.zip_centroid`; `bid.bid_line.grow_origin`/`ship_from_zip`/`distance_miles` |
| M4 itrade-receipt | E-08 | `perf.itrade_receipt` + indexes; re-point `historical_award_assignment` as a derived view/materialization |
| M5 kcms | E-09 | `perf.kcms_movement` |
| M6 scorecard | E-10 | `perf.supplier_scorecard` (snapshot_type kickoff/signoff, frozen_at) |
| M7 bid-score | E-18 | `eng.bid_score` (5 factors + composite + eligible + gate_flags) |
| M8 awd-layer | E-21/22/23 | `awd.award`, `awd.award_layer`, `awd.signoff`, `awd.generated_document` + freeze constraints |
| M9 kickoff-satellites | E-14 | `cyc.cycle_term`, `cycle_objective`, `cycle_pricing`/`cycle_safety`, `cycle_commercial_term`, `cycle_rfi_question`, `cycle_timeline_event`, `cycle_narrative` |
| M10 client-tenant | E-03 | `ref.client`; tenant FK columns + (Security: RLS policy lands here) |

**Breaking migrations (Phase D, isolated, feature-flagged — ship together per Ed):**

- **M-G1 split-award (G1).** Drop `uq_scenario_a_cell_assignment_cell UNIQUE(scenario_run_id,dc_id,lot_id,tf_id)`;
  re-grain `scenario_award` to `(run, dc, lot, tf, supplier)`; add `volume_share NUMERIC(9,6)` + `cap_breach_flag`.
  Rewrite the capacity-arithmetic CHECK (`scenario_a_capacity_usage.remaining = limit − assigned`) to sum across split suppliers.
- **M-G2 scenario-generalize (G2).** Rename/restructure `scenario_a_result` → `eng.scenario` carrying a `scenario_code` (A–G lens),
  `scenario_a_cell_assignment` → `eng.scenario_award`. Scenario A becomes the "lowest-cost reference" lens, not the only solver.

Both gated by `feature.split_award` and `feature.scenario_lenses`; the auto scenario still defaults to
one supplier per DC (permit-not-force) until a per-DC/per-lot `splittable` flag is set. These touch the
solver core, so they sequence **after** Phase B's pilot proves the additive store on real data, and ship
as one increment with E-18. Roundtrip test additionally asserts a forward data-migration of any seeded
scenario rows.

---

## 3. Naming canonicalization

**Decision: schema-qualified, brief-style names are canonical** (`cyc.cycle`, `eng.scenario_award`,
`perf.itrade_receipt`). Rationale: the eight logical layers become real PostgreSQL schemas
(grants, search_path, RLS, and "open last cycle" joins all read better); resolves `01 [X-3]`/`03 §3`;
and it is the placement the audit recommends promoting (`01 §6.1`). The as-built's flat physical names
(`rfp_cycle`, `scenario_a_*`) are the crosswalk source, not the target.

**Crosswalk rule (mechanical, applied at M0):**
1. Map each as-built table to its layer via `audit/03` (the `ref/norm/cyc/bid/eng/awd/perf/audit` columns) → that schema.
2. Strip layer-prefix noise: `rfp_cycle`→`cyc.cycle`, `cycle_tf`→`cyc.cycle_timeframe`, `dc_master_db`→`ref.dc`, `*_master(_db)`→drop `_master/_db`.
3. `scenario_a_*` → `eng.scenario*` with the `_a_` lens flattened into a `scenario_code` column (the G2 break carries this).
4. `commodity_master_db`→`ref.commodity`, etc. PK columns standardize to `id` for new tables; existing `*_id` text-UUID PKs retained on adopted tables for FK fidelity (documented).
5. Publish the full physical→canonical table as `db/baseline/CROSSWALK.md` so no read re-litigates a name.

We keep the as-built's column names inside adopted tables (changing them is needless churn and breaks the KEEP rigor mapping); only **table** names and **schema** placement canonicalize.

---

## 4. Data feeds design

The three feeds inherit the as-built's importer discipline wholesale (it is a KEEP): **flag-first
validation, impossible-date-span rejection, key off codes not filenames, persisted ingestion issues**
(the `historical_awarded_cost_ingestion_issue` pattern — 8 codes, severity HARD_REJECT / WARN_ACCEPT / DEDUPE).
Each feed writes a `source_artifact` (sha256) and a `normalization_run` lineage row first; no row lands without provenance.

**iTrade receipt-grain importer (E-08, the keystone feed).** Target = `perf.itrade_receipt` (receipt grain:
`po_number`, `line_no`, `subcommodity_code`, `item_id`, `dc_no`, `supplier_id`, two origins
`ship_from_state`/`ship_from_zip`, `routing`, qty + cost components `final_price_fob`/`freight`/`total_w_freight`/`xdock`/`cogs`,
fiscal stamp `fiscal_year`/`period`/`week_of_year`, `ship_date`/`received_date`, dirty flags
`flag_zero_cost`/`flag_zero_qty`/`flag_canceled`). Rules:
- **Flag-first**: trust `flag_*` columns before re-deriving; a flagged-canceled row is excluded from cost, not silently dropped.
- **Impossible-date-span rejection**: `received_date < ship_date` (received-before-shipped) → HARD_REJECT with a persisted issue row; never auto-corrected.
- **Key off codes, not filename**: resolve `subcommodity_code`/`dc_no`/`supplier_id` via the alias+quarantine layer; the source filename is lineage only, never an identity key.
- **Template variants**: support both the **43-column** and **51-column** iTrade export shapes — detect by header signature, map to one canonical column set, persist a `template_variant` tag on the `normalization_run`; an unrecognized header HARD_REJECTs the whole file (no positional guessing).
- One feed, two jobs: receipts power both historical cost and the scorecard. `historical_award_assignment` is re-pointed to a **derivation** over `itrade_receipt` (a materialized award-grain rollup), not a separate ingest.

**KCMS importer (E-09).** Target = `perf.kcms_movement` (`subcommodity_code`, `gtin`, fiscal, `scan_units`, `margin`,
PK on the four-tuple). **A DISTINCT feed** — scan/margin, not receipts; the importer must refuse to merge KCMS rows into iTrade and vice versa (codes/grain differ).

**Supplier scorecard as a derivation (E-10).** Not an importer. `perf.supplier_scorecard` is **two frozen
snapshots per cycle** (`snapshot_type IN ('kickoff','signoff')`, `frozen_at`). All metrics
(`volume_cases`, `pct_volume`, `pct_cost`, `fill_rate`, `adjusted_fill`, `on_time`, `dc_rejection`,
`cost_per_case`, `age_at_receipt`) **derive from `perf.itrade_receipt`** at snapshot time; once frozen,
a re-derivation writes a new row, never an update (append-only discipline). The snapshot is taken at the
kickoff in-gate and again at the sign-off out-gate.

---

## 5. Persistent-lot change plan (G8 / E-11)

Today the lot is **cycle-scoped** (`cycle_lot` + `cycle_lot_item`, one lot per item per cycle). The target
is a **persistent cross-cycle** `norm.lot` so "next cycle the same UPC arrives already mapped." Plan:

1. **Introduce `norm.lot`** as the persistent asset (canonical parent product, e.g. "PREMIUM SNACKING 9OZ"), plus the taxonomy `norm.attribute_def` (universal core ORGANIC/COLOR/SIZE/PACK + per-commodity extensions) and `norm.lot_attribute` (the decomposition — so "all organic" / "all field-process" regroup without re-mapping; load-bearing for the Conv/Org sign-off split).
2. **Introduce `norm.item_lot_map`** — sticky UPC/item→lot, `status` proposed (importer, from Ed's Norm-sheet rules) → confirmed (human), one live lot per item, **persists across cycles**.
3. **Back-fill `cyc.cycle_lot` as a scope/view over `norm.lot`.** It stops being the lot's home and becomes the in-cycle selection: which persistent lots are in scope this cycle. `cycle_lot_item` likewise becomes a cycle-scoped projection of the persistent `item_lot_map`. The as-built's typed-alias + quarantine machinery is **kept underneath** (KEEP #6) — it feeds the propose step.
4. **Sequencing**: this lands in Phase B (M2), **before** the first real cycle's normalization persistence matters and before the scorecard/feeds key off lots. Medium risk: the FK from `scenario_a_*`/`bid_line` that currently points at `cycle_lot.lot_id` must re-point at `norm.lot` (with `cycle_lot` retained as the scope join). We do a one-time data migration mapping existing per-cycle lots to persistent lots (identity = canonical description + commodity), with anything ambiguous routed to quarantine, never auto-merged.

One confirmation pass per commodity at onboarding (the open item both packages carry). Raw item stays underneath; attributes + lot sit on top; nothing is overwritten.

---

## 6. Risks + sample files needed

**Risks (squad-owned).**
- **R-PD1 (High) — real iTrade shape unverified.** `01 [D-12]` notes the export was "seen, not opened live"; the 43-vs-51-col variant split is inferred. The importer's header detection cannot be finalized until we hold a real export. *Mitigation: build flag-first + HARD_REJECT-on-unknown-header so an unseen variant fails loud, not silent; finalize mapping at sample intake.*
- **R-PD2 (High) — M0 fidelity.** Re-expressing 63 tables + 46 composite FKs + 67 CHECKs cleanly risks dropping a constraint. *Mitigation: the roundtrip + `alembic check` gate, plus a constraint-count assertion (≥46 composite FKs, the de-no-op'd CHECK count) in CI.*
- **R-PD3 (Med) — persistent-lot back-fill ambiguity.** Mapping per-cycle lots to persistent lots can mis-merge. *Mitigation: quarantine-on-ambiguity, human confirm; never auto-merge.*
- **R-PD4 (Med) — G1/G2 blast radius.** The two breaks touch every read assuming one winner. *Mitigation: feature-flagged, shipped together with E-18, after the Phase-B pilot; capacity-arithmetic CHECK rewritten and tested before flag-on.*
- **R-PD5 (Med, shared) — `client`/tenant policy.** We model the column + FK; Security owns RLS. Sequencing risk if RBAC spec lags M10. *Mitigation: land the nullable tenant column early (Phase A), enforce NOT NULL + RLS when Security's spec ratifies.*
- **R-PD6 (program, shared) — `X-1`/DEP-1.** Nothing has run on real data; the ECLS + as-built migrations/tests are not yet in hand (ADR-0001 isolated-access pending). *Mitigation: M0 is non-blocking on DEP-1 (we hold the schema); the reference-intake agent verifies the 14-migration/796-test claims when access lands.*

**Sample files needed from the sponsor (via `reference/samples/`, ADR-0001 §4):**
1. **A real iTrade export with headers** — ideally one of *each* template variant (the 43-col and the 51-col) — to finalize the importer column map, the flag semantics, and the impossible-date-span rules. *Top priority; gates E-08 and the Phase-B pilot.*
2. **A real KCMS scan/margin extract** with headers — to confirm `kcms_movement` grain and that it is genuinely distinct from iTrade.
3. **A real bid workbook** — one tomato flat-sheet and one onion 9-tab hybrid — to validate the multi-template→one-grain collapse and the two-origin columns.
4. **A real kickoff doc** (the setup file) — to validate the `cyc.*` keystone satellites (G5/E-14) and the timeline that drives the rail.
5. **A `us_zip_centroids` reference** (or confirmation we lift the v1.4 `us_zip_centroids.csv`) — to seed `ref.zip_centroid`.
6. **A prior sign-off deck / booking guide** — to confirm the split-award grain (G1) and the `awd` output records.
7. **The fiscal-calendar source** (or confirmation of the 2020–2037 lookup) — to seed `ref.fiscal_calendar`.
