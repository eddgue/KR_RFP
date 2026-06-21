"""auth.app_user — the web-console user (its own `auth` schema, separate from the eight layers).

Revision ID: 0017_auth_app_user
Revises: 0016_bid_line_period_uniqueness
Create Date: 2026-06-21

ADDITIVE, net-new. Adds a dedicated `auth` schema (NOT one of the eight governed layers — console
identity must not live inside the data spine) and the `auth.app_user` table behind login: a unique
username, an argon2 `password_hash`, the TOTP-2FA state (`totp_secret` nullable + `totp_enabled`),
an `is_active` flag, and a creation timestamp. The PK is a uuid with `gen_random_uuid()`, mirroring
the ref spine tables; the unique index on `username` enforces identity.

CREATE SCHEMA / DROP SCHEMA use IF [NOT] EXISTS so the migration is safe to re-run and round-trips
cleanly (up -> down -> up). Downgrade drops the table then the schema, leaving nothing behind. No
`app.*` module is imported — migrations stay frozen/standalone.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "0017_auth_app_user"
down_revision: str | None = "0016_bid_line_period_uniqueness"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.create_table(
        "app_user",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("totp_secret", sa.Text(), nullable=True),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_app_user"),
        sa.UniqueConstraint("username", name="uq_app_user_username"),
        schema="auth",
    )


def downgrade() -> None:
    op.drop_table("app_user", schema="auth")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")
