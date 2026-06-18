"""Mapped classes for the `norm` schema — the shared attribute taxonomy (D14 / G8).

Maps the additive `norm.*` tables shipped by migration 0004 (norm attribute taxonomy). Mirrors
backend/alembic/versions/0004_norm_attribute_taxonomy.py.

The persistent cross-cycle lot store (norm.lot, norm.item_lot_map) and the file-lineage spine
(norm.source_artifact, norm.normalization_run — already in the M0 baseline) remain migration-only
for now; only the net-new attribute catalog + sparse per-lot attributes are modelled here.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase

if TYPE_CHECKING:
    # SchemaBase builds the per-schema base dynamically at runtime; alias to the static
    # declarative `Base` so mapped classes have a valid base for the type checker.
    NormBase = Base
else:
    NormBase = SchemaBase("norm")


class AttributeDef(NormBase):
    """One shared, superset attribute catalog entry (D14). Mirrors norm.attribute_def (0004)."""

    __tablename__ = "attribute_def"

    attribute_code: Mapped[str] = mapped_column(String(60), primary_key=True)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    data_type: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    allowed_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    commodity_hint: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LotAttribute(NormBase):
    """Sparse per-lot attribute (D14). Mirrors norm.lot_attribute (0004).

    A lot carries only its applicable attributes from the shared catalog; the value lands in the
    column matching the def's data_type. lot_id is unconstrained until norm.lot lands (M2/G8).
    """

    __tablename__ = "lot_attribute"

    lot_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attribute_code: Mapped[str] = mapped_column(
        String(60), ForeignKey("norm.attribute_def.attribute_code"), primary_key=True
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    value_bool: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
