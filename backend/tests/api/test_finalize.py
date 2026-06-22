"""Finalize / close-out API: the run's terminal governed close-out (the design's "Finalize &
close run" step).

Integration (real Postgres + a temp vault): the finalize route hangs off the runs router and wraps
`PilotService` with `isolate_db=False`, sharing the rolled-back test session. Reuses the alignment
test's HTTP seed helpers (create → setup → template → import → analysis) + the post-award freeze
helper.

Covers: auth (401); finalize-after-freeze locks the run CLOSED, emits exactly one `CLOSED` audit
event (entity = the cycle), and surfaces the won/not-won notice counts; finalize-without-a-frozen
award is refused (409); re-finalize is idempotent (the same summary, no second CLOSED event); a
finalize of an unknown run is a 404.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from tests.api.test_alignment import _create_run, _login, _seed_sealed_run
from tests.api.test_post_award import _freeze_b

RUNS = "/api/v1/runs"


def _closed_event_count(db_session, cycle_id: str) -> int:  # type: ignore[no-untyped-def]
    return db_session.execute(
        text(
            "SELECT count(*) FROM audit.event_log "
            "WHERE event_type = 'CLOSED' AND entity_type = 'cyc.cycle' AND cycle_id = :cyc"
        ),
        {"cyc": cycle_id},
    ).scalar_one()


@pytest.mark.integration
def test_finalize_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Finalize with no session is a 401 (the governed close-out is authenticated)."""

    assert client.post(f"{RUNS}/x/finalize").status_code == 401


@pytest.mark.integration
def test_finalize_unknown_run_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Finalizing a run that doesn't exist is a clean 404 (DB-resolved identity)."""

    _login(client, seed_user)
    resp = client.post(f"{RUNS}/no-such-run/finalize")
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


@pytest.mark.integration
def test_finalize_without_frozen_award_is_conflict(  # type: ignore[no-untyped-def]
    client, seed_user, vault_root, db_session
) -> None:
    """A sealed-analysis run with NO frozen award can't be closed out — 409, no CLOSED event."""

    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)  # sealed analysis exists, but nothing frozen

    resp = client.post(f"{RUNS}/{slug}/finalize")
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "conflict"

    # The cycle id off the run row — assert NO CLOSED event was written.
    cycle_id = db_session.execute(
        text("SELECT cycle_id FROM pilot.run WHERE slug = :slug"), {"slug": slug}
    ).scalar_one()
    assert _closed_event_count(db_session, cycle_id) == 0


@pytest.mark.integration
def test_finalize_before_setup_is_conflict(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A run with no cycle yet (setup not ingested) has no frozen award — 409, not a 500."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.post(f"{RUNS}/{slug}/finalize")
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "conflict"


@pytest.mark.integration
def test_finalize_after_freeze_closes_and_surfaces_notices(  # type: ignore[no-untyped-def]
    client, seed_user, vault_root, db_session
) -> None:
    """freeze B → finalize → run CLOSED, exactly one CLOSED event, and the notices available."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_id = _freeze_b(client, slug, analysis_run_id, code="AWD-FIN-1")

    cycle_id = db_session.execute(
        text("SELECT cycle_id FROM pilot.run WHERE slug = :slug"), {"slug": slug}
    ).scalar_one()
    assert _closed_event_count(db_session, cycle_id) == 0  # not closed before finalize

    resp = client.post(f"{RUNS}/{slug}/finalize")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["closed"] is True
    assert body["award_id"] == award_id
    # Some suppliers won (the award notices) and some lost (the rejection notices) — both available.
    assert body["won_suppliers"] >= 1
    assert body["not_won_suppliers"] >= 1

    # The finalize summary counts EQUAL the notices the console actually renders on request.
    won_drafts = client.get(f"{RUNS}/{slug}/awards/{award_id}/comms/award").json()
    rej_drafts = client.get(f"{RUNS}/{slug}/awards/{award_id}/comms/rejection").json()
    assert body["won_suppliers"] == len(won_drafts)
    assert body["not_won_suppliers"] == len(rej_drafts)

    # Exactly one CLOSED audit event landed for the cycle (governed decision, in-txn), by the actor.
    assert _closed_event_count(db_session, cycle_id) == 1
    actor = db_session.execute(
        text("SELECT actor FROM audit.event_log WHERE event_type = 'CLOSED' AND cycle_id = :cyc"),
        {"cyc": cycle_id},
    ).scalar_one()
    assert actor == seed_user["username"]


@pytest.mark.integration
def test_finalize_is_idempotent(client, seed_user, vault_root, db_session) -> None:  # type: ignore[no-untyped-def]
    """Re-finalizing a closed run returns the same summary and emits NO second CLOSED event."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_id = _freeze_b(client, slug, analysis_run_id, code="AWD-FIN-2")

    cycle_id = db_session.execute(
        text("SELECT cycle_id FROM pilot.run WHERE slug = :slug"), {"slug": slug}
    ).scalar_one()

    first = client.post(f"{RUNS}/{slug}/finalize")
    assert first.status_code == 200, first.text
    assert _closed_event_count(db_session, cycle_id) == 1

    second = client.post(f"{RUNS}/{slug}/finalize")
    assert second.status_code == 200, second.text
    # Same summary on the re-finalize (clean no-op).
    assert second.json() == first.json()
    assert second.json()["award_id"] == award_id
    # Still exactly one CLOSED event — no second emission, the chain isn't forked.
    assert _closed_event_count(db_session, cycle_id) == 1
