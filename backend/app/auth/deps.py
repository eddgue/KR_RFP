"""Auth dependency: `get_current_user` — read+validate the session cookie, load the user.

The console session lives in the httpOnly `kr_session` cookie (a signed JWT). This dependency
decodes it, loads the referenced `auth.app_user`, and denies (401) when the cookie is missing,
the token is invalid/expired, or the user is gone/inactive. The runs API depends on it so every
runs route is authenticated.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.models import AppUser
from app.auth.security import SESSION_COOKIE_NAME, decode_session_token
from app.core.errors.taxonomy import AppError, ErrorCode


def _unauthenticated(detail: str = "Not authenticated.") -> AppError:
    return AppError(code=ErrorCode.UNAUTHENTICATED, message=detail, status_code=401)


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AppUser:
    """Return the active `AppUser` for the request's session cookie, or raise 401.

    Reads the `kr_session` cookie, validates the JWT, and loads the active user it names. Any
    failure (no cookie, bad/expired token, unknown or inactive user) is a uniform 401.
    """

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise _unauthenticated()

    claims = decode_session_token(token)
    if claims is None:
        raise _unauthenticated("Session is invalid or expired.")

    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise _unauthenticated("Session is invalid or expired.")
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise _unauthenticated("Session is invalid or expired.") from None

    user = db.execute(select(AppUser).where(AppUser.id == user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise _unauthenticated("Session is invalid or expired.")
    return user


CurrentUser = Annotated[AppUser, Depends(get_current_user)]
