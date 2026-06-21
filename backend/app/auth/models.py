"""SQLAlchemy mapped class for the `auth` schema — the web-console user.

`auth.app_user` is the credential record behind the console login: a unique username, an argon2
password hash, and the TOTP-2FA enrolment state (a secret + an `enabled` flag). It lives in its
own `auth` schema (created by the auth migration), separate from the eight domain layers — the
governed data spine never depends on who is logged into the console.

The PK mirrors the `ref` spine convention (a server-generatable UUID with a stable `pk_app_user`
name from the shared naming convention), so it round-trips like the other governed tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.core.db.types import created_at_column, uuid_pk


class AppUser(Base):
    """A web-console user (login credential + TOTP-2FA state). Mirrors `auth.app_user`."""

    __tablename__ = "app_user"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = uuid_pk()
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    # The TOTP shared secret (base32). Null until the user enrols; set on /2fa/enroll and only
    # honoured for login once `totp_enabled` flips true on /2fa/verify.
    totp_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = created_at_column()
