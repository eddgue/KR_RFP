"""awd.* — the frozen award + append-only VERSIONED post-award adjustment layers (ADR-0014).

Revision ID: 0010_awd_award_versioned
Revises: 0009_eng_award_rec_type
Create Date: 2026-06-19

ADDITIVE, on top of 0009. Owned by the Post-Award squad.

WHY (ADR-0014 freeze-and-layer, ADR-0006 no-hard-deletes, PILOT step 5):
  After a human selects an engine scenario, the recommendation in `eng.analysis_scenario_award`
  is PROMOTED to a real award here. The award is FROZEN: `awd.award` + an immutable `award_line`
  per cell capture the baseline (`frozen_price`) and are NEVER updated. Post-award negotiation /
  safety-driven price moves are recorded as APPEND-ONLY, date-stamped, VERSIONED LAYERS:
  `awd.award_adjustment` (version_no 1..N, who/when/why) + `awd.award_adjustment_line` (per-cell
  prior_price -> new_price -> delta). The raw frozen award is never overwritten (ADR-0014); a price
  move supersedes via a new layer, not an UPDATE (ADR-0006). The effective price for a cell at any
  version is the baseline overlaid by each layer's new_price up to that version. The post-award doc
  renders an explicit "which version" heading off these rows (PILOT step 5).

WHAT (all additive, idempotent):
  * awd.award — one frozen award per selected (cycle, run, scenario). FK -> cyc.cycle
                                / eng.analysis_run. UNIQUE(cycle, run, scenario).
  * awd.award_line            — the immutable baseline: one row per awarded cell (frozen_price).
                                Never updated (ADR-0014 raw-never-overwritten).
  * awd.award_adjustment      — an append-only VERSIONED layer (version_no, type, effective_date,
                                reason, who/when). UNIQUE(award, version_no).
  * awd.award_adjustment_line — per-cell prior_price -> new_price -> delta for a layer.

Downgrade drops the four tables (child-first) + the schema, so up->down->up is clean. Idempotent
raw DDL (CREATE SCHEMA / TABLE IF NOT EXISTS) so re-runs are no-ops.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_awd_award_versioned"
down_revision: str | None = "0009_eng_award_rec_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
CREATE SCHEMA IF NOT EXISTS awd;

-- awd.award — one FROZEN award per selected (cycle, run, scenario). The immutable baseline header.
CREATE TABLE IF NOT EXISTS awd.award (
    award_id         varchar(36)  NOT NULL,
    cycle_id         varchar(36)  NOT NULL,
    analysis_run_id  varchar(36)  NOT NULL,
    scenario_code    text         NOT NULL,
    award_code       text         NOT NULL,
    frozen_at        timestamp    NOT NULL,
    frozen_by        varchar(120) NOT NULL,
    status           text         NOT NULL DEFAULT 'FROZEN',
    PRIMARY KEY (award_id),
    CONSTRAINT uq_award_cycle_run_scenario UNIQUE (cycle_id, analysis_run_id, scenario_code),
    CONSTRAINT fk_award_cycle FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id),
    CONSTRAINT fk_award_run FOREIGN KEY (analysis_run_id)
        REFERENCES eng.analysis_run (analysis_run_id)
);
COMMENT ON TABLE awd.award IS
    'A FROZEN award promoted from a selected engine scenario (ADR-0006: a human selects; '
    'the engine never asserts). Freeze-and-layer (ADR-0014): this header + awd.award_line are the '
    'immutable baseline; post-award price moves are append-only VERSIONED layers in '
    'awd.award_adjustment — the raw award is NEVER overwritten.';

-- awd.award_line — the immutable baseline: one row per awarded cell at the frozen price.
CREATE TABLE IF NOT EXISTS awd.award_line (
    award_line_id  varchar(36)    NOT NULL,
    award_id       varchar(36)    NOT NULL,
    dc_id          varchar(36)    NOT NULL,
    lot_id         varchar(36)    NOT NULL,
    tf_id          varchar(36)    NOT NULL,
    supplier_id    varchar(36)    NOT NULL,
    volume_share   numeric(9, 6)  NOT NULL,
    frozen_price   numeric(18, 6) NOT NULL,
    PRIMARY KEY (award_line_id),
    CONSTRAINT uq_award_line_cell
        UNIQUE (award_id, dc_id, lot_id, tf_id, supplier_id),
    CONSTRAINT fk_award_line_award FOREIGN KEY (award_id)
        REFERENCES awd.award (award_id)
);
COMMENT ON COLUMN awd.award_line.frozen_price IS
    'The immutable baseline price for this cell at freeze time (= the selected scenario''s '
    'awarded_price). NEVER updated — post-award moves layer on top (ADR-0014 '
    'raw-never-overwritten).';

-- awd.award_adjustment — an APPEND-ONLY, date-stamped, VERSIONED post-award layer.
CREATE TABLE IF NOT EXISTS awd.award_adjustment (
    adjustment_id    varchar(36)  NOT NULL,
    award_id         varchar(36)  NOT NULL,
    version_no       integer      NOT NULL,
    adjustment_type  text         NOT NULL,
    effective_date   date         NOT NULL,
    reason           text         NOT NULL,
    created_at       timestamp    NOT NULL,
    created_by       varchar(120) NOT NULL,
    status           text         NOT NULL DEFAULT 'RECORDED',
    PRIMARY KEY (adjustment_id),
    CONSTRAINT uq_award_adjustment_version UNIQUE (award_id, version_no),
    CONSTRAINT ck_award_adjustment_version_positive CHECK (version_no >= 1),
    CONSTRAINT fk_award_adjustment_award FOREIGN KEY (award_id)
        REFERENCES awd.award (award_id)
);
COMMENT ON TABLE awd.award_adjustment IS
    'An APPEND-ONLY post-award negotiation/safety price layer on the frozen award (ADR-0014). '
    'version_no is 1..N per award (v0 = the frozen baseline). A price move SUPERSEDES via a new '
    'layer, never an UPDATE of the baseline (ADR-0006 no hard deletes / no overwrite).';

-- awd.award_adjustment_line — per-cell prior_price -> new_price -> delta for one layer.
CREATE TABLE IF NOT EXISTS awd.award_adjustment_line (
    adj_line_id    varchar(36)    NOT NULL,
    adjustment_id  varchar(36)    NOT NULL,
    dc_id          varchar(36)    NOT NULL,
    lot_id         varchar(36)    NOT NULL,
    tf_id          varchar(36)    NOT NULL,
    supplier_id    varchar(36)    NOT NULL,
    prior_price    numeric(18, 6) NOT NULL,
    new_price      numeric(18, 6) NOT NULL,
    delta          numeric(18, 6) NOT NULL,
    PRIMARY KEY (adj_line_id),
    CONSTRAINT uq_adj_line_cell
        UNIQUE (adjustment_id, dc_id, lot_id, tf_id, supplier_id),
    CONSTRAINT fk_adj_line_adjustment FOREIGN KEY (adjustment_id)
        REFERENCES awd.award_adjustment (adjustment_id)
);
COMMENT ON COLUMN awd.award_adjustment_line.prior_price IS
    'The cell''s effective price BEFORE this layer (baseline overlaid by all earlier layers); '
    'delta = new_price - prior_price. The frozen baseline in awd.award_line is never touched '
    '(ADR-0014 freeze-and-layer).';
"""

DOWNGRADE_SQL = """
DROP TABLE IF EXISTS awd.award_adjustment_line;
DROP TABLE IF EXISTS awd.award_adjustment;
DROP TABLE IF EXISTS awd.award_line;
DROP TABLE IF EXISTS awd.award;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
