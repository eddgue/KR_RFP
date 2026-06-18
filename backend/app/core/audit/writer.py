"""The single audit writer: domain event -> one hash-chained event_log row, same txn.

Wired once here (security/PLAN §3), not sprinkled across services. The writer:
  1. canonically serializes the entity's before/after state and sha256-hashes each;
  2. reads the tenant's current chain head (`prev_event_hash`, `seq`) under a row lock so
     the per-tenant chain is serialized;
  3. computes `event_hash = sha256(canonical(this row's fields) || prev_event_hash)`;
  4. appends the row in the SAME transaction as the change it records.

The hash construction is implemented as pure functions so it is unit-testable without a DB.
DB-level write-only enforcement (UPDATE/DELETE triggers, INSERT/SELECT-only grants) is owned
by Platform & Data's M1; this is the application-layer producer.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.audit.events import DomainEvent

# The genesis link for a tenant's first event (no prior hash).
GENESIS_HASH = "0" * 64


def _canonical(payload: Any) -> str:
    """Deterministic JSON serialization: sorted keys, compact, str-coerced for non-JSON types."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def hash_state(state: dict[str, Any] | None) -> str | None:
    """sha256 of the canonical serialization of an entity state (None -> None)."""

    if state is None:
        return None
    return hashlib.sha256(_canonical(state).encode("utf-8")).hexdigest()


def compute_event_hash(
    *,
    prev_event_hash: str,
    client_id: uuid.UUID,
    seq: int,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID,
    actor: str,
    occurred_at: datetime,
    before_state_hash: str | None,
    after_state_hash: str | None,
) -> str:
    """Compute the chain link: sha256(canonical(row fields) || prev_event_hash).

    Pure and deterministic — the same inputs always yield the same hash, which is what makes
    the chain verifiable. Any edit/reorder/delete breaks the recomputed link (tamper-evidence,
    security/PLAN §3).
    """

    body = _canonical(
        {
            "client_id": str(client_id),
            "seq": seq,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "actor": actor,
            "occurred_at": occurred_at.isoformat(),
            "before_state_hash": before_state_hash,
            "after_state_hash": after_state_hash,
        }
    )
    return hashlib.sha256((body + prev_event_hash).encode("utf-8")).hexdigest()


class AuditWriter:
    """Appends one hash-chained `audit.event_log` row per domain event, in the caller's txn."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _current_head(self, client_id: uuid.UUID) -> tuple[str, int]:
        """Return (prev_event_hash, last_seq) for the tenant's chain head under a row lock.

        Serializes per tenant so concurrent writers cannot fork the chain. Returns the genesis
        link and seq 0 when the tenant has no events yet.
        """

        row = self._session.execute(
            text(
                "SELECT event_hash, seq FROM audit.event_log "
                "WHERE client_id = :cid ORDER BY seq DESC LIMIT 1 FOR UPDATE"
            ),
            {"cid": str(client_id)},
        ).first()
        if row is None:
            return GENESIS_HASH, 0
        return row[0], row[1]

    def append(self, event: DomainEvent, occurred_at: datetime | None = None) -> str:
        """Append the chained row for `event`; return the new `event_hash`.

        Does NOT commit — the unit of work owns the commit, so this lands in the same
        transaction as the change it records (PLAN §7, security/PLAN §3).
        """

        occurred_at = occurred_at or datetime.now()
        prev_hash, last_seq = self._current_head(event.client_id)
        seq = last_seq + 1

        before_hash = hash_state(event.before)
        after_hash = hash_state(event.after)
        event_hash = compute_event_hash(
            prev_event_hash=prev_hash,
            client_id=event.client_id,
            seq=seq,
            event_type=event.event_type.value,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            actor=event.actor,
            occurred_at=occurred_at,
            before_state_hash=before_hash,
            after_state_hash=after_hash,
        )

        self._session.execute(
            text(
                "INSERT INTO audit.event_log "
                "(id, client_id, occurred_at, actor, source, event_type, entity_type, "
                " entity_id, cycle_id, before_state_hash, after_state_hash, "
                " prev_event_hash, event_hash, seq) "
                "VALUES "
                "(:id, :client_id, :occurred_at, :actor, :source, :event_type, :entity_type, "
                " :entity_id, :cycle_id, :before_state_hash, :after_state_hash, "
                " :prev_event_hash, :event_hash, :seq)"
            ),
            {
                "id": str(uuid.uuid4()),
                "client_id": str(event.client_id),
                "occurred_at": occurred_at,
                "actor": event.actor,
                "source": event.source,
                "event_type": event.event_type.value,
                "entity_type": event.entity_type,
                "entity_id": str(event.entity_id),
                "cycle_id": str(event.cycle_id) if event.cycle_id else None,
                "before_state_hash": before_hash,
                "after_state_hash": after_hash,
                "prev_event_hash": prev_hash,
                "event_hash": event_hash,
                "seq": seq,
            },
        )
        return event_hash
