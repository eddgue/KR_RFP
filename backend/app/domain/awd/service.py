"""The post-award service — freeze an award + record append-only VERSIONED adjustment layers.

This is the service seam between the sealed engine recommendations (`eng.analysis_scenario_award`)
and the FROZEN award baseline + its versioned price layers (`awd.*`). It implements the
freeze-and-layer discipline (ADR-0014): a human selects an engine scenario, the recommendation is
PROMOTED to a frozen award (the immutable baseline), and every post-award price move is an
append-only, date-stamped, VERSIONED layer on top — the raw award is NEVER overwritten; a move
supersedes via a new row, never an UPDATE/hard-delete of the baseline (ADR-0006).

The cell grain throughout is (dc_id, lot_id, tf_id, supplier_id).

Unit-of-work discipline (PLAN §7): every method add+flushes and NEVER commits; the caller's
unit_of_work owns the transaction so a freeze (or a layer) lands atomically.

CLEAN-ROOM (ADR-0001): no import from `reference/`; reads only the governed store ORM.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.audit.events import DomainEvent, EventType
from app.core.audit.recorder import client_id_for_award, client_id_for_cycle
from app.core.audit.writer import AuditWriter
from app.domain.awd.models import (
    Award,
    AwardAdjustment,
    AwardAdjustmentLine,
    AwardLine,
)
from app.domain.eng.models import AnalysisScenario, AnalysisScenarioAward
from app.engine.formulas import price_delta

# The keyed cell grain a price applies to: (dc_id, lot_id, tf_id, supplier_id).
CellKey = tuple[str, str, str, str]


class VersionRow(TypedDict):
    """One row of an award's version history (v0 baseline -> vN layers)."""

    version_no: int
    adjustment_type: str
    effective_date: date
    reason: str
    created_at: datetime
    created_by: str
    n_lines: int


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    """Naive UTC for the `timestamp` columns (matches the eng runner's clock handling)."""

    return datetime.now(UTC).replace(tzinfo=None)


def freeze_award(
    session: Session,
    *,
    cycle_id: str,
    analysis_run_id: str,
    scenario_code: str,
    award_code: str,
    frozen_by: str,
) -> str:
    """Promote a selected engine scenario to a FROZEN award (the immutable baseline).

    Reads the selected scenario's split awards from `eng.analysis_scenario_award` (joined to
    `eng.analysis_scenario` on scenario_code + analysis_run_id) and writes `awd.award` + one
    `awd.award_line` per cell with `frozen_price = awarded_price` (ADR-0014: this baseline is never
    overwritten). Idempotent: if an award already exists for that (cycle, run, scenario), the
    existing `award_id` is returned and nothing new is written. Add + flush only.

    Raises `ValueError` if the scenario has NO award rows (an unknown / typo `scenario_code`, or a
    code not sealed on this run): the read happens BEFORE anything is written, so a bad code can
    never leave a bogus zero-line FROZEN award or a spurious FROZEN audit event behind.
    """

    existing = session.execute(
        select(Award.award_id).where(
            Award.cycle_id == cycle_id,
            Award.analysis_run_id == analysis_run_id,
            Award.scenario_code == scenario_code,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    # The selected scenario's split award rows (per-supplier cell grain) -> the frozen baseline.
    # Read FIRST and refuse an empty set, so nothing is written for an unknown/unsealed scenario.
    rows = session.execute(
        select(
            AnalysisScenarioAward.dc_id,
            AnalysisScenarioAward.lot_id,
            AnalysisScenarioAward.tf_id,
            AnalysisScenarioAward.supplier_id,
            AnalysisScenarioAward.volume_share,
            AnalysisScenarioAward.awarded_price,
        )
        .join(
            AnalysisScenario,
            AnalysisScenario.analysis_scenario_id == AnalysisScenarioAward.analysis_scenario_id,
        )
        .where(
            AnalysisScenario.analysis_run_id == analysis_run_id,
            AnalysisScenario.scenario_code == scenario_code,
        )
    ).all()
    if not rows:
        raise ValueError(
            f"scenario {scenario_code!r} has no awards on run {analysis_run_id!r} — "
            "nothing to freeze (unknown or unsealed scenario code)."
        )

    award_id = _new_id()
    session.add(
        Award(
            award_id=award_id,
            cycle_id=cycle_id,
            analysis_run_id=analysis_run_id,
            scenario_code=scenario_code,
            award_code=award_code,
            frozen_at=_now(),
            frozen_by=frozen_by,
            status="FROZEN",
        )
    )
    session.flush()

    for dc_id, lot_id, tf_id, supplier_id, volume_share, awarded_price in rows:
        session.add(
            AwardLine(
                award_line_id=_new_id(),
                award_id=award_id,
                dc_id=dc_id,
                lot_id=lot_id,
                tf_id=tf_id,
                supplier_id=supplier_id,
                volume_share=volume_share,
                frozen_price=awarded_price,
            )
        )
    session.flush()

    # Governed decision: the award is frozen. Land its tamper-evident event in the same
    # transaction as the freeze (Gap G-B) — identifiers + counts only, no commercial values.
    AuditWriter(session).append(
        DomainEvent(
            event_type=EventType.FROZEN,
            client_id=client_id_for_cycle(session, cycle_id),
            entity_type="awd.award",
            entity_id=uuid.UUID(award_id),
            cycle_id=uuid.UUID(cycle_id),
            actor=frozen_by,
            source="api",
            after={
                "scenario_code": scenario_code,
                "analysis_run_id": analysis_run_id,
                "n_lines": len(rows),
            },
        )
    )
    return award_id


def add_adjustment(
    session: Session,
    *,
    award_id: str,
    adjustment_type: str,
    effective_date: date,
    reason: str,
    created_by: str,
    line_changes: list[tuple[str, str, str, str, Decimal]],
) -> int:
    """Record an append-only VERSIONED adjustment layer; return its `version_no`.

    `version_no` = max(existing) + 1 (the first layer is 1). For each (dc, lot, tf, supplier,
    new_price) change, `prior_price` is the cell's CURRENT effective price BEFORE this layer
    (baseline overlaid by every earlier layer) and `delta = new_price - prior_price`. Append-only:
    the frozen baseline is never touched (ADR-0014). Add + flush only.
    """

    next_version = (
        session.execute(
            select(func.coalesce(func.max(AwardAdjustment.version_no), 0)).where(
                AwardAdjustment.award_id == award_id
            )
        ).scalar_one()
    ) + 1

    # Prior price per cell = the effective price at the latest existing version (baseline overlaid
    # by all earlier layers). Computed BEFORE this layer is written.
    prior_by_cell = effective_award(session, award_id=award_id)

    adjustment_id = _new_id()
    session.add(
        AwardAdjustment(
            adjustment_id=adjustment_id,
            award_id=award_id,
            version_no=next_version,
            adjustment_type=adjustment_type,
            effective_date=effective_date,
            reason=reason,
            created_at=_now(),
            created_by=created_by,
            status="RECORDED",
        )
    )
    session.flush()

    for dc_id, lot_id, tf_id, supplier_id, new_price in line_changes:
        prior = prior_by_cell.get((dc_id, lot_id, tf_id, supplier_id), Decimal("0"))
        session.add(
            AwardAdjustmentLine(
                adj_line_id=_new_id(),
                adjustment_id=adjustment_id,
                dc_id=dc_id,
                lot_id=lot_id,
                tf_id=tf_id,
                supplier_id=supplier_id,
                prior_price=prior,
                new_price=new_price,
                delta=price_delta(new_price, prior),
            )
        )
    session.flush()

    # Governed decision: a post-award adjustment layer was applied. Land its tamper-evident event
    # in the same transaction (Gap G-B) — identifiers + counts only, no prices. The event's cycle
    # is the award's cycle.
    cycle_id = session.execute(
        text("SELECT cycle_id FROM awd.award WHERE award_id = :aid"),
        {"aid": award_id},
    ).scalar_one()
    AuditWriter(session).append(
        DomainEvent(
            event_type=EventType.CREATED,
            client_id=client_id_for_award(session, award_id),
            entity_type="awd.award_adjustment",
            entity_id=uuid.UUID(adjustment_id),
            cycle_id=uuid.UUID(cycle_id),
            actor=created_by,
            source="api",
            after={
                "version_no": next_version,
                "adjustment_type": adjustment_type,
                "n_lines": len(line_changes),
            },
        )
    )
    return next_version


def effective_award(
    session: Session,
    *,
    award_id: str,
    as_of_version: int | None = None,
) -> dict[CellKey, Decimal]:
    """The effective price per cell: the frozen baseline overlaid by each layer up to a version.

    Starts from `awd.award_line.frozen_price` (v0) and applies every `awd.award_adjustment_line`
    `new_price` in `version_no` order up to `as_of_version` (or the latest layer when None). Later
    layers win; the raw baseline is never mutated (ADR-0014).
    """

    effective: dict[CellKey, Decimal] = {}
    base_rows = session.execute(
        select(
            AwardLine.dc_id,
            AwardLine.lot_id,
            AwardLine.tf_id,
            AwardLine.supplier_id,
            AwardLine.frozen_price,
        ).where(AwardLine.award_id == award_id)
    ).all()
    for dc_id, lot_id, tf_id, supplier_id, frozen_price in base_rows:
        effective[(dc_id, lot_id, tf_id, supplier_id)] = frozen_price

    stmt = (
        select(
            AwardAdjustment.version_no,
            AwardAdjustmentLine.dc_id,
            AwardAdjustmentLine.lot_id,
            AwardAdjustmentLine.tf_id,
            AwardAdjustmentLine.supplier_id,
            AwardAdjustmentLine.new_price,
        )
        .join(
            AwardAdjustmentLine,
            AwardAdjustmentLine.adjustment_id == AwardAdjustment.adjustment_id,
        )
        .where(AwardAdjustment.award_id == award_id)
        .order_by(AwardAdjustment.version_no)
    )
    if as_of_version is not None:
        stmt = stmt.where(AwardAdjustment.version_no <= as_of_version)

    for _v, dc_id, lot_id, tf_id, supplier_id, new_price in session.execute(stmt).all():
        effective[(dc_id, lot_id, tf_id, supplier_id)] = new_price
    return effective


def award_versions(session: Session, *, award_id: str) -> list[VersionRow]:
    """The version history v0 (frozen baseline) -> vN, each with its metadata + # cells changed.

    v0 is the freeze itself (type FROZEN, the award's frozen_at/frozen_by, n_lines = baseline
    cells).
    v1..vN are the append-only layers in `version_no` order, each carrying its type, effective date,
    reason, who/when, and the count of cells it changed.
    """

    award = session.execute(select(Award).where(Award.award_id == award_id)).scalar_one_or_none()
    if award is None:
        return []

    baseline_cells = session.execute(
        select(func.count()).select_from(AwardLine).where(AwardLine.award_id == award_id)
    ).scalar_one()

    history: list[VersionRow] = [
        VersionRow(
            version_no=0,
            adjustment_type="FROZEN",
            effective_date=award.frozen_at.date(),
            reason=f"Frozen baseline (scenario {award.scenario_code})",
            created_at=award.frozen_at,
            created_by=award.frozen_by,
            n_lines=baseline_cells,
        )
    ]

    rows = session.execute(
        select(
            AwardAdjustment.version_no,
            AwardAdjustment.adjustment_type,
            AwardAdjustment.effective_date,
            AwardAdjustment.reason,
            AwardAdjustment.created_at,
            AwardAdjustment.created_by,
            func.count(AwardAdjustmentLine.adj_line_id),
        )
        .outerjoin(
            AwardAdjustmentLine,
            AwardAdjustmentLine.adjustment_id == AwardAdjustment.adjustment_id,
        )
        .where(AwardAdjustment.award_id == award_id)
        .group_by(
            AwardAdjustment.version_no,
            AwardAdjustment.adjustment_type,
            AwardAdjustment.effective_date,
            AwardAdjustment.reason,
            AwardAdjustment.created_at,
            AwardAdjustment.created_by,
        )
        .order_by(AwardAdjustment.version_no)
    ).all()

    for version_no, adj_type, eff_date, reason, created_at, created_by, n_lines in rows:
        history.append(
            VersionRow(
                version_no=version_no,
                adjustment_type=adj_type,
                effective_date=eff_date,
                reason=reason,
                created_at=created_at,
                created_by=created_by,
                n_lines=n_lines,
            )
        )
    return history
