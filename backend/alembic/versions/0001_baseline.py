"""baseline — eight schemas + the re-expressed as-built schema (or a minimal seed).

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-18

Behavior (ADR-0001, SKELETON §8):
  1. CREATE SCHEMA IF NOT EXISTS for all eight logical layers (ref norm cyc bid eng awd perf
     audit) — the layering is visible in the database from rev 0001.
  2. If `db/baseline/schema.sql` exists (the Platform & Data deliverable — the as-built schema
     re-expressed as clean PostgreSQL), execute it so the full baseline lands.
  3. Otherwise, create a minimal standalone seed (`ref.client`, `ref.commodity`) so
     `alembic upgrade head` succeeds on its own and the app's reference pattern works.
  4. EITHER path: ensure `audit.event_log` exists (idempotent). The audit writer
     (app/core/audit/writer.py) appends to it on every governed mutation, so it must exist
     from rev 0001. The baseline starter does not yet include it; this create is a no-op once
     Platform & Data add the full audit spine (M1) to db/baseline/schema.sql.

All statements use idempotent guards (IF [NOT] EXISTS) so the migration is safe to re-run and
round-trips cleanly (up -> down -> up). Downgrade drops the seed/audit objects and the eight
schemas (CASCADE), so the round-trip is clean regardless of which path upgrade() took.

PATH CONTRACT (for Platform & infra): this migration reads `db/baseline/schema.sql` resolved
as <repo-root>/db/baseline/schema.sql, where <repo-root> is the parent of `backend/`. The ORM
`ref` models (app/domain/ref/models.py) mirror that file's column names — keep them in lockstep.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The eight logical layers = the eight PostgreSQL schemas.
SCHEMAS: tuple[str, ...] = ("ref", "norm", "cyc", "bid", "eng", "awd", "perf", "audit")

# <repo-root>/db/baseline/schema.sql — this file is backend/alembic/versions/0001_baseline.py,
# so the repo root is three parents up from `backend/`.
REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_SQL = REPO_ROOT / "db" / "baseline" / "schema.sql"


# Minimal standalone seed used only when db/baseline/schema.sql is absent. Column names mirror
# the baseline's ref.client / ref.commodity (and the ORM models) so either path yields the same
# shape for the reference pattern.
MINIMAL_SEED_DDL = """
CREATE TABLE IF NOT EXISTS ref.client (
    id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_code     varchar(40)  NOT NULL,
    client_name     varchar(160) NOT NULL,
    is_active       boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_client_code UNIQUE (client_code),
    CONSTRAINT ck_client_code_not_empty CHECK (length(client_code) > 0)
);

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
CREATE INDEX IF NOT EXISTS ix_commodity_client ON ref.commodity (client_id);
"""

# The single hash-chained event log (writes via app/core/audit/writer.py only). Created on
# BOTH paths, idempotently. DB-layer write-only enforcement (triggers + grants) is Platform &
# Data's M1; this just ensures the writer's INSERT target exists from rev 0001.
AUDIT_EVENT_LOG_DDL = """
CREATE TABLE IF NOT EXISTS audit.event_log (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           uuid NOT NULL,
    occurred_at         timestamptz NOT NULL DEFAULT now(),
    actor               varchar(400) NOT NULL,
    source              varchar(32) NOT NULL,
    event_type          varchar(32) NOT NULL,
    entity_type         varchar(128) NOT NULL,
    entity_id           uuid NOT NULL,
    cycle_id            uuid,
    before_state_hash   char(64),
    after_state_hash    char(64),
    prev_event_hash     char(64) NOT NULL,
    event_hash          char(64) NOT NULL,
    seq                 bigint NOT NULL,
    CONSTRAINT uq_event_log_client_seq UNIQUE (client_id, seq)
);
CREATE INDEX IF NOT EXISTS ix_event_log_client_id ON audit.event_log (client_id);
"""


def upgrade() -> None:
    # 1. The eight schemas — always, idempotent.
    for schema in SCHEMAS:
        op.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')

    # 2 / 3. Apply the full baseline if present; else the minimal standalone seed.
    if BASELINE_SQL.exists():
        op.execute(BASELINE_SQL.read_text(encoding="utf-8"))
    else:
        op.execute(MINIMAL_SEED_DDL)

    # 4. Ensure the audit writer's target exists (no-op once the baseline adds it).
    op.execute(AUDIT_EVENT_LOG_DDL)


def downgrade() -> None:
    # Drop the eight schemas. CASCADE removes everything within them (seed, baseline, audit),
    # so up -> down -> up is clean regardless of which path upgrade() took.
    for schema in reversed(SCHEMAS):
        op.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
