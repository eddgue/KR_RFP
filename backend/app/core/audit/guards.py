"""Immutability guard listeners (PLAN §4.4, security/PLAN §6).

App-layer half of the double-enforced immutability control: SQLAlchemy `before_update` /
`before_delete` mapper listeners that refuse to mutate or delete sealed `eng.analysis_run`
outputs and frozen `awd.award` rows. `award_layer` is the only post-freeze write path; no
governed table grants DELETE. The DB-layer half (triggers + revoked grants) is owned by
Platform & Data; two layers is a control, one is a convention.

The mapped classes they attach to are wired when present: `eng.analysis_run` (modelled in 0008)
and `awd.award` (modelled in 0010). `register_immutability_guards()` is called by the app factory;
it imports each lazily and guards on Import/AttributeError so the seam stays wired even before a
model lands.
"""

from __future__ import annotations

from typing import Any

from app.core.errors.taxonomy import AppError, ErrorCode

# Attribute that, when truthy on an instance, marks the row as governed-immutable.
SEALED_FLAG = "is_sealed"
FROZEN_FLAG = "frozen_at"


def _is_sealed(target: Any) -> bool:
    return bool(getattr(target, SEALED_FLAG, False))


def _is_frozen(target: Any) -> bool:
    return getattr(target, FROZEN_FLAG, None) is not None


def block_update_if_sealed(mapper: Any, connection: Any, target: Any) -> None:
    """`before_update` listener: refuse to mutate a sealed run's outputs."""

    if _is_sealed(target):
        raise AppError(
            code=ErrorCode.IMMUTABLE,
            message="Sealed analysis-run outputs are immutable; a correction is a new run.",
            status_code=409,
        )


def block_delete_governed(mapper: Any, connection: Any, target: Any) -> None:
    """`before_delete` listener: governed rows are never hard-deleted."""

    if _is_sealed(target) or _is_frozen(target):
        raise AppError(
            code=ErrorCode.IMMUTABLE,
            message="Governed rows cannot be deleted; corrections insert superseding rows.",
            status_code=409,
        )


def block_update_if_frozen(mapper: Any, connection: Any, target: Any) -> None:
    """`before_update` listener: refuse to mutate a frozen award (use award_layer instead)."""

    if _is_frozen(target):
        raise AppError(
            code=ErrorCode.IMMUTABLE,
            message="Frozen awards are immutable; post-freeze changes go to award_layer only.",
            status_code=409,
        )


def register_immutability_guards() -> None:
    """Attach guard listeners to the governed mapped classes.

    Imports `eng.analysis_run` and `awd.award` lazily and guards on Import/AttributeError, so the
    seam stays wired whether or not a given model has landed yet. Both are modelled now (0008/0010),
    so the listeners attach: sealed runs + frozen awards refuse update/delete.
    """

    from sqlalchemy import event

    try:
        from app.domain.eng.models import AnalysisRun

        event.listen(AnalysisRun, "before_update", block_update_if_sealed)
        event.listen(AnalysisRun, "before_delete", block_delete_governed)
    except (ImportError, AttributeError):
        pass

    try:
        from app.domain.awd.models import Award

        event.listen(Award, "before_update", block_update_if_frozen)
        event.listen(Award, "before_delete", block_delete_governed)
    except (ImportError, AttributeError):
        pass
