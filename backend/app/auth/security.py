"""Auth primitives: argon2 password hashing, session JWT, TOTP helpers.

Pure functions over the credential material — no FastAPI, no DB. The routers and the seed-admin
CLI call these. Secrets/TTL come from settings; the cookie name is fixed here so issuer and reader
agree. Passlib verifies in constant time (argon2); pyjwt signs/validates the session token.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pyotp
from passlib.context import CryptContext

from app.core.config.settings import get_settings

# The httpOnly session cookie the login issues and `get_current_user` reads.
SESSION_COOKIE_NAME = "kr_session"
# Issuer label shown in authenticator apps (TOTP provisioning URI).
TOTP_ISSUER = "KR RFP"
_JWT_ALG = "HS256"

# argon2 only — the modern memory-hard default; verify() is constant-time.
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# --------------------------------------------------------------------------- #
# password hashing
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    """Return an argon2 hash of `password` (for storage in `auth.app_user.password_hash`)."""

    return str(_pwd_context.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time check of `password` against a stored argon2 hash (False on any mismatch)."""

    try:
        return bool(_pwd_context.verify(password, password_hash))
    except (ValueError, TypeError):
        # A malformed/empty stored hash must read as "does not verify", never raise.
        return False


# --------------------------------------------------------------------------- #
# session JWT (carried in the kr_session cookie)
# --------------------------------------------------------------------------- #
def create_session_token(user_id: str, *, username: str) -> str:
    """Sign a session JWT for `user_id`; `exp` is now + the configured TTL."""

    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.auth_token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=_JWT_ALG)


def decode_session_token(token: str) -> dict[str, Any] | None:
    """Validate + decode a session JWT; return its claims, or None if invalid/expired."""

    settings = get_settings()
    try:
        claims: dict[str, Any] = jwt.decode(token, settings.auth_secret_key, algorithms=[_JWT_ALG])
    except jwt.PyJWTError:
        return None
    return claims


def session_cookie_max_age_seconds() -> int:
    """The cookie Max-Age that matches the JWT TTL (so cookie and token expire together)."""

    return get_settings().auth_token_ttl_minutes * 60


# --------------------------------------------------------------------------- #
# TOTP (2FA)
# --------------------------------------------------------------------------- #
def generate_totp_secret() -> str:
    """A fresh base32 TOTP secret to store (not yet enabled) on enrolment."""

    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, *, username: str) -> str:
    """The otpauth:// URI an authenticator app scans (issuer 'KR RFP')."""

    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=TOTP_ISSUER)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP `code` against `secret` (valid_window=1 for clock skew)."""

    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)
