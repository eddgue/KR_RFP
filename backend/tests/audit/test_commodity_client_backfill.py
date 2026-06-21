"""Migration 0018 — a pre-G-B commodity (client_id NULL) gets a tenant so the audit chain resolves.

Before G-B, setup ingest left `ref.commodity.client_id` NULL; the now-mandatory resolver
(`app/core/audit/recorder.py`, which joins `cyc.cycle → ref.commodity.client_id`) then strands such
runs. This proves the backfill assigns those orphaned commodities a tenant — the exact column the
resolver's JOIN depends on. The backfill SQL mirrors migration 0018 (migrations can't be imported as
app code, so the two are intentionally kept in sync).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

# The sentinel "legacy" tenant from migration 0018.
_LEGACY_CLIENT_ID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.integration
def test_backfill_assigns_tenant_to_orphan_commodity(db_session) -> None:  # type: ignore[no-untyped-def]
    """An orphaned commodity (client_id NULL) is assigned the sentinel tenant by the backfill."""

    commodity_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO ref.commodity (id, client_id, commodity_code, commodity_name) "
            "VALUES (:cid, NULL, :code, 'Legacy Berries')"
        ),
        {"cid": commodity_id, "code": f"COMM-{commodity_id[:8]}"},
    )
    db_session.flush()

    # Pre-backfill: orphaned (no tenant) — the resolver would raise on this.
    assert (
        db_session.execute(
            text("SELECT client_id FROM ref.commodity WHERE id = :c"), {"c": commodity_id}
        ).scalar_one()
        is None
    )

    # The backfill (mirrors migration 0018): create the sentinel client, adopt every orphan.
    db_session.execute(
        text(
            "INSERT INTO ref.client (id, client_code, client_name) "
            "SELECT :sid, 'BACKFILL-LEGACY', 'Legacy backfill tenant' "
            "WHERE NOT EXISTS (SELECT 1 FROM ref.client WHERE id = :sid)"
        ),
        {"sid": _LEGACY_CLIENT_ID},
    )
    db_session.execute(
        text("UPDATE ref.commodity SET client_id = :sid WHERE client_id IS NULL"),
        {"sid": _LEGACY_CLIENT_ID},
    )
    db_session.flush()

    # Now the commodity carries a tenant — the resolver's JOIN resolves, the run is not stranded.
    assert db_session.execute(
        text("SELECT client_id FROM ref.commodity WHERE id = :c"), {"c": commodity_id}
    ).scalar_one() == uuid.UUID(_LEGACY_CLIENT_ID)
