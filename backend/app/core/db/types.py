"""Shared column types and mapped-column helpers (Postgres-targeted).

Canonical building blocks reused across all eight layers: UUID primary keys, fixed-precision
money (Numeric(18,6) — six decimal places carries case-level pricing without float drift),
and tenant-scoping (`client_id`) per security/PLAN §1.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

# Money: fixed precision/scale; never a float. 18 total digits, 6 after the point.
MONEY_PRECISION = 18
MONEY_SCALE = 6
Money = Numeric(MONEY_PRECISION, MONEY_SCALE, asdecimal=True)


def uuid_pk() -> Mapped[uuid.UUID]:
    """A server-generatable UUID primary key column."""

    return mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


def money_column(*, nullable: bool = True) -> Mapped[Decimal | None]:
    """A Numeric(18,6) money column."""

    return mapped_column(Money, nullable=nullable)


def client_id_column() -> Mapped[uuid.UUID]:
    """Non-null tenant FK to ``ref.client``.

    Tenant-scoped tables carry this; the value is stamped from request context, never from a
    client-supplied body (security/PLAN §1). Indexed because every scoped read filters on it.
    """

    return mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ref.client.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )


def created_at_column() -> Mapped[datetime]:
    """Server-defaulted creation timestamp (UTC)."""

    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
