"""Domain event types emitted by services (security/PLAN §3).

Population is NOT the caller's job to remember: services emit one of these on every governed
mutation, and the single `AuditWriter` subscriber turns it into a hash-chained `event_log`
row in the same transaction. The event carries the pre/post canonical state so the writer can
compute the before/after hashes without re-reading the row.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    """The governed state changes (security/PLAN §3)."""

    CREATED = "CREATED"
    SEALED = "SEALED"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"
    SIGNED_OFF = "SIGNED_OFF"
    SENT = "SENT"
    GATE_APPROVED = "GATE_APPROVED"
    IMPORTED = "IMPORTED"


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """One governed mutation, ready for the audit writer to chain.

    `before` / `after` are canonical-serializable dicts of the entity's relevant state; the
    writer hashes them. For a create, `before` is None; for a seal/freeze it captures the
    transition. No commercial values should be placed in `metadata` (it may surface in reads).
    """

    event_type: EventType
    client_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    actor: str
    cycle_id: uuid.UUID | None = None
    source: str = "api"  # api | worker | import
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
