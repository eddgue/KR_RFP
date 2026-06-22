# SLICE B7 — DATA MODEL (Layer-1, exhaustive) — Part 2 of 2: THE 20 MIGRATIONS + `env.py`

> **Scope of this file:** `/home/user/KR_RFP/backend/alembic/env.py`, `script.py.mako`, and **all 20** `backend/alembic/versions/*.py`.
> The baseline schema (`db/baseline/schema.sql`, `NAMING_MAP.md`, `README.md`) is documented in the sibling **`B7_schema.md`** (Part 1 of 2). This slice was split because one file could not hold the exhaustive table-by-column + migration-by-line detail at the AUDIT_STANDARD bar — see the reply note.
> **Read-only audit. Nothing in this slice was modified.**

---

## B7-M.0 — `env.py` and `script.py.mako` (the Alembic harness)

### B7-M.0.1 `backend/alembic/env.py` (census row 23; 3008 bytes; 87 lines)

**Purpose / WHY:** Wires the app's SQLAlchemy metadata + the app's settings DB URL into Alembic, **schema-aware**. Without it, autogenerate would not see the eight layer schemas, and the connection string would have to live in `alembic.ini` (a secret in the repo — forbidden).

**Line-by-line behavior:**
- Lines 17–24 — **imports every domain models module** (`app.domain.{audit,awd,bid,cyc,eng,norm,perf,ref}.models`) so their tables register on the shared `metadata`. Comment (line 16): "Most are stubs this phase, but importing them fixes the seam and keeps autogenerate honest." **WHY:** if a models module is not imported, its tables are invisible to autogenerate and would drift silently.
- Lines 25–26 — imports `get_settings` (the single typed config surface) and `SCHEMAS, metadata` from `app.core.db.base`.
- Lines 32–33 — **injects the DB URL from settings** onto the Alembic `Config` only if not already set. Comment: a caller may pre-set the URL (per-run database provisioning, **D30**) — "respect it and don't override." **WHY:** keeps `alembic.ini` free of any connection string, and supports per-run databases.
- Lines 41–44 — `_include_object(...)` returns `False` for any table whose `.schema` is **not** in `SCHEMAS` (the eight layers). **WHY:** Alembic only manages objects in the eight governed layers — anything else present in the database (e.g. `auth`, `pilot`, `ref.fiscal_period` is in `ref` so it's managed) is ignored by autogenerate. **NOTE/DRIFT:** the `auth` and `pilot` schemas created by migrations 0017/0019 are **outside** `SCHEMAS`, so autogenerate will not manage them — those migrations are hand-authored `op.create_table`, which is consistent with that exclusion (the doc strings call them "NOT one of the eight governed layers").
- Lines 47–61 — `run_migrations_offline()`: emits SQL without a live connection (`literal_binds=True`, `include_schemas=True`, `include_object=_include_object`, `compare_type=True`). `compare_type=True` is what makes autogenerate notice a type change (relevant to the §B7-S.14 drift register).
- Lines 63–80 — `run_migrations_online()`: runs against a live connection via `engine_from_config(...)` with `pool.NullPool` (no pooling for one-shot migrations), same `include_schemas`/`include_object`/`compare_type` flags.
- Lines 83–86 — dispatch on `context.is_offline_mode()`.

### B7-M.0.2 `backend/alembic/script.py.mako` (census row 24; 657 bytes; 29 lines)

**Purpose / WHY:** The template Alembic stamps new migration files from. Standard Alembic mako with `from __future__ import annotations`, `from collections.abc import Sequence`, and typed `revision`/`down_revision`/`branch_labels`/`depends_on`. Every hand-written migration in this slice follows this shape (which is why they all carry those identical header lines). Empty `upgrade()/downgrade()` default to `pass`.

### B7-M.0.3 The chain (linear, no branches)

```
0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009 → 0010 →
0011 → 0012 → 0013 → 0014 → 0015 → 0016 → 0017 → 0018 → 0019 → 0020 (head)
```
Each `down_revision` points at exactly the prior `revision` (verified file-by-file below). **No branch labels, no `depends_on`, no merge points** — a single linear chain. `0001` has `down_revision = None` (the root). `0020` is head.

---

## B7-M.1 — Migration-by-migration (revision, down_revision, what line-by-line, WHY)

> Convention below: **rev** / **down** / **created** / **owner**. Every migration uses idempotent guards and a real downgrade so the CI `up→down→up` roundtrip stays clean (stated in each docstring).

### §M01 — `0001_baseline.py` — the baseline (census row 25; 5592 bytes)
- **rev** `0001_baseline` · **down** `None` (chain root) · **created** 2026-06-18 · ADR-0001 / SKELETON §8.
- **WHAT (line-by-line):**
  1. `upgrade()` lines 104–106 — `CREATE SCHEMA IF NOT EXISTS "<s>"` for all eight layers (`SCHEMAS` tuple line 42: `ref norm cyc bid eng awd perf audit`). **WHY:** the layering is visible in the DB from rev 0001.
  2. Lines 108–112 — **if `<repo-root>/db/baseline/schema.sql` exists, `op.execute(read_text())`** (the full baseline — Part 1). Else `op.execute(MINIMAL_SEED_DDL)` (a `ref.client` + `ref.commodity` standalone seed, lines 53–76, so `alembic upgrade head` succeeds even without the baseline file). `REPO_ROOT = Path(__file__).resolve().parents[3]` (line 46) — three parents up from `backend/alembic/versions/`.
  3. Lines 114–115 — **always** `op.execute(AUDIT_EVENT_LOG_DDL)` (lines 81–100): ensures `audit.event_log` exists idempotently on BOTH paths, because the audit writer appends to it on every governed mutation. No-op once the baseline includes it (it does — Part 1 §B7-S.8.1).
- **downgrade()** lines 118–122 — `DROP SCHEMA IF EXISTS "<s>" CASCADE` for all eight (reversed). **WHY:** CASCADE removes everything within them (seed, baseline, audit), so `up→down→up` is clean regardless of which path `upgrade()` took.
- **WHY this design:** the path-contract + dual-path (full baseline OR minimal seed) means the chain is self-sufficient even before Platform & Data deliver `schema.sql`; the always-on audit DDL guarantees the writer's target exists from rev 0001. The minimal seed's columns mirror the baseline's `ref.client`/`ref.commodity` so either path yields the same reference-pattern shape.

### §M02 — `0002_cyc_kickoff_satellites.py` — the kickoff keystone (census row 26; 12663 bytes — the largest)
- **rev** `0002_cyc_kickoff_satellites` · **down** `0001_baseline` · **created** 2026-06-18 · G5/E-14, D9, D12, ADR-0013 · ADDITIVE on the frozen M0 baseline.
- **WHAT (UPGRADE_SQL, 10 numbered blocks):**
  1. Lines 61–68 — **EXTEND `cyc.cycle`** with 8 additive columns `ADD COLUMN IF NOT EXISTS`: `annual_spend numeric(18,2)`, `horizon_label text`, `tf_start_fiscal text`, `tf_end_fiscal text`, `tf_start_calendar date`, `tf_end_calendar date`, `prior_structure_note text`, `dcs_scope text DEFAULT 'ALL'`. **WHY:** the kickoff header fields (the brief's horizon/spend the M0 baseline deferred).
  2. Lines 73–85 — **`cyc.cycle_objective`** (`cycle_id`, `objective_code` text, `is_primary boolean DEFAULT false`, `objective_note`), PK `(cycle_id, objective_code)`, `ck_cycle_objective_code CHECK (objective_code IN ('SAVINGS','SUPPLY_ASSURANCE','QUALITY','DIVERSIFICATION','STRATEGIC'))`, FK `(cycle_id)→cyc.cycle`. **Partial unique** `uq_cycle_objective_one_primary ON (cycle_id) WHERE is_primary = true` — **exactly one primary objective per cycle**.
  3. Lines 92–110 — **`cyc.cycle_pricing`** — **ONE row per cycle (D9)**, PK `(cycle_id)`. Columns: `pricing_basis` NN, `duration_cadence` NN, `cadence_n integer`, `baseline_then_negotiate boolean DEFAULT false`, `volume_split_rule`, `routing_basis`, `sourcing_region_per_period`. CHECKs: `ck_cycle_pricing_basis IN ('FIXED','INDEX','HYBRID')`; `ck_cycle_pricing_cadence IN ('FULL_YEAR','SEASONAL','TIMEFRAMES','PERIOD_BY_PERIOD','QUARTERLY','MONTHLY','WEEKLY')`; `ck_cycle_pricing_routing (NULL OR IN ('FOB','DELIVERED','XDOCK','CBS_FREIGHT'))`; `ck_cycle_pricing_cadence_n_positive (NULL OR > 0)`. FK `(cycle_id)→cyc.cycle`. **WHY:** the **declared render contract** (ADR-0013/D12) — PK=cycle_id enforces one pricing model per RFP; heterogeneity is handled by item participation, NOT by mixing pricing structures.
  4. Lines 120–131 — **`cyc.cycle_scope_item`** — item-level participation. Columns: `subcommodity_code` text NN, `gtin_code text NOT NULL DEFAULT ''`, `participates boolean DEFAULT false`, `lot_id varchar(36)` (unconstrained), `projected_volume numeric(18,3)`. PK `(cycle_id, subcommodity_code, gtin_code)` — the **gtin coalesces to `''`** so subcommodity-grain rows (no gtin) stay unique. Index `ix_cycle_scope_item_participates (cycle_id, participates)`. FK `(cycle_id)→cyc.cycle`. **WHY:** `participates` is the manual signal-from-noise switch (D9). `lot_id` is unconstrained because persistent `norm.lot` is a later migration — **unenforced reference** (Part 1 §B7-S.14 #4).
  5. Lines 136–143 — **`cyc.cycle_pba_term`** (`cycle_id`, `metric` NN, `threshold` NN, `enforcement`), PK `(cycle_id, metric)`, FK `(cycle_id)→cyc.cycle`. PBA governance.
  6. Lines 148–159 — **`cyc.cycle_commercial_term`** (`cycle_id`, `term_type` NN, `target_value`, `benefit_value numeric(18,2)`, `treatment`, `note`), PK `(cycle_id, term_type)`, `ck_cycle_commercial_term_type IN ('WORKING_CAPITAL','KPM','OTHER')`, FK `(cycle_id)→cyc.cycle`.
  7. Lines 164–174 — **`cyc.cycle_rfi_question`** (`cycle_id`, `question_code` NN, `question_text` NN, `answer_type`, `seq integer` NN), PK `(cycle_id, question_code)`, `ck_cycle_rfi_answer_type (NULL OR IN ('TEXT','PCT','BOOL','ENUM'))`, FK `(cycle_id)→cyc.cycle`. **WHY:** stable codes for cross-cycle comparability.
  8. Lines 179–189 — **`cyc.cycle_timeline_event`** (`cycle_id`, `event_seq integer` NN, `event_name` NN, `event_date date`, `is_leadership_gate boolean DEFAULT false`, `round_no integer`, `bcg_support_needed boolean DEFAULT false`), PK `(cycle_id, event_seq)`, FK `(cycle_id)→cyc.cycle`. **WHY:** the "Next Steps" rail (E-16).
  9. Lines 194–207 — **`cyc.cycle_narrative`** (`cycle_id`, `narrative_type` NN, `version integer DEFAULT 1`, `body_richtext` NN, `authored_by`, `authored_at timestamptz DEFAULT now()`), PK `(cycle_id, narrative_type, version)`, `ck_cycle_narrative_type IN ('BACKGROUND','DATA_DIVE','INDUSTRY_INSIGHTS','CATEGORY_STRATEGY','SOURCING_STRATEGY','GENERAL_GOALS','APPENDIX_LINK')`, `ck_cycle_narrative_version_positive (version > 0)`, FK `(cycle_id)→cyc.cycle`. **WHY:** versioned rich text, never field-ified.
  10. Lines 213–214 — **EXTEND `cyc.cycle_invited_supplier`** with `is_incumbent boolean NOT NULL DEFAULT false`. **WHY:** the denominator split (N total, X incumbent, Y non-incumbent).
- **downgrade()** lines 218–238 — drops `is_incumbent`, then the 8 satellite tables (reverse create order), then the 8 `cyc.cycle` columns. Clean roundtrip.
- **Grain note (lines 26–31):** every satellite FKs `cyc.cycle(cycle_id) varchar(36)` — **reconciled to the M0 baseline, NOT the spec's illustrative `bigint`**. This is the migration honoring the baseline's type over the spec's example — a deliberate fidelity choice.

### §M03 — `0003_cyc_cycle_safety.py` — the five PRICING safeties (census row 27; 3736 bytes)
- **rev** `0003_cyc_cycle_safety` · **down** `0002_cyc_kickoff_satellites` · **created** 2026-06-18 · D13/ADR-0014 · ADDITIVE.
- **WHAT:** Creates `cyc.cycle_safety` — **one row per applied safety per cycle**, PK `(cycle_id, safety_type)`. Columns are **real typed columns** (not a jsonb blob) so terms are queryable/renderable: `cap`/`floor numeric(18,6)` (COLLAR), `lookback_weeks`/`reset_cadence_weeks integer` (ROLLING_MIDPOINT), `band numeric(18,6)`/`min_duration_weeks`/`reprice_window_weeks integer` (TOLERANCE_BAND), `reverts_to_contract boolean DEFAULT true`/`notes` (DISASTER/INVERSE_DISASTER). CHECKs: `ck_cycle_safety_type IN ('COLLAR','ROLLING_MIDPOINT','TOLERANCE_BAND','DISASTER','INVERSE_DISASTER')`; `ck_cycle_safety_weeks_positive` (all four week columns NULL-or-`>0`); `ck_cycle_safety_collar_ordered (cap IS NULL OR floor IS NULL OR cap >= floor)`. FK `(cycle_id)→cyc.cycle`. `COMMENT ON TABLE` records "Terms only; engine ignores them."
- **WHY (D13/ADR-0014):** the five pricing safeties are **CONTRACT terms** (risk-sharing incentives governing post-award price movement), declared at kickoff. **TERMS ONLY — the engine does NOT consume these** (contrast with migration 0012's *engine* safeties). All windows/cadences/bands are set INDIVIDUALLY per RFP, not fixed defaults — hence every parameter is nullable and carries weight only for its safety types.
- **downgrade()** drops the table. Clean.

### §M04 — `0004_norm_attribute_taxonomy.py` — one shared catalog + sparse per-lot attributes (census row 28; 4170 bytes)
- **rev** `0004_norm_attribute_taxonomy` · **down** `0003_cyc_cycle_safety` · **created** 2026-06-18 · D14/G8 · ADDITIVE.
- **WHAT:**
  1. **`norm.attribute_def`** — the **one shared superset catalog** (D14). Columns: `attribute_code varchar(60)` PK, `label varchar(160)` NN, `data_type text` NN, `unit varchar(40)`, `allowed_values text` (delimited/JSON for ENUM), `commodity_hint varchar(120)`, `active_flag boolean DEFAULT true`, `created_at timestamptz DEFAULT now()`. CHECKs: `ck_attribute_def_data_type IN ('TEXT','NUMERIC','BOOL','ENUM','DATE')`; `ck_attribute_def_label_not_empty (length(label) > 0)`. **WHY:** ONE shared taxonomy, not per-commodity schemas; extended only when a genuinely new attribute appears.
  2. **`norm.lot_attribute`** — **SPARSE** per-lot attributes. Columns: `lot_id varchar(36)`, `attribute_code varchar(60)`, `value_text text`, `value_numeric numeric(18,6)`, `value_bool boolean`, `value_date date`, `source text`, `created_at timestamptz DEFAULT now()`. PK `(lot_id, attribute_code)`. FK `(attribute_code)→norm.attribute_def`. Index `ix_lot_attribute_attribute_code`. **WHY:** a lot carries only its applicable attributes; the value lands in the column matching the def's `data_type` (all value columns nullable). `lot_id` is **unconstrained varchar(36)** — the persistent `norm.lot` is M2/G8 (not on disk), so the FK is deferred to a later additive migration. `attribute_code` IS FK'd so a lot attribute must reference a defined attribute.
- **downgrade()** drops `lot_attribute` then `attribute_def` (child first). Clean.

### §M05 — `0005_eng_scenario_award_split.py` — split re-grain schema prep (census row 29; 5031 bytes)
- **rev** `0005_eng_scenario_award_split` · **down** `0004_norm_attribute_taxonomy` · **created** 2026-06-18 · G1/D10 · ADDITIVE, **SCHEMA PREP ONLY** (the split LOGIC ships post-pilot behind a `split_award` flag).
- **WHAT (ALTERs the existing `eng.scenario_award`):**
  1. Lines 53–58 — `ADD COLUMN IF NOT EXISTS volume_share numeric(9,6)` (cell volume fraction), `is_fallback boolean NOT NULL DEFAULT false` (lot filled outside the top-N set — V3 §4.3 transparency), `cap_breach_flag boolean NOT NULL DEFAULT false` (manual selection exceeded the auto cap — V3 §4.4/D10).
  2. Lines 61–71 — guarded `DO` block adds `ck_scenario_award_volume_share_range CHECK (volume_share IS NULL OR (>= 0 AND <= 1))` — fraction in [0,1], **without** forcing per-cell shares to sum to 1 (partial/fallback fills are legitimate; the sum invariant is engine-side).
  3. Lines 73–86 — **`DROP CONSTRAINT IF EXISTS uq_scenario_a_cell_assignment_cell`** (the single-winner unique) and add `uq_scenario_award_cell_supplier UNIQUE (scenario_run_id, dc_id, lot_id, tf_id, supplier_id)` (guarded) — **re-grain to per-supplier so a cell may hold N suppliers**.
- **WHY:** ALTER the **existing** table (NAMING_MAP calls `eng.scenario_award` the split target) rather than create a new one — its identity FKs, status-shape CHECK, and line/capacity detail tables already point at it, so altering in place keeps the spine intact. This directly modifies the M0 baseline table from Part 1 §B7-S.6.2.
- **downgrade()** lines 93–111 — restores `uq_scenario_a_cell_assignment_cell`, drops the range CHECK + the 3 columns. **Caveat in docstring:** the downgrade is only safe while no cell yet holds >1 supplier (true at schema-prep time, before the split LOGIC ships).

### §M06 — `0006_perf_itrade_baseline.py` — iTrade 43-col feed + actual-paid view (census row 30; 8709 bytes)
- **rev** `0006_perf_itrade_baseline` · **down** `0005_eng_scenario_award_split` · **created** 2026-06-18 · E-08/D11 · ADDITIVE.
- **WHAT:**
  1. Lines 48–106 — **CREATE `perf.itrade_receipt`** at the **real 43-column iTrade "Data" structure** (FEEDS_ITRADE.md). `receipt_id uuid PK DEFAULT gen_random_uuid()`. Column groups (commented inline): identity (cols 1–2, 12–21: `commodity_desc`, `subcommodity_desc` = "the anchor", `dc_no`, `dc_name`, `case_size`, `item_gross_weight`/`case_net_weight numeric(18,6)`, `ship_pack_qty`/`warehouse_ship_pack_qty numeric(18,3)`, `upc`, `warehouse_desc`); lineage (`po_number`, `po_purchase_order_no`, `line_no`, `field_buying_office`); the **7-date chain** (`po_creation_date`, `po_arrival_date`, `received_date`, `ship_date_request`, `p200_final_sent_date`, `ship_date_indicated`, `ship_date_recorded`); vendor/origin (`supplier_name`, `ship_from_address`, `ship_from_state` = ship-from NOT grow-origin, `ship_from_zip` = freight proxy, `routing`); performance (`qty_received`/`qty_shipped`/`qc_reject_qty numeric(18,3)`); cost (`final_price_fob`, `freight`, `total_w_freight`, `xdock_charges`, `total_xdock`, `cogs` = cost actually booked — all `numeric(18,6)`); flags (`flag_canceled`/`flag_zero_cost`/`flag_zero_qty boolean DEFAULT false` — the flag-first gate); fiscal stamping (`fiscal_ypw`, `fiscal_year`, `period`, `week_of_year`); ingestion lineage (`ingestion_run_id`, `source_artifact`, `source_row`, `created_at`). **No identity FKs** — resolution is the importer's job (Vendor/UPC → alias → quarantine, never guess).
  2. Lines 110–117 — **reconcile pattern**: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for 8 key columns (no-op if present) so a partial earlier `itrade_receipt` reconciles to the full shape.
  3. Lines 119–122 — indexes `ix_itrade_receipt_grain (subcommodity_desc, dc_no, fiscal_year, period)`, `ix_itrade_receipt_supplier (supplier_name)`.
  4. Lines 131–152 — **CREATE OR REPLACE VIEW `perf.v_itrade_actual_paid_baseline`** — the **D11 savings baseline**: volume-weighted average actual-paid (`sum(cogs*qty_received)/NULLIF(sum(qty_received),0)`) per `subcommodity_desc × dc_no × fiscal_year × period`, plus `min/max(cogs)` for the contracted-vs-paid context, and `receipt_line_count`. **WHERE** excludes `flag_canceled`/`flag_zero_cost`/`flag_zero_qty` = true and requires `qty_received > 0` and `cogs NOT NULL` (the flag-first gate). **WHY the grain:** iTrade receipts carry no RFP `lot_id` (lots are an RFP construct); the natural anchor is `subcommodity_desc`, which lots are built over, so the view labels that grain the "lot×DC×fiscal_period" baseline.
- **downgrade()** lines 158–161 — `DROP VIEW` then `DROP TABLE`. Clean.
- **WHY:** `perf.itrade_receipt` is deferred to M4/G6 in the baseline; this lands it at the real feed shape now. **This is the only migration that creates a VIEW.** It is also one of only two migrations whose new table uses a `uuid` PK while living next to text-UUID siblings (the other net-new uuid tables are `ref.fiscal_period`, `auth.app_user`).

### §M07 — `0007_bid_components.py` — engine cost-component columns on bid_line (census row 31; 4400 bytes)
- **rev** `0007_bid_components` · **down** `0006_perf_itrade_baseline` · **created** 2026-06-19 · V3 §7 / D20 · ADDITIVE.
- **WHAT (ALTERs `bid.bid_line`):**
  - `ADD COLUMN IF NOT EXISTS delivery_surcharge_case numeric(18,6)` (engine Delivery Surcharge), `vegcool_surcharge_case numeric(18,6)` (cold-chain), `lot_discount_case numeric(18,6)` (fallback-only), `price_basis_resolved text` ('ALL_IN' | 'COMPONENT_FALLBACK' provenance).
  - Guarded `DO` block adds `ck_bid_line_no_double_discount CHECK (submitted_all_in_case IS NULL OR lot_discount_case IS NULL OR lot_discount_case = 0)` — **the §7 double-subtract guard at rest**: when a submitted All-In is present, a Lot Discount must NOT also be populated (the ambiguous double-subtract the ingester quarantines is also a hard CHECK).
  - `COMMENT ON COLUMN` on all four.
- **WHY (D20 round-trip):** the engine's IN_Bids cost stack = All-In + {FOB, Delivery Surcharge, VegCool Surcharge, Lot Discount}. The baseline `bid.bid_line` carries a *generic* landed-cost vocabulary (`freight_case`/`accessorial_case`/`item_discount_case`) with no clean home for the engine's named components; overloading them would silently re-map and break "components round-trip exactly." So the three engine components get their OWN columns + a resolved-basis column. This modifies the central price fact from Part 1 §B7-S.5.2.
- **downgrade()** drops the CHECK + 4 columns (reverse). Clean.

### §M08 — `0008_eng_analysis_run.py` — the lightweight sealed decision-support spine (census row 32; 8550 bytes)
- **rev** `0008_eng_analysis_run` · **down** `0007_bid_components` · **created** 2026-06-19 · ENG-PLAN §3 / ADR-0006 / D19 · ADDITIVE · owner Engine & Domain.
- **WHAT (4 tables):**
  1. **`eng.analysis_run`** — one sealed run per (cycle, round, engine call). Columns: `analysis_run_id varchar(36)` PK, `cycle_id`/`round_id` NN, `engine_version varchar(60)` NN, `config_preset varchar(40)` NN, `status text` NN, `is_sealed boolean DEFAULT false`, `input_hash_manifest`/`output_hash_manifest varchar(128)` NN, `run_started_at`/`run_finished_at timestamp` NN, `run_by varchar(120)` NN. CHECKs: `uq_analysis_run_identity UNIQUE (analysis_run_id, cycle_id, round_id)`; `ck_analysis_run_input_hash_len`/`_output_hash_len (>= 8)`; `ck_analysis_run_sealed_finished (is_sealed=false OR run_finished_at NOT NULL)`. FK `fk_analysis_run_round_in_cycle (round_id, cycle_id)→cyc.cycle_round` **(composite)** + `(cycle_id)→cyc.cycle`. **Extended by 0020 (`label`).**
  2. **`eng.bid_score`** — the **five banded factors → rec_score** per scored bid. Columns: `bid_score_id` PK, `analysis_run_id`, `bid_line_id`, `supplier_id`/`dc_id`/`lot_id`/`tf_id`, then `price_score`/`coverage_score`/`hist_score`/`zrisk_score`/`continuity_score`/`rec_score numeric(9,4)` NN, `is_eligible boolean` NN, `gate_flags text`. `uq_bid_score_per_run_line UNIQUE (analysis_run_id, bid_line_id)`; FK `(analysis_run_id)→eng.analysis_run`. **This is the `eng.bid_score` table NAMING_MAP listed as net-new (line 57).**
  3. **`eng.analysis_scenario`** — the A–G lens headers. `analysis_scenario_id` PK, `analysis_run_id`, `scenario_code varchar(4)` NN, `label varchar(160)` NN, `description`, `objective_total_spend numeric(18,6)`. `uq_analysis_scenario_per_run_code UNIQUE (analysis_run_id, scenario_code)`; FK `(analysis_run_id)→eng.analysis_run`.
  4. **`eng.analysis_scenario_award`** — the **SPLIT award rows** (per-supplier cell grain; G1/D10 columns). `award_id` PK, `analysis_scenario_id`, `dc_id`/`lot_id`/`tf_id`/`supplier_id`, `volume_share numeric(9,6)` NN, `awarded_price numeric(18,6)` NN, `is_recommended boolean DEFAULT false`, `is_fallback boolean DEFAULT false`, `cap_breach_flag boolean DEFAULT false`. CHECKs: `uq_analysis_award_cell_supplier UNIQUE (analysis_scenario_id, dc_id, lot_id, tf_id, supplier_id)`; `ck_analysis_award_volume_share_range (0..1)`; `ck_analysis_award_price_positive (> 0)`. FKs: `(analysis_scenario_id)→eng.analysis_scenario`, `fk_analysis_award_lot_in_cycle (lot_id)→cyc.cycle_lot`, `fk_analysis_award_tf_in_cycle (tf_id)→cyc.cycle_timeframe`, `(dc_id)→ref.dc`, `(supplier_id)→ref.supplier`. **Extended by 0009 (`rec_type`).**
- **WHY (ADR-0006):** the M0 baseline's heavyweight governed solver spine (`calculation_run`+`scenario`+`scenario_award`) requires the full eligibility/landed-cost chain. The decision-support prototype needs a **LIGHTWEIGHT** sealed spine recording the same audit-grade facts (hashed manifests, engine version pin, is_sealed) + per-bid 5-factor scores + A–G lenses with SPLIT awards, **without** the solver chain — FK'd into the SAME governed cyc/ref keys so outputs are real governed rows, not a side file. **Decision-support only:** an award row RECOMMENDS a split; it never asserts the award (the real award lands in `awd.*` after a human selects).
- **downgrade()** drops all 4 (child-first). Clean.

### §M09 — `0009_eng_award_rec_type.py` — the B reason label (census row 33; 2185 bytes)
- **rev** `0009_eng_award_rec_type` · **down** `0008_eng_analysis_run` · **created** 2026-06-19 · V3 §5 B / D28 · ADDITIVE.
- **WHAT:** `ALTER TABLE eng.analysis_scenario_award ADD COLUMN IF NOT EXISTS rec_type varchar(40)` (nullable) + a `COMMENT ON COLUMN`.
- **WHY (D28):** every Scenario-B pick gets a **RecType** (Lowest cost / Coverage advantage / Comparable premium / Defensible premium / Risk-adjusted) computed from config-driven thresholds — the **authoritative "why this pick"** rendered from sealed records, never a generic catch-all clause generated at output time. B-only — NULL for the other lenses.
- **downgrade()** drops the column. Clean.

### §M10 — `0010_awd_award_versioned.py` — the greenfield award layer (census row 34; 7114 bytes)
- **rev** `0010_awd_award_versioned` · **down** `0009_eng_award_rec_type` · **created** 2026-06-19 · ADR-0014 freeze-and-layer / ADR-0006 no-hard-deletes / PILOT step 5 · ADDITIVE · owner Post-Award. **This is the whole `awd.*` schema (NAMING_MAP line 65) — NOT in the baseline.**
- **WHAT:** `CREATE SCHEMA IF NOT EXISTS awd` + 4 tables:
  1. **`awd.award`** — one FROZEN award per selected (cycle, run, scenario). `award_id` PK, `cycle_id` NN, `analysis_run_id` NN, `scenario_code text` NN, `award_code text` NN, `frozen_at`/`frozen_by` NN, `status text DEFAULT 'FROZEN'`. `uq_award_cycle_run_scenario UNIQUE (cycle_id, analysis_run_id, scenario_code)`; FKs `(cycle_id)→cyc.cycle`, `(analysis_run_id)→eng.analysis_run`.
  2. **`awd.award_line`** — the **immutable baseline**: one row per awarded cell at `frozen_price`. `award_line_id` PK, `award_id`, `dc_id`/`lot_id`/`tf_id`/`supplier_id`, `volume_share numeric(9,6)` NN, `frozen_price numeric(18,6)` NN. `uq_award_line_cell UNIQUE (award_id, dc_id, lot_id, tf_id, supplier_id)`; FK `(award_id)→awd.award`. `frozen_price` NEVER updated.
  3. **`awd.award_adjustment`** — an APPEND-ONLY VERSIONED layer. `adjustment_id` PK, `award_id`, `version_no integer` NN, `adjustment_type text` NN, `effective_date date` NN, `reason text` NN, `created_at`/`created_by` NN, `status text DEFAULT 'RECORDED'`. `uq_award_adjustment_version UNIQUE (award_id, version_no)`; `ck_award_adjustment_version_positive (>= 1)`; FK `(award_id)→awd.award`.
  4. **`awd.award_adjustment_line`** — per-cell `prior_price → new_price → delta` for one layer. `adj_line_id` PK, `adjustment_id`, `dc_id`/`lot_id`/`tf_id`/`supplier_id`, `prior_price`/`new_price`/`delta numeric(18,6)` NN. `uq_adj_line_cell UNIQUE (adjustment_id, dc_id, lot_id, tf_id, supplier_id)`; FK `(adjustment_id)→awd.award_adjustment`.
- **WHY (ADR-0014/ADR-0006):** after a human selects an engine scenario, the recommendation is PROMOTED to a real **frozen** award. The frozen baseline is **NEVER overwritten**; post-award negotiation/safety price moves are recorded as **append-only, date-stamped, versioned layers** (the effective price at any version = baseline overlaid by each layer's new_price up to that version). A price move SUPERSEDES via a new layer, never an UPDATE. The post-award doc renders an explicit "which version" heading off these rows.
- **downgrade()** drops the 4 tables child-first (the docstring says "+ the schema", but `DOWNGRADE_SQL` lines 137–141 drop only the 4 tables — **see G-B7-M-1 below**). 
- **GAP G-B7-M-1:** the docstring (line 29) says "Downgrade drops the four tables (child-first) + the schema", but `DOWNGRADE_SQL` does **not** `DROP SCHEMA awd` — it leaves the empty `awd` schema behind. Harmless (the schema is idempotently re-created on re-upgrade), but a **doc-vs-code mismatch**. Contrast with 0017/0019 which DO drop their schemas.

### §M11 — `0011_bid_transit_days.py` — transit days on bid_line (census row 35; 1730 bytes)
- **rev** `0011_bid_transit_days` · **down** `0010_awd_award_versioned` · **created** 2026-06-20 · ADDITIVE.
- **WHAT:** `ALTER TABLE bid.bid_line ADD COLUMN IF NOT EXISTS transit_days integer` (nullable) + `COMMENT`.
- **WHY:** supplier-stated lane transit (origin→DC) is a real bid attribute (the booking guide records Transit Days). It is a **HIDDEN COST** surfaced in the analysis (freshness/lead-time), **not** an engine scoring factor. Nullable because not every cycle/supplier populates it — and when absent the analysis shows no transit (**no synthetic proxy** — consistent with CLAUDE.md "no fudged data").
- **downgrade()** drops the column. Clean.

### §M12 — `0012_cyc_engine_safeties.py` — the four ENGINE safeties on cyc.cycle (census row 36; 2968 bytes)
- **rev** `0012_cyc_engine_safeties` · **down** `0011_bid_transit_days` · **created** 2026-06-20 · ADDITIVE.
- **WHAT:** `ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS` (all nullable) — `engine_premium_ceiling numeric(18,6)`, `engine_coverage_floor numeric(18,6)`, `engine_conc_thresh numeric(18,6)`, `engine_max_sup_dc integer` + 4 `COMMENT`s.
- **WHY:** the setup workbook lets the buyer set four **engine** safeties per RFP — premium eligibility ceiling, coverage floor, category-concentration flag, max suppliers per DC. **These the engine DOES consume** (contrast with migration 0003's pricing-CONTRACT safeties the engine ignores — the two "safety" concepts are distinct and live in different tables, which the auditor must not conflate). Until now they were dropped on ingest and the engine silently used preset defaults; storing them lets `run_round` honor the buyer's values, falling back to the preset where blank (hence all nullable).
- **downgrade()** drops all 4 columns. Clean.

### §M13 — `0013_cyc_engine_weight_preset.py` — the scoring-weight preset (census row 37; 1963 bytes)
- **rev** `0013_cyc_engine_weight_preset` · **down** `0012_cyc_engine_safeties` · **created** 2026-06-20 · ADR-0016 · ADDITIVE.
- **WHAT:** `ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS engine_weight_preset text`; then `DROP CONSTRAINT IF EXISTS ck_cycle_weight_preset` + `ADD CONSTRAINT ck_cycle_weight_preset CHECK (engine_weight_preset IS NULL OR IN ('balanced','price_focus','coverage_focus','risk_averse','custom'))` (the drop-then-add makes the CHECK itself idempotent) + `COMMENT`.
- **WHY:** the buyer picks a named scoring preset that remaps the engine's five scoring weights. Like the engine safeties (0012), it was collected but dropped on ingest; storing it lets `run_round` apply the preset's weight vector. Nullable — blank uses the default (`balanced`).
- **downgrade()** drops the CHECK then the column (order matters). Clean.

### §M14 — `0014_ref_fiscal_period.py` — the seeded fiscal-period dimension (census row 38; 3825 bytes)
- **rev** `0014_ref_fiscal_period` · **down** `0013_cyc_engine_weight_preset` · **created** 2026-06-20 · ADDITIVE, net-new ref spine. **Uses the Python Alembic API (`op.create_table`/`op.bulk_insert`), not raw SQL.**
- **WHAT (line-by-line):**
  - Lines 43–45 — `_CSV_PATH` = `backend/app/fiscal/data/kroger_fiscal_periods.csv` (resolved via `Path(__file__).resolve().parents[2]`).
  - Lines 48–64 — `_read_seed_rows()` parses the CSV with **stdlib only** (`csv` + `pathlib` + `datetime.date`) into bulk-insert payloads (`fiscal_year`, `period`, `quarter`, `begin_date`, `end_date`, `weeks`). **No `app.*` import** — migrations stay frozen/standalone.
  - Lines 68–85 — `op.create_table("fiscal_period", schema="ref")` with `id PG_UUID DEFAULT gen_random_uuid()` PK (`pk_fiscal_period`), `fiscal_year`/`period`/`quarter`/`weeks Integer` NN, `begin_date`/`end_date Date` NN, `UniqueConstraint("fiscal_year","period", name="fiscal_period_year_period")`.
  - Line 89 — `op.bulk_insert(fiscal_period, _read_seed_rows())` — **SEEDS all 273 rows (FY16..FY36)**.
- **WHY:** Kroger runs a 4-3-3-3 retail fiscal calendar — exactly 13 four-week periods per year (Q1=P1-4, Q2=P5-7, Q3=P8-10, Q4=P11-13); P13 of a 53-week year carries a 5th week. The authoritative conversion table already ships as data; this lands it as a **governed period dimension** other tables can FK to. **NOTE:** this is the table `bid.bid_line.fiscal_period_id` (migration 0015) logically references — and the **uuid PK here vs the varchar(36) reference there is the confirmed type drift** (Part 1 §B7-S.14 #1). Distinct from `ref.fiscal_calendar` (a *date* dimension, Part 1 §B7-S.1.8).
- **downgrade()** `op.drop_table("fiscal_period", schema="ref")`. Clean.

### §M15 — `0015_bid_line_fiscal_period.py` — the flat-13 storage column (census row 39; 2150 bytes)
- **rev** `0015_bid_line_fiscal_period` · **down** `0014_ref_fiscal_period` · **created** 2026-06-20 · INTAKE_TEMPLATE_DESIGN §1a · ADDITIVE + BACKWARD-COMPATIBLE.
- **WHAT:** `ALTER TABLE bid.bid_line ADD COLUMN IF NOT EXISTS fiscal_period_id varchar(36)` (nullable) + `COMMENT`.
- **WHY:** the flat-13 model records every offer against exactly ONE of the 13 fiscal periods; a cycle's bid template groups periods into timeframes and intake FANS a timeframe's price out to each period. This lands the storage column the fan-out writes to. Nullable + **no constraint change**: existing (pilot) rows stay NULL and behave as before (engine reads `tf_id`). The reference is **LOGICAL (unenforced in DDL)**, matching `tf_id` — hence `varchar(36)` to match the sibling id columns, despite `ref.fiscal_period.id` being `uuid` (**the drift, §B7-S.14 #1**). The uniqueness flip is deliberately the NEXT migration (0016).
- **downgrade()** drops the column. Clean.

### §M16 — `0016_bid_line_period_uniqueness.py` — flip uniqueness to the flat-13 grain (census row 40; 2528 bytes)
- **rev** `0016_bid_line_period_uniqueness` · **down** `0015_bid_line_fiscal_period` · **created** 2026-06-21 · INTAKE §1a · constraint-only, backward-compatible.
- **WHAT:**
  - `ALTER TABLE bid.bid_line DROP CONSTRAINT IF EXISTS uq_bid_line_cell_per_submission` (the original 5-col single-grain unique from the baseline — Part 1 §B7-S.5.2).
  - `CREATE UNIQUE INDEX uq_bid_line_cell_tf_when_no_period ON (submission_id, dc_id, lot_id, item_id, tf_id) WHERE fiscal_period_id IS NULL` — the legacy/pilot timeframe grain, UNCHANGED.
  - `CREATE UNIQUE INDEX uq_bid_line_cell_period ON (submission_id, dc_id, lot_id, item_id, fiscal_period_id) WHERE fiscal_period_id IS NOT NULL` — the fanned-out flat-13 grain (one price per period per cell).
- **WHY:** the flat-13 fan-out makes several bid_line rows legitimately share `(submission, dc, lot, item, tf_id)`, which the old single unique forbids. Replacing it with **two filtered partial-unique indexes** lets both grains coexist: NULL-period rows keep the identical legacy guarantee; non-NULL-period rows get the per-period guarantee. The composite `uq_bid_line_identity_full` (FK target for landed_cost) is **left untouched** — this does not touch the engine read path.
- **downgrade()** drops both indexes (`DROP INDEX IF EXISTS bid.<name>`) and restores the original `uq_bid_line_cell_per_submission`. Clean on the empty/legacy grain.

### §M17 — `0017_auth_app_user.py` — the web-console user (census row 41; 2463 bytes)
- **rev** `0017_auth_app_user` · **down** `0016_bid_line_period_uniqueness` · **created** 2026-06-21 · ADDITIVE, net-new. **Own `auth` schema (NOT one of the eight layers).**
- **WHAT:** `CREATE SCHEMA IF NOT EXISTS auth` + `op.create_table("app_user", schema="auth")`: `id PG_UUID DEFAULT gen_random_uuid()` PK (`pk_app_user`), `username Text` NN, `password_hash Text` NN (argon2), `totp_secret Text` (nullable, 2FA), `totp_enabled Boolean DEFAULT false` NN, `is_active Boolean DEFAULT true` NN, `created_at DateTime(tz) DEFAULT now()` NN, `UniqueConstraint("username", name="uq_app_user_username")`.
- **WHY:** console identity must **not** live inside the data spine, so it gets a dedicated `auth` schema. The table behind login: unique username, argon2 hash, TOTP-2FA state, active flag. No `app.*` import (frozen/standalone).
- **downgrade()** `op.drop_table` then `DROP SCHEMA IF EXISTS auth CASCADE`. Clean (nothing left behind).

### §M18 — `0018_backfill_commodity_client.py` — DATA backfill of orphan commodities (census row 42; 3676 bytes)
- **rev** `0018_backfill_commodity_client` · **down** `0017_auth_app_user` · **created** 2026-06-21 · DATA backfill (**no schema change**).
- **WHAT (line-by-line):**
  - `_LEGACY_CLIENT_ID_SQL = "md5('legacy-client:' || c.id::text)::uuid"` (line 43) — a **deterministic per-orphan** legacy client id.
  - `upgrade()` lines 50–59 — (1) `INSERT INTO ref.client (id, client_code, client_name) SELECT <derived id>, 'BF-'||replace(c.id,'-',''), 'Legacy backfill tenant (pre-G-B)' FROM ref.commodity c WHERE c.client_id IS NULL ON CONFLICT (id) DO NOTHING`; (2) `UPDATE ref.commodity c SET client_id = <derived id> WHERE c.client_id IS NULL`.
  - `client_code = 'BF-' + 32-hex` is unique (`uq_client_code`) and 35 chars (within `varchar(40)`).
- **WHY (the load-bearing detail):** before G-B, setup ingest inserted commodities with `client_id = NULL` (the schema permits it — Part 1 §B7-S.1.2). G-B made tenant resolution MANDATORY at every governed decision (`app/core/audit/recorder.py` raises when a commodity has no client), so a pre-G-B cycle would now raise on ingest/run/freeze/adjust. This adopts every orphan into a legacy tenant. **Crucially, each orphan gets its OWN derived client, NOT a shared sentinel** — because two orphaned commodities may legitimately share a `commodity_code`, and `uq_commodity_code_per_client UNIQUE (client_id, commodity_code)` treats NULL `client_id` rows as distinct; a common `client_id` would VIOLATE that unique and abort the upgrade. A per-orphan client keeps each `(client_id, commodity_code)` pair distinct. Touches only orphans → a no-op on a fresh DB / any post-G-B run. Idempotent (`ON CONFLICT DO NOTHING`).
- **downgrade()** lines 66–71 — `UPDATE ref.commodity SET client_id = NULL WHERE client_id = <derived id>` (detach first — the FK requires it), then `DELETE FROM ref.client WHERE id IN (SELECT <derived id> FROM ref.commodity c)`. Clean.
- **SCOPE NOTE (docstring):** fixes the shared app DB (D36) + any per-run DB migrated to head. A pre-G-B per-run DB **rehydrated from a vault snapshot is NOT re-migrated** (D34 — restore loads the dump without re-running migrations), so such a snapshot stays orphaned — a rare edge. **Flagged as an audit edge case.**

### §M19 — `0019_pilot_run.py` — the DB-backed run identity (census row 43; 2717 bytes)
- **rev** `0019_pilot_run` · **down** `0018_backfill_commodity_client` · **created** 2026-06-21 · ADR-0018 Slice 2 (no-server-side-file-storage) · ADDITIVE, net-new. **Own `pilot` schema (NOT one of the eight layers).**
- **WHAT:** `CREATE SCHEMA IF NOT EXISTS pilot` + `op.create_table("run", schema="pilot")`: `slug Text` PK (`pk_run` — the existing `<commodity>-<date>-<short-id>` identifier), `commodity Text` NN, `label Text` NN, `rehearsal Boolean DEFAULT false` NN (the SYNTHETIC-provenance flag, replacing the `.rehearsal` sentinel), `cycle_id Text` (nullable, set on setup ingest, replacing `cycle_id.txt`), `created_at DateTime(tz) DEFAULT now()` NN.
- **WHY:** severs run identity from the vault folder — a "run" was only a `runs/<slug>/` folder linked by `cycle_id.txt`; this makes the run a first-class DB row so the stateless console can resolve/list runs with no filesystem (the no-file-storage contract, CLAUDE.md req #4). **`cycle_id` is intentionally plain `text`, NOT an FK** — cycle ids are text throughout the pilot path and the row must be insertable before a cycle exists (**Part 1 §B7-S.14 #3 drift**). The MCP harness is untouched (it keeps its file vault); this is the console's store.
- **downgrade()** `op.drop_table` then `DROP SCHEMA IF EXISTS pilot CASCADE`. Clean (mirrors 0017).

### §M20 — `0020_eng_analysis_run_label.py` — the named savepoint (census row 44; 1881 bytes — head)
- **rev** `0020_eng_analysis_run_label` · **down** `0019_pilot_run` · **created** 2026-06-22 · E-43 · ADDITIVE · owner Engine & Domain. **CHAIN HEAD.**
- **WHAT:** `ALTER TABLE eng.analysis_run ADD COLUMN IF NOT EXISTS label varchar(120)` (nullable) + `COMMENT`.
- **WHY (E-43, sponsor-ruled vital for the first live test):** during a live alignment meeting the buyer builds test versions (tune → run → repeat) and must SAVE a NAMED version freely, mid-meeting, DISTINCT from the terminal FREEZE (E-21). A version exists the moment `run_round` seals an `eng.analysis_run`; the missing piece is a human-given NAME. **Naming is plain metadata — NOT a governed decision: it writes NO audit event; FREEZE stays the only governed seal.** This extends the table created in migration 0008.
- **downgrade()** drops the column. Clean.

---

## B7-M.2 — Cross-cutting observations across the 20 migrations

### B7-M.2.1 Authoring style (two families)
- **Raw-SQL via `op.execute(UPGRADE_SQL)`** — migrations 0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0009, 0010, 0011, 0012, 0013, 0015, 0016, 0020 (16). Idempotency via `IF [NOT] EXISTS` and guarded `DO $$ ... $$` blocks checking `pg_constraint` for constraint adds (0005, 0007).
- **Python Alembic API via `op.create_table`/`op.bulk_insert`/`op.drop_table`** — migrations 0014, 0017, 0019 (3). These are the net-new-table migrations that also create their own schema (or seed data).
- **Pure data DML** — migration 0018 (1), `op.execute` of INSERT/UPDATE/DELETE only, no DDL.

### B7-M.2.2 Schema creation outside the eight layers
Three migrations create schemas **outside** `env.py`'s `SCHEMAS` set: `awd` (0010 — but `awd` IS in the baseline `SCHEMAS` tuple at 0001 and in `env.py`'s eight; 0010 just `CREATE SCHEMA IF NOT EXISTS awd` defensively since the baseline already made it), `auth` (0017), `pilot` (0019). `auth`/`pilot` are deliberately **not** governed layers (console identity / run orchestration must not live in the data spine). `env.py._include_object` ignores tables outside the eight layers, so autogenerate will not manage `auth.app_user`/`pilot.run`/`ref.fiscal_period`'s sibling schemas — consistent with their hand-authored DDL. **`ref.fiscal_period` (0014) IS in a governed schema (`ref`)**, so it would be autogenerate-managed.

### B7-M.2.3 The `cyc.cycle` table is the most-extended (migrations 0002, 0012, 0013)
`cyc.cycle` starts at 13 columns in the baseline (Part 1 §B7-S.2.1) and grows by: +8 (0002 kickoff header), +4 (0012 engine safeties), +1 (0013 weight preset) = **+13 columns + 1 CHECK** across three migrations → 26 columns at head. `bid.bid_line` is the second-most-extended: +4 (0007 engine components, +1 CHECK), +1 (0011 transit_days), +1 (0015 fiscal_period_id), and a constraint flip (0016) → the central price fact grows from 35 to 41 columns.

### B7-M.2.4 What each migration touches (one-line index)
| Rev | Schema/Table touched | Op | Net-new objects |
|---|---|---|---|
| 0001 | 8 schemas + full baseline | execute schema.sql + audit DDL | 64 tables (Part 1) |
| 0002 | `cyc.cycle` (+8 col), `cyc.cycle_invited_supplier` (+1 col) | ALTER + 8 CREATE | 8 cyc satellites |
| 0003 | `cyc` | CREATE | `cyc.cycle_safety` |
| 0004 | `norm` | CREATE×2 | `norm.attribute_def`, `norm.lot_attribute` |
| 0005 | `eng.scenario_award` | ALTER (+3 col, drop/add unique, +CHECK) | — |
| 0006 | `perf` | CREATE table + VIEW | `perf.itrade_receipt`, `v_itrade_actual_paid_baseline` |
| 0007 | `bid.bid_line` (+4 col, +CHECK) | ALTER | — |
| 0008 | `eng` | CREATE×4 | `analysis_run`, `bid_score`, `analysis_scenario`, `analysis_scenario_award` |
| 0009 | `eng.analysis_scenario_award` (+1 col) | ALTER | — |
| 0010 | `awd` (schema + 4 tables) | CREATE | whole `awd.*` layer |
| 0011 | `bid.bid_line` (+1 col) | ALTER | — |
| 0012 | `cyc.cycle` (+4 col) | ALTER | — |
| 0013 | `cyc.cycle` (+1 col, +CHECK) | ALTER | — |
| 0014 | `ref` | CREATE + seed 273 rows | `ref.fiscal_period` |
| 0015 | `bid.bid_line` (+1 col) | ALTER | — |
| 0016 | `bid.bid_line` (constraint flip) | DROP unique + 2 partial-unique idx | — |
| 0017 | `auth` (schema + table) | CREATE | `auth.app_user` |
| 0018 | `ref.client`, `ref.commodity` | DML backfill | data only |
| 0019 | `pilot` (schema + table) | CREATE | `pilot.run` |
| 0020 | `eng.analysis_run` (+1 col) | ALTER | — |

---

## B7-M.3 — GAPS / deviations found in the migrations

- **G-B7-M-1 (doc-vs-code, migration 0010):** docstring says downgrade "drops the four tables (child-first) + the schema", but `DOWNGRADE_SQL` drops only the four tables — it does **not** `DROP SCHEMA awd`. Harmless (idempotent re-create) but a real mismatch vs the 0017/0019 pattern which DO drop their schemas.
- **G-B7-M-2 (type drift, migrations 0014↔0015):** confirmed and load-bearing — `bid.bid_line.fiscal_period_id varchar(36)` (0015, unenforced) references `ref.fiscal_period.id uuid` (0014). Intentional per the PK convention but a silent type discontinuity. (Full analysis in Part 1 §B7-S.14 #1.)
- **G-B7-M-3 (unenforced lot references):** `cyc.cycle_scope_item.lot_id` (0002) and `norm.lot_attribute.lot_id` (0004) are `varchar(36)` with **no FK** because the persistent `norm.lot` store (M2/G8) does not exist on disk. Both docstrings promise an additive FK "when norm.lot lands" — that table is **not present**, so the references stay unenforced. A delivered-vs-promised gap dependent on a future migration.
- **G-B7-M-4 (rehydrated-snapshot edge, migration 0018):** a pre-G-B per-run DB rehydrated from a vault snapshot is not re-migrated (D34), so it stays orphaned and would raise on tenant resolution. The migration explicitly scopes this out — a known, accepted edge, flagged here so it is not mistaken for a bug.
- **G-B7-M-5 (downgrade safety caveat, migration 0005):** the 0005 downgrade (restore single-winner unique) is only safe while no cell holds >1 supplier. After the split LOGIC ships and a cell holds N suppliers, downgrading 0005 would fail on the re-added unique. The docstring states this; it is a real one-way-door once split data exists.
- **Census cross-check (all clean):** `env.py` (row 23), `script.py.mako` (row 24), and all 20 versions (rows 25–44) are present, non-empty, sizes match the on-disk `ls` exactly. The `__pycache__` dirs under `backend/alembic/` and `backend/alembic/versions/` are accounted for in bulk at FILE_CENSUS line 911 (`__pycache__ — 4671 files: third-party/generated, excluded from per-file audit`). **No file in this slice's scope is unaccounted for or silently skipped.**

---

*End of B7_migrations.md (Part 2 of 2). The baseline schema (every table, every column, the 46 composite FKs, the ER diagram, the constraint floor) is in `B7_schema.md` (Part 1 of 2).*
