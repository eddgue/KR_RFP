"""Backfill ref.commodity.client_id so pre-G-B cycles resolve a tenant for the audit chain.

Revision ID: 0018_backfill_commodity_client
Revises: 0017_auth_app_user
Create Date: 2026-06-21

DATA backfill (no schema change). Before the G-B change, setup ingest inserted commodities with
`client_id = NULL` (the schema permits it). G-B made tenant resolution MANDATORY at every governed
decision (`app/core/audit/recorder.py` raises when a commodity has no client), so a cycle created
BEFORE that change would now raise on ingest/run/freeze/adjust — its run is effectively stranded.

This assigns every orphaned commodity (client_id IS NULL) to a single sentinel "legacy" client so
those runs resolve a tenant again. It is created ONLY when orphans exist, so a fresh database (and
every post-G-B run, which already stamps the client) gets nothing — keeping the migration a no-op
where there is nothing to fix. Idempotent and reversible (round-trips up -> down -> up cleanly).

SCOPE NOTE: this fixes the shared app database (D36) and any per-run database that is migrated to
head. A pre-G-B per-run database REHYDRATED from a vault snapshot is NOT re-migrated (D34, restore
loads the dump without re-running migrations), so such a snapshot would remain orphaned — a rare
edge given pre-G-B runs. No `app.*` import — migrations stay frozen/standalone.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018_backfill_commodity_client"
down_revision: str | None = "0017_auth_app_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A fixed, obviously-synthetic tenant id for pre-G-B (orphaned) commodities. Constant so the
# migration is deterministic + idempotent; literal in the SQL (a migration constant, never input).
_LEGACY_CLIENT_ID = "11111111-1111-1111-1111-111111111111"


def upgrade() -> None:
    # Create the sentinel client ONLY if there is something to backfill (keeps fresh DBs clean).
    op.execute(
        "INSERT INTO ref.client (id, client_code, client_name) "
        f"SELECT '{_LEGACY_CLIENT_ID}', 'BACKFILL-LEGACY', "
        "'Legacy backfill tenant (pre-G-B commodities)' "
        "WHERE EXISTS (SELECT 1 FROM ref.commodity WHERE client_id IS NULL) "
        f"AND NOT EXISTS (SELECT 1 FROM ref.client WHERE id = '{_LEGACY_CLIENT_ID}')"
    )
    op.execute(
        f"UPDATE ref.commodity SET client_id = '{_LEGACY_CLIENT_ID}' WHERE client_id IS NULL"
    )


def downgrade() -> None:
    # Reverse only what this migration assigned: null the sentinel-owned commodities, drop the
    # sentinel client. Commodities with a real client are untouched.
    op.execute(f"UPDATE ref.commodity SET client_id = NULL WHERE client_id = '{_LEGACY_CLIENT_ID}'")
    op.execute(f"DELETE FROM ref.client WHERE id = '{_LEGACY_CLIENT_ID}'")
