"""Auth API: login success, wrong password (401), and the 2FA-required path.

Integration (real Postgres): the user row is seeded into the rolled-back test session and the
TestClient shares it via the `get_db` override. The pure unit test at the bottom needs no DB.
"""

from __future__ import annotations

import pyotp
import pytest

from app.api.v1.auth import TWO_FACTOR_REQUIRED_DETAIL
from app.auth.security import SESSION_COOKIE_NAME, hash_password, verify_password

PREFIX = "/api/v1/auth"


# ---------------------------------------------------------------------------
# PURE — password hashing round-trips, wrong password fails
# ---------------------------------------------------------------------------
def test_password_hash_roundtrip() -> None:
    """argon2 hash verifies for the right password and rejects the wrong one."""

    h = hash_password("correct-horse")
    assert verify_password("correct-horse", h)
    assert not verify_password("wrong", h)
    assert not verify_password("anything", "not-a-real-hash")


# ---------------------------------------------------------------------------
# INTEGRATION — login flows
# ---------------------------------------------------------------------------
@pytest.mark.integration
def test_login_success_sets_cookie(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    """A correct username+password returns 200, the user view, and a session cookie."""

    resp = client.post(
        f"{PREFIX}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "admin"
    assert body["user"]["totp_enabled"] is False
    assert "id" in body["user"]
    assert SESSION_COOKIE_NAME in resp.cookies

    # The cookie is a working session: /me returns the same user.
    me = client.get(f"{PREFIX}/me")
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


@pytest.mark.integration
def test_login_wrong_password_401(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    """A wrong password is a 401 and sets no session cookie."""

    resp = client.post(
        f"{PREFIX}/login",
        json={"username": seed_user["username"], "password": "nope"},
    )
    assert resp.status_code == 401
    assert SESSION_COOKIE_NAME not in resp.cookies
    # The detail must NOT be the 2FA prompt (this is a credential failure).
    assert resp.json()["detail"] != TWO_FACTOR_REQUIRED_DETAIL


@pytest.mark.integration
def test_login_unknown_user_401(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    """An unknown username is the same opaque 401 (no user enumeration)."""

    resp = client.post(
        f"{PREFIX}/login",
        json={"username": "ghost", "password": "whatever"},
    )
    assert resp.status_code == 401


@pytest.mark.integration
def test_login_2fa_required_path(client, seed_user, db_session) -> None:  # type: ignore[no-untyped-def]
    """When 2FA is enabled: password alone gives the distinct '2FA code required' 401; the right
    code then logs in."""

    secret = pyotp.random_base32()
    user = seed_user["user"]
    user.totp_secret = secret
    user.totp_enabled = True
    db_session.flush()

    # Password correct but no code -> 401 with the distinct, UI-detectable detail.
    resp = client.post(
        f"{PREFIX}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == TWO_FACTOR_REQUIRED_DETAIL
    assert SESSION_COOKIE_NAME not in resp.cookies

    # A wrong code -> still the 2FA-required 401.
    bad = client.post(
        f"{PREFIX}/login",
        json={
            "username": seed_user["username"],
            "password": seed_user["password"],
            "totp_code": "000000",
        },
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == TWO_FACTOR_REQUIRED_DETAIL

    # The valid current code -> 200 + session cookie.
    code = pyotp.TOTP(secret).now()
    ok = client.post(
        f"{PREFIX}/login",
        json={
            "username": seed_user["username"],
            "password": seed_user["password"],
            "totp_code": code,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["user"]["totp_enabled"] is True
    assert SESSION_COOKIE_NAME in ok.cookies


@pytest.mark.integration
def test_me_requires_session_401(client) -> None:  # type: ignore[no-untyped-def]
    """/me with no session cookie is a 401."""

    resp = client.get(f"{PREFIX}/me")
    assert resp.status_code == 401


@pytest.mark.integration
def test_logout_clears_cookie(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    """Logout returns 204 and clears the session so /me then 401s."""

    client.post(
        f"{PREFIX}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    out = client.post(f"{PREFIX}/logout")
    assert out.status_code == 204
    # The cookie jar drops it; a follow-up /me is unauthenticated.
    assert client.get(f"{PREFIX}/me").status_code == 401


@pytest.mark.integration
def test_2fa_enroll_then_verify(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    """Enroll returns an otpauth URI + secret; verifying a real code enables 2FA."""

    client.post(
        f"{PREFIX}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    enroll = client.post(f"{PREFIX}/2fa/enroll")
    assert enroll.status_code == 200
    secret = enroll.json()["secret"]
    assert enroll.json()["otpauth_uri"].startswith("otpauth://totp/")
    assert "KR%20RFP" in enroll.json()["otpauth_uri"] or "KR RFP" in enroll.json()["otpauth_uri"]

    verify = client.post(f"{PREFIX}/2fa/verify", json={"code": pyotp.TOTP(secret).now()})
    assert verify.status_code == 200
    assert verify.json()["totp_enabled"] is True
