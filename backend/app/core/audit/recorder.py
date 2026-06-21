"""Tenant resolution for decision-site audit events (Gap G-B).

The governed decision sites (pilot ingest/run, award freeze/adjust) hold a `cycle_id` or an
`award_id` — not a tenant. The per-tenant audit chain keys on `client_id`, so these resolvers
walk the FK spine (cycle/award → commodity → client) to recover the owning tenant for the event.

Kept separate from `AuditWriter` so the writer stays a pure chain-appender and the SQL lives in
one place. The queries are literal strings with bound parameters (no f-string interpolation), so
the bandit/ruff S-rules stay satisfied.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session


def client_id_for_cycle(session: Session, cycle_id: str) -> uuid.UUID:
    """The owning tenant for a cycle (cyc.cycle → ref.commodity.client_id).

    Raises `ValueError` if the cycle is unknown or its commodity carries no client — the audit
    chain cannot key an event without a tenant.
    """

    row = session.execute(
        text(
            "SELECT co.client_id FROM cyc.cycle cy "
            "JOIN ref.commodity co ON co.id::text = cy.commodity_id "
            "WHERE cy.cycle_id = :cid"
        ),
        {"cid": cycle_id},
    ).first()
    if row is None or row[0] is None:
        raise ValueError(f"no client_id resolvable for cycle_id={cycle_id!r}")
    return uuid.UUID(str(row[0]))


def client_id_for_award(session: Session, award_id: str) -> uuid.UUID:
    """The owning tenant for an award (awd.award → cyc.cycle → ref.commodity.client_id).

    Raises `ValueError` if the award is unknown or its commodity carries no client.
    """

    row = session.execute(
        text(
            "SELECT co.client_id FROM awd.award a "
            "JOIN cyc.cycle cy ON cy.cycle_id = a.cycle_id "
            "JOIN ref.commodity co ON co.id::text = cy.commodity_id "
            "WHERE a.award_id = :aid"
        ),
        {"aid": award_id},
    ).first()
    if row is None or row[0] is None:
        raise ValueError(f"no client_id resolvable for award_id={award_id!r}")
    return uuid.UUID(str(row[0]))
