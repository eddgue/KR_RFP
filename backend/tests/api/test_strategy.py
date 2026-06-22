"""Strategy panel API — read + set the run's engine strategy (the minimal A1 slice).

Integration (real Postgres + a temp vault): the `/strategy` routes wrap `PilotService` and persist
the named weight preset + the four engine safeties onto `cyc.cycle` — the SAME fields the setup
workbook seeds and that `run_round` already layers over the default config. So a set here is what
the next analysis runs under (no new store, no engine change). Reuses the alignment helpers to
drive the run to a cycle through the HTTP surface.
"""

from __future__ import annotations

import pytest

from app.engine.interface import PRESET_WEIGHTS, WeightPreset
from tests.api.test_alignment import _create_run, _login
from tests.pilot.test_pilot_cycle_e2e import _build_filled_setup

RUNS = "/api/v1/runs"
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_FULL = {
    "weight_preset": "balanced",
    "premium_ceiling": "0.12",
    "coverage_floor": "0.80",
    "conc_thresh": "0.40",
    "max_sup_dc": 2,
}


def _ingest_setup(client, slug: str) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        f"{RUNS}/{slug}/setup", files={"file": ("setup.xlsx", _build_filled_setup(), _XLSX)}
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.integration
def test_strategy_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """No session → 401 on both read and write."""

    assert client.get(f"{RUNS}/x/strategy").status_code == 401
    assert client.put(f"{RUNS}/x/strategy", json=_FULL).status_code == 401


@pytest.mark.integration
def test_strategy_gate_before_cycle(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A run with no cycle yet → 400 gate_required (setup must be ingested first)."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.get(f"{RUNS}/{slug}/strategy")
    assert resp.status_code == 400
    assert resp.json()["code"] == "gate_required"


@pytest.mark.integration
def test_strategy_get_then_set_roundtrips(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """GET the effective strategy, PUT a new one, and a fresh GET reflects it (persisted)."""

    _login(client, seed_user)
    slug = _create_run(client)
    _ingest_setup(client, slug)

    got = client.get(f"{RUNS}/{slug}/strategy")
    assert got.status_code == 200, got.text
    s = got.json()
    assert {
        "weight_preset",
        "weight_price",
        "premium_ceiling",
        "coverage_floor",
        "conc_thresh",
        "max_sup_dc",
    } <= set(s)
    assert s["max_sup_dc"] >= 1
    for k in ("premium_ceiling", "coverage_floor", "conc_thresh"):
        assert 0 < float(s[k]) <= 1

    # Set price_focus + new safeties; the response echoes the resolved config.
    payload = {
        "weight_preset": "price_focus",
        "premium_ceiling": "0.10",
        "coverage_floor": "0.75",
        "conc_thresh": "0.50",
        "max_sup_dc": 3,
    }
    put = client.put(f"{RUNS}/{slug}/strategy", json=payload)
    assert put.status_code == 200, put.text
    out = put.json()
    expected = PRESET_WEIGHTS[WeightPreset("price_focus")]
    assert out["weight_preset"] == "price_focus"
    assert float(out["weight_price"]) == pytest.approx(float(expected["weight_price"]))
    assert float(out["coverage_floor"]) == pytest.approx(0.75)
    assert out["max_sup_dc"] == 3

    # Persisted: a fresh GET (new request) returns the same values.
    again = client.get(f"{RUNS}/{slug}/strategy").json()
    assert again["weight_preset"] == "price_focus"
    assert float(again["premium_ceiling"]) == pytest.approx(0.10)
    assert again["max_sup_dc"] == 3


@pytest.mark.integration
def test_strategy_rejects_bad_input(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Unknown preset → 400 validation_error; an out-of-range safety → 422 (schema bound)."""

    _login(client, seed_user)
    slug = _create_run(client)
    _ingest_setup(client, slug)

    bad_preset = client.put(f"{RUNS}/{slug}/strategy", json={**_FULL, "weight_preset": "bogus"})
    assert bad_preset.status_code == 400
    assert bad_preset.json()["code"] == "validation_error"

    bad_range = client.put(f"{RUNS}/{slug}/strategy", json={**_FULL, "coverage_floor": "1.5"})
    assert bad_range.status_code == 422
