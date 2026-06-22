"""eng.analysis_run.label — a lightweight NAMED savepoint for an alignment version (E-43 slice).

Revision ID: 0020_eng_analysis_run_label
Revises: 0019_pilot_run
Create Date: 2026-06-22

ADDITIVE, on top of 0019. Owned by the Engine & Domain squad.

WHY (E-43 in-alignment versioned save — sponsor-ruled vital for the first live test):
  During a live alignment meeting the buyer builds test versions (tune strategy -> run analysis ->
  repeat) and must be able to SAVE a NAMED version freely, mid-meeting, DISTINCT from the terminal
  FREEZE (E-21). A version already exists the moment `run_round` seals an `eng.analysis_run`; the
  missing piece is a human-given NAME so saved versions are recognizable + pickable. Naming is plain
  metadata — NOT a governed decision: it writes NO audit event; FREEZE stays the only governed seal.

WHAT (additive, idempotent):
  * eng.analysis_run ADD COLUMN label varchar(120) NULL.

Downgrade drops the column, so up->down->up is clean. Idempotent raw DDL (IF NOT EXISTS).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020_eng_analysis_run_label"
down_revision: str | None = "0019_pilot_run"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE eng.analysis_run
    ADD COLUMN IF NOT EXISTS label varchar(120);
COMMENT ON COLUMN eng.analysis_run.label IS
    'E-43 savepoint: an optional human-given name for a sealed alignment version. Plain metadata, '
    'NOT a governed decision (no audit event); freeze (E-21) stays the only governed seal.';
"""

DOWNGRADE_SQL = """
ALTER TABLE eng.analysis_run DROP COLUMN IF EXISTS label;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
