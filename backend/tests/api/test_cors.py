"""CORS preflight contract for the browser console.

The Next console is a separate origin and calls the API with credentials (the session cookie), so
the API must answer a CORS preflight for an allowed origin and reflect that exact origin with
credentials enabled — and must NOT hand the allow-origin header to an origin that isn't configured.
These are pure middleware checks: the preflight is short-circuited by CORSMiddleware before any
route/DB is touched, so the app is built straight from `create_app()` with no fixtures.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config.settings import get_settings
from app.main import create_app

_ALLOWED_ORIGIN = "http://localhost:3000"
_PREFLIGHT_HEADERS = {
    "Origin": _ALLOWED_ORIGIN,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


def test_preflight_allows_configured_origin_with_credentials() -> None:
    """An allowed origin's preflight gets that exact origin echoed + credentials enabled."""

    # The default settings list http://localhost:3000; assert the test's origin is actually in it so
    # this stays meaningful if the default ever changes.
    assert _ALLOWED_ORIGIN in get_settings().cors_allow_origins

    client = TestClient(create_app())
    resp = client.options("/api/v1/auth/login", headers=_PREFLIGHT_HEADERS)

    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == _ALLOWED_ORIGIN
    assert resp.headers["access-control-allow-credentials"] == "true"


def test_preflight_does_not_allow_unknown_origin() -> None:
    """An origin that isn't configured gets no allow-origin header (browser blocks the call)."""

    client = TestClient(create_app())
    resp = client.options(
        "/api/v1/auth/login",
        headers={**_PREFLIGHT_HEADERS, "Origin": "https://evil.example.com"},
    )

    assert "access-control-allow-origin" not in resp.headers
