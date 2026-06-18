"""Mapped classes for the `perf` schema — the iTrade receipt feed (E-08 / D11).

Maps the additive `perf.itrade_receipt` table shipped by migration 0006 (the real 43-col iTrade
"Data" feed). Mirrors backend/alembic/versions/0006_perf_itrade_baseline.py.

The D11 savings baseline `perf.v_itrade_actual_paid_baseline` is a VIEW (migration-only — not an
ORM-mapped table). KCMS / supplier_scorecard and the commercial-pricing tables (already in the M0
baseline) remain migration-only for now; only the net-new itrade_receipt table is modelled here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase

if TYPE_CHECKING:
    # SchemaBase builds the per-schema base dynamically at runtime; alias to the static
    # declarative `Base` so mapped classes have a valid base for the type checker.
    PerfBase = Base
else:
    PerfBase = SchemaBase("perf")


class ItradeReceipt(PerfBase):
    """One iTrade receipt line (the real 43-col "Data" feed). Mirrors perf.itrade_receipt (0006).

    Raw text identity columns are persisted as-is; resolution to ref.* (commodity/dc/item/supplier
    via alias → quarantine, never guess) is the importer's job, downstream of this raw grain.
    """

    __tablename__ = "itrade_receipt"

    receipt_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # identity
    commodity_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    subcommodity_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    dc_no: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dc_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_size: Mapped[str | None] = mapped_column(Text, nullable=True)
    item_gross_weight: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    case_net_weight: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    ship_pack_qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)
    warehouse_ship_pack_qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(40), nullable=True)
    warehouse_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    # lineage
    po_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    po_purchase_order_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    line_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    field_buying_office: Mapped[str | None] = mapped_column(Text, nullable=True)
    # the 7-date chain
    po_creation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    po_arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ship_date_request: Mapped[date | None] = mapped_column(Date, nullable=True)
    p200_final_sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ship_date_indicated: Mapped[date | None] = mapped_column(Date, nullable=True)
    ship_date_recorded: Mapped[date | None] = mapped_column(Date, nullable=True)
    # vendor / origin
    supplier_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    ship_from_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    ship_from_state: Mapped[str | None] = mapped_column(String(8), nullable=True)
    ship_from_zip: Mapped[str | None] = mapped_column(String(16), nullable=True)
    routing: Mapped[str | None] = mapped_column(Text, nullable=True)
    # performance
    qty_received: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)
    qty_shipped: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)
    qc_reject_qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)
    # cost
    final_price_fob: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    freight: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    total_w_freight: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    xdock_charges: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    total_xdock: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    cogs: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    # flags (the flag-first gate)
    flag_canceled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    flag_zero_cost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    flag_zero_qty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # fiscal stamping
    fiscal_ypw: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fiscal_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week_of_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # ingestion lineage
    ingestion_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_artifact: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
