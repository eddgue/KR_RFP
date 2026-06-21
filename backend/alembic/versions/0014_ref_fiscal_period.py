"""ref.fiscal_period — the governed Kroger fiscal-calendar period dimension (seeded from CSV).

Revision ID: 0014_ref_fiscal_period
Revises: 0013_cyc_engine_weight_preset
Create Date: 2026-06-20

ADDITIVE, net-new ref spine table. Kroger runs a 4-3-3-3 retail fiscal calendar: every fiscal year
has EXACTLY 13 four-week periods grouped into four quarters (Q1=P1-4, Q2=P5-7, Q3=P8-10, Q4=P11-13);
period 13 of a 53-week year carries a 5th week. The authoritative conversion table (FY16..FY36,
fully contiguous) already ships as data at app/fiscal/data/kroger_fiscal_periods.csv and is exposed
by the typed library app.fiscal.calendar. This migration lands that calendar in the database as a
governed period dimension other tables can FK to: it creates ref.fiscal_period (uuid PK like the
other net-new ref spine tables, UNIQUE on (fiscal_year, period)) and SEEDS all 273 rows.

The CSV is read with ONLY the stdlib (csv + pathlib); the path is resolved relative to this file
(backend/alembic/versions/ -> backend/app/fiscal/data/). NO app.* module is imported — migrations
stay frozen/standalone, independent of any later refactor of the app package.

Downgrade drops the table, so up->down->up is clean.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision: str = "0014_ref_fiscal_period"
down_revision: str | None = "0013_cyc_engine_weight_preset"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# This file:  backend/alembic/versions/0014_ref_fiscal_period.py
# CSV:        backend/app/fiscal/data/kroger_fiscal_periods.csv
# parents[2] climbs versions/ -> alembic/ -> backend/, then down into app/fiscal/data/.
_CSV_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "fiscal" / "data" / "kroger_fiscal_periods.csv"
)


def _read_seed_rows() -> list[dict[str, object]]:
    """Parse the shipped fiscal-calendar CSV into bulk_insert payload rows (stdlib only)."""

    rows: list[dict[str, object]] = []
    with _CSV_PATH.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "fiscal_year": int(r["fiscal_year"]),
                    "period": int(r["period"]),
                    "quarter": int(r["quarter"]),
                    "begin_date": date.fromisoformat(r["begin_date"]),
                    "end_date": date.fromisoformat(r["end_date"]),
                    "weeks": int(r["weeks"]),
                }
            )
    return rows


def upgrade() -> None:
    fiscal_period = op.create_table(
        "fiscal_period",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("begin_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("weeks", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_fiscal_period"),
        sa.UniqueConstraint("fiscal_year", "period", name="fiscal_period_year_period"),
        schema="ref",
    )

    # Seed all 273 rows (FY16..FY36) from the authoritative CSV. The table handle returned by
    # create_table carries the column definitions bulk_insert needs.
    op.bulk_insert(fiscal_period, _read_seed_rows())


def downgrade() -> None:
    op.drop_table("fiscal_period", schema="ref")
