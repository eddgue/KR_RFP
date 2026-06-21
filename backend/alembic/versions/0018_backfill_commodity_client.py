"""Backfill ref.commodity.client_id so pre-G-B cycles resolve a tenant for the audit chain.

Revision ID: 0018_backfill_commodity_client
Revises: 0017_auth_app_user
Create Date: 2026-06-21

DATA backfill (no schema change). Before the G-B change, setup ingest inserted commodities with
`client_id = NULL` (the schema permits it). G-B made tenant resolution MANDATORY at every governed
decision (`app/core/audit/recorder.py` raises when a commodity has no client), so a cycle created
BEFORE that change would now raise on ingest/run/freeze/adjust — its run is effectively stranded.

This adopts every orphaned commodity (client_id IS NULL) into a legacy tenant so those runs resolve
again. Each orphan gets its OWN deterministic legacy client (id = `md5('legacy-client:'||id)`), NOT
a single shared sentinel: two orphaned commodities may legitimately share a `commodity_code` today
(the `uq_commodity_code_per_client` UNIQUE(client_id, commodity_code) treats NULL client_id rows as
distinct), so assigning them a common client_id would VIOLATE that unique and abort the upgrade. A
per-orphan client keeps each (client_id, commodity_code) pair distinct.

It touches only orphans, so a fresh database (and every post-G-B run, which already stamps the
client) gets nothing — a no-op where there is nothing to fix. Idempotent (`ON CONFLICT (id) DO
NOTHING`) and reversible (round-trips up -> down -> up cleanly).

SCOPE NOTE: this fixes the shared app database (D36) and any per-run database migrated to head. A
pre-G-B per-run database REHYDRATED from a vault snapshot is NOT re-migrated (D34, restore loads the
dump without re-running migrations), so such a snapshot would remain orphaned — a rare edge given
pre-G-B runs. No `app.*` import — migrations stay frozen/standalone.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018_backfill_commodity_client"
down_revision: str | None = "0017_auth_app_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Deterministic per-orphan legacy client id, derived from the commodity id (distinct per commodity,
# so duplicate commodity_codes land under distinct clients). A salted md5 cast to uuid.
_LEGACY_CLIENT_ID_SQL = "md5('legacy-client:' || c.id::text)::uuid"


def upgrade() -> None:
    # One legacy client PER orphaned commodity (distinct client_id => no collision on
    # uq_commodity_code_per_client even when two orphans share a commodity_code). client_code =
    # 'BF-' + the commodity's 32-hex id: unique (uq_client_code) and 35 chars, within varchar(40).
    op.execute(
        "INSERT INTO ref.client (id, client_code, client_name) "
        f"SELECT {_LEGACY_CLIENT_ID_SQL}, 'BF-' || replace(c.id::text, '-', ''), "
        "'Legacy backfill tenant (pre-G-B)' "
        "FROM ref.commodity c WHERE c.client_id IS NULL "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute(
        f"UPDATE ref.commodity c SET client_id = {_LEGACY_CLIENT_ID_SQL} WHERE c.client_id IS NULL"
    )


def downgrade() -> None:
    # Null the backfilled commodities (those pointing at their OWN derived legacy client), then drop
    # those legacy clients (id recomputed from the still-present commodity ids). Order matters: the
    # FK commodity.client_id -> client.id means the commodities must be detached first.
    op.execute(
        f"UPDATE ref.commodity c SET client_id = NULL WHERE c.client_id = {_LEGACY_CLIENT_ID_SQL}"
    )
    op.execute(
        f"DELETE FROM ref.client WHERE id IN (SELECT {_LEGACY_CLIENT_ID_SQL} FROM ref.commodity c)"
    )
