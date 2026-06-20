"""cyc.cycle — per-RFP scoring weight preset the buyer chooses at kickoff.

Revision ID: 0013_cyc_engine_weight_preset
Revises: 0012_cyc_engine_safeties
Create Date: 2026-06-20

ADDITIVE. The setup/kickoff workbook lets the buyer pick a named scoring preset (balanced /
price_focus / coverage_focus / risk_averse / custom) that remaps the engine's five scoring weights.
Like the engine safeties (0012) this was collected but dropped on ingest; storing it here lets
run_round apply the preset's weight vector. Nullable — blank uses the engine's default (balanced).

WHAT:
  * engine_weight_preset text  — one of the five ratified presets, or NULL (= default).

Downgrade drops the column, so up->down->up stays clean. Idempotent raw DDL (ADD COLUMN IF NOT
EXISTS); the value check is enforced at ingest too.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013_cyc_engine_weight_preset"
down_revision: str | None = "0012_cyc_engine_safeties"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE cyc.cycle
    ADD COLUMN IF NOT EXISTS engine_weight_preset text;

ALTER TABLE cyc.cycle DROP CONSTRAINT IF EXISTS ck_cycle_weight_preset;
ALTER TABLE cyc.cycle ADD CONSTRAINT ck_cycle_weight_preset CHECK (
    engine_weight_preset IS NULL OR engine_weight_preset IN (
        'balanced', 'price_focus', 'coverage_focus', 'risk_averse', 'custom'));

COMMENT ON COLUMN cyc.cycle.engine_weight_preset IS
    'Per-RFP scoring weight preset (ADR-0016). Nullable — blank uses the default (balanced).';
"""

DOWNGRADE_SQL = """
ALTER TABLE cyc.cycle DROP CONSTRAINT IF EXISTS ck_cycle_weight_preset;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS engine_weight_preset;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
