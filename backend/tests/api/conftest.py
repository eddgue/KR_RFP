"""Fixtures for the API tests: a TestClient wired to a rolled-back DB session + a temp vault.

The integration fixtures reuse the root `db_session` (a transaction rolled back per test), so the
console's routes write to the same isolated session and nothing leaks between tests. `get_db` is
overridden to yield that session; the runs router's vault root is redirected to a temp dir.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.auth.models import AppUser
from app.auth.security import hash_password
from app.main import app


@pytest.fixture
def vault_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the runs router at a per-test temp vault (the lru_cached resolver is replaced)."""

    root = tmp_path / "vault"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.api.v1.runs._vault_root", lambda: root)
    return root


@pytest.fixture
def client(db_session) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    """A TestClient whose `get_db` yields the rolled-back test session (shared across the request).

    The transaction is owned by the `db_session` fixture (rolled back after the test); the override
    must NOT commit/close it, so it just yields the same session for every request in the test.
    """

    def _override_get_db() -> Iterator:  # type: ignore[type-arg]
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        # https base_url so the Secure session cookie is sent back on follow-up requests (httpx
        # withholds Secure cookies over http) — mirrors how the cookie behaves behind TLS in prod.
        with TestClient(app, base_url="https://testserver") as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def seed_user(db_session):  # type: ignore[no-untyped-def]
    """Insert an active console user (no 2FA); returns its username/password and the row."""

    user = AppUser(
        username="admin",
        password_hash=hash_password("s3cret-pw"),
        is_active=True,
        totp_enabled=False,
    )
    db_session.add(user)
    db_session.flush()
    return {"username": "admin", "password": "s3cret-pw", "user": user}
