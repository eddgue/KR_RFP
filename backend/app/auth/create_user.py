"""Seed/upsert a web-console user — `python -m app.auth.create_user <username> <password>`.

Tiny operational entrypoint: create the user (or reset its password if it already exists) with an
argon2 hash, active and without 2FA. Use it to bootstrap the first admin so someone can log in;
the user enrols TOTP later through the API. Runs inside the standard unit of work.
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.auth.models import AppUser
from app.auth.security import hash_password
from app.core.db.session import unit_of_work


def upsert_user(username: str, password: str) -> str:
    """Create `username` (or reset its password) and return its id as a string."""

    with unit_of_work() as session:
        user = session.execute(
            select(AppUser).where(AppUser.username == username)
        ).scalar_one_or_none()
        if user is None:
            user = AppUser(
                username=username,
                password_hash=hash_password(password),
                is_active=True,
                totp_enabled=False,
            )
            session.add(user)
            session.flush()
        else:
            user.password_hash = hash_password(password)
            user.is_active = True
            session.flush()
        return str(user.id)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m app.auth.create_user <username> <password>", file=sys.stderr)
        return 2
    username, password = argv
    user_id = upsert_user(username, password)
    print(f"upserted user {username!r} (id={user_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
