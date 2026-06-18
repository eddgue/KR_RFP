"""eng.scenario_award split re-grain — schema prep (G1 / D10).

Revision ID: 0005_eng_scenario_award_split
Revises: 0004_norm_attribute_taxonomy
Create Date: 2026-06-18

ADDITIVE, on top of the M0 baseline (frozen).

SCHEMA PREP ONLY; the engine split LOGIC ships post-pilot behind the `split_award` flag. Default
behavior is unchanged (auto max 2 suppliers per DC — D10; the cap is engine logic, not a DB rule).

What this does (V3_ENGINE_LOGIC.md §9 gap #1, D10):
  The M0 baseline's eng.scenario_award (the CLEAN of scenario_a_cell_assignment, the canonical
  re-grain target per db/baseline/NAMING_MAP.md line 54) carries a SINGLE-WINNER uniqueness
  UNIQUE(scenario_run_id, dc_id, lot_id, tf_id) and lacks split columns. To let a (run, dc, lot, tf)
  cell hold N suppliers with a volume split, this migration ALTERS the EXISTING table:
    * ADD volume_share    numeric        — the cell's volume fraction for this supplier.
    * ADD is_fallback     boolean default false — lot filled outside the consolidated top-N set
                                                  (V3 §4.3 transparency flag).
    * ADD cap_breach_flag boolean default false — a manual selection exceeded the auto cap
                                                  (V3 §4.4 / D10).
    * RELAX the single-winner unique to per-supplier: re-grain to
      UNIQUE(scenario_run_id, dc_id, lot_id, tf_id, supplier_id) so the cell may hold N suppliers.

We ALTER the existing eng.scenario_award (NAMING_MAP calls it the split target) rather than create
a new table — its identity FKs, the status-shape CHECK, and the line/capacity detail tables already
point at it, so altering in place keeps the spine intact.

volume_share semantics: nullable (NO_FEASIBLE_ASSIGNMENT rows have none); when present it is a
fraction in [0, 1]; a CHECK enforces the range without forcing the per-cell shares to sum to 1
(partial/fallback fills are legitimate and the sum invariant is engine-side).

Idempotent raw DDL; real downgrade restores the single-winner unique and drops the three columns,
so up->down->up stays clean. (The downgrade is only safe while no cell yet holds >1 supplier — true
at schema-prep time, before the split LOGIC ships.)
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_eng_scenario_award_split"
down_revision: str | None = "0004_norm_attribute_taxonomy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
-- Split columns (additive, idempotent).
ALTER TABLE eng.scenario_award
    ADD COLUMN IF NOT EXISTS volume_share    numeric(9, 6);
ALTER TABLE eng.scenario_award
    ADD COLUMN IF NOT EXISTS is_fallback     boolean NOT NULL DEFAULT false;
ALTER TABLE eng.scenario_award
    ADD COLUMN IF NOT EXISTS cap_breach_flag boolean NOT NULL DEFAULT false;

-- volume_share range guard (added once, guarded so re-run is a no-op).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_scenario_award_volume_share_range'
    ) THEN
        ALTER TABLE eng.scenario_award
            ADD CONSTRAINT ck_scenario_award_volume_share_range
            CHECK (volume_share IS NULL OR (volume_share >= 0 AND volume_share <= 1));
    END IF;
END
$$;

-- Re-grain the single-winner uniqueness to per-supplier so a cell may hold N suppliers.
-- The baseline named the single-winner unique uq_scenario_a_cell_assignment_cell.
ALTER TABLE eng.scenario_award DROP CONSTRAINT IF EXISTS uq_scenario_a_cell_assignment_cell;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_scenario_award_cell_supplier'
    ) THEN
        ALTER TABLE eng.scenario_award
            ADD CONSTRAINT uq_scenario_award_cell_supplier
            UNIQUE (scenario_run_id, dc_id, lot_id, tf_id, supplier_id);
    END IF;
END
$$;

COMMENT ON COLUMN eng.scenario_award.volume_share IS
    'G1/D10 schema prep: per-supplier cell volume fraction. Split LOGIC ships post-pilot.';
"""


DOWNGRADE_SQL = """
-- Restore the single-winner unique (safe only while no cell holds >1 supplier — schema-prep state).
ALTER TABLE eng.scenario_award DROP CONSTRAINT IF EXISTS uq_scenario_award_cell_supplier;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_scenario_a_cell_assignment_cell'
    ) THEN
        ALTER TABLE eng.scenario_award
            ADD CONSTRAINT uq_scenario_a_cell_assignment_cell
            UNIQUE (scenario_run_id, dc_id, lot_id, tf_id);
    END IF;
END
$$;

ALTER TABLE eng.scenario_award DROP CONSTRAINT IF EXISTS ck_scenario_award_volume_share_range;
ALTER TABLE eng.scenario_award DROP COLUMN IF EXISTS cap_breach_flag;
ALTER TABLE eng.scenario_award DROP COLUMN IF EXISTS is_fallback;
ALTER TABLE eng.scenario_award DROP COLUMN IF EXISTS volume_share;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
