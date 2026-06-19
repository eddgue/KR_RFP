"""SQLAlchemy mapped classes for the `bid` schema — the intake module's write target.

`BidLine` maps `bid.bid_line` (db/baseline/schema.sql) PLUS the engine cost-component columns
added by migration 0007 (`delivery_surcharge_case`, `vegcool_surcharge_case`, `lot_discount_case`,
`price_basis_resolved`). This is the row the bid ingester writes (D20 ingest end) and the engine
reads (V3 §7 cost construction). The grain is the identity octuple — one row per
submission x DC x lot x item x TF (and, via the submission, supplier x round x cycle).

COLUMN ALIGNMENT: mirrors `bid.bid_line` verbatim so the ORM round-trips against the migration
(the same lockstep rule the `ref` models follow). Only the columns the intake/engine path needs
are mapped here; the remaining baseline columns exist in the table and are managed by SQL.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase

if TYPE_CHECKING:
    BidBaseT = Base
else:
    BidBaseT = SchemaBase("bid")

# Re-export the legacy attribute name some callers / the alembic seam expect.
BidBase = BidBaseT

_Money = Numeric(18, 6)


class BidLine(BidBaseT):
    """A priced bid line — the round-trip target. Mirrors `bid.bid_line` + migration 0007."""

    __tablename__ = "bid_line"

    bid_line_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), nullable=False)
    cycle_id: Mapped[str] = mapped_column(String(36), nullable=False)
    round_id: Mapped[str] = mapped_column(String(36), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dc_id: Mapped[str] = mapped_column(String(36), nullable=False)
    lot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tf_id: Mapped[str] = mapped_column(String(36), nullable=False)

    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    price_basis: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Engine IN_Bids cost stack (All-In primary + §7 fallback components). ---
    submitted_all_in_case: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    fob_case: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    # Added by migration 0007 — the engine's named surcharge/discount components.
    delivery_surcharge_case: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    vegcool_surcharge_case: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    lot_discount_case: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    price_basis_resolved: Mapped[str | None] = mapped_column(Text, nullable=True)

    commercial_conditions_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusivity_required_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    effective_date_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    validity_status: Mapped[str] = mapped_column(Text, nullable=False)
    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    bid_line_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_scoreable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_awardable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    incomplete_reason_code: Mapped[str | None] = mapped_column(Text, nullable=True)
