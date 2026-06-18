"""Smoke test: the app boots and /health is green (SKELETON tests).

`/health` (liveness) needs no DB. `/ready` (readiness) touches the store, so it is integration.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config.settings import get_settings
from app.main import app

client = TestClient(app)
PREFIX = get_settings().api_v1_prefix


def test_health_is_green() -> None:
    """Liveness: the app boots and /health returns ok (no DB required)."""

    resp = client.get(f"{PREFIX}/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.integration
def test_ready_checks_the_store() -> None:
    """Readiness: /ready returns ready when the store is reachable."""

    resp = client.get(f"{PREFIX}/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}
