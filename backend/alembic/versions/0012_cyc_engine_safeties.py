"""cyc.cycle — per-RFP engine safeties the buyer sets at kickoff (adjustable, not preset defaults).

Revision ID: 0012_cyc_engine_safeties
Revises: 0011_bid_transit_days
Create Date: 2026-06-20

ADDITIVE. The setup/kickoff workbook lets the buyer set four ENGINE safeties per RFP — the premium
eligibility ceiling, the coverage floor, the category-concentration flag, and the max suppliers per
DC. These are scoring/allocation knobs the engine DOES consume (unlike cyc.cycle_safety, which
holds the five pricing CONTRACT terms the engine ignores). Until now they were dropped on ingest and
the engine silently used the strategy-preset defaults; storing them here lets run_round honour the
buyer's values, falling back to the preset where a field is left blank.

WHAT (all nullable — blank means "use the preset default"):
  * engine_premium_ceiling numeric(18,6)  — max premium vs lowest before a bid is gated ineligible
  * engine_coverage_floor   numeric(18,6)  — min coverage ratio to be eligible
  * engine_conc_thresh      numeric(18,6)  — category-concentration flag threshold
  * engine_max_sup_dc       integer        — split cap (max suppliers per DC)

Downgrade drops the columns, so up->down->up stays clean. Idempotent raw DDL (ADD COLUMN IF NOT
EXISTS).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_cyc_engine_safeties"
down_revision: str | None = "0011_bid_transit_days"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE cyc.cycle
    ADD COLUMN IF NOT EXISTS engine_premium_ceiling numeric(18, 6),
    ADD COLUMN IF NOT EXISTS engine_coverage_floor  numeric(18, 6),
    ADD COLUMN IF NOT EXISTS engine_conc_thresh     numeric(18, 6),
    ADD COLUMN IF NOT EXISTS engine_max_sup_dc      integer;

COMMENT ON COLUMN cyc.cycle.engine_premium_ceiling IS
    'Per-RFP engine safety: max premium vs lowest before a bid is gated ineligible. '
    'Nullable — blank uses the strategy-preset default (EngineConfig.global_premium_threshold).';
COMMENT ON COLUMN cyc.cycle.engine_coverage_floor IS
    'Per-RFP engine safety: min coverage ratio to be eligible. Nullable — blank uses the preset.';
COMMENT ON COLUMN cyc.cycle.engine_conc_thresh IS
    'Per-RFP engine safety: category-concentration flag threshold. Nullable — blank uses preset.';
COMMENT ON COLUMN cyc.cycle.engine_max_sup_dc IS
    'Per-RFP engine safety: split cap (max suppliers per DC). Nullable — blank uses the preset.';
"""

DOWNGRADE_SQL = """
ALTER TABLE cyc.cycle
    DROP COLUMN IF EXISTS engine_premium_ceiling,
    DROP COLUMN IF EXISTS engine_coverage_floor,
    DROP COLUMN IF EXISTS engine_conc_thresh,
    DROP COLUMN IF EXISTS engine_max_sup_dc;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
