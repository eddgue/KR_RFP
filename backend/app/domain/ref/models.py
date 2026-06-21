"""SQLAlchemy mapped classes for the `ref` schema.

`Client` is the first-class tenant entity (multi-tenant from the first migration, PLAN §1.5,
security/PLAN §1). `Commodity` demonstrates tenant scoping: it carries `client_id` so the
reference repository/service can show the tenant-scoped query + add+flush pattern the other
seven layers follow.

COLUMN ALIGNMENT: these classes map onto the columns Platform & Data ship in
`db/baseline/schema.sql` (the owned baseline, ADR-0001) — `client_code`/`client_name`/
`is_active` on `ref.client`, `commodity_code`/`commodity_name`/`active_flag` on `ref.commodity`.
Keep this in lockstep with that file; the migration applies schema.sql verbatim, so the ORM
must mirror its column names or the reference pattern won't round-trip.

Scope note: security/PLAN §1 classes pure global reference (`commodity`, ...) as NOT
tenant-scoped in the *final* model; the baseline carries `client_id` (nullable for now, NOT
NULL + RLS when Security ratifies). It is kept here to make the tenant-scoping pattern concrete
and testable in the reference package this phase.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase
from app.core.db.types import created_at_column, uuid_pk

if TYPE_CHECKING:
    # The factory builds the per-schema base dynamically at runtime; for the type checker we
    # alias it to the static declarative `Base` so mapped classes have a valid base class.
    RefBase = Base
else:
    RefBase = SchemaBase("ref")


class Client(RefBase):
    """A governed tenant (a Kroger sourcing org / business unit). The tenancy keystone.

    Mirrors `ref.client` in db/baseline/schema.sql.
    """

    __tablename__ = "client"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    client_name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = created_at_column()


class Commodity(RefBase):
    """A produce commodity (reference dimension), shown tenant-scoped via `client_id`.

    Mirrors `ref.commodity` in db/baseline/schema.sql.
    """

    __tablename__ = "commodity"
    __table_args__ = (
        UniqueConstraint("client_id", "commodity_code", name="commodity_code_per_client"),
        {"schema": "ref"},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    # Nullable to match the baseline (NOT NULL + RLS land when Security ratifies, R-PD5).
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ref.client.id"),
        nullable=True,
        index=True,
    )
    commodity_code: Mapped[str] = mapped_column(String(40), nullable=False)
    commodity_name: Mapped[str] = mapped_column(String(120), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = created_at_column()


class FiscalPeriod(RefBase):
    """One period of the Kroger 4-3-3-3 fiscal calendar — the governed period dimension.

    Mirrors the authoritative conversion table shipped as data
    (`app/fiscal/data/kroger_fiscal_periods.csv`) and the typed library `app.fiscal.calendar`
    (FiscalPeriod): a fiscal year carries EXACTLY 13 four-week periods grouped 4-3-3-3 into four
    quarters, with begin/end dates from the sponsor's table (period 13 of a 53-week year has 5
    weeks). This is the period grain other tables FK to; the row set is seeded by migration 0014.
    """

    __tablename__ = "fiscal_period"
    __table_args__ = (
        UniqueConstraint("fiscal_year", "period", name="fiscal_period_year_period"),
        {"schema": "ref"},
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    begin_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    weeks: Mapped[int] = mapped_column(Integer, nullable=False)
