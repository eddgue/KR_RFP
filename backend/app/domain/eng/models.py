"""Mapped classes for the `eng` schema — the engine runner's sealed output spine.

Target tables (ENG-PLAN §3, migration 0008): the runner's decision-support output rows —
`analysis_run` (sealed run: hashed input/output manifest + engine version pin + is_sealed),
`bid_score` (the five banded factors -> rec_score), `analysis_scenario` (the A-G lens headers),
`analysis_scenario_award` (the SPLIT award rows with volume_share / is_fallback / cap_breach_flag).

The runner (`runner.py`) seals the run, freezes the inputs, hashes the canonical input/output
manifests, records the engine version pin, and calls the pure engine library; the outputs are
append-only and immutable once sealed (ADR-0006). Decision-support only: an award row RECOMMENDS a
split; it never asserts the award (the real award lands in `awd.*` after a human selects a lens).

COLUMN ALIGNMENT: mirrors migration 0008 verbatim so the ORM round-trips against the migration
(the same lockstep rule the `ref`/`bid` models follow).

The heavyweight governed solver spine (`eng.calculation_run` / `eng.scenario` / `eng.scenario_award`
from the M0 baseline) is managed by SQL and is NOT mapped here; the runner writes the lightweight
sealed decision-support spine these classes map.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base, SchemaBase

if TYPE_CHECKING:
    # SchemaBase builds the per-schema base dynamically at runtime; alias to the static
    # declarative `Base` so mapped classes have a valid base for the type checker.
    EngBase = Base
else:
    EngBase = SchemaBase("eng")

_Money = Numeric(18, 6)
_Score = Numeric(9, 4)
_Share = Numeric(9, 6)


class AnalysisRun(EngBase):
    """A sealed decision-support run — hashed manifests + engine version pin + is_sealed."""

    __tablename__ = "analysis_run"

    analysis_run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cycle_id: Mapped[str] = mapped_column(String(36), nullable=False)
    round_id: Mapped[str] = mapped_column(String(36), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(60), nullable=False)
    config_preset: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    is_sealed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    input_hash_manifest: Mapped[str] = mapped_column(String(128), nullable=False)
    output_hash_manifest: Mapped[str] = mapped_column(String(128), nullable=False)
    run_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    run_finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    run_by: Mapped[str] = mapped_column(String(120), nullable=False)


class BidScore(EngBase):
    """The five banded factors -> rec_score for one scored bid line (per run)."""

    __tablename__ = "bid_score"

    bid_score_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    bid_line_id: Mapped[str] = mapped_column(String(36), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dc_id: Mapped[str] = mapped_column(String(36), nullable=False)
    lot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tf_id: Mapped[str] = mapped_column(String(36), nullable=False)
    price_score: Mapped[Decimal] = mapped_column(_Score, nullable=False)
    coverage_score: Mapped[Decimal] = mapped_column(_Score, nullable=False)
    hist_score: Mapped[Decimal] = mapped_column(_Score, nullable=False)
    zrisk_score: Mapped[Decimal] = mapped_column(_Score, nullable=False)
    continuity_score: Mapped[Decimal] = mapped_column(_Score, nullable=False)
    rec_score: Mapped[Decimal] = mapped_column(_Score, nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    gate_flags: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalysisScenario(EngBase):
    """An A-G lens header (decision-support label, never an assertion)."""

    __tablename__ = "analysis_scenario"

    analysis_scenario_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    scenario_code: Mapped[str] = mapped_column(String(4), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective_total_spend: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)


class AnalysisScenarioAward(EngBase):
    """One SPLIT award row: a supplier's share of a (scenario, dc, lot, tf) cell (G1/D10)."""

    __tablename__ = "analysis_scenario_award"

    award_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_scenario_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dc_id: Mapped[str] = mapped_column(String(36), nullable=False)
    lot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tf_id: Mapped[str] = mapped_column(String(36), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    volume_share: Mapped[Decimal] = mapped_column(_Share, nullable=False)
    awarded_price: Mapped[Decimal] = mapped_column(_Money, nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cap_breach_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
