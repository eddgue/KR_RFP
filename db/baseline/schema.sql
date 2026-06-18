-- ============================================================================
-- db/baseline/schema.sql — the Alembic baseline (revision 0001)
-- ============================================================================
-- Clean-room re-expression of the as-built schema as clean PostgreSQL 15 DDL.
-- This is OUR OWN artifact (ADR-0001), NOT an import of the existing codebase.
-- Source provenance + the canonicalization rule: see README.md and NAMING_MAP.md.
--
-- *** FULL RECONCILED BASELINE (M0) ***
-- All 63 as-built tables re-expressed as clean PostgreSQL 15, organized into the
-- eight logical-layer schemas (ref/norm/cyc/bid/eng/awd/perf/audit), schema-qualified
-- per NAMING_MAP.md. The KEEP spine, all 46 composite-identity FKs, the partial unique
-- indexes, and all 67 CHECK constraints (the no-op error_log branch de-no-op'd) are
-- preserved. SQLite-isms removed (native boolean, real predicates). Enums rendered as
-- governed `text` columns with the as-built membership CHECKs preserved where the
-- source proves the value set (the auto-generated as-built SQL does not emit the ENUM
-- value lists; rather than invent values we keep the columns as text and retain every
-- CHECK that constrains them — faithful to PLAN §2 "CHECK ... IN" option).
--
-- INVARIANTS this file must always hold (backend alembic 0001 executes it verbatim):
--   * IDEMPOTENT  — re-running is a no-op (IF NOT EXISTS everywhere; guarded DO blocks).
--   * SELF-CONTAINED — no \i includes, no external functions, runs on a bare PG15.
--   * CLEAN PG — native `boolean` (no DEFAULT 0/1), no SQLite-isms, real predicates.
--
-- TENANCY (M10, NOT M0): ADR-0004's broad client_id weave across all 63 tables is a
-- LATER migration (M10 / E-03). M0 keeps client_id ONLY where it already exists:
-- ref.client (the tenant root) and ref.commodity (the tenant-scoping demonstrator the
-- ORM is wired to). The other ~60 tables are NOT yet tenant-scoped here.
--
-- PK CONVENTION (Phase-0 decision, README.md): net-new spine tables (ref.client,
-- ref.commodity, audit.event_log) use native `uuid` PKs. The ~60 ADOPTED as-built
-- tables retain their text-UUID (varchar(36)) PKs verbatim so the 46 composite-identity
-- FKs re-express byte-for-byte (changing the key type would break that rigor mapping).
--
-- RECONCILED TOWARD LIVE CODE:
--   * ref.client / ref.commodity columns are kept EXACTLY as app/domain/ref/models.py
--     maps them (uuid id, client_id, client_code/client_name/is_active, commodity_code/
--     commodity_name/active_flag). The as-built `commodity_master_db` had a text
--     commodity_id PK and global UNIQUE(commodity_code); the canonical commodity is the
--     uuid-keyed, tenant-scoped table. Consequence: the 4 single-column as-built FKs that
--     pointed at commodity_master_db(commodity_id) are DROPPED (the canonical commodity
--     has no text commodity_id to reference). The adopted reference tables KEEP their own
--     commodity_id varchar(36) columns and ALL composite identity pairs/FKs among
--     themselves (item↔subcommodity↔cycle) — the enterprise rigor survives intact.
--   * audit.event_log columns are kept EXACTLY as app/core/audit/writer.py INSERTs
--     (id, client_id, occurred_at, actor, source, event_type, entity_type, entity_id,
--     cycle_id, before_state_hash, after_state_hash, prev_event_hash, event_hash, seq).
--     The as-built `audit_event` (event_id/event_ts/before_state_hash/after_state_hash/
--     prev_event_hash/event_hash/success_status/...) is reconciled toward the writer
--     (live code wins). The as-built's extra provenance columns are noted in the audit
--     section; M1 makes the chain write-only (triggers + grants).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. The eight logical-layer schemas (PLAN §2). Idempotent; Alembic + the infra
--    init script (infra/postgres/init/01_schemas.sql) both ensure these.
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS ref;     -- reference / master data + tenant
CREATE SCHEMA IF NOT EXISTS norm;    -- normalization: lineage, runs, source artifacts
CREATE SCHEMA IF NOT EXISTS cyc;     -- RFP cycle keystone + scope + rounds
CREATE SCHEMA IF NOT EXISTS bid;     -- bid submissions, landed cost, eligibility, capacity, volume
CREATE SCHEMA IF NOT EXISTS eng;     -- sealed calc runs, scenarios, version pins
CREATE SCHEMA IF NOT EXISTS awd;     -- awards, layers, signoff, generated documents (greenfield; M8)
CREATE SCHEMA IF NOT EXISTS perf;    -- historical award cost, commercial pricing layer
CREATE SCHEMA IF NOT EXISTS audit;   -- hash-chained event log + decision notes + round lifecycle


-- ===========================================================================
-- 2. ref — reference / dimensions + tenant root
-- ===========================================================================

-- ref.client — the tenant root (ADD; net-new enterprise layer). KEEP EXACTLY as the ORM
-- (app/domain/ref/models.py Client) maps it. client_id FK columns hang off this; the broad
-- tenant weave + RLS policy is M10 (E-03, Security).
CREATE TABLE IF NOT EXISTS ref.client (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_code     varchar(40)  NOT NULL,
    client_name     varchar(160) NOT NULL,
    is_active       boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_client_code UNIQUE (client_code),
    CONSTRAINT ck_client_code_not_empty CHECK (length(client_code) > 0)
);
COMMENT ON TABLE ref.client IS
    'Tenant root (net-new). client_id FK columns hang off this; broad tenant weave + RLS at M10.';

-- ref.commodity — ADOPT of as-built commodity_master_db, schema-qualified + tenant-scoped.
-- KEEP EXACTLY as the ORM (Commodity) maps it (uuid id, client_id, commodity_code/_name,
-- abbreviation, active_flag). As-built global UNIQUE(commodity_code)/(commodity_name) become
-- a per-tenant unique on (client_id, commodity_code).
CREATE TABLE IF NOT EXISTS ref.commodity (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       uuid         REFERENCES ref.client (id),
    commodity_code  varchar(40)  NOT NULL,
    commodity_name  varchar(120) NOT NULL,
    abbreviation    varchar(20),
    active_flag     boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_commodity_code_per_client UNIQUE (client_id, commodity_code),
    CONSTRAINT ck_commodity_code_not_empty  CHECK (length(commodity_code) > 0)
);
COMMENT ON TABLE ref.commodity IS
    'ADOPT of as-built commodity_master_db, schema-qualified + tenant-scoped (client_id). Mirrors ORM.';
CREATE INDEX IF NOT EXISTS ix_commodity_client ON ref.commodity (client_id);

-- ref.subcommodity — ADOPT of subcommodity_master. Keeps its text commodity_id column +
-- the (subcommodity_id, commodity_id) composite identity pair that item/cycle reference.
-- (The single-col FK to commodity_master_db(commodity_id) is dropped — see header.)
CREATE TABLE IF NOT EXISTS ref.subcommodity (
    subcommodity_id     varchar(36)  NOT NULL,
    commodity_id        varchar(36)  NOT NULL,
    subcommodity_code   varchar(40)  NOT NULL,
    subcommodity_name   varchar(120) NOT NULL,
    active_flag         boolean      NOT NULL,
    PRIMARY KEY (subcommodity_id),
    CONSTRAINT uq_subcom_code_per_commodity UNIQUE (commodity_id, subcommodity_code),
    CONSTRAINT uq_subcom_commodity_pair UNIQUE (subcommodity_id, commodity_id)
);

-- ref.dc — ADOPT of dc_master_db (drop _master_db).
CREATE TABLE IF NOT EXISTS ref.dc (
    dc_id        varchar(36)  NOT NULL,
    dc_code      varchar(10)  NOT NULL,
    dc_name      varchar(120) NOT NULL,
    region       varchar(40),
    division     varchar(40),
    active_flag  boolean      NOT NULL,
    PRIMARY KEY (dc_id),
    UNIQUE (dc_code),
    UNIQUE (dc_name)
);

-- ref.supplier — ADOPT of supplier_master.
CREATE TABLE IF NOT EXISTS ref.supplier (
    supplier_id     varchar(36)  NOT NULL,
    canonical_name  varchar(200) NOT NULL,
    aliases         text,
    active_flag     boolean      NOT NULL,
    created_at      timestamp    NOT NULL,
    PRIMARY KEY (supplier_id),
    UNIQUE (canonical_name)
);

-- ref.item — ADOPT of item_master. Keeps composite (item_id, commodity_id)/(item_id,
-- subcommodity_id) pairs + the (subcommodity_id, commodity_id) FK to ref.subcommodity.
CREATE TABLE IF NOT EXISTS ref.item (
    item_id          varchar(36)  NOT NULL,
    upc              varchar(40),
    item_code        varchar(60)  NOT NULL,
    description      varchar(300) NOT NULL,
    pack_desc        varchar(60),
    commodity_id     varchar(36)  NOT NULL,
    subcommodity_id  varchar(36),
    active_start     date,
    active_end       date,
    PRIMARY KEY (item_id),
    CONSTRAINT fk_item_subcom_in_commodity FOREIGN KEY (subcommodity_id, commodity_id)
        REFERENCES ref.subcommodity (subcommodity_id, commodity_id),
    CONSTRAINT uq_item_commodity_pair UNIQUE (item_id, commodity_id),
    CONSTRAINT uq_item_subcom_pair UNIQUE (item_id, subcommodity_id),
    UNIQUE (upc),
    UNIQUE (item_code)
);

-- ref.loading_location — ADOPT of loading_location. Composite (location_id, supplier_id).
CREATE TABLE IF NOT EXISTS ref.loading_location (
    location_id        varchar(36)  NOT NULL,
    supplier_id        varchar(36)  NOT NULL,
    location_name      varchar(160) NOT NULL,
    address_line       varchar(300),
    city               varchar(80)  NOT NULL,
    country_code       varchar(2)   NOT NULL,
    region_code        varchar(10),
    postal_code        varchar(20),
    active_start       date,
    active_end         date,
    evidence_reference text,
    active_flag        boolean      NOT NULL,
    PRIMARY KEY (location_id),
    CONSTRAINT uq_loc_supplier_pair UNIQUE (location_id, supplier_id),
    CONSTRAINT ck_loc_country_code_two_char CHECK (length(country_code) = 2),
    CONSTRAINT ck_loc_active_dates_ordered
        CHECK (active_end IS NULL OR active_start IS NULL OR active_end >= active_start),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_loc_supplier_name_geo
    ON ref.loading_location (supplier_id, location_name, country_code, COALESCE(region_code, ''), city);

-- ref.fiscal_calendar — ADOPT of fiscal_date_conversion (CLEAN: → ref.fiscal_calendar; seed at M-later).
CREATE TABLE IF NOT EXISTS ref.fiscal_calendar (
    calendar_date              date    NOT NULL,
    fiscal_year                integer NOT NULL,
    fiscal_quarter_number      integer NOT NULL,
    fiscal_quarter_label       varchar(20),
    fiscal_period_number       integer NOT NULL,
    fiscal_period_label        varchar(20),
    fiscal_period_week_number  integer NOT NULL,
    fiscal_week_number         integer NOT NULL,
    fiscal_week_label          varchar(20),
    source_calendar_id         varchar(36),
    source_file                text,
    loaded_at                  timestamp,
    loaded_by                  varchar(120),
    PRIMARY KEY (calendar_date),
    CONSTRAINT ck_fiscal_date_quarter_range CHECK (fiscal_quarter_number >= 1 AND fiscal_quarter_number <= 4),
    CONSTRAINT ck_fiscal_date_period_range CHECK (fiscal_period_number >= 1 AND fiscal_period_number <= 13),
    CONSTRAINT ck_fiscal_date_period_week_range CHECK (fiscal_period_week_number >= 1 AND fiscal_period_week_number <= 5),
    CONSTRAINT ck_fiscal_date_week_range CHECK (fiscal_week_number >= 1 AND fiscal_week_number <= 53)
);

-- ref.supplier_alias — ADOPT (KEEP #6). Typed, partial-unique-active, deactivation lineage.
-- SQLite-ism cleaned: active_flag = 1/0 → boolean predicates.
CREATE TABLE IF NOT EXISTS ref.supplier_alias (
    supplier_alias_id     varchar(36) NOT NULL,
    alias_text            text        NOT NULL,
    normalized_alias_text text        NOT NULL,
    supplier_id           varchar(36) NOT NULL,
    alias_type            text        NOT NULL,
    source                text        NOT NULL,
    created_by            varchar(120) NOT NULL,
    created_at            timestamp   NOT NULL,
    active_flag           boolean     NOT NULL,
    notes                 text,
    active_from           timestamp,
    active_until          timestamp,
    deactivated_by        varchar(120),
    deactivated_at        timestamp,
    deactivation_reason   text,
    PRIMARY KEY (supplier_alias_id),
    CONSTRAINT ck_supplier_alias_deactivation_consistency CHECK (
        (active_flag = true  AND deactivated_at IS NULL AND deactivated_by IS NULL AND deactivation_reason IS NULL)
     OR (active_flag = false AND deactivated_at IS NOT NULL AND deactivated_by IS NOT NULL AND deactivation_reason IS NOT NULL)),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_supplier_alias_norm_typed_active
    ON ref.supplier_alias (alias_type, normalized_alias_text) WHERE active_flag = true;

-- ref.item_alias — ADOPT (KEEP #6). Commodity/subcom-scoped partial unique index.
CREATE TABLE IF NOT EXISTS ref.item_alias (
    item_alias_id         varchar(36) NOT NULL,
    alias_text            text        NOT NULL,
    normalized_alias_text text        NOT NULL,
    item_id               varchar(36) NOT NULL,
    alias_type            text        NOT NULL,
    source                text        NOT NULL,
    created_by            varchar(120) NOT NULL,
    created_at            timestamp   NOT NULL,
    active_flag           boolean     NOT NULL,
    notes                 text,
    commodity_id          varchar(36),
    subcommodity_id       varchar(36),
    active_from           timestamp,
    active_until          timestamp,
    deactivated_by        varchar(120),
    deactivated_at        timestamp,
    deactivation_reason   text,
    PRIMARY KEY (item_alias_id),
    CONSTRAINT ck_item_alias_deactivation_consistency CHECK (
        (active_flag = true  AND deactivated_at IS NULL AND deactivated_by IS NULL AND deactivation_reason IS NULL)
     OR (active_flag = false AND deactivated_at IS NOT NULL AND deactivated_by IS NOT NULL AND deactivation_reason IS NOT NULL)),
    FOREIGN KEY (item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (subcommodity_id) REFERENCES ref.subcommodity (subcommodity_id)
);
-- Partial unique index: as-built keyed on COALESCE sentinels ('__GLOBAL__','__ANY__'). text
-- columns coalesce cleanly here (varchar values, not uuid), preserving the as-built semantics.
CREATE UNIQUE INDEX IF NOT EXISTS uq_item_alias_norm_typed_active
    ON ref.item_alias (alias_type, normalized_alias_text,
                       COALESCE(commodity_id, '__GLOBAL__'),
                       COALESCE(subcommodity_id, '__ANY__'))
    WHERE active_flag = true;

-- ref.dc_alias — ADOPT (KEEP #6). DC text resolution.
CREATE TABLE IF NOT EXISTS ref.dc_alias (
    dc_alias_id           varchar(36) NOT NULL,
    alias_text            text        NOT NULL,
    normalized_alias_text text        NOT NULL,
    dc_id                 varchar(36) NOT NULL,
    source                text        NOT NULL,
    created_by            varchar(120) NOT NULL,
    created_at            timestamp   NOT NULL,
    active_flag           boolean     NOT NULL,
    notes                 text,
    active_from           timestamp,
    active_until          timestamp,
    deactivated_by        varchar(120),
    deactivated_at        timestamp,
    deactivation_reason   text,
    PRIMARY KEY (dc_alias_id),
    CONSTRAINT ck_dc_alias_deactivation_consistency CHECK (
        (active_flag = true  AND deactivated_at IS NULL AND deactivated_by IS NULL AND deactivation_reason IS NULL)
     OR (active_flag = false AND deactivated_at IS NOT NULL AND deactivated_by IS NOT NULL AND deactivation_reason IS NOT NULL)),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_dc_alias_normalized_active
    ON ref.dc_alias (normalized_alias_text) WHERE active_flag = true;

-- ref.master_data_quarantine — ADOPT (KEEP #6). The "never guess" queue.
CREATE TABLE IF NOT EXISTS ref.master_data_quarantine (
    quarantine_id          varchar(36) NOT NULL,
    source_artifact        text        NOT NULL,
    source_sheet           text        NOT NULL,
    source_row             integer     NOT NULL,
    raw_value              text        NOT NULL,
    normalized_value       text        NOT NULL,
    domain                 text        NOT NULL,
    rejection_reason       text        NOT NULL,
    candidate_matches_json text,
    ingestion_run_id       varchar(80) NOT NULL,
    cycle_id               varchar(36),
    resolved_action        text,
    analyst_resolution     text        NOT NULL,
    resolved_alias_id      varchar(36),
    resolved_to_target_id  varchar(36),
    resolved_by            varchar(120),
    resolved_at            timestamp,
    notes                  text,
    PRIMARY KEY (quarantine_id),
    CONSTRAINT uq_quarantine_source_row_domain UNIQUE (source_artifact, source_sheet, source_row, domain)
    -- FK cycle_id → cyc.cycle is deferred to the end of this file (cyc.cycle is defined later;
    -- ref ↔ cyc ↔ norm have a cross-schema cycle that forbids a single linear creation order).
);


-- ===========================================================================
-- 3. cyc — cycle / setup (the keystone)
-- ===========================================================================

-- cyc.cycle — CLEAN of rfp_cycle (NAMING_MAP). Keeps why_now/target_savings_amt/round_count
-- CHECK 2–6 + the (cycle_id, commodity_id) composite pair + (subcommodity_id, commodity_id)
-- FK to ref.subcommodity. The single-col FK to commodity_master_db(commodity_id) is dropped
-- (canonical ref.commodity is uuid-keyed). brief's pricing_basis/objective/horizon are M9.
CREATE TABLE IF NOT EXISTS cyc.cycle (
    cycle_id              varchar(36)  NOT NULL,
    cycle_code            varchar(40)  NOT NULL,
    cycle_name            varchar(120) NOT NULL,
    commodity_id          varchar(36)  NOT NULL,
    subcommodity_id       varchar(36),
    status                text         NOT NULL,
    why_now               text         NOT NULL,
    target_effective_date date         NOT NULL,
    target_savings_amt    numeric(18, 2),
    round_count           integer      NOT NULL,
    owner_actor_id        varchar(120),
    created_at            timestamp    NOT NULL,
    created_by            varchar(120) NOT NULL,
    PRIMARY KEY (cycle_id),
    CONSTRAINT ck_cycle_round_count_range CHECK (round_count BETWEEN 2 AND 6),
    CONSTRAINT fk_cycle_subcom_in_commodity FOREIGN KEY (subcommodity_id, commodity_id)
        REFERENCES ref.subcommodity (subcommodity_id, commodity_id),
    CONSTRAINT uq_cycle_commodity_pair UNIQUE (cycle_id, commodity_id),
    CONSTRAINT uq_cycle_subcom_pair UNIQUE (cycle_id, subcommodity_id),
    UNIQUE (cycle_code)
);

-- cyc.cycle_timeframe — ADOPT of cycle_tf. Composite (tf_id, cycle_id).
CREATE TABLE IF NOT EXISTS cyc.cycle_timeframe (
    tf_id       varchar(36)  NOT NULL,
    cycle_id    varchar(36)  NOT NULL,
    tf_code     varchar(20)  NOT NULL,
    tf_name     varchar(120) NOT NULL,
    start_date  date         NOT NULL,
    end_date    date         NOT NULL,
    week_count  integer      NOT NULL,
    rationale   text,
    PRIMARY KEY (tf_id),
    CONSTRAINT uq_tf_code_per_cycle UNIQUE (cycle_id, tf_code),
    CONSTRAINT uq_tf_cycle_pair UNIQUE (tf_id, cycle_id),
    CONSTRAINT ck_tf_week_count_positive CHECK (week_count > 0),
    CONSTRAINT ck_tf_date_range_positive CHECK (end_date > start_date),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- cyc.cycle_round — ADOPT of cycle_round. Forward-only round_status; (round_id, cycle_id).
CREATE TABLE IF NOT EXISTS cyc.cycle_round (
    round_id        varchar(36) NOT NULL,
    cycle_id        varchar(36) NOT NULL,
    round_number    integer     NOT NULL,
    status          varchar(40) NOT NULL,
    round_status    text,
    is_final        boolean     NOT NULL,
    invite_due_at   timestamp,
    bid_due_at      timestamp,
    meeting_due_at  timestamp,
    PRIMARY KEY (round_id),
    CONSTRAINT uq_round_number_per_cycle UNIQUE (cycle_id, round_number),
    CONSTRAINT uq_round_cycle_pair UNIQUE (round_id, cycle_id),
    CONSTRAINT ck_round_number_positive CHECK (round_number > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- cyc.cycle_item_scope — ADOPT. In/out scope with rationale. Composite identity FKs to
-- cycle (cycle_id, commodity_id)/(cycle_id, subcommodity_id) and item.
CREATE TABLE IF NOT EXISTS cyc.cycle_item_scope (
    cycle_id          varchar(36)  NOT NULL,
    item_id           varchar(36)  NOT NULL,
    commodity_id      varchar(36)  NOT NULL,
    subcommodity_id   varchar(36),
    inclusion_status  text         NOT NULL,
    rationale         text,
    added_at          timestamp    NOT NULL,
    added_by          varchar(120) NOT NULL,
    PRIMARY KEY (cycle_id, item_id),
    CONSTRAINT fk_scope_cycle_commodity FOREIGN KEY (cycle_id, commodity_id)
        REFERENCES cyc.cycle (cycle_id, commodity_id),
    CONSTRAINT fk_scope_cycle_subcom FOREIGN KEY (cycle_id, subcommodity_id)
        REFERENCES cyc.cycle (cycle_id, subcommodity_id),
    CONSTRAINT fk_scope_item_commodity FOREIGN KEY (item_id, commodity_id)
        REFERENCES ref.item (item_id, commodity_id),
    CONSTRAINT fk_scope_item_subcom FOREIGN KEY (item_id, subcommodity_id)
        REFERENCES ref.item (item_id, subcommodity_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (item_id) REFERENCES ref.item (item_id)
);

-- cyc.cycle_lot — CLEAN of cycle_lot (becomes scope over persistent norm.lot at M2/G8).
CREATE TABLE IF NOT EXISTS cyc.cycle_lot (
    lot_id       varchar(36)  NOT NULL,
    cycle_id     varchar(36)  NOT NULL,
    lot_code     varchar(40)  NOT NULL,
    lot_name     varchar(120) NOT NULL,
    rationale    text,
    active_flag  boolean      NOT NULL,
    PRIMARY KEY (lot_id),
    CONSTRAINT uq_lot_code_per_cycle UNIQUE (cycle_id, lot_code),
    CONSTRAINT uq_lot_cycle_pair UNIQUE (lot_id, cycle_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- cyc.cycle_lot_item — CLEAN of cycle_lot_item. One lot per item per cycle.
CREATE TABLE IF NOT EXISTS cyc.cycle_lot_item (
    lot_item_id    varchar(36) NOT NULL,
    cycle_id       varchar(36) NOT NULL,
    lot_id         varchar(36) NOT NULL,
    item_id        varchar(36) NOT NULL,
    required_flag  boolean     NOT NULL,
    sort_order     integer     NOT NULL,
    PRIMARY KEY (lot_item_id),
    CONSTRAINT uq_item_per_lot UNIQUE (lot_id, item_id),
    CONSTRAINT uq_one_lot_per_item_per_cycle UNIQUE (cycle_id, item_id),
    CONSTRAINT fk_lotitem_lot_in_cycle FOREIGN KEY (lot_id, cycle_id)
        REFERENCES cyc.cycle_lot (lot_id, cycle_id),
    CONSTRAINT fk_lotitem_in_cycle_scope FOREIGN KEY (cycle_id, item_id)
        REFERENCES cyc.cycle_item_scope (cycle_id, item_id)
);

-- cyc.cycle_projected_volume — ADOPT. Demand at DC×item×tf.
CREATE TABLE IF NOT EXISTS cyc.cycle_projected_volume (
    volume_id               varchar(36) NOT NULL,
    cycle_id                varchar(36) NOT NULL,
    dc_id                   varchar(36) NOT NULL,
    item_id                 varchar(36) NOT NULL,
    tf_id                   varchar(36) NOT NULL,
    volume_input_method     text        NOT NULL,
    projected_weekly_cases  numeric(18, 3),
    projected_period_cases  numeric(18, 3) NOT NULL,
    growth_override_pct     numeric(9, 6),
    normalization_run_id    varchar(36),
    PRIMARY KEY (volume_id),
    CONSTRAINT uq_volume_cell UNIQUE (cycle_id, dc_id, item_id, tf_id),
    CONSTRAINT fk_volume_tf_in_cycle FOREIGN KEY (tf_id, cycle_id)
        REFERENCES cyc.cycle_timeframe (tf_id, cycle_id),
    CONSTRAINT fk_volume_item_in_cycle_scope FOREIGN KEY (cycle_id, item_id)
        REFERENCES cyc.cycle_item_scope (cycle_id, item_id),
    CONSTRAINT ck_volume_method_consistency CHECK (
        (volume_input_method = 'WEEKLY_X_WEEKS' AND projected_weekly_cases IS NOT NULL)
     OR (volume_input_method = 'DIRECT_PERIOD_CASES' AND projected_weekly_cases IS NULL)),
    CONSTRAINT ck_volume_period_nonneg CHECK (projected_period_cases >= 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
    -- FK normalization_run_id → norm.normalization_run is deferred to the end of this file
    -- (norm.* is created after cyc.* to break the cross-schema dependency cycle).
);

-- cyc.cycle_invited_supplier — ADOPT (KEEP). The submitted-vs-missing denominator.
CREATE TABLE IF NOT EXISTS cyc.cycle_invited_supplier (
    cycle_id     varchar(36)  NOT NULL,
    supplier_id  varchar(36)  NOT NULL,
    invited_at   timestamp    NOT NULL,
    invited_by   varchar(120) NOT NULL,
    PRIMARY KEY (cycle_id, supplier_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);


-- ===========================================================================
-- 4. norm — normalization lineage (source artifacts, runs)
-- ===========================================================================

-- norm.source_artifact — ADOPT (KEEP). sha256 lineage + provenance identity quads.
CREATE TABLE IF NOT EXISTS norm.source_artifact (
    artifact_id        varchar(36)  NOT NULL,
    artifact_type      text         NOT NULL,
    file_name          varchar(300) NOT NULL,
    file_hash_sha256   varchar(64)  NOT NULL,
    received_at        timestamp    NOT NULL,
    location_reference varchar(500),
    status             text         NOT NULL,
    cycle_id           varchar(36),
    round_id           varchar(36),
    supplier_id        varchar(36),
    created_by         varchar(120) NOT NULL,
    PRIMARY KEY (artifact_id),
    CONSTRAINT fk_artifact_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT ck_artifact_bid_provenance CHECK (
        artifact_type <> 'BID_SUBMISSION'
     OR (cycle_id IS NOT NULL AND round_id IS NOT NULL AND supplier_id IS NOT NULL)),
    CONSTRAINT ck_artifact_capacity_provenance CHECK (
        artifact_type <> 'CAPACITY_EVIDENCE'
     OR (cycle_id IS NOT NULL AND supplier_id IS NOT NULL)),
    CONSTRAINT uq_artifact_identity_quad UNIQUE (artifact_id, cycle_id, round_id, supplier_id),
    CONSTRAINT uq_artifact_cycle_supplier UNIQUE (artifact_id, cycle_id, supplier_id),
    CONSTRAINT uq_artifact_round UNIQUE (artifact_id, round_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);

-- norm.normalization_run — ADOPT (KEEP). Which files fed a normalized load.
CREATE TABLE IF NOT EXISTS norm.normalization_run (
    normalization_run_id varchar(36) NOT NULL,
    dataset_type         text        NOT NULL,
    cycle_id             varchar(36),
    status               text        NOT NULL,
    approved_at          timestamp,
    approved_by          varchar(120),
    PRIMARY KEY (normalization_run_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- norm.normalization_run_source — ADOPT (KEEP). Run ↔ source artifact link.
CREATE TABLE IF NOT EXISTS norm.normalization_run_source (
    normalization_run_id varchar(36) NOT NULL,
    source_artifact_id   varchar(36) NOT NULL,
    source_role          text        NOT NULL,
    added_at             timestamp   NOT NULL,
    PRIMARY KEY (normalization_run_id, source_artifact_id),
    FOREIGN KEY (normalization_run_id) REFERENCES norm.normalization_run (normalization_run_id),
    FOREIGN KEY (source_artifact_id) REFERENCES norm.source_artifact (artifact_id)
);


-- ===========================================================================
-- 5. eng — sealed calc-run spine, version pins, Scenario A (KEEP #2)
--    (Authored before bid.* because bid.landed_cost_result / eligibility_* FK into it.)
-- ===========================================================================

-- eng.metric_definition_version — ADOPT (KEEP). Formula version pin.
CREATE TABLE IF NOT EXISTS eng.metric_definition_version (
    metric_version_id varchar(36) NOT NULL,
    formula_family    varchar(80) NOT NULL,
    version_code      varchar(40) NOT NULL,
    status            text        NOT NULL,
    expression_text   text        NOT NULL,
    effective_from    timestamp   NOT NULL,
    approved_by       varchar(120),
    tolerance_abs     numeric(18, 6),
    tolerance_pct     numeric(9, 6),
    PRIMARY KEY (metric_version_id),
    CONSTRAINT uq_formula_family_version UNIQUE (formula_family, version_code)
);

-- eng.scenario_config_version — ADOPT (KEEP). Config version pin.
CREATE TABLE IF NOT EXISTS eng.scenario_config_version (
    scenario_config_version_id varchar(36)  NOT NULL,
    config_label               varchar(120) NOT NULL,
    version_code               varchar(40)  NOT NULL,
    status                     text         NOT NULL,
    parameters_json            text         NOT NULL,
    effective_from             timestamp    NOT NULL,
    approved_by                varchar(120),
    PRIMARY KEY (scenario_config_version_id),
    CONSTRAINT uq_scenario_config_label_version UNIQUE (config_label, version_code)
);

-- eng.engine_release — ADOPT (KEEP). Engine version pin (git sha).
CREATE TABLE IF NOT EXISTS eng.engine_release (
    engine_release_id varchar(36) NOT NULL,
    release_label     varchar(60) NOT NULL,
    git_commit_sha    varchar(64) NOT NULL,
    status            text        NOT NULL,
    released_at       timestamp,
    test_status       varchar(40),
    notes             text,
    PRIMARY KEY (engine_release_id),
    CONSTRAINT uq_engine_release_label UNIQUE (release_label),
    CONSTRAINT uq_engine_release_sha UNIQUE (git_commit_sha),
    CONSTRAINT ck_engine_released_requires_timestamp CHECK (
        (status IN ('RELEASED', 'DEPRECATED') AND released_at IS NOT NULL)
     OR status IN ('DRAFT', 'TESTED')),
    CONSTRAINT ck_engine_sha_min_length CHECK (length(git_commit_sha) >= 7)
);

-- eng.calculation_run — ADOPT (KEEP #2). Sealed run spine: hashed manifests, execution
-- contract, version pins, identity triples. The no-op error_log CHECK branch is DE-NO-OP'd.
CREATE TABLE IF NOT EXISTS eng.calculation_run (
    calc_run_id                 varchar(36)  NOT NULL,
    cycle_id                    varchar(36)  NOT NULL,
    round_id                    varchar(36),
    run_type                    text         NOT NULL,
    status                      text         NOT NULL,
    source_snapshot_id          varchar(36),
    metric_version_id           varchar(36),
    scenario_config_version_id  varchar(36),
    engine_release_id           varchar(36),
    run_started_at              timestamp    NOT NULL,
    run_finished_at             timestamp,
    run_by                      varchar(120) NOT NULL,
    input_hash_manifest         text,
    output_hash_manifest        text,
    error_log                   text,
    execution_contract          text,
    upstream_calc_run_id        varchar(36),
    PRIMARY KEY (calc_run_id),
    CONSTRAINT fk_calcrun_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT uq_calcrun_identity_triple UNIQUE (calc_run_id, cycle_id, round_id),
    CONSTRAINT uq_calcrun_identity_metric_quad UNIQUE (calc_run_id, cycle_id, round_id, metric_version_id),
    CONSTRAINT ck_calcrun_success_completeness CHECK (
        (status IN ('SUCCEEDED', 'FINAL_APPROVED')
            AND run_finished_at IS NOT NULL
            AND source_snapshot_id IS NOT NULL
            AND metric_version_id IS NOT NULL
            AND scenario_config_version_id IS NOT NULL
            AND engine_release_id IS NOT NULL)
     OR status NOT IN ('SUCCEEDED', 'FINAL_APPROVED')),
    -- DE-NO-OP'd: the as-built had a no-op `OR length(error_log) >= 0` branch (audit [D-6]).
    -- Cleaned to the real rule: FAILED ⇒ error_log present; non-FAILED ⇒ error_log NULL.
    CONSTRAINT ck_calcrun_failed_has_errorlog CHECK (
        (status = 'FAILED' AND error_log IS NOT NULL)
     OR (status <> 'FAILED' AND error_log IS NULL)),
    CONSTRAINT ck_calcrun_final_has_output_manifest CHECK (
        status <> 'FINAL_APPROVED' OR output_hash_manifest IS NOT NULL),
    CONSTRAINT ck_calcrun_round_required_for_round_scoped_types CHECK (
        run_type NOT IN ('ROUND_ANALYSIS', 'CAT_MAN_RERUN', 'FINAL_ALIGNED', 'SCENARIO_A_BENCHMARK')
     OR round_id IS NOT NULL),
    CONSTRAINT ck_calcrun_scenario_a_requires_upstream CHECK (
        (execution_contract = 'GOVERNED_SCENARIO_A' AND upstream_calc_run_id IS NOT NULL)
     OR ((execution_contract IS NULL OR execution_contract <> 'GOVERNED_SCENARIO_A')
            AND upstream_calc_run_id IS NULL)),
    CONSTRAINT ck_calcrun_contract_matches_run_type CHECK (
        execution_contract IS NULL
     OR (execution_contract = 'GOVERNED_CANDIDATE_ANALYSIS' AND run_type = 'ROUND_ANALYSIS')
     OR (execution_contract = 'GOVERNED_SCENARIO_A' AND run_type = 'SCENARIO_A_BENCHMARK')),
    CONSTRAINT ck_calcrun_success_has_input_manifest CHECK (
        status NOT IN ('SUCCEEDED', 'FINAL_APPROVED') OR input_hash_manifest IS NOT NULL),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (source_snapshot_id) REFERENCES norm.normalization_run (normalization_run_id),
    FOREIGN KEY (metric_version_id) REFERENCES eng.metric_definition_version (metric_version_id),
    FOREIGN KEY (scenario_config_version_id) REFERENCES eng.scenario_config_version (scenario_config_version_id),
    FOREIGN KEY (engine_release_id) REFERENCES eng.engine_release (engine_release_id),
    FOREIGN KEY (upstream_calc_run_id) REFERENCES eng.calculation_run (calc_run_id)
);

-- eng.calculation_run_input — ADOPT (KEEP). Frozen inputs, one-per-type, hash.
CREATE TABLE IF NOT EXISTS eng.calculation_run_input (
    calc_run_input_id    varchar(36)  NOT NULL,
    calc_run_id          varchar(36)  NOT NULL,
    input_type           text         NOT NULL,
    source_entity_type   varchar(80)  NOT NULL,
    source_entity_reference text      NOT NULL,
    canonical_hash       varchar(128) NOT NULL,
    row_count            integer,
    included_at          timestamp    NOT NULL,
    PRIMARY KEY (calc_run_input_id),
    CONSTRAINT uq_calcrun_input_one_per_type UNIQUE (calc_run_id, input_type),
    CONSTRAINT ck_calcrun_input_row_count_nonneg CHECK (row_count IS NULL OR row_count >= 0),
    CONSTRAINT ck_calcrun_input_hash_min_length CHECK (length(canonical_hash) >= 8),
    FOREIGN KEY (calc_run_id) REFERENCES eng.calculation_run (calc_run_id)
);

-- eng.round_analysis_snapshot — ADOPT (KEEP). One canonical run per round.
CREATE TABLE IF NOT EXISTS eng.round_analysis_snapshot (
    snapshot_id     varchar(36)  NOT NULL,
    cycle_id        varchar(36)  NOT NULL,
    round_id        varchar(36)  NOT NULL,
    calc_run_id     varchar(36)  NOT NULL,
    snapshot_label  varchar(160) NOT NULL,
    is_canonical    boolean      NOT NULL,
    created_at      timestamp    NOT NULL,
    created_by      varchar(120) NOT NULL,
    PRIMARY KEY (snapshot_id),
    CONSTRAINT fk_ras_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT uq_ras_one_link_per_run_per_round UNIQUE (cycle_id, round_id, calc_run_id),
    CONSTRAINT ck_ras_label_not_empty CHECK (length(snapshot_label) > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (calc_run_id) REFERENCES eng.calculation_run (calc_run_id)
);


-- ===========================================================================
-- 6. bid — intake, eligibility, capacity, landed cost, volume scope (KEEP #3/#4/#5)
-- ===========================================================================

-- bid.bid_submission — ADOPT. Submission header; identity quad; artifact provenance.
CREATE TABLE IF NOT EXISTS bid.bid_submission (
    submission_id           varchar(36) NOT NULL,
    cycle_id                varchar(36) NOT NULL,
    round_id                varchar(36) NOT NULL,
    supplier_id             varchar(36) NOT NULL,
    source_artifact_id      varchar(36) NOT NULL,
    submitted_at            timestamp   NOT NULL,
    version_number          integer     NOT NULL,
    overall_status          text        NOT NULL,
    standard_terms_accepted boolean     NOT NULL,
    terms_exceptions_text   text,
    PRIMARY KEY (submission_id),
    CONSTRAINT uq_submission_identity_quad UNIQUE (submission_id, cycle_id, round_id, supplier_id),
    CONSTRAINT fk_submission_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT fk_submission_artifact_provenance FOREIGN KEY (source_artifact_id, cycle_id, round_id, supplier_id)
        REFERENCES norm.source_artifact (artifact_id, cycle_id, round_id, supplier_id),
    CONSTRAINT ck_submission_version_positive CHECK (version_number > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);

-- bid.bid_line — CLEAN of bid_line. Priced line + identity octuple; is_scoreable/is_awardable
-- + leverage signals. SQLite-ism cleaned: BOOLEAN DEFAULT 0 → boolean DEFAULT false.
-- (grow_origin/ship_from_zip/distance_miles are G7/M3, not M0.)
CREATE TABLE IF NOT EXISTS bid.bid_line (
    bid_line_id                  varchar(36) NOT NULL,
    submission_id                varchar(36) NOT NULL,
    cycle_id                     varchar(36) NOT NULL,
    round_id                     varchar(36) NOT NULL,
    supplier_id                  varchar(36) NOT NULL,
    dc_id                        varchar(36) NOT NULL,
    lot_id                       varchar(36) NOT NULL,
    item_id                      varchar(36) NOT NULL,
    tf_id                        varchar(36) NOT NULL,
    currency_code                varchar(3)  NOT NULL,
    price_basis                  text        NOT NULL,
    submitted_all_in_case        numeric(18, 6),
    fob_case                     numeric(18, 6),
    freight_case                 numeric(18, 6),
    fuel_case                    numeric(18, 6),
    accessorial_case             numeric(18, 6),
    item_discount_case           numeric(18, 6),
    shrink_case                  numeric(18, 6),
    commercial_conditions_text   text,
    moq_cases                    numeric(18, 3),
    volume_minimum_cases         numeric(18, 3),
    exclusivity_required_flag    boolean     NOT NULL,
    effective_date_start         date,
    effective_date_end           date,
    loading_location_id          varchar(36),
    validity_status              text        NOT NULL,
    source_row_number            integer,
    created_at                   timestamp   NOT NULL,
    bid_line_status              text,
    is_scoreable                 boolean     NOT NULL DEFAULT false,
    is_awardable                 boolean     NOT NULL DEFAULT false,
    incomplete_reason_code       text,
    leverage_signal_flag         boolean     NOT NULL DEFAULT false,
    leverage_signal_reason       text,
    best_in_class_signal_flag    boolean     NOT NULL DEFAULT false,
    follow_up_recommended_flag   boolean     NOT NULL DEFAULT false,
    PRIMARY KEY (bid_line_id),
    CONSTRAINT uq_bid_line_cell_per_submission UNIQUE (submission_id, dc_id, lot_id, item_id, tf_id),
    CONSTRAINT uq_bid_line_identity_full UNIQUE (bid_line_id, cycle_id, round_id, supplier_id, dc_id, lot_id, item_id, tf_id),
    CONSTRAINT fk_bidline_to_submission_identity FOREIGN KEY (submission_id, cycle_id, round_id, supplier_id)
        REFERENCES bid.bid_submission (submission_id, cycle_id, round_id, supplier_id),
    CONSTRAINT fk_bidline_lot_in_cycle FOREIGN KEY (lot_id, cycle_id)
        REFERENCES cyc.cycle_lot (lot_id, cycle_id),
    CONSTRAINT fk_bidline_tf_in_cycle FOREIGN KEY (tf_id, cycle_id)
        REFERENCES cyc.cycle_timeframe (tf_id, cycle_id),
    CONSTRAINT fk_bidline_item_in_lot FOREIGN KEY (lot_id, item_id)
        REFERENCES cyc.cycle_lot_item (lot_id, item_id),
    CONSTRAINT fk_bidline_loc_belongs_to_supplier FOREIGN KEY (loading_location_id, supplier_id)
        REFERENCES ref.loading_location (location_id, supplier_id),
    CONSTRAINT ck_bid_all_in_positive CHECK (submitted_all_in_case IS NULL OR submitted_all_in_case > 0),
    CONSTRAINT ck_bid_fob_positive CHECK (fob_case IS NULL OR fob_case > 0),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);
CREATE INDEX IF NOT EXISTS ix_bid_line_cell
    ON bid.bid_line (cycle_id, round_id, dc_id, lot_id, item_id, tf_id);

-- bid.supplier_capability — ADOPT (KEEP #4). CONFIRMED_CAPABLE gate.
CREATE TABLE IF NOT EXISTS bid.supplier_capability (
    capability_id        varchar(36) NOT NULL,
    cycle_id             varchar(36) NOT NULL,
    supplier_id          varchar(36) NOT NULL,
    dc_id                varchar(36) NOT NULL,
    lot_id               varchar(36) NOT NULL,
    tf_id                varchar(36) NOT NULL,
    status               text        NOT NULL,
    evidence_reference   text,
    confirmed_by_actor_id varchar(120),
    confirmed_at         timestamp,
    notes                text,
    PRIMARY KEY (capability_id),
    CONSTRAINT uq_capability_per_cell UNIQUE (cycle_id, supplier_id, dc_id, lot_id, tf_id),
    CONSTRAINT fk_capability_lot_in_cycle FOREIGN KEY (lot_id, cycle_id)
        REFERENCES cyc.cycle_lot (lot_id, cycle_id),
    CONSTRAINT fk_capability_tf_in_cycle FOREIGN KEY (tf_id, cycle_id)
        REFERENCES cyc.cycle_timeframe (tf_id, cycle_id),
    CONSTRAINT ck_capability_confirmed_requires_evidence CHECK (
        status <> 'CONFIRMED_CAPABLE'
     OR (evidence_reference IS NOT NULL AND confirmed_by_actor_id IS NOT NULL AND confirmed_at IS NOT NULL)),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);

-- bid.capacity_statement — ADOPT (KEEP #4).
CREATE TABLE IF NOT EXISTS bid.capacity_statement (
    capacity_statement_id varchar(36) NOT NULL,
    cycle_id              varchar(36) NOT NULL,
    round_id             varchar(36),
    supplier_id          varchar(36) NOT NULL,
    submission_id        varchar(36),
    source_artifact_id   varchar(36) NOT NULL,
    status               text        NOT NULL,
    effective_at         timestamp   NOT NULL,
    notes                text,
    PRIMARY KEY (capacity_statement_id),
    CONSTRAINT fk_capacity_stmt_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT fk_capstmt_artifact_cycle_supplier FOREIGN KEY (source_artifact_id, cycle_id, supplier_id)
        REFERENCES norm.source_artifact (artifact_id, cycle_id, supplier_id),
    CONSTRAINT fk_capstmt_artifact_round_match FOREIGN KEY (source_artifact_id, round_id)
        REFERENCES norm.source_artifact (artifact_id, round_id),
    CONSTRAINT fk_capstmt_submission_identity FOREIGN KEY (submission_id, cycle_id, round_id, supplier_id)
        REFERENCES bid.bid_submission (submission_id, cycle_id, round_id, supplier_id),
    CONSTRAINT ck_capstmt_submission_requires_round CHECK (submission_id IS NULL OR round_id IS NOT NULL),
    CONSTRAINT uq_capstmt_id_cycle UNIQUE (capacity_statement_id, cycle_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);

-- bid.capacity_constraint — ADOPT (KEEP #4). 5 capacity scopes, scope/field-match CHECK.
CREATE TABLE IF NOT EXISTS bid.capacity_constraint (
    capacity_constraint_id varchar(36) NOT NULL,
    capacity_statement_id  varchar(36) NOT NULL,
    cycle_id               varchar(36) NOT NULL,
    scope_type             text        NOT NULL,
    dc_id                  varchar(36),
    lot_id                 varchar(36),
    tf_id                  varchar(36),
    max_weekly_cases       numeric(18, 3),
    max_period_cases       numeric(18, 3),
    conditions_text        text,
    PRIMARY KEY (capacity_constraint_id),
    CONSTRAINT fk_capcon_stmt_cycle FOREIGN KEY (capacity_statement_id, cycle_id)
        REFERENCES bid.capacity_statement (capacity_statement_id, cycle_id),
    CONSTRAINT fk_capcon_lot_in_cycle FOREIGN KEY (lot_id, cycle_id)
        REFERENCES cyc.cycle_lot (lot_id, cycle_id),
    CONSTRAINT fk_capcon_tf_in_cycle FOREIGN KEY (tf_id, cycle_id)
        REFERENCES cyc.cycle_timeframe (tf_id, cycle_id),
    CONSTRAINT ck_capacity_scope_field_match CHECK (
        (scope_type = 'CELL'        AND dc_id IS NOT NULL AND lot_id IS NOT NULL AND tf_id IS NOT NULL)
     OR (scope_type = 'DC_TF'       AND dc_id IS NOT NULL AND lot_id IS NULL     AND tf_id IS NOT NULL)
     OR (scope_type = 'LOT_TF'      AND dc_id IS NULL     AND lot_id IS NOT NULL AND tf_id IS NOT NULL)
     OR (scope_type = 'SUPPLIER_TF' AND dc_id IS NULL     AND lot_id IS NULL     AND tf_id IS NOT NULL)
     OR (scope_type = 'TOTAL_CYCLE' AND dc_id IS NULL     AND lot_id IS NULL     AND tf_id IS NULL)),
    CONSTRAINT ck_capacity_has_a_max CHECK (max_weekly_cases IS NOT NULL OR max_period_cases IS NOT NULL),
    CONSTRAINT ck_capacity_weekly_nonneg CHECK (max_weekly_cases IS NULL OR max_weekly_cases >= 0),
    CONSTRAINT ck_capacity_period_nonneg CHECK (max_period_cases IS NULL OR max_period_cases >= 0),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);

-- bid.eligibility_result — ADOPT (KEEP #4). SQLite-ism cleaned: is_eligible = 0/1 → boolean.
CREATE TABLE IF NOT EXISTS bid.eligibility_result (
    eligibility_result_id varchar(36) NOT NULL,
    cycle_id              varchar(36) NOT NULL,
    round_id             varchar(36) NOT NULL,
    calc_run_id          varchar(36) NOT NULL,
    submission_id        varchar(36),
    supplier_id          varchar(36) NOT NULL,
    dc_id                varchar(36) NOT NULL,
    lot_id               varchar(36) NOT NULL,
    tf_id                varchar(36) NOT NULL,
    is_eligible          boolean     NOT NULL,
    reason_code          text        NOT NULL,
    reason_detail        text,
    input_snapshot_reference text,
    evaluated_at         timestamp   NOT NULL,
    eligibility_scope    text        NOT NULL,
    requires_scenario_capacity_validation boolean NOT NULL,
    PRIMARY KEY (eligibility_result_id),
    CONSTRAINT uq_eligibility_per_cell_per_run UNIQUE (cycle_id, round_id, calc_run_id, supplier_id, dc_id, lot_id, tf_id),
    CONSTRAINT uq_eligibility_result_full_identity UNIQUE (eligibility_result_id, calc_run_id, cycle_id, round_id, supplier_id, dc_id, lot_id, tf_id),
    CONSTRAINT fk_eligibility_lot_in_cycle FOREIGN KEY (lot_id, cycle_id)
        REFERENCES cyc.cycle_lot (lot_id, cycle_id),
    CONSTRAINT fk_eligibility_tf_in_cycle FOREIGN KEY (tf_id, cycle_id)
        REFERENCES cyc.cycle_timeframe (tf_id, cycle_id),
    CONSTRAINT fk_eligibility_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT fk_eligibility_calc_run_identity FOREIGN KEY (calc_run_id, cycle_id, round_id)
        REFERENCES eng.calculation_run (calc_run_id, cycle_id, round_id),
    CONSTRAINT fk_eligibility_submission_identity FOREIGN KEY (submission_id, cycle_id, round_id, supplier_id)
        REFERENCES bid.bid_submission (submission_id, cycle_id, round_id, supplier_id),
    CONSTRAINT ck_eligibility_true_requires_eligible_reason_and_submission CHECK (
        (is_eligible = false) OR (reason_code = 'ELIGIBLE' AND submission_id IS NOT NULL)),
    CONSTRAINT ck_eligibility_reason_eligible_requires_true_and_submission CHECK (
        (reason_code <> 'ELIGIBLE') OR (is_eligible = true AND submission_id IS NOT NULL)),
    CONSTRAINT ck_eligibility_null_submission_blocks_eligible CHECK (
        (submission_id IS NOT NULL) OR (is_eligible = false)),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);

-- bid.eligibility_gate_result — ADOPT (KEEP #4). Per-gate outcome rows.
CREATE TABLE IF NOT EXISTS bid.eligibility_gate_result (
    eligibility_gate_result_id varchar(36) NOT NULL,
    eligibility_result_id      varchar(36) NOT NULL,
    calc_run_id                varchar(36) NOT NULL,
    cycle_id                   varchar(36) NOT NULL,
    round_id                   varchar(36) NOT NULL,
    submission_id              varchar(36),
    supplier_id                varchar(36) NOT NULL,
    dc_id                      varchar(36) NOT NULL,
    lot_id                     varchar(36) NOT NULL,
    tf_id                      varchar(36) NOT NULL,
    gate_code                  text        NOT NULL,
    gate_status                text        NOT NULL,
    reason_code                text,
    reason_detail              text,
    evidence_reference         text,
    evaluated_at               timestamp   NOT NULL,
    PRIMARY KEY (eligibility_gate_result_id),
    CONSTRAINT uq_gate_per_eligibility_result UNIQUE (eligibility_result_id, gate_code),
    CONSTRAINT fk_gate_calc_run_identity FOREIGN KEY (calc_run_id, cycle_id, round_id)
        REFERENCES eng.calculation_run (calc_run_id, cycle_id, round_id),
    CONSTRAINT fk_gate_eligibility_full_identity
        FOREIGN KEY (eligibility_result_id, calc_run_id, cycle_id, round_id, supplier_id, dc_id, lot_id, tf_id)
        REFERENCES bid.eligibility_result (eligibility_result_id, calc_run_id, cycle_id, round_id, supplier_id, dc_id, lot_id, tf_id),
    CONSTRAINT fk_gate_submission_identity FOREIGN KEY (submission_id, cycle_id, round_id, supplier_id)
        REFERENCES bid.bid_submission (submission_id, cycle_id, round_id, supplier_id),
    CONSTRAINT ck_gate_deferred_only_for_capacity CHECK (
        gate_status <> 'DEFERRED_SCENARIO' OR gate_code = 'CAPACITY'),
    CONSTRAINT ck_gate_blocked_has_reason CHECK (
        gate_status <> 'BLOCKED' OR reason_code IS NOT NULL),
    CONSTRAINT ck_gate_pass_or_na_has_no_reason CHECK (
        gate_status NOT IN ('PASS', 'NOT_APPLICABLE') OR reason_code IS NULL),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);

-- bid.eligibility_exception — ADOPT (KEEP #4). Recorded overrides.
CREATE TABLE IF NOT EXISTS bid.eligibility_exception (
    exception_id        varchar(36) NOT NULL,
    cycle_id            varchar(36) NOT NULL,
    supplier_id         varchar(36) NOT NULL,
    dc_id               varchar(36) NOT NULL,
    lot_id              varchar(36) NOT NULL,
    tf_id               varchar(36) NOT NULL,
    exception_type      text        NOT NULL,
    rationale           text        NOT NULL,
    approver_actor_id   varchar(120) NOT NULL,
    approved_at         timestamp   NOT NULL,
    evidence_reference  text,
    active              boolean     NOT NULL,
    PRIMARY KEY (exception_id),
    CONSTRAINT uq_exception_per_cell_type UNIQUE (cycle_id, supplier_id, dc_id, lot_id, tf_id, exception_type),
    CONSTRAINT fk_exception_lot_in_cycle FOREIGN KEY (lot_id, cycle_id)
        REFERENCES cyc.cycle_lot (lot_id, cycle_id),
    CONSTRAINT fk_exception_tf_in_cycle FOREIGN KEY (tf_id, cycle_id)
        REFERENCES cyc.cycle_timeframe (tf_id, cycle_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id)
);

-- bid.landed_cost_result — ADOPT (KEEP #3). 5 modes, 8 blocking reasons, awardable-shape
-- CHECKs. SQLite-ism cleaned: is_cost_awardable = 0/1 → boolean predicates.
CREATE TABLE IF NOT EXISTS bid.landed_cost_result (
    landed_cost_result_id      varchar(36)  NOT NULL,
    calc_run_id                varchar(36)  NOT NULL,
    cycle_id                   varchar(36)  NOT NULL,
    round_id                   varchar(36)  NOT NULL,
    bid_line_id                varchar(36)  NOT NULL,
    supplier_id                varchar(36)  NOT NULL,
    dc_id                      varchar(36)  NOT NULL,
    lot_id                     varchar(36)  NOT NULL,
    item_id                    varchar(36)  NOT NULL,
    tf_id                      varchar(36)  NOT NULL,
    metric_version_id          varchar(36)  NOT NULL,
    landed_cost_mode           text         NOT NULL,
    is_cost_awardable          boolean      NOT NULL,
    blocking_reason_code       text,
    blocking_reason_detail     text,
    submitted_all_in_case      numeric(18, 6),
    reconstructed_all_in_case  numeric(18, 6),
    authoritative_landed_cost_case numeric(18, 6),
    variance_case              numeric(18, 6),
    tolerance_case_used        numeric(18, 6) NOT NULL,
    loading_location_id        varchar(36),
    loading_location_valid_flag boolean     NOT NULL,
    formula_version_reference  varchar(120) NOT NULL,
    calculated_at              timestamp    NOT NULL,
    PRIMARY KEY (landed_cost_result_id),
    CONSTRAINT uq_landed_cost_per_bidline_per_run UNIQUE (calc_run_id, bid_line_id),
    CONSTRAINT fk_landed_cost_calc_run_identity FOREIGN KEY (calc_run_id, cycle_id, round_id)
        REFERENCES eng.calculation_run (calc_run_id, cycle_id, round_id),
    CONSTRAINT fk_landed_cost_metric_matches_run FOREIGN KEY (calc_run_id, cycle_id, round_id, metric_version_id)
        REFERENCES eng.calculation_run (calc_run_id, cycle_id, round_id, metric_version_id),
    CONSTRAINT fk_landed_cost_bidline_full_identity
        FOREIGN KEY (bid_line_id, cycle_id, round_id, supplier_id, dc_id, lot_id, item_id, tf_id)
        REFERENCES bid.bid_line (bid_line_id, cycle_id, round_id, supplier_id, dc_id, lot_id, item_id, tf_id),
    CONSTRAINT fk_landed_cost_loc_belongs_to_supplier FOREIGN KEY (loading_location_id, supplier_id)
        REFERENCES ref.loading_location (location_id, supplier_id),
    CONSTRAINT ck_landed_cost_tol_nonneg CHECK (tolerance_case_used >= 0),
    CONSTRAINT ck_landed_cost_awardable_shape CHECK (
        (is_cost_awardable = false)
     OR (landed_cost_mode IN ('DIRECT_ALL_IN', 'RECONCILED_ALL_IN', 'RECONSTRUCTED_APPROVED')
            AND authoritative_landed_cost_case IS NOT NULL
            AND authoritative_landed_cost_case > 0
            AND blocking_reason_code IS NULL)),
    CONSTRAINT ck_landed_cost_nonawardable_shape CHECK (
        (is_cost_awardable = true)
     OR (landed_cost_mode IN ('MISMATCH_BLOCKED', 'FOB_PREVIEW_ONLY')
            AND authoritative_landed_cost_case IS NULL
            AND blocking_reason_code IS NOT NULL)),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (metric_version_id) REFERENCES eng.metric_definition_version (metric_version_id)
);

-- bid.volume_scope_source_row — ADOPT (KEEP #5). demand≠capacity CHECK (cleaned to boolean).
CREATE TABLE IF NOT EXISTS bid.volume_scope_source_row (
    source_row_id        varchar(36) NOT NULL,
    cycle_id             varchar(36) NOT NULL,
    ingestion_run_id     varchar(36) NOT NULL,
    input_class          text        NOT NULL,
    source_type          text        NOT NULL,
    precedence_rank      integer,
    raw_dc_text          text,
    raw_item_text        text,
    raw_supplier_text    text,
    resolved_dc_id       varchar(36),
    resolved_item_id     varchar(36),
    resolved_supplier_id varchar(36),
    commodity_id         varchar(36),
    subcommodity_id      varchar(36),
    timeframe_start_date date,
    timeframe_end_date   date,
    volume_measure       numeric(18, 6),
    unit_of_measure      varchar(40),
    routing_basis        text,
    zero_reason          text,
    status               text        NOT NULL,
    active_demand_flag   boolean     NOT NULL,
    source_artifact      text,
    source_sheet         text,
    source_row           integer,
    created_at           timestamp   NOT NULL,
    created_by           varchar(120) NOT NULL,
    PRIMARY KEY (source_row_id),
    CONSTRAINT ck_vsp_source_timeframe_range CHECK (
        timeframe_end_date IS NULL OR timeframe_start_date IS NULL OR timeframe_end_date >= timeframe_start_date),
    CONSTRAINT ck_vsp_capacity_never_active_demand CHECK (
        input_class = 'DEMAND' OR active_demand_flag = false),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
CREATE INDEX IF NOT EXISTS ix_vsp_source_cycle_active
    ON bid.volume_scope_source_row (cycle_id, active_demand_flag);
CREATE INDEX IF NOT EXISTS ix_vsp_source_run_status
    ON bid.volume_scope_source_row (ingestion_run_id, status);

-- bid.normalized_volume_scope — ADOPT (KEEP #5). Validated demand-only output.
CREATE TABLE IF NOT EXISTS bid.normalized_volume_scope (
    scope_id             varchar(36) NOT NULL,
    cycle_id             varchar(36) NOT NULL,
    source_row_id        varchar(36) NOT NULL,
    dc_id                varchar(36) NOT NULL,
    item_id              varchar(36) NOT NULL,
    supplier_id          varchar(36),
    commodity_id         varchar(36),
    subcommodity_id      varchar(36),
    source_type          text        NOT NULL,
    precedence_rank      integer     NOT NULL,
    timeframe_start_date date        NOT NULL,
    timeframe_end_date   date        NOT NULL,
    volume_measure       numeric(18, 6) NOT NULL,
    unit_of_measure      varchar(40) NOT NULL,
    fiscal_year          integer,
    fiscal_period_number integer,
    routing_basis        text,
    active_demand_flag   boolean     NOT NULL,
    created_at           timestamp   NOT NULL,
    created_by           varchar(120) NOT NULL,
    PRIMARY KEY (scope_id),
    CONSTRAINT ck_vsp_norm_volume_nonneg CHECK (volume_measure >= 0),
    CONSTRAINT ck_vsp_norm_timeframe_range CHECK (timeframe_end_date >= timeframe_start_date),
    CONSTRAINT ck_vsp_norm_precedence_range CHECK (precedence_rank >= 1 AND precedence_rank <= 4),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (source_row_id) REFERENCES bid.volume_scope_source_row (source_row_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
CREATE INDEX IF NOT EXISTS ix_vsp_norm_cycle_grain
    ON bid.normalized_volume_scope (cycle_id, dc_id, item_id);

-- bid.volume_scope_override — ADOPT (KEEP #5). Overrides with lineage.
CREATE TABLE IF NOT EXISTS bid.volume_scope_override (
    override_id         varchar(36) NOT NULL,
    cycle_id            varchar(36) NOT NULL,
    source_row_id       varchar(36),
    scope_id            varchar(36),
    affected_scope_desc text        NOT NULL,
    source_type         text        NOT NULL,
    original_value      numeric(18, 6),
    override_value      numeric(18, 6),
    reason_note         text        NOT NULL,
    override_user       varchar(120) NOT NULL,
    override_timestamp  timestamp   NOT NULL,
    approval_status     text        NOT NULL,
    created_at          timestamp   NOT NULL,
    PRIMARY KEY (override_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (source_row_id) REFERENCES bid.volume_scope_source_row (source_row_id),
    FOREIGN KEY (scope_id) REFERENCES bid.normalized_volume_scope (scope_id)
);
CREATE INDEX IF NOT EXISTS ix_vsp_override_cycle
    ON bid.volume_scope_override (cycle_id, source_type);

-- bid.volume_scope_prep_issue — ADOPT (KEEP #5). ~24 issue codes.
CREATE TABLE IF NOT EXISTS bid.volume_scope_prep_issue (
    issue_id         varchar(36) NOT NULL,
    ingestion_run_id varchar(36) NOT NULL,
    cycle_id         varchar(36),
    source_row_id    varchar(36),
    input_class      text,
    issue_code       text        NOT NULL,
    severity         text        NOT NULL,
    field_name       text,
    raw_value        text,
    normalized_value text,
    message          text        NOT NULL,
    action_needed    text,
    resolved_status  text        NOT NULL,
    resolved_by      varchar(120),
    resolved_at      timestamp,
    source_artifact  text,
    source_sheet     text,
    source_row       integer,
    created_at       timestamp   NOT NULL,
    PRIMARY KEY (issue_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (source_row_id) REFERENCES bid.volume_scope_source_row (source_row_id)
);
CREATE INDEX IF NOT EXISTS ix_vsp_issue_cycle_resolved
    ON bid.volume_scope_prep_issue (cycle_id, resolved_status);
CREATE INDEX IF NOT EXISTS ix_vsp_issue_run_severity
    ON bid.volume_scope_prep_issue (ingestion_run_id, severity);


-- ===========================================================================
-- 7. eng (continued) — Scenario A result family (KEEP; G1/G2 generalize at Phase D)
-- ===========================================================================

-- eng.scenario — CLEAN of scenario_a_result (NAMING_MAP: scenario_a_* → eng.scenario*).
-- The G2 break adds the scenario_code lens generalization; here we re-express faithfully.
CREATE TABLE IF NOT EXISTS eng.scenario (
    scenario_run_id          varchar(36)  NOT NULL,
    upstream_calc_run_id     varchar(36)  NOT NULL,
    scenario_code            text         NOT NULL,
    solve_status             text         NOT NULL,
    objective_total_spend    numeric(18, 6),
    solver_version_reference varchar(120) NOT NULL,
    calculated_at            timestamp    NOT NULL,
    PRIMARY KEY (scenario_run_id),
    CONSTRAINT ck_scenario_a_result_status_objective CHECK (
        (solve_status = 'FEASIBLE'   AND objective_total_spend IS NOT NULL AND objective_total_spend > 0)
     OR (solve_status = 'INFEASIBLE' AND objective_total_spend IS NULL)),
    FOREIGN KEY (scenario_run_id) REFERENCES eng.calculation_run (calc_run_id),
    FOREIGN KEY (upstream_calc_run_id) REFERENCES eng.calculation_run (calc_run_id)
);

-- eng.scenario_award — CLEAN of scenario_a_cell_assignment. Single-winner cell (G1 relaxes
-- the uniqueness + adds volume_share at Phase D). SQLite-ism cleaned: status-shape CHECK.
CREATE TABLE IF NOT EXISTS eng.scenario_award (
    cell_assignment_id            varchar(36) NOT NULL,
    scenario_run_id               varchar(36) NOT NULL,
    dc_id                         varchar(36) NOT NULL,
    lot_id                        varchar(36) NOT NULL,
    tf_id                         varchar(36) NOT NULL,
    assignment_status             text        NOT NULL,
    supplier_id                   varchar(36),
    upstream_eligibility_result_id varchar(36),
    cell_period_cases             numeric(18, 3) NOT NULL,
    cell_spend                    numeric(18, 6),
    PRIMARY KEY (cell_assignment_id),
    CONSTRAINT uq_scenario_a_cell_assignment_cell UNIQUE (scenario_run_id, dc_id, lot_id, tf_id),
    CONSTRAINT ck_scenario_a_cell_assignment_status_shape CHECK (
        (assignment_status = 'AWARDED'
            AND supplier_id IS NOT NULL
            AND cell_spend IS NOT NULL AND cell_spend > 0
            AND upstream_eligibility_result_id IS NOT NULL)
     OR (assignment_status = 'NO_FEASIBLE_ASSIGNMENT'
            AND supplier_id IS NULL
            AND cell_spend IS NULL
            AND upstream_eligibility_result_id IS NULL)),
    CONSTRAINT ck_scenario_a_cell_period_cases_positive CHECK (cell_period_cases > 0),
    FOREIGN KEY (scenario_run_id) REFERENCES eng.calculation_run (calc_run_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (lot_id) REFERENCES cyc.cycle_lot (lot_id),
    FOREIGN KEY (tf_id) REFERENCES cyc.cycle_timeframe (tf_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (upstream_eligibility_result_id) REFERENCES bid.eligibility_result (eligibility_result_id)
);

-- eng.scenario_line_detail — CLEAN of scenario_a_line_detail. Per-item cost detail under a cell.
CREATE TABLE IF NOT EXISTS eng.scenario_line_detail (
    line_detail_id                 varchar(36) NOT NULL,
    scenario_run_id                varchar(36) NOT NULL,
    dc_id                          varchar(36) NOT NULL,
    lot_id                         varchar(36) NOT NULL,
    tf_id                          varchar(36) NOT NULL,
    item_id                        varchar(36) NOT NULL,
    supplier_id                    varchar(36) NOT NULL,
    upstream_landed_cost_result_id varchar(36) NOT NULL,
    projected_period_cases         numeric(18, 3) NOT NULL,
    authoritative_landed_cost_case numeric(18, 6) NOT NULL,
    line_spend                     numeric(18, 6) NOT NULL,
    PRIMARY KEY (line_detail_id),
    CONSTRAINT uq_scenario_a_line_detail_cell_item UNIQUE (scenario_run_id, dc_id, lot_id, tf_id, item_id),
    CONSTRAINT ck_scenario_a_line_detail_positive CHECK (
        projected_period_cases > 0 AND authoritative_landed_cost_case > 0 AND line_spend > 0),
    FOREIGN KEY (scenario_run_id) REFERENCES eng.calculation_run (calc_run_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (lot_id) REFERENCES cyc.cycle_lot (lot_id),
    FOREIGN KEY (tf_id) REFERENCES cyc.cycle_timeframe (tf_id),
    FOREIGN KEY (item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (upstream_landed_cost_result_id) REFERENCES bid.landed_cost_result (landed_cost_result_id)
);

-- eng.scenario_capacity_usage — CLEAN of scenario_a_capacity_usage. Capacity arithmetic CHECK
-- (remaining = limit − assigned). SQLite-ism cleaned: constraint_satisfied = 1/0 → boolean.
CREATE TABLE IF NOT EXISTS eng.scenario_capacity_usage (
    capacity_usage_id           varchar(36) NOT NULL,
    scenario_run_id             varchar(36) NOT NULL,
    supplier_id                 varchar(36) NOT NULL,
    capacity_statement_id       varchar(36) NOT NULL,
    capacity_constraint_id      varchar(36) NOT NULL,
    scope_type                  text        NOT NULL,
    capacity_limit_period_cases numeric(18, 3) NOT NULL,
    assigned_usage_period_cases numeric(18, 3) NOT NULL,
    remaining_capacity_cases    numeric(18, 3) NOT NULL,
    constraint_satisfied        boolean     NOT NULL,
    PRIMARY KEY (capacity_usage_id),
    CONSTRAINT uq_scenario_a_capacity_usage_per_constraint UNIQUE (scenario_run_id, capacity_constraint_id),
    CONSTRAINT ck_scenario_a_capacity_usage_non_negative CHECK (
        capacity_limit_period_cases >= 0 AND assigned_usage_period_cases >= 0),
    CONSTRAINT ck_scenario_a_capacity_usage_arithmetic CHECK (
        remaining_capacity_cases = capacity_limit_period_cases - assigned_usage_period_cases),
    CONSTRAINT ck_scenario_a_capacity_usage_satisfied_consistent CHECK (
        (constraint_satisfied = true  AND assigned_usage_period_cases <= capacity_limit_period_cases)
     OR (constraint_satisfied = false AND assigned_usage_period_cases > capacity_limit_period_cases)),
    FOREIGN KEY (scenario_run_id) REFERENCES eng.calculation_run (calc_run_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (capacity_statement_id) REFERENCES bid.capacity_statement (capacity_statement_id),
    FOREIGN KEY (capacity_constraint_id) REFERENCES bid.capacity_constraint (capacity_constraint_id)
);


-- ===========================================================================
-- 8. perf — historical award cost + commercial pricing layer (KEEP)
-- ===========================================================================

-- perf.historical_award_assignment — CLEAN of historical_award_assignment. Becomes a
-- derivation over perf.itrade_receipt at M4 (G6); re-expressed faithfully here.
CREATE TABLE IF NOT EXISTS perf.historical_award_assignment (
    assignment_id        varchar(36) NOT NULL,
    cycle_id             varchar(36) NOT NULL,
    dc_id                varchar(36) NOT NULL,
    item_id              varchar(36) NOT NULL,
    supplier_id          varchar(36) NOT NULL,
    effective_start_date date        NOT NULL,
    effective_end_date   date        NOT NULL,
    awarded_volume_cases numeric(18, 6) NOT NULL,
    weekly_volume_cases  numeric(18, 6),
    nat_local_tag        text,
    conv_org_tag         text,
    rpc_required_flag    boolean,
    rpc_size_text        text,
    source_artifact      text,
    source_sheet         text,
    source_row           integer,
    ingestion_run_id     varchar(36) NOT NULL,
    award_round_id       varchar(36),
    incumbent_flag       boolean,
    notes                text,
    created_at           timestamp   NOT NULL,
    created_by           varchar(120) NOT NULL,
    PRIMARY KEY (assignment_id),
    CONSTRAINT uq_historical_award_assignment_identity
        UNIQUE (cycle_id, dc_id, item_id, supplier_id, effective_start_date, effective_end_date),
    CONSTRAINT ck_historical_award_date_range CHECK (effective_end_date >= effective_start_date),
    CONSTRAINT ck_historical_award_volume_nonneg CHECK (awarded_volume_cases >= 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (award_round_id) REFERENCES cyc.cycle_round (round_id)
);

-- perf.historical_awarded_price_basis — ADOPT. Partial unique: one preferred basis per assignment.
CREATE TABLE IF NOT EXISTS perf.historical_awarded_price_basis (
    price_basis_id        varchar(36) NOT NULL,
    assignment_id         varchar(36) NOT NULL,
    routing_basis         text        NOT NULL,
    awarded_price_per_case numeric(18, 6) NOT NULL,
    preferred_basis_flag  boolean     NOT NULL,
    preferred_basis_source text,
    created_at            timestamp   NOT NULL,
    PRIMARY KEY (price_basis_id),
    CONSTRAINT uq_historical_price_basis_per_assignment UNIQUE (assignment_id, routing_basis),
    CONSTRAINT ck_historical_price_nonneg CHECK (awarded_price_per_case >= 0),
    FOREIGN KEY (assignment_id) REFERENCES perf.historical_award_assignment (assignment_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_historical_price_basis_one_preferred
    ON perf.historical_awarded_price_basis (assignment_id) WHERE preferred_basis_flag = true;

-- perf.historical_awarded_cost_ingestion_issue — ADOPT. Persisted importer issues.
CREATE TABLE IF NOT EXISTS perf.historical_awarded_cost_ingestion_issue (
    issue_id         varchar(36) NOT NULL,
    ingestion_run_id varchar(36) NOT NULL,
    cycle_id         varchar(36),
    source_artifact  text,
    source_sheet     text,
    source_row       integer,
    field_name       text,
    issue_code       text        NOT NULL,
    severity         text        NOT NULL,
    raw_value        text,
    normalized_value text,
    message          text        NOT NULL,
    action_needed    text,
    resolved_status  text        NOT NULL,
    resolved_by      varchar(120),
    resolved_at      timestamp,
    created_at       timestamp   NOT NULL,
    assignment_id    varchar(36),
    PRIMARY KEY (issue_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (assignment_id) REFERENCES perf.historical_award_assignment (assignment_id)
);
CREATE INDEX IF NOT EXISTS ix_hac_ingestion_issue_cycle_resolved
    ON perf.historical_awarded_cost_ingestion_issue (cycle_id, resolved_status);
CREATE INDEX IF NOT EXISTS ix_hac_ingestion_issue_run_severity
    ON perf.historical_awarded_cost_ingestion_issue (ingestion_run_id, severity);

-- --- Commercial pricing layer (10 tables) — ADOPT (KEEP, re-point to kickoff at G4) ---

-- perf.commercial_pricing_window — referenced by commercial_pricing_model.window_id.
CREATE TABLE IF NOT EXISTS perf.commercial_pricing_window (
    window_id        varchar(36)  NOT NULL,
    cycle_id         varchar(36)  NOT NULL,
    label            text         NOT NULL,
    window_start     date         NOT NULL,
    window_end       date         NOT NULL,
    source_owner     varchar(120) NOT NULL,
    commodity_id     varchar(36),
    subcommodity_id  varchar(36),
    created_at       timestamp    NOT NULL,
    created_by       varchar(120) NOT NULL,
    PRIMARY KEY (window_id),
    CONSTRAINT ck_cpm_window_range CHECK (window_end >= window_start),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_window_cycle ON perf.commercial_pricing_window (cycle_id, label);

-- perf.commercial_market_reference — holds the safety parameters (reset/trigger/collar).
CREATE TABLE IF NOT EXISTS perf.commercial_market_reference (
    market_reference_id      varchar(36)  NOT NULL,
    cycle_id                 varchar(36)  NOT NULL,
    reference_source         varchar(120) NOT NULL,
    reference_commodity      varchar(120),
    reference_pack           varchar(120),
    reference_region         varchar(120),
    reference_price_type     varchar(60),
    market_reference_price   numeric(18, 6),
    market_reference_mid     numeric(18, 6),
    derived_trailing_mid     numeric(18, 6),
    awarded_spread           numeric(18, 6),
    reset_cadence            text,
    trigger_band_pct         numeric(9, 6),
    trigger_confirmation_days integer,
    collar_floor             numeric(18, 6),
    collar_cap               numeric(18, 6),
    freight_passthrough      boolean      NOT NULL,
    as_of_date               date,
    created_at               timestamp    NOT NULL,
    created_by               varchar(120) NOT NULL,
    PRIMARY KEY (market_reference_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_market_ref_cycle
    ON perf.commercial_market_reference (cycle_id, reference_source);

-- perf.commercial_pricing_model — three-value raw/derived/normalized rule.
CREATE TABLE IF NOT EXISTS perf.commercial_pricing_model (
    pricing_model_id          varchar(36)  NOT NULL,
    pricing_run_id            varchar(36)  NOT NULL,
    cycle_id                  varchar(36)  NOT NULL,
    dc_id                     varchar(36)  NOT NULL,
    item_id                   varchar(36)  NOT NULL,
    supplier_id               varchar(36),
    window_id                 varchar(36),
    pricing_model_type        text         NOT NULL,
    lane                      text         NOT NULL,
    routing_basis             text,
    market_reference_id       varchar(36),
    raw_supplier_value        numeric(18, 6),
    system_derived_value      numeric(18, 6),
    normalized_comparable_value numeric(18, 6),
    raw_routing_basis         varchar(40),
    normalization_status      text         NOT NULL,
    override_value            numeric(18, 6),
    override_reason           text,
    override_user             varchar(120),
    created_at                timestamp    NOT NULL,
    created_by                varchar(120) NOT NULL,
    PRIMARY KEY (pricing_model_id),
    CONSTRAINT uq_cpm_priced_offer_grain UNIQUE (cycle_id, dc_id, item_id, supplier_id, window_id, pricing_model_type),
    CONSTRAINT ck_cpm_normalized_nonneg CHECK (
        normalized_comparable_value IS NULL OR normalized_comparable_value >= 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (window_id) REFERENCES perf.commercial_pricing_window (window_id),
    FOREIGN KEY (market_reference_id) REFERENCES perf.commercial_market_reference (market_reference_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_cycle_grain ON perf.commercial_pricing_model (cycle_id, dc_id, item_id);
CREATE INDEX IF NOT EXISTS ix_cpm_run ON perf.commercial_pricing_model (pricing_run_id);

-- perf.commercial_price_component — 20 component types.
CREATE TABLE IF NOT EXISTS perf.commercial_price_component (
    component_id     varchar(36) NOT NULL,
    pricing_model_id varchar(36) NOT NULL,
    component_type   text        NOT NULL,
    plane            text        NOT NULL,
    component_value  numeric(18, 6),
    notes            text,
    created_at       timestamp   NOT NULL,
    PRIMARY KEY (component_id),
    FOREIGN KEY (pricing_model_id) REFERENCES perf.commercial_pricing_model (pricing_model_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_component_model ON perf.commercial_price_component (pricing_model_id, plane);

-- perf.commercial_market_proxy_basis — 5-level fallback proxy.
CREATE TABLE IF NOT EXISTS perf.commercial_market_proxy_basis (
    proxy_id                 varchar(36)  NOT NULL,
    cycle_id                 varchar(36)  NOT NULL,
    pricing_model_id         varchar(36),
    target_item_id           varchar(36),
    reference_market_fob     numeric(18, 6) NOT NULL,
    historical_contract_delta numeric(18, 6) NOT NULL,
    target_lot_proxy_fob     numeric(18, 6) NOT NULL,
    delta_type               text         NOT NULL,
    delta_basis              text         NOT NULL,
    fallback_level_used      integer      NOT NULL,
    confidence_level         text         NOT NULL,
    manual_override_flag     boolean      NOT NULL,
    manual_override_reason   text,
    delta_source_contract    varchar(120),
    delta_source_date        date,
    notes                    text,
    created_at               timestamp    NOT NULL,
    created_by               varchar(120) NOT NULL,
    PRIMARY KEY (proxy_id),
    CONSTRAINT ck_cpm_proxy_fallback_range CHECK (fallback_level_used >= 1 AND fallback_level_used <= 5),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (pricing_model_id) REFERENCES perf.commercial_pricing_model (pricing_model_id),
    FOREIGN KEY (target_item_id) REFERENCES ref.item (item_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_proxy_cycle ON perf.commercial_market_proxy_basis (cycle_id);

-- perf.commercial_pricing_formula_audit — replayable audit (KEEP).
CREATE TABLE IF NOT EXISTS perf.commercial_pricing_formula_audit (
    audit_id              varchar(36)  NOT NULL,
    pricing_model_id      varchar(36)  NOT NULL,
    formula_type          text         NOT NULL,
    formula_inputs        text,
    source_rows           text,
    market_reference_id   varchar(36),
    proxy_id              varchar(36),
    user_override_applied boolean      NOT NULL,
    user_override_reason  text,
    calculated_value      numeric(18, 6) NOT NULL,
    raw_value_link        numeric(18, 6),
    derived_value_link    numeric(18, 6),
    formula_version       varchar(40)  NOT NULL,
    created_at            timestamp    NOT NULL,
    created_by            varchar(120) NOT NULL,
    PRIMARY KEY (audit_id),
    FOREIGN KEY (pricing_model_id) REFERENCES perf.commercial_pricing_model (pricing_model_id),
    FOREIGN KEY (market_reference_id) REFERENCES perf.commercial_market_reference (market_reference_id),
    FOREIGN KEY (proxy_id) REFERENCES perf.commercial_market_proxy_basis (proxy_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_audit_model ON perf.commercial_pricing_formula_audit (pricing_model_id);

-- perf.commercial_pricing_validation_issue — 18 codes.
CREATE TABLE IF NOT EXISTS perf.commercial_pricing_validation_issue (
    issue_id         varchar(36) NOT NULL,
    pricing_run_id   varchar(36) NOT NULL,
    cycle_id         varchar(36),
    pricing_model_id varchar(36),
    issue_code       text        NOT NULL,
    severity         text        NOT NULL,
    field_name       text,
    raw_value        text,
    message          text        NOT NULL,
    action_needed    text,
    created_at       timestamp   NOT NULL,
    PRIMARY KEY (issue_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (pricing_model_id) REFERENCES perf.commercial_pricing_model (pricing_model_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_issue_run_severity
    ON perf.commercial_pricing_validation_issue (pricing_run_id, severity);

-- perf.commercial_qdp — quantity-discount pricing.
CREATE TABLE IF NOT EXISTS perf.commercial_qdp (
    qdp_id                  varchar(36)  NOT NULL,
    cycle_id                varchar(36)  NOT NULL,
    pricing_model_id        varchar(36),
    qdp_basis               text         NOT NULL,
    qdp_rate                numeric(9, 6),
    qdp_value               numeric(18, 6),
    qdp_source              varchar(120) NOT NULL,
    applies_before_discount boolean      NOT NULL,
    created_at              timestamp    NOT NULL,
    created_by              varchar(120) NOT NULL,
    PRIMARY KEY (qdp_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (pricing_model_id) REFERENCES perf.commercial_pricing_model (pricing_model_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_qdp_cycle ON perf.commercial_qdp (cycle_id);

-- perf.commercial_lot_market_delta.
CREATE TABLE IF NOT EXISTS perf.commercial_lot_market_delta (
    delta_id                    varchar(36)  NOT NULL,
    cycle_id                    varchar(36)  NOT NULL,
    reference_item_id           varchar(36),
    target_item_id              varchar(36),
    dc_id                       varchar(36),
    supplier_id                 varchar(36),
    timeframe_label             varchar(120),
    last_contracted_reference_fob numeric(18, 6),
    last_contracted_target_fob  numeric(18, 6),
    delta_value                 numeric(18, 6) NOT NULL,
    delta_type                  text         NOT NULL,
    source_contract             varchar(120),
    source_date                 date,
    created_at                  timestamp    NOT NULL,
    created_by                  varchar(120) NOT NULL,
    PRIMARY KEY (delta_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (reference_item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (target_item_id) REFERENCES ref.item (item_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_lot_delta_cycle ON perf.commercial_lot_market_delta (cycle_id);

-- perf.commercial_market_kickoff_snapshot.
CREATE TABLE IF NOT EXISTS perf.commercial_market_kickoff_snapshot (
    snapshot_id        varchar(36)  NOT NULL,
    cycle_id           varchar(36)  NOT NULL,
    market_reference_id varchar(36),
    reference_name     varchar(120) NOT NULL,
    reference_basis    varchar(60),
    lot_label          varchar(120),
    location           varchar(120),
    market_price       numeric(18, 6) NOT NULL,
    market_as_of_date  date         NOT NULL,
    captured_at        timestamp    NOT NULL,
    captured_by        varchar(120) NOT NULL,
    source_notes       text,
    PRIMARY KEY (snapshot_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (market_reference_id) REFERENCES perf.commercial_market_reference (market_reference_id)
);
CREATE INDEX IF NOT EXISTS ix_cpm_kickoff_cycle ON perf.commercial_market_kickoff_snapshot (cycle_id);


-- ===========================================================================
-- 9. audit — hash-chained event log + decision notes + round lifecycle
-- ===========================================================================

-- audit.event_log — ADOPT→FINISH of as-built audit_event, RECONCILED TOWARD THE LIVE WRITER
-- (app/core/audit/writer.py). The writer INSERTs these exact columns and reads (client_id, seq)
-- as the per-tenant hash-chain head, so we use the writer's shape, NOT the as-built audit_event
-- (which had event_id/event_ts/success_status and no per-tenant seq chain). M1 adds the
-- write-only enforcement (UPDATE/DELETE triggers + INSERT/SELECT-only grants).
CREATE TABLE IF NOT EXISTS audit.event_log (
    id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id         uuid        NOT NULL,
    occurred_at       timestamptz NOT NULL DEFAULT now(),
    actor             varchar(400) NOT NULL,
    source            varchar(32) NOT NULL,
    event_type        varchar(32) NOT NULL,
    entity_type       varchar(128) NOT NULL,
    entity_id         uuid        NOT NULL,
    cycle_id          uuid,
    before_state_hash char(64),
    after_state_hash  char(64),
    prev_event_hash   char(64)    NOT NULL,
    event_hash        char(64)    NOT NULL,
    seq               bigint      NOT NULL,
    CONSTRAINT uq_event_log_client_seq UNIQUE (client_id, seq)
);
COMMENT ON TABLE audit.event_log IS
    'Hash-chained event log. Columns mirror app/core/audit/writer.py (live). Write-only at M1.';
CREATE INDEX IF NOT EXISTS ix_event_log_client_id ON audit.event_log (client_id);

-- audit.decision_note — ADOPT (KEEP). Append-only free-text note, 8-scope bindable.
CREATE TABLE IF NOT EXISTS audit.decision_note (
    note_id         varchar(36)  NOT NULL,
    cycle_id        varchar(36)  NOT NULL,
    round_id        varchar(36),
    scenario_run_id varchar(36),
    supplier_id     varchar(36),
    dc_id           varchar(36),
    lot_id          varchar(36),
    tf_id           varchar(36),
    author          varchar(120) NOT NULL,
    created_at      timestamp    NOT NULL,
    note_text       text         NOT NULL,
    PRIMARY KEY (note_id),
    CONSTRAINT ck_decision_note_text_not_empty CHECK (length(note_text) > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (round_id) REFERENCES cyc.cycle_round (round_id),
    FOREIGN KEY (scenario_run_id) REFERENCES eng.calculation_run (calc_run_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (lot_id) REFERENCES cyc.cycle_lot (lot_id),
    FOREIGN KEY (tf_id) REFERENCES cyc.cycle_timeframe (tf_id)
);

-- audit.round_supplier_participation — ADOPT (KEEP). Round lifecycle.
CREATE TABLE IF NOT EXISTS audit.round_supplier_participation (
    participation_id     varchar(36) NOT NULL,
    cycle_id             varchar(36) NOT NULL,
    round_id             varchar(36) NOT NULL,
    supplier_id          varchar(36) NOT NULL,
    participation_status text        NOT NULL,
    decision_at          timestamp   NOT NULL,
    decided_by           varchar(120) NOT NULL,
    decision_reason_text text,
    PRIMARY KEY (participation_id),
    CONSTRAINT fk_rsp_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
CREATE INDEX IF NOT EXISTS ix_rsp_cycle_round_supplier
    ON audit.round_supplier_participation (cycle_id, round_id, supplier_id);

-- audit.round_feedback_issued — ADOPT (KEEP). Drafted-only feedback (SENT state added at G9).
CREATE TABLE IF NOT EXISTS audit.round_feedback_issued (
    feedback_id   varchar(36) NOT NULL,
    cycle_id      varchar(36) NOT NULL,
    round_id      varchar(36) NOT NULL,
    supplier_id   varchar(36) NOT NULL,
    feedback_text text        NOT NULL,
    drafted_at    timestamp   NOT NULL,
    drafted_by    varchar(120) NOT NULL,
    status        text        NOT NULL,
    PRIMARY KEY (feedback_id),
    CONSTRAINT fk_rfi_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    CONSTRAINT ck_rfi_feedback_text_not_empty CHECK (length(feedback_text) > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
CREATE INDEX IF NOT EXISTS ix_rfi_cycle_round_supplier
    ON audit.round_feedback_issued (cycle_id, round_id, supplier_id);

-- audit.round_field_reduction_decision — ADOPT (KEEP). Next-round invitation list.
CREATE TABLE IF NOT EXISTS audit.round_field_reduction_decision (
    decision_id                   varchar(36) NOT NULL,
    cycle_id                      varchar(36) NOT NULL,
    round_id                      varchar(36) NOT NULL,
    next_round_invitation_list_json text      NOT NULL,
    decided_at                    timestamp   NOT NULL,
    decided_by                    varchar(120) NOT NULL,
    rationale_text                text,
    PRIMARY KEY (decision_id),
    CONSTRAINT fk_rfrd_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
CREATE INDEX IF NOT EXISTS ix_rfrd_cycle_round
    ON audit.round_field_reduction_decision (cycle_id, round_id);


-- ===========================================================================
-- 10. Deferred cross-schema FKs. ref/cyc/norm form a cross-schema reference cycle
--     (norm.source_artifact → cyc.cycle_round, cyc.cycle_projected_volume →
--     norm.normalization_run, ref.master_data_quarantine → cyc.cycle), so these two
--     edges cannot be inline in a single linear CREATE order. Added here once both
--     ends exist. Guarded so the whole file stays idempotent (ADD CONSTRAINT has no
--     IF NOT EXISTS before PG16; the catalog check makes it a no-op on re-run).
-- ===========================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_quarantine_cycle') THEN
        ALTER TABLE ref.master_data_quarantine
            ADD CONSTRAINT fk_quarantine_cycle
            FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_volume_normalization_run') THEN
        ALTER TABLE cyc.cycle_projected_volume
            ADD CONSTRAINT fk_volume_normalization_run
            FOREIGN KEY (normalization_run_id) REFERENCES norm.normalization_run (normalization_run_id);
    END IF;
END
$$;


-- ============================================================================
-- END M0 BASELINE. 63 as-built tables re-expressed (count below). Net-new layers
-- still greenfield and authored in LATER migrations (NOT M0):
--   * awd.* (award/award_layer/signoff/generated_document) — M8 (G3).
--   * eng.bid_score — M7 (G2). perf.itrade_receipt/kcms_movement/supplier_scorecard — M4–M6 (G6).
--   * norm.lot/attribute_def/lot_attribute/item_lot_map — M2 (G8).
--   * ref.zip_centroid — M3 (G7). cyc kickoff satellites — M9 (G5). ref.client tenant weave — M10.
--
-- TABLE COUNT (this file): 63 re-expressed as-built tables.
--   ref(11): client*, commodity*, subcommodity, dc, supplier, item, loading_location,
--            fiscal_calendar, supplier_alias, item_alias, dc_alias, master_data_quarantine  (12 incl. client)
--   NB: client is net-new (the 63rd as-built has no client); commodity..quarantine = 11 as-built ref tables.
-- The constraint-floor CI assertion (≥46 composite FKs, the 67 de-no-op'd CHECKs) gates fidelity (R-PD2).
-- ============================================================================
