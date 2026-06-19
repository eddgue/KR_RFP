"""Mapped classes for the `awd` schema — the frozen award + versioned adjustment layers.

Target tables (PLAN §2, migration 0010): a FROZEN award promoted from a selected engine scenario
plus the append-only VERSIONED post-award adjustment layers (ADR-0014 freeze-and-layer):
  * `award`                 — one frozen award per selected (cycle, run, scenario); the baseline
                              header (`frozen_at`, `frozen_by`, status).
  * `award_line`            — the immutable baseline: one row per awarded cell (`frozen_price`).
                              NEVER updated (raw-never-overwritten).
  * `award_adjustment`      — an append-only VERSIONED layer (`version_no` 1..N, type, effective
                              date, reason, who/when). UNIQUE(award, version_no).
  * `award_adjustment_line` — per-cell `prior_price` -> `new_price` -> `delta` for a layer.

Selection promotes a scenario to an award (ADR-0006: a human selects; the engine never asserts).
Post-award price moves are append-only date-stamped layers on the frozen award; the raw award is
never overwritten (ADR-0014). A price change supersedes via a new row, never a hard delete/UPDATE
of the baseline (ADR-0006).

COLUMN ALIGNMENT: mirrors migration 0010 verbatim so the ORM round-trips against the migration
(the same lockstep rule the `ref`/`eng`/`bid` models follow).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase

if TYPE_CHECKING:
    # SchemaBase builds the per-schema base dynamically at runtime; alias to the static
    # declarative `Base` so mapped classes have a valid base for the type checker.
    AwdBase = Base
else:
    AwdBase = SchemaBase("awd")

_Money = Numeric(18, 6)
_Share = Numeric(9, 6)


class Award(AwdBase):
    """A FROZEN award promoted from a selected engine scenario — the immutable baseline header."""

    __tablename__ = "award"

    award_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cycle_id: Mapped[str] = mapped_column(String(36), nullable=False)
    analysis_run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    scenario_code: Mapped[str] = mapped_column(Text, nullable=False)
    award_code: Mapped[str] = mapped_column(Text, nullable=False)
    frozen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    frozen_by: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="FROZEN")


class AwardLine(AwdBase):
    """The immutable baseline: one row per awarded cell at the frozen price (never updated)."""

    __tablename__ = "award_line"

    award_line_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    award_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dc_id: Mapped[str] = mapped_column(String(36), nullable=False)
    lot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tf_id: Mapped[str] = mapped_column(String(36), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    volume_share: Mapped[Decimal] = mapped_column(_Share, nullable=False)
    frozen_price: Mapped[Decimal] = mapped_column(_Money, nullable=False)


class AwardAdjustment(AwdBase):
    """An append-only, date-stamped, VERSIONED post-award price layer (ADR-0014)."""

    __tablename__ = "award_adjustment"

    adjustment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    award_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    adjustment_type: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="RECORDED")


class AwardAdjustmentLine(AwdBase):
    """Per-cell prior_price -> new_price -> delta for one adjustment layer."""

    __tablename__ = "award_adjustment_line"

    adj_line_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    adjustment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dc_id: Mapped[str] = mapped_column(String(36), nullable=False)
    lot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tf_id: Mapped[str] = mapped_column(String(36), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    prior_price: Mapped[Decimal] = mapped_column(_Money, nullable=False)
    new_price: Mapped[Decimal] = mapped_column(_Money, nullable=False)
    delta: Mapped[Decimal] = mapped_column(_Money, nullable=False)
