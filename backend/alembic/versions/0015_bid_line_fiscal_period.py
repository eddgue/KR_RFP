"""bid.bid_line — add the flat-13 fiscal-period reference (storage grain, additive/nullable).

Revision ID: 0015_bid_line_fiscal_period
Revises: 0014_ref_fiscal_period
Create Date: 2026-06-20

ADDITIVE and BACKWARD-COMPATIBLE. The flat-13 model (INTAKE_TEMPLATE_DESIGN §1a) records every
offer against exactly ONE of the 13 Kroger fiscal periods (ref.fiscal_period, seeded by 0014); a
cycle's bid template groups periods into timeframes and intake FANS a timeframe's price out to each
period in its span. This migration lands the storage column that fan-out writes to.

WHAT:
  * ADD fiscal_period_id varchar(36)  — the ref.fiscal_period the line records against, nullable.

It is nullable and carries NO constraint change: existing (pilot) rows stay NULL and behave exactly
as before — the engine still reads the timeframe (tf_id), nothing is fanned out, nothing breaks. The
reference is LOGICAL (unenforced in DDL), matching tf_id and the other id columns on bid_line. The
uniqueness flip (a filtered unique index on the period grain) and the engine read-path activation
are deliberate LATER slices, intentionally not in this storage-only step.

Downgrade drops the column, so up->down->up is clean. Idempotent raw DDL (ADD COLUMN IF NOT EXISTS).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015_bid_line_fiscal_period"
down_revision: str | None = "0014_ref_fiscal_period"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE bid.bid_line
    ADD COLUMN IF NOT EXISTS fiscal_period_id varchar(36);

COMMENT ON COLUMN bid.bid_line.fiscal_period_id IS
    'The ref.fiscal_period this line is recorded against (flat-13 grain, INTAKE §1a). Nullable: '
    'NULL = pre-fan-out (pilot/timeframe-only) rows. Logical reference, unenforced like tf_id.';
"""

DOWNGRADE_SQL = """
ALTER TABLE bid.bid_line DROP COLUMN IF EXISTS fiscal_period_id;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
