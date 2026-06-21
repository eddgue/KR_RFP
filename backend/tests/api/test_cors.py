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


def test_actual_response_exposes_content_disposition() -> None:
    """An actual cross-origin response exposes Content-Disposition so the console reads filenames.

    Run-file + zip downloads send the saved name on Content-Disposition; a browser only surfaces it
    cross-origin when it is in Access-Control-Expose-Headers. An unauthenticated GET still flows
    through CORSMiddleware, so its 401 carries the expose-headers for the allowed origin.
    """

    client = TestClient(create_app())
    resp = client.get("/api/v1/auth/me", headers={"Origin": _ALLOWED_ORIGIN})

    assert resp.headers["access-control-allow-origin"] == _ALLOWED_ORIGIN
    assert "content-disposition" in resp.headers.get("access-control-expose-headers", "").lower()


def test_unexpected_500_carries_cors_for_allowed_origin() -> None:
    """An unhandled 500 still gets CORS headers so the console reads the error, not a CORS failure.

    The catch-all Exception handler runs in ServerErrorMiddleware, outside CORSMiddleware, so this
    guards the explicit header-echo in the 500 handler. A throwaway route raises so the catch-all
    fires; `raise_server_exceptions=False` makes TestClient return the 500 instead of re-raising.
    """

    app = create_app()

    @app.get("/api/v1/_boom")
    def _boom() -> None:
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v1/_boom", headers={"Origin": _ALLOWED_ORIGIN})

    assert resp.status_code == 500
    assert resp.headers["access-control-allow-origin"] == _ALLOWED_ORIGIN
    assert resp.headers["access-control-allow-credentials"] == "true"
