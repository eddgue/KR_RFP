"""eng.analysis_scenario_award.rec_type — the authoritative per-cell B reason label (§5 / D28).

Revision ID: 0009_eng_award_rec_type
Revises: 0008_eng_analysis_run
Create Date: 2026-06-19

ADDITIVE, on top of 0008. Owned by the Engine & Domain squad.

WHY (V3_ENGINE_LOGIC §5 B / D28 — explanations are engine-derived, not boilerplate):
  The V3 spec assigns every Scenario-B pick a RecType — Lowest cost / Coverage advantage /
  Comparable premium / Defensible premium / Risk-adjusted — from config-driven thresholds. This is
  the AUTHORITATIVE "why this pick" reason. Per the governing principle (D28), explanatory text in
  any output must be the engine's actual computed reason rendered from the sealed records — never a
  generic catch-all phrase and never generated at output time. So the engine now computes RecType
  for the B awards and we SEAL it here; the outputs (e.g. the Lowest-Cost Check "why not lowest")
  render this column instead of a hardcoded clause. B-only — NULL for the other lenses.

WHAT (additive, idempotent):
  * eng.analysis_scenario_award ADD COLUMN rec_type varchar(40) NULL.

Downgrade drops the column, so up->down->up is clean. Idempotent raw DDL (IF NOT EXISTS).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_eng_award_rec_type"
down_revision: str | None = "0008_eng_analysis_run"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE eng.analysis_scenario_award
    ADD COLUMN IF NOT EXISTS rec_type varchar(40);
COMMENT ON COLUMN eng.analysis_scenario_award.rec_type IS
    'V3 §5 Scenario-B reason label (Lowest cost / Coverage advantage / Comparable / Defensible / '
    'Risk-adjusted). The authoritative per-cell "why this pick"; outputs render it, never a '
    'hardcoded clause (D28). B-only, NULL for other lenses.';
"""

DOWNGRADE_SQL = """
ALTER TABLE eng.analysis_scenario_award DROP COLUMN IF EXISTS rec_type;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
