-- ============================================================================
-- RFP / Sourcing Engine — Persistent Governed Data Layer
-- PostgreSQL 15+ DDL
-- ----------------------------------------------------------------------------
-- This schema is the SPINE the v3 engine lacks. The engine (scoring + allocation)
-- is a stateless library that reads from and writes into these tables. Nothing is
-- deleted; awarded terms freeze; live values layer on top; every change is logged.
--
-- Design rules baked in (from the intake, sessions 1-6):
--   * Grain: supplier x lot x DC x timeframe x round x price. (Period grain.)
--   * Lot (parent product), not UPC, is the bid/award grain. UPC maps up to lot.
--   * Awards are SPLIT: multiple suppliers per cell, each with a volume share.
--   * Two origins kept separate: grow-origin (supplier-stated) vs ship-from (PO).
--   * Freeze-and-layer: frozen_at seals a record; changes go to *_layer tables.
--   * Runs are immutable and config-snapshotted. Corrections = new runs.
--   * One feed (iTrade) powers BOTH historical cost AND the supplier scorecard.
--   * Decision-support, not auto-award: engine scores and proposes; humans select.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ref;     -- reference / dimensions
CREATE SCHEMA IF NOT EXISTS norm;    -- normalization (lot store)
CREATE SCHEMA IF NOT EXISTS cyc;     -- cycle / setup (the kickoff file)
CREATE SCHEMA IF NOT EXISTS bid;     -- bids + volumes
CREATE SCHEMA IF NOT EXISTS eng;     -- engine: runs, scores, scenarios
CREATE SCHEMA IF NOT EXISTS awd;     -- awards + generated outputs
CREATE SCHEMA IF NOT EXISTS perf;    -- iTrade / KCMS / scorecard
CREATE SCHEMA IF NOT EXISTS audit;   -- event log

-- ============================================================================
-- REF — reference / dimensions
-- ============================================================================

CREATE TABLE ref.commodity (
    code            text PRIMARY KEY,            -- SAP commodity code, e.g. '619'
    name            text NOT NULL                -- 'ONIONS'
);

CREATE TABLE ref.subcommodity (
    code            text PRIMARY KEY,            -- e.g. '61901'
    commodity_code  text NOT NULL REFERENCES ref.commodity(code),
    description     text NOT NULL,               -- 'ONIONS RED (BULK&BAG) ORGANIC'
    is_organic      boolean,                     -- parsed from description (NOP)
    pack_type       text                         -- parsed: bulk/bag/RPC/carton, nullable
);
COMMENT ON TABLE ref.subcommodity IS
  'The anchor. SubCommodity code carries grouped specs + packing variants. is_organic/pack_type are parsed hints, not authority; the lot decomposition is authoritative.';

CREATE TABLE ref.dc (
    dc_no           text PRIMARY KEY,            -- '015'
    name            text NOT NULL,               -- 'PUYALLUP'
    region          text                         -- 'West' / 'East' (drives FOB region)
);

CREATE TABLE ref.supplier (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    canonical_name  text NOT NULL UNIQUE         -- 'Onions52', resolved name
);

CREATE TABLE ref.supplier_alias (
    supplier_id     bigint NOT NULL REFERENCES ref.supplier(id),
    alias           text NOT NULL,               -- as seen on a bid/PO
    source          text,                        -- 'IN_Bids' | 'iTrade' | manual
    PRIMARY KEY (supplier_id, alias)
);
COMMENT ON TABLE ref.supplier_alias IS
  'Suppliers auto-upsert from bid intake; aliases collapse name variants to one canonical supplier.';

CREATE TABLE ref.item (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subcommodity_code text REFERENCES ref.subcommodity(code),
    primary_upc     text,                        -- 13-digit Case UPC
    case_size       text,                        -- '40 LB', '15 CT/10OZ' (raw)
    net_weight      numeric,
    ship_pack_qty   integer,
    warehouse_desc  text                         -- 'ONIONS RED ORGNC'
);

CREATE TABLE ref.item_alias (
    item_id         bigint NOT NULL REFERENCES ref.item(id),
    alias_type      text NOT NULL CHECK (alias_type IN ('UPC','KLN','RMS_SKU','DESCRIPTION')),
    alias_value     text NOT NULL,
    PRIMARY KEY (alias_type, alias_value)
);
COMMENT ON TABLE ref.item_alias IS
  'Items carry KLN + UPC + RMS Case SKU. All resolve to one item, which maps to one lot.';

CREATE TABLE ref.fiscal_calendar (
    cal_date        date PRIMARY KEY,
    fiscal_year     integer NOT NULL,
    period          integer NOT NULL,            -- 1..13 (Kroger periods)
    week_of_year    integer NOT NULL,
    period_week     integer                      -- 1..4 within period
);
COMMENT ON TABLE ref.fiscal_calendar IS
  'Loaded through 2037. Enables STLY (Same Time Last Year), the headline savings metric.';

CREATE TABLE ref.zip_centroid (
    zip             text PRIMARY KEY,
    lat             numeric NOT NULL,
    lon             numeric NOT NULL
);
COMMENT ON TABLE ref.zip_centroid IS
  'us_zip_centroids.csv. Source for ship-from -> DC distance (freight proxy).';

-- ============================================================================
-- NORM — normalization (the lot store; replaces the string-concat match key)
-- ============================================================================

CREATE TABLE norm.lot (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subcommodity_code text REFERENCES ref.subcommodity(code),
    lot_final_name  text NOT NULL,               -- canonical, e.g. 'PREMIUM SNACKING 9OZ'
    UNIQUE (subcommodity_code, lot_final_name)
);
COMMENT ON TABLE norm.lot IS
  'The parent product / canonical lot. The bid and award grain. Suppliers bid items; you award lots.';

CREATE TABLE norm.attribute_def (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    commodity_code  text REFERENCES ref.commodity(code),  -- NULL = universal
    name            text NOT NULL,               -- ORGANIC, COLOR, SIZE, PACK, PROCESS, STORAGE, VARIETY, GRADE, MOD
    is_universal    boolean NOT NULL DEFAULT false,
    UNIQUE (commodity_code, name)
);
COMMENT ON TABLE norm.attribute_def IS
  'Taxonomy = universal core (ORGANIC, COLOR, SIZE, PACK) + per-category extensions (tomato: VARIETY, PROCESS; onion: PACK TYPE, STORAGE). Confirm one pass per commodity at onboarding.';

CREATE TABLE norm.lot_attribute (
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    attribute_def_id bigint NOT NULL REFERENCES norm.attribute_def(id),
    value           text NOT NULL,               -- 'FIELD', 'RED', 'BEEFSTAKE', '9OZ'
    PRIMARY KEY (lot_id, attribute_def_id)
);
COMMENT ON TABLE norm.lot_attribute IS
  'The decomposition behind each lot. Storing attributes (not just the lot name) lets you regroup (all organic, all field-process) without re-mapping.';

CREATE TABLE norm.item_lot_map (
    item_id         bigint NOT NULL REFERENCES ref.item(id),
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    status          text NOT NULL DEFAULT 'proposed'
                       CHECK (status IN ('proposed','confirmed')),
    confirmed_by    text,
    confirmed_at    timestamptz,
    source          text,                        -- 'engine_propose' | 'manual'
    PRIMARY KEY (item_id)                         -- one live lot per item (sticky)
);
COMMENT ON TABLE norm.item_lot_map IS
  'UPC->lot, sticky. System proposes (status=proposed) from the description; a human confirms. Once confirmed it persists across cycles. This replaces the fragile product&DC string key.';

-- ============================================================================
-- CYC — cycle / setup (the kickoff file = the keystone)
-- ============================================================================

CREATE TABLE cyc.cycle (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    commodity_code  text NOT NULL REFERENCES ref.commodity(code),
    label           text NOT NULL,               -- 'Potato 2026'
    output_prefix   text,
    objective       text,                        -- savings|continuity|quality|diversification|strategic
    pricing_basis   text CHECK (pricing_basis IN ('fixed','index')),
    horizon         text CHECK (horizon IN ('short','long')),
    start_date      date,
    end_date        date,
    status          text NOT NULL DEFAULT 'draft'
                       CHECK (status IN ('draft','kickoff','open','final','signed_off','contracted','closed')),
    created_by      text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE cyc.cycle IS
  'The setup file. Declared at the strategy kickoff (the in-gate). Drives every downstream read. status traces the lifecycle through both governance gates.';

CREATE TABLE cyc.cycle_timeframe (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    tf_code         text NOT NULL,               -- 'TF1'
    start_date      date,
    end_date        date,
    weeks           integer,
    is_active       boolean NOT NULL DEFAULT true,
    UNIQUE (cycle_id, tf_code)
);
COMMENT ON TABLE cyc.cycle_timeframe IS
  'Timeframe is a DIMENSION, not a forked workbook. N timeframes run in one engine. This kills the Colored-Potato per-TF clone — the single biggest efficiency win.';

CREATE TABLE cyc.cycle_round (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    round_code      text NOT NULL,               -- 'R1'
    label           text,
    bid_type        text,                        -- 'FOB' | 'Delivered' | 'Hybrid'
    sequence        integer NOT NULL,
    is_final        boolean NOT NULL DEFAULT false,
    is_active       boolean NOT NULL DEFAULT true,
    UNIQUE (cycle_id, round_code)
);
COMMENT ON TABLE cyc.cycle_round IS
  'Rounds are variable (3 default, more if there is juice; R4 seen). Final/prior are flags, not hardcoded stage numbers.';

CREATE TABLE cyc.cycle_dc (
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    dc_no           text NOT NULL REFERENCES ref.dc(dc_no),
    in_scope        boolean NOT NULL DEFAULT true,
    PRIMARY KEY (cycle_id, dc_no)
);
COMMENT ON TABLE cyc.cycle_dc IS 'DC scope. Default ALL (national).';

CREATE TABLE cyc.cycle_lot (
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    in_scope        boolean NOT NULL DEFAULT true,
    PRIMARY KEY (cycle_id, lot_id)
);

CREATE TABLE cyc.cycle_term (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    topic           text NOT NULL,               -- 'Cost Structure','Food Safety','Service Level'
    detail          text,
    penalty         text,
    reward          text,
    accepted        boolean
);
COMMENT ON TABLE cyc.cycle_term IS
  'PBA / program terms. Presented in the bid packet (onion Program Details tab) and accepted Y/N by the supplier.';

-- ============================================================================
-- BID — bids + volumes (multi-template intake collapses to one grain)
-- ============================================================================

CREATE TABLE bid.bid (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    round_code      text NOT NULL,
    tf_code         text NOT NULL,
    supplier_id     bigint NOT NULL REFERENCES ref.supplier(id),
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    dc_no           text NOT NULL REFERENCES ref.dc(dc_no),
    completeness    text NOT NULL DEFAULT 'bid'
                       CHECK (completeness IN ('bid','no_bid','incomplete')),
    grow_origin     text,                        -- supplier-stated growing location
    ship_from_zip   text,                        -- ship-from (distinct from grow)
    distance_miles  numeric,                     -- derived ship-from -> DC
    weekly_vol_offered numeric,
    total_vol_offered  numeric,
    source_template text,                        -- 'tomato_flat' | 'onion_hybrid_9tab'
    imported_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (cycle_id, round_code, tf_code, supplier_id, lot_id, dc_no)
);
COMMENT ON TABLE bid.bid IS
  'One destination grain absorbs different intake shapes. The importer maps each template to this; grow-origin and ship-from are never auto-derived from each other.';

CREATE TABLE bid.bid_price (
    bid_id          bigint PRIMARY KEY REFERENCES bid.bid(id),
    all_in          numeric,                     -- PRIMARY: true delivered cost if populated
    fob             numeric,
    freight         numeric,
    delivered       numeric,
    xdock           numeric,
    vegcool_surcharge numeric,                   -- cold-chain surcharge component
    lot_discount    numeric,
    is_rpc          boolean,                     -- RPC vs corrugate pricing
    is_all_in_net_of_discount boolean,           -- guard flag (see CHECK below)
    CONSTRAINT no_double_discount CHECK (
        NOT (all_in IS NOT NULL AND is_all_in_net_of_discount IS TRUE
             AND lot_discount IS NOT NULL AND lot_discount <> 0)
    )
);
COMMENT ON TABLE bid.bid_price IS
  'Landed-cost reconstruction. all_in is primary; fallback = fob + freight + vegcool_surcharge - lot_discount. The CHECK enforces the double-subtraction guard the engine glossary flagged: if all_in is already net, lot_discount must be blank.';

CREATE TABLE bid.bid_index_component (
    bid_id          bigint NOT NULL REFERENCES bid.bid(id),
    component       text NOT NULL,               -- 'basis','index_ref','adder'
    value_text      text,
    PRIMARY KEY (bid_id, component)
);
COMMENT ON TABLE bid.bid_index_component IS
  'For index-basis cycles: store the components; the resolved price is computed, not stored as a fixed number.';

CREATE TABLE bid.volume_requirement (
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    dc_no           text NOT NULL REFERENCES ref.dc(dc_no),
    tf_code         text NOT NULL,
    weekly_required numeric,
    total_required  numeric,
    is_as_needed    boolean NOT NULL DEFAULT false,
    PRIMARY KEY (cycle_id, lot_id, dc_no, tf_code)
);
COMMENT ON TABLE bid.volume_requirement IS
  '"As needed" is a first-class value, not a number. Coverage scoring skips as-needed lots.';

CREATE TABLE bid.volume_limit (
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    supplier_id     bigint NOT NULL REFERENCES ref.supplier(id),
    dc_no           text,                        -- NULL = applies across DCs
    lot_id          bigint,                      -- NULL = applies across lots
    tf_code         text,
    weekly_cap      numeric,
    total_cap       numeric
);
COMMENT ON TABLE bid.volume_limit IS
  'Supplier capacity. Constrains the split allocation; no single supplier absorbs a whole cell.';

-- ============================================================================
-- ENG — engine: immutable runs, scores, scenarios
-- ============================================================================

CREATE TABLE eng.analysis_run (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    round_code      text NOT NULL,
    engine_version  text NOT NULL,               -- e.g. 'v3.c73ffc5'
    run_at          timestamptz NOT NULL DEFAULT now(),
    config_json     jsonb NOT NULL,              -- weights, thresholds, max_sup_dc, conc_thresh
    created_by      text,
    is_sealed       boolean NOT NULL DEFAULT true
);
COMMENT ON TABLE eng.analysis_run IS
  'Immutable. The full config is snapshotted into config_json so a run is reproducible and auditable. A correction is a NEW run, never an edit.';

CREATE TABLE eng.bid_score (
    run_id          bigint NOT NULL REFERENCES eng.analysis_run(id),
    bid_id          bigint NOT NULL REFERENCES bid.bid(id),
    price_score     numeric,
    coverage_score  numeric,
    hist_score      numeric,
    zrisk_score     numeric,
    continuity_score numeric,
    rec_score       numeric,                     -- weighted composite, max 100
    prem_vs_low     numeric,                     -- premium over market low
    z_score         numeric,
    eligible        boolean NOT NULL,
    gate_flags      text,                        -- reason codes when ineligible
    PRIMARY KEY (run_id, bid_id)
);
COMMENT ON TABLE eng.bid_score IS
  'Five banded factors (Price .35, Coverage .25, Historical .20, Z-Risk .10, Continuity .10) + composite. Cost is 35% of the decision, not 100%. gate_flags carry the eligibility reasons.';

CREATE TABLE eng.scenario (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          bigint NOT NULL REFERENCES eng.analysis_run(id),
    code            text NOT NULL,               -- 'A'..'G'
    label           text,
    description     text,
    UNIQUE (run_id, code)
);
COMMENT ON TABLE eng.scenario IS
  'Lenses: A lowest-cost benchmark, B risk-adjusted recommendation, C incumbent defense, D max-N per DC, E exclusion, F custom override, G preferred supplier.';

CREATE TABLE eng.scenario_award (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id     bigint NOT NULL REFERENCES eng.scenario(id),
    dc_no           text NOT NULL REFERENCES ref.dc(dc_no),
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    tf_code         text NOT NULL,
    supplier_id     bigint NOT NULL REFERENCES ref.supplier(id),
    volume_share    numeric,                     -- share of the cell's volume
    awarded_price   numeric,
    is_recommended  boolean NOT NULL DEFAULT false,
    is_fallback     boolean NOT NULL DEFAULT false,
    cap_breach_flag boolean NOT NULL DEFAULT false
);
COMMENT ON TABLE eng.scenario_award IS
  'THE SPLIT AWARD. A cell (dc x lot x tf) has one row PER awarded supplier, each with a volume_share. This is why they are "Allocation" models. The old single-winner rule is wrong.';

CREATE INDEX ix_scenario_award_cell
    ON eng.scenario_award (scenario_id, dc_no, lot_id, tf_code);

-- ============================================================================
-- AWD — selected awards (frozen) + freeze/layer + generated outputs
-- ============================================================================

CREATE TABLE awd.award (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    scenario_id     bigint NOT NULL REFERENCES eng.scenario(id),  -- the selected scenario
    dc_no           text NOT NULL REFERENCES ref.dc(dc_no),
    lot_id          bigint NOT NULL REFERENCES norm.lot(id),
    tf_code         text NOT NULL,
    supplier_id     bigint NOT NULL REFERENCES ref.supplier(id),
    volume_share    numeric,
    awarded_price   numeric,
    status          text NOT NULL DEFAULT 'recommended'
                       CHECK (status IN ('recommended','signed_off','contracted')),
    frozen_at       timestamptz                  -- set at sign-off; sealing the terms
);
COMMENT ON TABLE awd.award IS
  'The human-selected award, promoted from a scenario_award. Multiple rows per cell (split). frozen_at seals it at sign-off.';

CREATE TABLE awd.award_layer (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    award_id        bigint NOT NULL REFERENCES awd.award(id),
    layer_type      text NOT NULL CHECK (layer_type IN ('live','change')),
    field           text NOT NULL,
    value           text,
    effective_at    timestamptz NOT NULL DEFAULT now(),
    source          text
);
COMMENT ON TABLE awd.award_layer IS
  'Freeze-and-layer. Once awd.award.frozen_at is set, changes never overwrite it; they land here, date-stamped. The raw award is always recoverable.';

CREATE TABLE awd.signoff (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    scenario_id     bigint NOT NULL REFERENCES eng.scenario(id),
    total_savings_vs_stly numeric,
    status          text NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','approved')),
    approved_by     text,
    approved_at     timestamptz
);
COMMENT ON TABLE awd.signoff IS
  'The out-gate. Portfolio-level approval; savings vs STLY is the headline. Per-DC detail lives in awd.award / scenario_award.';

CREATE TABLE awd.generated_document (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    run_id          bigint REFERENCES eng.analysis_run(id),
    doc_type        text NOT NULL CHECK (doc_type IN
                       ('booking_guide','signoff_deck','award_letter',
                        'no_award_letter','feedback_letter','confirmation_email')),
    generated_at    timestamptz NOT NULL DEFAULT now(),
    payload_ref     text                         -- path / blob key to the rendered artifact
);
COMMENT ON TABLE awd.generated_document IS
  'Booking guide, sign-off deck, and letters are GENERATED from stored records, not hand-built. The confirmation email is the official record (draft->sent is a governance gate).';

-- ============================================================================
-- PERF — iTrade (one feed, two jobs) + KCMS + scorecard
-- ============================================================================

CREATE TABLE perf.itrade_receipt (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    po_number       text,
    line_no         text,
    subcommodity_code text REFERENCES ref.subcommodity(code),
    item_id         bigint REFERENCES ref.item(id),
    dc_no           text REFERENCES ref.dc(dc_no),
    supplier_id     bigint REFERENCES ref.supplier(id),
    ship_from_state text,
    ship_from_zip   text,
    routing         text,                        -- 'Delivered' | 'FOB' | ...
    qty_shipped     numeric,
    qty_received    numeric,
    qc_reject_qty   numeric,
    final_price_fob numeric,
    freight         numeric,
    total_w_freight numeric,
    xdock           numeric,
    cogs            numeric,
    fiscal_year     integer,
    period          integer,
    week_of_year    integer,
    ship_date       date,
    received_date   date,
    flag_zero_cost  boolean,
    flag_zero_qty   boolean,
    flag_canceled   boolean
);
COMMENT ON TABLE perf.itrade_receipt IS
  'Every PO receipt. ONE feed that powers BOTH historical awarded cost AND the scorecard. Importer trusts the flags first and rejects impossible date spans (received-before-shipped style dirt).';

CREATE INDEX ix_itrade_fiscal ON perf.itrade_receipt (fiscal_year, period, week_of_year);
CREATE INDEX ix_itrade_supplier ON perf.itrade_receipt (supplier_id, dc_no);

CREATE TABLE perf.kcms_movement (
    subcommodity_code text REFERENCES ref.subcommodity(code),
    gtin            text,
    fiscal_year     integer,
    period          integer,
    scan_units      numeric,
    margin          numeric,
    PRIMARY KEY (subcommodity_code, gtin, fiscal_year, period)
);
COMMENT ON TABLE perf.kcms_movement IS
  'KCMS scan movement / margin. A DISTINCT feed from iTrade (scan vs receipts). Do not conflate.';

CREATE TABLE perf.supplier_scorecard (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cycle_id        bigint NOT NULL REFERENCES cyc.cycle(id),
    snapshot_type   text NOT NULL CHECK (snapshot_type IN ('kickoff','signoff')),
    supplier_id     bigint NOT NULL REFERENCES ref.supplier(id),
    dc_no           text REFERENCES ref.dc(dc_no),
    volume_cases    numeric,
    pct_volume      numeric,
    pct_cost        numeric,
    fill_rate       numeric,
    adjusted_fill   numeric,
    on_time         numeric,
    dc_rejection    numeric,
    cost_per_case   numeric,
    age_at_receipt  numeric,
    frozen_at       timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE perf.supplier_scorecard IS
  'Captured TWICE per cycle (kickoff snapshot + sign-off snapshot), both frozen. All metrics derive from perf.itrade_receipt.';

-- ============================================================================
-- AUDIT — the event log (the _event_log utility, promoted to a governed store)
-- ============================================================================

CREATE TABLE audit.event_log (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at     timestamptz NOT NULL DEFAULT now(),
    actor           text,
    entity_schema   text NOT NULL,               -- 'cyc','bid','awd',...
    entity_table    text NOT NULL,
    entity_id       text NOT NULL,
    event_type      text NOT NULL,               -- 'created','sealed','frozen','superseded',...
    payload         jsonb
);
COMMENT ON TABLE audit.event_log IS
  'Append-only. The difference between a system of record and a pile of file generators. Every state change is an event. "Open last cycle" is a query over cyc.cycle + its rounds/bids/runs/scenarios/awards joined through this trail.';

CREATE INDEX ix_event_entity ON audit.event_log (entity_schema, entity_table, entity_id);
CREATE INDEX ix_event_time ON audit.event_log (occurred_at);

-- ============================================================================
-- END
-- ============================================================================
