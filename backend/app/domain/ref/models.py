"""SQLAlchemy mapped classes for the `ref` schema.

`Client` is the first-class tenant entity (multi-tenant from the first migration, PLAN §1.5,
security/PLAN §1). `Commodity` demonstrates tenant scoping: it carries `client_id` so the
reference repository/service can show the tenant-scoped query + add+flush pattern the other
seven layers follow.

Note on scope: security/PLAN §1 classes pure global reference (`commodity`, `dc`, ...) as NOT
tenant-scoped in the final model. Here `commodity` carries `client_id` deliberately, as the
SKELETON directs, to make the tenant-scoping pattern concrete and testable in the reference
package this phase; the final tenancy classification table governs production scope.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import SchemaBase
from app.core.db.types import client_id_column, created_at_column, uuid_pk

RefBase = SchemaBase("ref")


class ClientStatus(StrEnum):
    """Tenant lifecycle (security/PLAN §1). SUSPENDED denies access but retains data."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Client(RefBase):
    """A governed tenant (a Kroger sourcing org / business unit). The tenancy keystone."""

    __tablename__ = "client"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[ClientStatus] = mapped_column(
        SAEnum(ClientStatus, name="client_status", schema="ref"),
        nullable=False,
        default=ClientStatus.ACTIVE,
    )
    data_residency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    classification_ceiling: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = created_at_column()
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Commodity(RefBase):
    """A produce commodity (reference dimension), shown tenant-scoped via `client_id`."""

    __tablename__ = "commodity"
    __table_args__ = (
        UniqueConstraint("client_id", "code", name="commodity_client_code"),
        {"schema": "ref"},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    client_id: Mapped[uuid.UUID] = client_id_column()
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = created_at_column()
