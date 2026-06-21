"""Auth surface (`/api/v1/auth`): login, logout, me, and TOTP-2FA enrol/verify.

Username/password sign-in with optional TOTP second factor. On success the session JWT is set in
an httpOnly, secure, SameSite=Lax cookie (`kr_session`); `/me` reads it; `/logout` clears it. The
2FA endpoints (authed) enrol a secret then flip it on once a code verifies. Domain logic is the
auth primitives in `app/auth/security.py`; this layer only does request/response + cookie I/O.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.deps import CurrentUser
from app.auth.models import AppUser
from app.auth.security import (
    SESSION_COOKIE_NAME,
    create_session_token,
    generate_totp_secret,
    session_cookie_max_age_seconds,
    totp_provisioning_uri,
    verify_password,
    verify_totp,
)
from app.core.config.settings import get_settings
from app.core.errors.taxonomy import AppError, ErrorCode

router = APIRouter()

# A distinct detail string so the UI can tell "needs a 2FA code" apart from "bad credentials" and
# prompt for the code instead of failing the whole login.
TWO_FACTOR_REQUIRED_DETAIL = "2FA code required"


# --------------------------------------------------------------------------- #
# request / response models
# --------------------------------------------------------------------------- #
class LoginRequest(BaseModel):
    """Credentials for `POST /login`; `totp_code` is supplied only when 2FA is enabled."""

    username: str
    password: str
    totp_code: str | None = None


class UserView(BaseModel):
    """The user identity returned to the console (never the hash or the TOTP secret)."""

    id: str
    username: str
    totp_enabled: bool


class LoginResponse(BaseModel):
    user: UserView


class EnrollResponse(BaseModel):
    """The TOTP enrolment material the UI renders as a QR code + manual-entry secret."""

    otpauth_uri: str
    secret: str


class VerifyRequest(BaseModel):
    code: str = Field(description="The 6-digit TOTP code from the authenticator app.")


class VerifyResponse(BaseModel):
    totp_enabled: bool


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _user_view(user: AppUser) -> UserView:
    return UserView(id=str(user.id), username=user.username, totp_enabled=user.totp_enabled)


def _set_session_cookie(response: Response, user: AppUser) -> None:
    token = create_session_token(str(user.id), username=user.username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=session_cookie_max_age_seconds(),
        httponly=True,
        secure=get_settings().auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def _unauthorized(detail: str) -> AppError:
    return AppError(code=ErrorCode.UNAUTHENTICATED, message=detail, status_code=401)


# --------------------------------------------------------------------------- #
# endpoints
# --------------------------------------------------------------------------- #
@router.post("/login", response_model=LoginResponse, summary="Sign in (password + optional 2FA)")
def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    """Verify credentials (+ TOTP when enabled), set the session cookie, return the user.

    A wrong username, an inactive user, or a wrong password are one indistinguishable 401 (no user
    enumeration). When 2FA is enabled the password must be correct AND a valid `totp_code` given —
    a missing/invalid code returns 401 with the distinct `2FA code required` detail so the UI can
    prompt for the second factor rather than treat it as a failed sign-in.
    """

    user = db.execute(select(AppUser).where(AppUser.username == body.username)).scalar_one_or_none()

    # Same opaque 401 whether the user is missing, inactive, or the password is wrong.
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise _unauthorized("Invalid username or password.")

    if user.totp_enabled:
        if not body.totp_code:
            raise _unauthorized(TWO_FACTOR_REQUIRED_DETAIL)
        if not verify_totp(user.totp_secret or "", body.totp_code):
            raise _unauthorized(TWO_FACTOR_REQUIRED_DETAIL)

    _set_session_cookie(response, user)
    return LoginResponse(user=_user_view(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sign out")
def logout(response: Response) -> Response:
    """Clear the session cookie (idempotent — safe to call without a session)."""

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserView, summary="The current session's user")
def me(user: CurrentUser) -> UserView:
    """Return the signed-in user, or 401 if there is no valid session."""

    return _user_view(user)


@router.post("/2fa/enroll", response_model=EnrollResponse, summary="Begin TOTP enrolment")
def enroll_2fa(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollResponse:
    """Generate + store a TOTP secret (not yet enabled); return the otpauth URI + secret.

    Enrolment is two-step: this stores a fresh secret and hands back the provisioning material;
    2FA only takes effect once `/2fa/verify` confirms the user can produce a valid code.
    """

    secret = generate_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    db.flush()
    return EnrollResponse(
        otpauth_uri=totp_provisioning_uri(secret, username=user.username),
        secret=secret,
    )


@router.post("/2fa/verify", response_model=VerifyResponse, summary="Confirm + enable TOTP")
def verify_2fa(
    body: VerifyRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> VerifyResponse:
    """Verify a code against the enrolled secret and flip `totp_enabled` on.

    400 if the user never enrolled (no secret); 401 if the code is wrong. On success 2FA is
    required for every subsequent login.
    """

    if not user.totp_secret:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="No TOTP enrolment in progress — call /2fa/enroll first.",
            status_code=400,
        )
    if not verify_totp(user.totp_secret, body.code):
        raise _unauthorized("Invalid 2FA code.")

    user.totp_enabled = True
    db.flush()
    return VerifyResponse(totp_enabled=True)
