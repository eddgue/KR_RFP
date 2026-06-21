"""Runs API: auth gate (401 without a session) + create-then-list against a temp vault.

Integration (real Postgres + a temp vault dir): the runs router wraps PilotService with
`isolate_db=False`, so it shares the rolled-back test session and provisions no per-run DB. The
`vault_root` fixture redirects the router's vault to a temp dir; `client` shares the test session.
"""

from __future__ import annotations

import pytest

AUTH = "/api/v1/auth"
RUNS = "/api/v1/runs"


def _login(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        f"{AUTH}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    assert resp.status_code == 200


@pytest.mark.integration
def test_runs_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """GET /runs with no session is a 401 (every runs route is authenticated)."""

    resp = client.get(RUNS)
    assert resp.status_code == 401


@pytest.mark.integration
def test_runs_list_empty_when_authed(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A signed-in user with an empty vault gets an empty list (200)."""

    _login(client, seed_user)
    resp = client.get(RUNS)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.integration
def test_create_run_then_appears_in_list(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """POST /runs is 201 with a RunDetail; the run then lists and reads back by slug."""

    _login(client, seed_user)

    created = client.post(
        f"{RUNS}",
        json={"commodity": "Field Tomatoes", "label": "Console E2E", "rehearsal": False},
    )
    assert created.status_code == 201
    detail = created.json()
    slug = detail["slug"]
    assert detail["commodity"] == "Field Tomatoes"
    assert detail["label"] == "Console E2E"
    assert detail["rehearsal"] is False
    assert detail["stage"]  # a non-empty human stage label
    # The full kanban board is present with all four buckets.
    assert set(detail["kanban"]) == {"Done", "Doing", "Next", "Waiting on you"}
    assert "Run folder created" in detail["kanban"]["Done"]

    # It appears in the list as a RunSummary.
    listed = client.get(RUNS)
    assert listed.status_code == 200
    slugs = [r["slug"] for r in listed.json()]
    assert slug in slugs
    summary = next(r for r in listed.json() if r["slug"] == slug)
    assert summary["commodity"] == "Field Tomatoes"
    assert summary["label"] == "Console E2E"

    # And reads back by slug.
    one = client.get(f"{RUNS}/{slug}")
    assert one.status_code == 200
    assert one.json()["slug"] == slug
    assert "kanban" in one.json()


@pytest.mark.integration
def test_create_rehearsal_run_marks_synthetic(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A rehearsal run is flagged rehearsal=True in both the create detail and the list."""

    _login(client, seed_user)
    created = client.post(
        f"{RUNS}",
        json={"commodity": "Test Greens", "label": "Practice", "rehearsal": True},
    )
    assert created.status_code == 201
    assert created.json()["rehearsal"] is True

    summary = next(r for r in client.get(RUNS).json() if r["slug"] == created.json()["slug"])
    assert summary["rehearsal"] is True


@pytest.mark.integration
def test_get_unknown_run_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """An unknown slug is a 404 (not a 500 / empty detail)."""

    _login(client, seed_user)
    resp = client.get(f"{RUNS}/does-not-exist-20260101-abcdef")
    assert resp.status_code == 404
