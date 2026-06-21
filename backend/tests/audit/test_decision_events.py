"""Gap G-B — decision-point audit events land on the decision's own transaction.

Drives the REAL pilot loop (the same path + synthetic builders as
`tests/pilot/test_pilot_cycle_e2e.py`) and asserts that every governed decision appended a
hash-chained `audit.event_log` row in the SAME transaction as the decision:

  * Coverage — a full run emits IMPORTED, SEALED, FROZEN and a CREATED (adjustment) event with the
    right entity_types.
  * Chain integrity — the tenant's events have contiguous seq 1..N, each `prev_event_hash` chains
    to the prior `event_hash`, and recomputing with `compute_event_hash` reproduces every stored
    hash (tamper-evidence).
  * SUPERSEDED — a re-ingest of the same supplier's bids emits SUPERSEDED for the prior submission.
  * Atomicity — an event appended then rolled back leaves zero rows (it shares the decision's UoW).

Synthetic only (clean-room, ADR-0001). DB-touching tests are marked integration (skip when no DB).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.audit.events import DomainEvent, EventType
from app.core.audit.recorder import client_id_for_cycle
from app.core.audit.writer import AuditWriter, compute_event_hash
from app.pilot.service import PilotService
from app.pilot.vault import stage_filename
from tests.pilot.test_pilot_cycle_e2e import (
    _build_filled_setup,
    _fill_bid_template,
    _first_award_cell,
    _latest_run_id,
)


def _events_for_client(db_session, client_id: uuid.UUID) -> list[dict[str, object]]:  # type: ignore[no-untyped-def]
    """Every audit.event_log row for a tenant, in chain (seq) order, as plain dicts."""

    rows = db_session.execute(
        text(
            "SELECT seq, event_type, entity_type, entity_id, actor, occurred_at, "
            "before_state_hash, after_state_hash, prev_event_hash, event_hash "
            "FROM audit.event_log WHERE client_id = :cid ORDER BY seq"
        ),
        {"cid": str(client_id)},
    ).all()
    return [
        {
            "seq": r[0],
            "event_type": r[1],
            "entity_type": r[2],
            "entity_id": r[3],
            "actor": r[4],
            "occurred_at": r[5],
            "before_state_hash": r[6],
            "after_state_hash": r[7],
            "prev_event_hash": r[8],
            "event_hash": r[9],
        }
        for r in rows
    ]


def _drive_full_run(service: PilotService, db_session, tmp_path: Path) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """Run the whole synthetic loop (setup→bids→run→freeze→adjust); return (cycle_id, award_id)."""

    paths = service.start_run(commodity="Field Tomatoes", label="Audit G-B")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)

    template_path = service.generate_bid_template(db_session, paths, 1)
    template_path.write_bytes(_fill_bid_template(template_path.read_bytes()))
    service.ingest_bids(db_session, paths, 1, template_path)

    service.run_round(db_session, paths, 1)

    analysis_run_id = _latest_run_id(db_session, cycle_id)
    award_id = service.freeze_award(
        db_session,
        paths,
        analysis_run_id=analysis_run_id,
        scenario_code="B",
        award_code="AWD-AUDIT-1",
    )

    dc_id, lot_id, tf_id, sup_id, frozen_price = _first_award_cell(db_session, award_id)
    service.record_adjustment(
        db_session,
        paths,
        award_id=award_id,
        adjustment_type="NEGOTIATED_REPRICE",
        effective_date=date(2026, 7, 1),
        reason="Synthetic audit reprice",
        line_changes=[(dc_id, lot_id, tf_id, sup_id, frozen_price - Decimal("0.25"))],
    )
    return cycle_id, award_id


@pytest.mark.integration
def test_full_run_emits_decision_events(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """A full run lands IMPORTED, SEALED, FROZEN and a CREATED (adjustment) event for the tenant."""

    service = PilotService(tmp_path, isolate_db=False)
    cycle_id, _award_id = _drive_full_run(service, db_session, tmp_path)
    client_id = client_id_for_cycle(db_session, cycle_id)

    events = _events_for_client(db_session, client_id)
    by_type: dict[str, list[dict[str, object]]] = {}
    for ev in events:
        by_type.setdefault(str(ev["event_type"]), []).append(ev)

    # The four governed decisions of a run are recorded.
    assert by_type.get(EventType.IMPORTED.value), "ingest must emit IMPORTED"
    assert by_type.get(EventType.SEALED.value), "run_round must emit SEALED"
    assert by_type.get(EventType.FROZEN.value), "freeze must emit FROZEN"
    assert by_type.get(EventType.CREATED.value), "adjustment must emit CREATED"

    # Each carries the right entity_type.
    assert all(e["entity_type"] == "bid.bid_submission" for e in by_type[EventType.IMPORTED.value])
    assert by_type[EventType.SEALED.value][0]["entity_type"] == "eng.analysis_run"
    assert by_type[EventType.FROZEN.value][0]["entity_type"] == "awd.award"
    assert by_type[EventType.CREATED.value][0]["entity_type"] == "awd.award_adjustment"

    # Two suppliers ingested in the round → two IMPORTED events.
    assert len(by_type[EventType.IMPORTED.value]) == 2


@pytest.mark.integration
def test_chain_is_contiguous_and_tamper_evident(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """The tenant's chain has seq 1..N, links prev→event, and recomputes to the stored hashes."""

    service = PilotService(tmp_path, isolate_db=False)
    cycle_id, _award_id = _drive_full_run(service, db_session, tmp_path)
    client_id = client_id_for_cycle(db_session, cycle_id)

    events = _events_for_client(db_session, client_id)
    assert len(events) >= 4

    # Contiguous seq starting at 1.
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))

    genesis = "0" * 64
    prev = genesis
    for ev in events:
        # Each row chains to the previous row's event_hash (genesis for the first).
        assert ev["prev_event_hash"] == prev

        # Recomputing the link from the stored fields reproduces the stored event_hash. The DB
        # returns occurred_at tz-aware (UTC); the writer hashed the naive value, so strip tz to
        # recover the exact input (the test session runs in UTC).
        occurred = ev["occurred_at"].replace(tzinfo=None)  # type: ignore[union-attr]
        recomputed = compute_event_hash(
            prev_event_hash=str(ev["prev_event_hash"]),
            client_id=client_id,
            seq=int(ev["seq"]),  # type: ignore[arg-type]
            event_type=str(ev["event_type"]),
            entity_type=str(ev["entity_type"]),
            entity_id=uuid.UUID(str(ev["entity_id"])),
            actor=str(ev["actor"]),
            occurred_at=occurred,
            before_state_hash=ev["before_state_hash"],  # type: ignore[arg-type]
            after_state_hash=ev["after_state_hash"],  # type: ignore[arg-type]
        )
        assert recomputed == ev["event_hash"], f"chain broken at seq {ev['seq']}"
        prev = str(ev["event_hash"])


@pytest.mark.integration
def test_resubmission_emits_superseded(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """Re-ingesting a supplier's bids in a round emits SUPERSEDED for the prior submission."""

    service = PilotService(tmp_path, isolate_db=False)
    paths = service.start_run(commodity="Field Tomatoes", label="Audit Supersede")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)

    template_path = service.generate_bid_template(db_session, paths, 1)
    template_path.write_bytes(_fill_bid_template(template_path.read_bytes()))

    # First ingest → IMPORTED for each supplier's submission.
    service.ingest_bids(db_session, paths, 1, template_path)
    first_submissions = {
        sid
        for (sid,) in db_session.execute(
            text("SELECT submission_id FROM bid.bid_submission WHERE cycle_id = :c"),
            {"c": cycle_id},
        ).all()
    }

    # Second ingest of the same file → the prior submissions are superseded.
    service.ingest_bids(db_session, paths, 1, template_path)

    client_id = client_id_for_cycle(db_session, cycle_id)
    superseded = [
        e
        for e in _events_for_client(db_session, client_id)
        if e["event_type"] == EventType.SUPERSEDED.value
    ]
    assert superseded, "a re-ingest must emit SUPERSEDED for the prior submission(s)"
    # The SUPERSEDED events point at the FIRST round's submissions, not the new ones.
    superseded_ids = {str(e["entity_id"]) for e in superseded}
    assert superseded_ids <= first_submissions
    assert all(e["entity_type"] == "bid.bid_submission" for e in superseded)


@pytest.mark.integration
def test_actor_threads_to_audit_events(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """The caller's `actor` is recorded on the IMPORTED + SEALED events (HTTP passes the user).

    The web console threads the authenticated `user.username` into ingest_bids / run_round; the
    audit chain must then record that real identity, not the hardcoded "pilot" / "pilot-runner"
    fallback the MCP harness uses.
    """

    service = PilotService(tmp_path, isolate_db=False)
    paths = service.start_run(commodity="Field Tomatoes", label="Audit Actor")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)

    template_path = service.generate_bid_template(db_session, paths, 1)
    template_path.write_bytes(_fill_bid_template(template_path.read_bytes()))
    service.ingest_bids(db_session, paths, 1, template_path, actor="alice@buyer.example")
    service.run_round(db_session, paths, 1, actor="alice@buyer.example")

    client_id = client_id_for_cycle(db_session, cycle_id)
    by_type: dict[str, list[dict[str, object]]] = {}
    for ev in _events_for_client(db_session, client_id):
        by_type.setdefault(str(ev["event_type"]), []).append(ev)

    assert all(e["actor"] == "alice@buyer.example" for e in by_type[EventType.IMPORTED.value])
    assert by_type[EventType.SEALED.value][0]["actor"] == "alice@buyer.example"

    # The importing user is also stamped on the bid's source artifact (created_by).
    created_by = {
        cb
        for (cb,) in db_session.execute(
            text("SELECT created_by FROM norm.source_artifact WHERE cycle_id = :c"),
            {"c": cycle_id},
        ).all()
    }
    assert created_by == {"alice@buyer.example"}


@pytest.mark.integration
def test_event_rides_caller_transaction_rollback(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """An appended event is dropped when the caller's unit of work rolls back (shared txn).

    Append onto a SAVEPOINT, prove the row is visible, then roll the savepoint back and prove zero
    rows persist — the event never committed on its own, it rides the decision's transaction.
    """

    service = PilotService(tmp_path, isolate_db=False)
    paths = service.start_run(commodity="Field Tomatoes", label="Audit Atomic")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)
    client_id = client_id_for_cycle(db_session, cycle_id)

    before = len(_events_for_client(db_session, client_id))

    savepoint = db_session.begin_nested()
    AuditWriter(db_session).append(
        DomainEvent(
            event_type=EventType.IMPORTED,
            client_id=client_id,
            entity_type="bid.bid_submission",
            entity_id=uuid.uuid4(),
            cycle_id=uuid.UUID(cycle_id),
            actor="pilot",
            source="import",
            after={"round_id": "r-test", "supplier_id": "s-test"},
        )
    )
    db_session.flush()
    assert len(_events_for_client(db_session, client_id)) == before + 1, "appended, not yet rolled"

    savepoint.rollback()
    assert len(_events_for_client(db_session, client_id)) == before, "rollback drops the event"
