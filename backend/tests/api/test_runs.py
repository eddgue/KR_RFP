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


@pytest.mark.integration
def test_run_resolves_from_db_with_no_folder(  # type: ignore[no-untyped-def]
    client, seed_user, vault_root, db_session
) -> None:
    """A run existing ONLY as a pilot.run row (no vault folder) still lists + reads back (Slice 3).

    Run identity is DB-resolved: the console surfaces a run from its `pilot.run` row even when no
    `runs/<slug>/` folder exists (the stateless target). This inserts a row directly (the vault dir
    is the empty temp `vault_root`), then asserts the list + detail resolve it from the DB.
    """

    from app.pilot.run_repo import create_run_record

    _login(client, seed_user)

    slug = "ghost-tomato-20260621-deadbe"
    create_run_record(
        db_session, slug=slug, commodity="Ghost Tomatoes", label="Folderless", rehearsal=False
    )

    # It lists from the DB even though no vault folder was ever created.
    listed = client.get(RUNS)
    assert listed.status_code == 200
    summary = next((r for r in listed.json() if r["slug"] == slug), None)
    assert summary is not None, listed.json()
    assert summary["commodity"] == "Ghost Tomatoes"
    assert summary["label"] == "Folderless"
    assert summary["has_cycle"] is False

    # And reads back by slug from the DB row (no folder on disk).
    one = client.get(f"{RUNS}/{slug}")
    assert one.status_code == 200
    body = one.json()
    assert body["slug"] == slug
    assert body["commodity"] == "Ghost Tomatoes"
    assert set(body["kanban"]) == {"Done", "Doing", "Next", "Waiting on you"}


@pytest.mark.integration
def test_created_run_scaffolds_no_vault_folder(  # type: ignore[no-untyped-def]
    client, seed_user, vault_root, db_session
) -> None:
    """A console-created run scaffolds NO vault folder — its identity is the pilot.run row (Sl. 6).

    create_run mints a slug + writes only the DB-backed identity (no `runs/<slug>/` folder, no
    RUN.md/NOTES.md/cycle_id.txt/.rehearsal/git). The run still lists + reads back from the DB.
    """

    _login(client, seed_user)
    created = client.post(
        RUNS, json={"commodity": "Field Tomatoes", "label": "No Folder", "rehearsal": False}
    )
    assert created.status_code == 201
    slug = created.json()["slug"]

    # No vault folder was created — the console persists nothing server-side.
    assert not (vault_root / "runs" / slug).exists()

    # The run still lists + reads back, resolved entirely from the pilot.run row.
    assert slug in {r["slug"] for r in client.get(RUNS).json()}
    one = client.get(f"{RUNS}/{slug}")
    assert one.status_code == 200
    assert one.json()["slug"] == slug
