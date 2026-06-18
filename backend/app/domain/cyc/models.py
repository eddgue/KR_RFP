"""Mapped classes for the `cyc` schema — the kickoff keystone satellites.

These map the additive `cyc.*` tables shipped by migrations 0002 (kickoff satellites) and 0003
(cycle_safety). They mirror the DDL in:
  * backend/alembic/versions/0002_cyc_kickoff_satellites.py
  * backend/alembic/versions/0003_cyc_cycle_safety.py

Grain: cyc.cycle's PK is `cycle_id varchar(36)` in the M0 baseline, so every satellite FKs that
type (these classes use `cycle_id: Mapped[str]`). The baseline cyc.cycle itself is migration-only
(re-expressed in db/baseline/schema.sql); these are the net-new satellites the ORM now owns.

The keystone tables for the baseline cyc spine (cycle, cycle_round, cycle_lot, ...) remain
migration-only for now; only the additive satellites are modelled here.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase

if TYPE_CHECKING:
    # SchemaBase builds the per-schema base dynamically at runtime; alias to the static
    # declarative `Base` so mapped classes have a valid base for the type checker.
    CycBase = Base
else:
    CycBase = SchemaBase("cyc")


class CycleObjective(CycBase):
    """A cycle objective (multi, exactly one primary). Mirrors cyc.cycle_objective (0002)."""

    __tablename__ = "cycle_objective"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    objective_code: Mapped[str] = mapped_column(Text, primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    objective_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class CyclePricing(CycBase):
    """The ONE-per-cycle pricing render contract (D9/D12). Mirrors cyc.cycle_pricing (0002)."""

    __tablename__ = "cycle_pricing"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    pricing_basis: Mapped[str] = mapped_column(Text, nullable=False)
    duration_cadence: Mapped[str] = mapped_column(Text, nullable=False)
    cadence_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_then_negotiate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    volume_split_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    routing_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    sourcing_region_per_period: Mapped[str | None] = mapped_column(Text, nullable=True)


class CycleScopeItem(CycBase):
    """Item-level participation (D9 `participates`). Mirrors cyc.cycle_scope_item (0002)."""

    __tablename__ = "cycle_scope_item"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    subcommodity_code: Mapped[str] = mapped_column(Text, primary_key=True)
    gtin_code: Mapped[str] = mapped_column(Text, primary_key=True, default="")
    participates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # lot_id is unconstrained until persistent norm.lot lands (M2/G8).
    lot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    projected_volume: Mapped[Decimal | None] = mapped_column(Numeric(18, 3), nullable=True)


class CyclePbaTerm(CycBase):
    """PBA governance term. Mirrors cyc.cycle_pba_term (0002)."""

    __tablename__ = "cycle_pba_term"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    metric: Mapped[str] = mapped_column(Text, primary_key=True)
    threshold: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement: Mapped[str | None] = mapped_column(Text, nullable=True)


class CycleCommercialTerm(CycBase):
    """Working-capital / KPM / other term. Mirrors cyc.cycle_commercial_term (0002)."""

    __tablename__ = "cycle_commercial_term"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    term_type: Mapped[str] = mapped_column(Text, primary_key=True)
    target_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    treatment: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class CycleRfiQuestion(CycBase):
    """Configurable RFI question (stable code). Mirrors cyc.cycle_rfi_question (0002)."""

    __tablename__ = "cycle_rfi_question"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    question_code: Mapped[str] = mapped_column(Text, primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)


class CycleTimelineEvent(CycBase):
    """A "Next Steps" rail event (E-16). Mirrors cyc.cycle_timeline_event (0002)."""

    __tablename__ = "cycle_timeline_event"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    event_seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_leadership_gate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    round_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bcg_support_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CycleNarrative(CycBase):
    """Versioned rich-text narrative block. Mirrors cyc.cycle_narrative (0002)."""

    __tablename__ = "cycle_narrative"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    narrative_type: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    body_richtext: Mapped[str] = mapped_column(Text, nullable=False)
    authored_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    authored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CycleSafety(CycBase):
    """A per-RFP pricing-safety CONTRACT term (D13/ADR-0014). Mirrors cyc.cycle_safety (0003).

    Terms only — the engine does not consume these. One row per applied safety type per cycle.
    """

    __tablename__ = "cycle_safety"

    cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cyc.cycle.cycle_id"), primary_key=True
    )
    safety_type: Mapped[str] = mapped_column(Text, primary_key=True)
    # COLLAR
    cap: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    floor: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    # ROLLING_MIDPOINT
    lookback_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reset_cadence_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # TOLERANCE_BAND
    band: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    min_duration_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reprice_window_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # DISASTER / INVERSE_DISASTER
    reverts_to_contract: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
