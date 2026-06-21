"""Migration 0018 — pre-G-B commodities (client_id NULL) get a tenant so the audit chain resolves.

Before G-B, setup ingest left `ref.commodity.client_id` NULL; the now-mandatory resolver
(`app/core/audit/recorder.py`, which joins `cyc.cycle → ref.commodity.client_id`) then strands such
runs. This proves the backfill adopts orphaned commodities into a tenant — and that two orphans
sharing a `commodity_code` each get their OWN client, so the backfill cannot violate
`uq_commodity_code_per_client` and abort the upgrade. The backfill SQL mirrors migration 0018
(migrations can't be imported as app code, so the two are intentionally kept in sync).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

# Mirrors migration 0018: one deterministic legacy client per orphaned commodity.
_INSERT_LEGACY_CLIENTS = (
    "INSERT INTO ref.client (id, client_code, client_name) "
    "SELECT md5('legacy-client:' || c.id::text)::uuid, 'BF-' || replace(c.id::text, '-', ''), "
    "'Legacy' FROM ref.commodity c WHERE c.client_id IS NULL ON CONFLICT (id) DO NOTHING"
)
_ADOPT_ORPHANS = (
    "UPDATE ref.commodity c SET client_id = md5('legacy-client:' || c.id::text)::uuid "
    "WHERE c.client_id IS NULL"
)


def _client_of(db_session, commodity_id: str):  # type: ignore[no-untyped-def]
    return db_session.execute(
        text("SELECT client_id FROM ref.commodity WHERE id = :c"), {"c": commodity_id}
    ).scalar_one()


@pytest.mark.integration
def test_backfill_adopts_orphans_with_a_distinct_client_per_duplicate_code(db_session) -> None:  # type: ignore[no-untyped-def]
    """Two orphan commodities sharing a commodity_code each get their OWN legacy client.

    They are valid pre-migration because NULL client_id makes `uq_commodity_code_per_client`
    distinct; a single shared sentinel would violate that unique on backfill, so each orphan must
    get a per-row client.
    """

    shared_code = f"COMM-DUP-{uuid.uuid4().hex[:8]}"
    com_a, com_b = str(uuid.uuid4()), str(uuid.uuid4())
    for cid in (com_a, com_b):
        db_session.execute(
            text(
                "INSERT INTO ref.commodity (id, client_id, commodity_code, commodity_name) "
                "VALUES (:cid, NULL, :code, 'Legacy Berries')"
            ),
            {"cid": cid, "code": shared_code},  # same code, NULL client → allowed today
        )
    db_session.flush()
    assert _client_of(db_session, com_a) is None  # orphaned (resolver would raise)

    db_session.execute(text(_INSERT_LEGACY_CLIENTS))
    db_session.execute(text(_ADOPT_ORPHANS))  # would abort here if it used one shared client
    db_session.flush()

    client_a, client_b = _client_of(db_session, com_a), _client_of(db_session, com_b)
    # Both adopted a tenant (the resolver's JOIN now resolves) ...
    assert client_a is not None
    assert client_b is not None
    # ... and the duplicate code lands under DISTINCT clients, so the unique is never violated.
    assert client_a != client_b
