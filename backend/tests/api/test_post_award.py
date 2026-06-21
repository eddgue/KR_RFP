"""Post-award API: read a frozen award + record append-only adjustment layers (HTTP surface).

Integration (real Postgres + a temp vault): the award routes hang off the runs router and wrap
`PilotService` with `isolate_db=False`, sharing the rolled-back test session. Reuses the alignment
test's HTTP seed helpers (create → setup → template → import → analysis), freezes lens B, then
exercises the award read endpoints and the governed adjustment-write endpoint (scope, cell
validation, the layered effective price, and the CREATED audit event).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from tests.api.test_alignment import _create_run, _login, _seed_sealed_run

RUNS = "/api/v1/runs"

_VALID_CHANGE = {
    "dc_id": "a",
    "lot_id": "b",
    "tf_id": "c",
    "supplier_id": "d",
    "new_price": 1.0,
}


def _freeze_b(client, slug, analysis_run_id, code="AWD-PA-1"):  # type: ignore[no-untyped-def]
    resp = client.post(
        f"{RUNS}/{slug}/awards/freeze",
        json={"analysis_run_id": analysis_run_id, "scenario_code": "B", "award_code": code},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["award_id"]


@pytest.mark.integration
def test_award_routes_require_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Every award route with no session is a 401 (valid body, so the only failure is auth)."""

    assert client.get(f"{RUNS}/x/awards").status_code == 401
    assert client.get(f"{RUNS}/x/awards/a-1").status_code == 401
    assert (
        client.post(
            f"{RUNS}/x/awards/a-1/adjustments",
            json={
                "adjustment_type": "MARKET_HIKE",
                "effective_date": "2026-04-01",
                "reason": "r",
                "changes": [_VALID_CHANGE],
            },
        ).status_code
        == 401
    )


@pytest.mark.integration
def test_award_read_and_adjustment_e2e(client, seed_user, vault_root, db_session) -> None:  # type: ignore[no-untyped-def]
    """freeze B → list/read award → record a +$5 layer → re-read shows the delta + v1 + event."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)

    # No award yet — the list is empty, never a gate.
    assert client.get(f"{RUNS}/{slug}/awards").json() == []

    award_id = _freeze_b(client, slug, analysis_run_id)

    # list_awards → one frozen award, baseline only.
    awards = client.get(f"{RUNS}/{slug}/awards").json()
    assert len(awards) == 1
    assert awards[0]["award_id"] == award_id
    assert awards[0]["latest_version"] == 0
    assert awards[0]["line_count"] > 0

    # award detail → baseline lines carry both the cell-key ids and the names; v0 FROZEN only.
    detail = client.get(f"{RUNS}/{slug}/awards/{award_id}").json()
    assert detail["lines"]
    line = detail["lines"][0]
    for key in ("dc_id", "lot_id", "tf_id", "supplier_id", "dc", "supplier"):
        assert line[key]
    assert all(line_["delta"] == 0 for line_ in detail["lines"])
    assert [v["version_no"] for v in detail["versions"]] == [0]

    # Record a +$5 adjustment on the first cell.
    new_price = round(line["frozen_price"] + 5.0, 2)
    rec = client.post(
        f"{RUNS}/{slug}/awards/{award_id}/adjustments",
        json={
            "adjustment_type": "MARKET_HIKE",
            "effective_date": "2026-04-01",
            "reason": "trailing-4wk reset",
            "changes": [
                {
                    "dc_id": line["dc_id"],
                    "lot_id": line["lot_id"],
                    "tf_id": line["tf_id"],
                    "supplier_id": line["supplier_id"],
                    "new_price": new_price,
                }
            ],
        },
    )
    assert rec.status_code == 200, rec.text
    rb = rec.json()
    assert rb["version_no"] == 1
    assert rb["filename"].endswith(".xlsx")

    # Re-read: the cell's effective price + delta moved; history now v0 + v1.
    detail2 = client.get(f"{RUNS}/{slug}/awards/{award_id}").json()
    adjusted = [line_ for line_ in detail2["lines"] if line_["delta"] != 0]
    assert len(adjusted) == 1
    assert adjusted[0]["effective_price"] == pytest.approx(new_price)
    assert [v["version_no"] for v in detail2["versions"]] == [0, 1]
    assert detail2["latest_version"] == 1

    # A CREATED audit event landed for the layer (governed decision, in-txn).
    events = db_session.execute(
        text(
            "SELECT count(*) FROM audit.event_log "
            "WHERE event_type = 'CREATED' AND entity_type = 'awd.award_adjustment'"
        ),
    ).scalar_one()
    assert events == 1


@pytest.mark.integration
def test_adjustment_unknown_cell_is_validation_error(  # type: ignore[no-untyped-def]
    client, seed_user, vault_root, db_session
) -> None:
    """A change referencing a cell that isn't on the award is a clean 400 — and writes NO layer."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_id = _freeze_b(client, slug, analysis_run_id, code="AWD-PA-2")

    resp = client.post(
        f"{RUNS}/{slug}/awards/{award_id}/adjustments",
        json={
            "adjustment_type": "MARKET_HIKE",
            "effective_date": "2026-04-01",
            "reason": "off-award cell",
            "changes": [_VALID_CHANGE],  # ids that aren't on the award
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"

    n = db_session.execute(
        text("SELECT count(*) FROM awd.award_adjustment WHERE award_id = :aid"),
        {"aid": award_id},
    ).scalar_one()
    assert n == 0


@pytest.mark.integration
def test_adjustment_unknown_award_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A real run + cycle but an unknown award id is a 404 (scoped to the run's cycle)."""

    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)  # a cycle exists, but no such award
    resp = client.post(
        f"{RUNS}/{slug}/awards/no-such-award/adjustments",
        json={
            "adjustment_type": "MARKET_HIKE",
            "effective_date": "2026-04-01",
            "reason": "r",
            "changes": [_VALID_CHANGE],
        },
    )
    assert resp.status_code == 404


@pytest.mark.integration
def test_adjustment_empty_changes_rejected(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """An adjustment with no changes is rejected by request validation (422)."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_id = _freeze_b(client, slug, analysis_run_id, code="AWD-PA-3")
    resp = client.post(
        f"{RUNS}/{slug}/awards/{award_id}/adjustments",
        json={
            "adjustment_type": "MARKET_HIKE",
            "effective_date": "2026-04-01",
            "reason": "r",
            "changes": [],
        },
    )
    assert resp.status_code == 422
