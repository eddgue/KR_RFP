-- ============================================================================
-- db/baseline/schema.sql — the Alembic baseline (revision 0001)
-- ============================================================================
-- Clean-room re-expression of the as-built schema as clean PostgreSQL 15 DDL.
-- This is OUR OWN artifact (ADR-0001), NOT an import of the existing codebase.
-- Source provenance + the canonicalization rule: see README.md and NAMING_MAP.md.
--
-- *** STARTER BASELINE — FILLED INCREMENTALLY ***
-- This file currently lands the eight schemas plus a minimal, REAL slice of the KEEP
-- spine (ref.client tenant + ref.commodity). The FULL reconciled 63-table DDL — the
-- KEEP spine, all 46 composite-identity FKs, the de-no-op'd CHECKs — is the Platform &
-- Data squad's first deliverable (E-01 / M0), authored incrementally per
-- project/squads/platform-data/PLAN.md §2. Fidelity is gated in CI by the migration
-- roundtrip + `alembic check` + the ≥46-composite-FK constraint floor (R-PD2).
--
-- INVARIANTS this file must always hold (backend alembic 0001 executes it verbatim):
--   * IDEMPOTENT  — re-running is a no-op (IF NOT EXISTS everywhere; guarded DO blocks).
--   * SELF-CONTAINED — no \i includes, no external functions, runs on a bare PG15.
--   * CLEAN PG — native `boolean` (no DEFAULT 0/1), no SQLite-isms, real predicates.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. The eight logical-layer schemas (PLAN §2). Idempotent; Alembic + the infra
--    init script (infra/postgres/init/01_schemas.sql) both ensure these — safe to
--    run in any order, any number of times.
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS ref;     -- reference / master data + tenant
CREATE SCHEMA IF NOT EXISTS norm;    -- normalization: persistent lots, attributes, lineage
CREATE SCHEMA IF NOT EXISTS cyc;     -- RFP cycle keystone + kickoff satellites
CREATE SCHEMA IF NOT EXISTS bid;     -- bid submissions, landed cost, eligibility, capacity
CREATE SCHEMA IF NOT EXISTS eng;     -- sealed calc runs, scenarios, scores
CREATE SCHEMA IF NOT EXISTS awd;     -- awards, layers, signoff, generated documents
CREATE SCHEMA IF NOT EXISTS perf;    -- feeds: iTrade receipts, KCMS, scorecards, commercial
CREATE SCHEMA IF NOT EXISTS audit;   -- hash-chained event log + decision notes

-- ---------------------------------------------------------------------------
-- 2. KEEP-spine starter (real, minimal). Net-new spine tables use native `uuid`
--    PKs (the Phase-0 decision for net-new/clean tables; adopted tables retain
--    text-UUID PKs for composite-FK fidelity — see README.md / NAMING_MAP.md).
--    `gen_random_uuid()` is built in on PostgreSQL 13+ (no extension needed).
-- ---------------------------------------------------------------------------

-- ref.client — the tenant root (ADD; net-new enterprise layer). Every tenant-scoped
-- table carries a client_id FK; Security owns the RLS policy that lands at M10 (E-03).
CREATE TABLE IF NOT EXISTS ref.client (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_code     varchar(40)  NOT NULL,
    client_name     varchar(160) NOT NULL,
    is_active       boolean      NOT NULL DEFAULT true,   -- native boolean, not DEFAULT 1
    created_at      timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_client_code UNIQUE (client_code),
    CONSTRAINT ck_client_code_not_empty CHECK (length(client_code) > 0)
);

COMMENT ON TABLE ref.client IS
    'Tenant root (net-new). client_id FK columns hang off this; RLS policy lands at M10 (Security).';

-- ref.commodity — ADOPT of as-built commodity_master_db (NAMING_MAP: drop _master_db).
-- Tenant-scoped via client_id (net-new tenancy column; nullable for now, NOT NULL +
-- RLS when Security's spec ratifies — Platform & Data PLAN §6 R-PD5).
CREATE TABLE IF NOT EXISTS ref.commodity (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       uuid         REFERENCES ref.client (id),
    commodity_code  varchar(40)  NOT NULL,
    commodity_name  varchar(120) NOT NULL,
    abbreviation    varchar(20),
    active_flag     boolean      NOT NULL DEFAULT true,   -- as-built BOOLEAN NOT NULL, cleaned
    created_at      timestamptz  NOT NULL DEFAULT now(),
    -- As-built used global UNIQUE(commodity_code); under tenancy it is unique PER tenant.
    CONSTRAINT uq_commodity_code_per_client UNIQUE (client_id, commodity_code),
    CONSTRAINT ck_commodity_code_not_empty  CHECK (length(commodity_code) > 0)
);

COMMENT ON TABLE ref.commodity IS
    'ADOPT of as-built commodity_master_db, schema-qualified + tenant-scoped (client_id).';

CREATE INDEX IF NOT EXISTS ix_commodity_client ON ref.commodity (client_id);

-- ============================================================================
-- END STARTER. The remaining ~61 tables, the 46 composite-identity FKs, and the
-- 67 (de-no-op'd) CHECK constraints are appended here at M0, schema by schema,
-- per project/squads/platform-data/PLAN.md §2. Keep every addition IDEMPOTENT
-- and CLEAN so this file remains safe for alembic 0001 to execute verbatim.
-- ============================================================================
