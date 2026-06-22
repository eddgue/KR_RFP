"""Version savepoint API — name a sealed alignment version (E-43, decoupled from freeze).

Integration (real Postgres + a temp vault): naming sets `eng.analysis_run.label` via
`PATCH /runs/{slug}/analysis/{id}`. It is a lightweight SAVEPOINT, **not** a governed decision — it
writes no audit event and creates no award; FREEZE stays the only governed seal. Reuses the
alignment helpers to seal a run through the HTTP surface.
"""

from __future__ import annotations

import pytest

from tests.api.test_alignment import _create_run, _login, _seed_sealed_run

RUNS = "/api/v1/runs"


@pytest.mark.integration
def test_name_version_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    assert client.patch(f"{RUNS}/x/analysis/y", json={"label": "v1"}).status_code == 401


@pytest.mark.integration
def test_name_version_sets_label_without_freezing(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)

    # Name the version — a savepoint, not a freeze.
    resp = client.patch(
        f"{RUNS}/{slug}/analysis/{analysis_run_id}", json={"label": "Balanced baseline"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["analysis_run_id"] == analysis_run_id
    assert body["label"] == "Balanced baseline"
    assert body["version"] == 1

    # The list reflects the name on that version.
    listed = client.get(f"{RUNS}/{slug}/analysis").json()
    named = next(a for a in listed if a["analysis_run_id"] == analysis_run_id)
    assert named["label"] == "Balanced baseline"

    # Naming did NOT freeze: no award exists (freeze stays the only governed seal).
    assert client.get(f"{RUNS}/{slug}/awards").json() == []


@pytest.mark.integration
def test_name_version_unknown_run_is_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)
    resp = client.patch(f"{RUNS}/{slug}/analysis/not-a-real-run", json={"label": "x"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


@pytest.mark.integration
def test_name_version_rejects_empty(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    rid = _seed_sealed_run(client, slug)
    # Pydantic min_length=1: "" -> 422.
    assert client.patch(f"{RUNS}/{slug}/analysis/{rid}", json={"label": ""}).status_code == 422
    # Whitespace-only passes the length bound but the service strips it -> 400 validation_error.
    ws = client.patch(f"{RUNS}/{slug}/analysis/{rid}", json={"label": "   "})
    assert ws.status_code == 400
    assert ws.json()["code"] == "validation_error"
