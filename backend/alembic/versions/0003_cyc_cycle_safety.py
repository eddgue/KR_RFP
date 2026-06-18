"""cyc.cycle_safety — the five safeties as per-RFP contract terms (D13 / ADR-0014).

Revision ID: 0003_cyc_cycle_safety
Revises: 0002_cyc_kickoff_satellites
Create Date: 2026-06-18

ADDITIVE, on top of the M0 baseline (frozen).

The five pricing safeties are CONTRACT terms (risk-sharing incentives that govern post-award
price movement during execution), declared at kickoff. Per D13/ADR-0014:
  * TERMS ONLY — the engine (scoring/allocation) does NOT consume these. They live here so the
    contract/execution module (Phase E+) can apply/record reprices into awd.award_layer; the
    pilot/engine work is independent of safeties.
  * All windows/cadences/bands are set INDIVIDUALLY per RFP — not fixed defaults.

Storage shape: one row per APPLIED safety on a cycle (a per-cycle configurable menu). Rather than
an opaque jsonb blob, the parameters are real typed columns (cap, floor, lookback_weeks,
reset_cadence_weeks, band, min_duration_weeks, reprice_window_weeks, reverts_to_contract, notes)
so the terms are queryable/renderable. Each parameter is nullable and carries weight only for the
safety types that use it; a CHECK pins safety_type to the five ratified values.

Grain alignment: cyc.cycle's PK is cycle_id varchar(36) in the baseline; PK (cycle_id, safety_type)
gives at most one row per safety type per cycle.

Idempotent raw DDL; real downgrade drops the table so up->down->up stays clean.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_cyc_cycle_safety"
down_revision: str | None = "0002_cyc_kickoff_satellites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS cyc.cycle_safety (
    cycle_id             varchar(36) NOT NULL,
    safety_type          text        NOT NULL,
    -- COLLAR
    cap                  numeric(18, 6),   -- Kroger upside protection on a hike
    floor                numeric(18, 6),   -- supplier downside protection (Kroger may go to 0)
    -- ROLLING_MIDPOINT
    lookback_weeks       integer,          -- trailing window the midpoint is taken over
    reset_cadence_weeks  integer,          -- how often the price is re-set to that midpoint
    -- TOLERANCE_BAND
    band                 numeric(18, 6),   -- anomaly threshold
    min_duration_weeks   integer,          -- sustained-move requirement before triggering
    reprice_window_weeks integer,          -- temporary-reprice hold window before re-review
    -- DISASTER / INVERSE_DISASTER
    reverts_to_contract  boolean     NOT NULL DEFAULT true,  -- always reverts after the event
    notes                text,
    PRIMARY KEY (cycle_id, safety_type),
    CONSTRAINT ck_cycle_safety_type CHECK (safety_type IN (
        'COLLAR', 'ROLLING_MIDPOINT', 'TOLERANCE_BAND', 'DISASTER', 'INVERSE_DISASTER')),
    CONSTRAINT ck_cycle_safety_weeks_positive CHECK (
        (lookback_weeks       IS NULL OR lookback_weeks       > 0)
    AND (reset_cadence_weeks  IS NULL OR reset_cadence_weeks  > 0)
    AND (min_duration_weeks   IS NULL OR min_duration_weeks   > 0)
    AND (reprice_window_weeks IS NULL OR reprice_window_weeks > 0)),
    CONSTRAINT ck_cycle_safety_collar_ordered CHECK (
        cap IS NULL OR floor IS NULL OR cap >= floor),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
COMMENT ON TABLE cyc.cycle_safety IS
    'Per-RFP pricing-safety CONTRACT terms (D13/ADR-0014). Terms only; engine ignores them.';
"""


DOWNGRADE_SQL = """
DROP TABLE IF EXISTS cyc.cycle_safety;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
