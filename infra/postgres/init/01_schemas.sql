-- infra/postgres/init/01_schemas.sql
-- Bootstrap for the local `db` service (SKELETON §4). Runs once on an empty data volume
-- via /docker-entrypoint-initdb.d. Kept fully IDEMPOTENT because Alembic's rev 0001 also
-- ensures these schemas (db/baseline/schema.sql) — both paths must be safe to run.
--
-- Creates: the eight logical-layer schemas, and a least-privilege application role.
-- This is local convenience only; staging/prod provision roles via IaC (DevOps PLAN §4).

-- ---- the eight domain schemas (one per logical layer, PLAN §2) ----
CREATE SCHEMA IF NOT EXISTS ref;     -- reference / master data + tenant
CREATE SCHEMA IF NOT EXISTS norm;    -- normalization: persistent lots, attributes, lineage
CREATE SCHEMA IF NOT EXISTS cyc;     -- RFP cycle keystone + kickoff satellites
CREATE SCHEMA IF NOT EXISTS bid;     -- bid submissions, landed cost, eligibility, capacity
CREATE SCHEMA IF NOT EXISTS eng;     -- sealed calc runs, scenarios, scores
CREATE SCHEMA IF NOT EXISTS awd;     -- awards, layers, signoff, generated documents
CREATE SCHEMA IF NOT EXISTS perf;    -- feeds: iTrade receipts, KCMS, scorecards, commercial
CREATE SCHEMA IF NOT EXISTS audit;   -- hash-chained event log + decision notes

-- ---- least-privilege application role ----
-- The app connects as a non-superuser. Idempotent create (CREATE ROLE has no IF NOT EXISTS).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kr_rfp_app') THEN
    CREATE ROLE kr_rfp_app LOGIN PASSWORD 'kr_rfp_app';
  END IF;
END
$$;

-- Grant usage on the schemas (DML grants on tables are issued by migrations as tables land).
GRANT USAGE ON SCHEMA ref, norm, cyc, bid, eng, awd, perf, audit TO kr_rfp_app;

-- Future tables/sequences created in these schemas are usable by the app role by default.
DO $$
DECLARE
  s text;
BEGIN
  FOREACH s IN ARRAY ARRAY['ref','norm','cyc','bid','eng','awd','perf','audit']
  LOOP
    EXECUTE format(
      'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
      'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO kr_rfp_app', s);
    EXECUTE format(
      'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
      'GRANT USAGE, SELECT ON SEQUENCES TO kr_rfp_app', s);
  END LOOP;
END
$$;
