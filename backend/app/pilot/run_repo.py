"""Repository for `pilot.run` — the DB-backed run identity (ADR-0018 Slice 2).

Thin, session-taking CRUD over the `Run` ORM row, mirroring the codebase's repo style (the caller's
unit of work owns the transaction). The console's `PilotService` dual-writes through these alongside
the vault files in Slice 2 (so the row exists for every run before Slice 3 flips the reads onto it);
the MCP harness never calls them. `cycle_id` is set separately (`set_run_cycle`) on setup ingest, so
a run row is created the moment the run starts and gains its cycle link once the cycle exists.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.pilot.models import Run


def create_run_record(
    session: Session, *, slug: str, commodity: str, label: str, rehearsal: bool
) -> Run:
    """Insert the `pilot.run` row for a new run (no cycle yet) and return it."""

    run = Run(
        slug=slug,
        commodity=commodity,
        label=label,
        rehearsal=rehearsal,
        cycle_id=None,
    )
    session.add(run)
    session.flush()
    return run


def get_run(session: Session, slug: str) -> Run | None:
    """The `pilot.run` row for a slug, or None if there is no such run."""

    return session.get(Run, slug)


def list_run_records(session: Session) -> list[Run]:
    """Every `pilot.run` row, ordered by slug (so runs sort by commodity then date)."""

    return list(session.execute(select(Run).order_by(Run.slug)).scalars().all())


def set_run_cycle(session: Session, slug: str, cycle_id: str) -> None:
    """Link a run to its governed cycle (set on setup ingest); raises if the run is unknown."""

    run = session.get(Run, slug)
    if run is None:
        raise ValueError(f"no pilot.run row for slug {slug!r}")
    run.cycle_id = cycle_id
    session.flush()


def delete_run_record(session: Session, slug: str) -> None:
    """Remove a run's `pilot.run` row (close-out). Idempotent: a missing row is a no-op."""

    run = session.get(Run, slug)
    if run is not None:
        session.delete(run)
        session.flush()
