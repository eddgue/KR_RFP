"""pilot.run — the DB-backed run identity for the web console (its own `pilot` schema).

Revision ID: 0019_pilot_run
Revises: 0018_backfill_commodity_client
Create Date: 2026-06-21

ADDITIVE, net-new (no-server-side-file-storage refactor, ADR-0018 Slice 2). Adds a dedicated
`pilot` schema (NOT one of the eight governed layers — a "run" is console orchestration metadata,
not part of the data spine) and the `pilot.run` table that severs run identity from the vault
folder. Today a "run" is only a `runs/<slug>/` folder linked to a cycle by `cycle_id.txt`; this
table makes the run a first-class DB row so the stateless web console can resolve/list runs with no
filesystem: `slug` (PK, the existing `<commodity>-<date>-<short-id>` identifier), `commodity`,
`label`, `rehearsal` (the SYNTHETIC-provenance flag, replacing the `.rehearsal` sentinel), a
nullable `cycle_id` (set on setup ingest, replacing `cycle_id.txt`), and a creation timestamp.

`cycle_id` is intentionally a plain text column (NOT an FK): cycle ids are stored as text throughout
the pilot path (`cycle_id.txt`, `bid.bid_line.cycle_id`, etc.), and the row must be insertable
before a cycle exists. The MCP harness is untouched — it keeps its file vault; this is the console's
store.

CREATE SCHEMA / DROP SCHEMA use IF [NOT] EXISTS so the migration is safe to re-run and round-trips
cleanly (up -> down -> up). Downgrade drops the table then the schema, leaving nothing behind. No
`app.*` module is imported — migrations stay frozen/standalone (mirrors 0017_auth_app_user).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019_pilot_run"
down_revision: str | None = "0018_backfill_commodity_client"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS pilot")
    op.create_table(
        "run",
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("commodity", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("rehearsal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cycle_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("slug", name="pk_run"),
        schema="pilot",
    )


def downgrade() -> None:
    op.drop_table("run", schema="pilot")
    op.execute("DROP SCHEMA IF EXISTS pilot CASCADE")
