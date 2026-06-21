"""bid.bid_line — flip uniqueness to the flat-13 period grain (filtered, backward-compatible).

Revision ID: 0016_bid_line_period_uniqueness
Revises: 0015_bid_line_fiscal_period
Create Date: 2026-06-20

The flat-13 model (INTAKE_TEMPLATE_DESIGN §1a) fans one TIMEFRAME's price out to EVERY fiscal period
in its span, so several bid_line rows legitimately share (submission, dc, lot, item, tf_id) — which
the old `uq_bid_line_cell_per_submission UNIQUE (submission_id, dc_id, lot_id, item_id, tf_id)`
forbids. Replace that one constraint with TWO filtered unique indexes so both grains coexist:

  * fiscal_period_id IS NULL  -> one row per (submission, dc, lot, item, tf_id) — the legacy/pilot
    timeframe grain, UNCHANGED (so resubmission/supersession behaves exactly as before).
  * fiscal_period_id IS NOT NULL -> one row per (submission, dc, lot, item, fiscal_period_id) — the
    fanned-out flat-13 grain (one price per period per cell).

Backward-compatible: existing rows (all NULL-period) keep the identical guarantee under the first
index. The composite `uq_bid_line_identity_full` (an FK target for the landed-cost table) is left
untouched. This is a CONSTRAINT-only change — it does not touch the engine read path.

Downgrade restores the original single constraint (clean on the empty/legacy grain). Idempotent DDL.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016_bid_line_period_uniqueness"
down_revision: str | None = "0015_bid_line_fiscal_period"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE bid.bid_line DROP CONSTRAINT IF EXISTS uq_bid_line_cell_per_submission;

CREATE UNIQUE INDEX IF NOT EXISTS uq_bid_line_cell_tf_when_no_period
    ON bid.bid_line (submission_id, dc_id, lot_id, item_id, tf_id)
    WHERE fiscal_period_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_bid_line_cell_period
    ON bid.bid_line (submission_id, dc_id, lot_id, item_id, fiscal_period_id)
    WHERE fiscal_period_id IS NOT NULL;
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS bid.uq_bid_line_cell_period;
DROP INDEX IF EXISTS bid.uq_bid_line_cell_tf_when_no_period;

ALTER TABLE bid.bid_line
    ADD CONSTRAINT uq_bid_line_cell_per_submission
    UNIQUE (submission_id, dc_id, lot_id, item_id, tf_id);
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
