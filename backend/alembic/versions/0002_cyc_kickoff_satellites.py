"""cyc kickoff satellites — the kickoff keystone (G5/E-14, D9, D12).

Revision ID: 0002_cyc_kickoff_satellites
Revises: 0001_baseline
Create Date: 2026-06-18

ADDITIVE, on top of the M0 baseline (db/baseline/schema.sql is frozen — never edited).

What this adds (KICKOFF_KEYSTONE_SPEC.md §c, ratified by D9/D12):
  * Additive columns on cyc.cycle: annual_spend, fiscal+calendar horizon, prior_structure_note,
    horizon_label, dcs_scope.
  * cyc.cycle_objective       — multi-objective with exactly-one-primary (partial unique index).
  * cyc.cycle_pricing         — ONE row per cycle (D9): basis / cadence / baseline-then-negotiate
                                / volume-split / routing. The render contract (ADR-0013/D12).
  * cyc.cycle_scope_item      — item-level participation with `participates boolean` (D9): product
                                heterogeneity handled by scoping items in/out, NOT by mixing
                                pricing structures.
  * cyc.cycle_pba_term        — PBA governance (metric / threshold / enforcement).
  * cyc.cycle_commercial_term — working-capital / KPM / other terms.
  * cyc.cycle_rfi_question    — configurable RFI set (stable codes for cross-cycle comparability).
  * cyc.cycle_timeline_event  — the "Next Steps" rail that drives the rendered process (E-16).
  * cyc.cycle_narrative       — versioned rich-text narrative blocks (never field-ified).
  * cyc.cycle_invited_supplier.is_incumbent — EXTEND the existing baseline table (the spec asks
                                for EXTEND, and the table already exists in M0).

Grain & key alignment (reconciled to the M0 baseline, NOT the spec's illustrative `bigint`):
  cyc.cycle's PK is `cycle_id varchar(36)` in the baseline, so every satellite FKs that type.
  Composite-identity discipline is preserved where the baseline offers a pair (e.g. the
  (cycle_id, commodity_id) pair on cyc.cycle); these satellites are cycle-scoped, so a single
  cycle_id FK is the right grain.

Pricing storage (ADR-0013 / D12) — period-grain component facts: the M0 baseline ALREADY carries
  this. bid.bid_line stores per-cell (supplier × dc × lot × item × tf) component columns (fob_case,
  freight_case, fuel_case, accessorial_case, item_discount_case, shrink_case, submitted_all_in_case)
  and perf.commercial_pricing_model/_price_component store period-grain (window_id) components.
  cyc.cycle_pricing here is the DECLARED render contract (the "setup file"), not the facts — so no
  new bid/price storage is added; the period-grain component store is already present.

Idempotent raw DDL via op.execute; real downgrade drops exactly what is created so the CI
up->down->up roundtrip stays clean.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_cyc_kickoff_satellites"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
-- ---------------------------------------------------------------------------
-- 1. EXTEND cyc.cycle with the kickoff header fields (additive columns only).
--    ALTER ... ADD COLUMN IF NOT EXISTS is idempotent on PG.
-- ---------------------------------------------------------------------------
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS annual_spend         numeric(18, 2);
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS horizon_label        text;
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS tf_start_fiscal      text;
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS tf_end_fiscal        text;
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS tf_start_calendar    date;
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS tf_end_calendar      date;
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS prior_structure_note text;
ALTER TABLE cyc.cycle ADD COLUMN IF NOT EXISTS dcs_scope            text DEFAULT 'ALL';

-- ---------------------------------------------------------------------------
-- 2. cyc.cycle_objective — multi-objective, exactly one primary per cycle.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_objective (
    cycle_id       varchar(36) NOT NULL,
    objective_code text        NOT NULL,
    is_primary     boolean     NOT NULL DEFAULT false,
    objective_note text,
    PRIMARY KEY (cycle_id, objective_code),
    CONSTRAINT ck_cycle_objective_code CHECK (
        objective_code IN ('SAVINGS', 'SUPPLY_ASSURANCE', 'QUALITY', 'DIVERSIFICATION', 'STRATEGIC')),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
-- Exactly one primary objective per cycle (partial unique index on the primary flag).
CREATE UNIQUE INDEX IF NOT EXISTS uq_cycle_objective_one_primary
    ON cyc.cycle_objective (cycle_id) WHERE is_primary = true;

-- ---------------------------------------------------------------------------
-- 3. cyc.cycle_pricing — ONE per cycle (D9). The declared render contract (ADR-0013/D12):
--    basis / cadence / baseline-then-negotiate / volume-split / routing. PK = cycle_id enforces
--    the one-model-per-RFP grain (heterogeneity handled by item participation, not by mixing).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_pricing (
    cycle_id                varchar(36) NOT NULL,
    pricing_basis           text        NOT NULL,
    duration_cadence        text        NOT NULL,
    cadence_n               integer,
    baseline_then_negotiate boolean     NOT NULL DEFAULT false,
    volume_split_rule       text,
    routing_basis           text,
    sourcing_region_per_period text,
    PRIMARY KEY (cycle_id),
    CONSTRAINT ck_cycle_pricing_basis CHECK (pricing_basis IN ('FIXED', 'INDEX', 'HYBRID')),
    CONSTRAINT ck_cycle_pricing_cadence CHECK (duration_cadence IN (
        'FULL_YEAR', 'SEASONAL', 'TIMEFRAMES', 'PERIOD_BY_PERIOD', 'QUARTERLY', 'MONTHLY', 'WEEKLY')),
    CONSTRAINT ck_cycle_pricing_routing CHECK (
        routing_basis IS NULL OR routing_basis IN ('FOB', 'DELIVERED', 'XDOCK', 'CBS_FREIGHT')),
    CONSTRAINT ck_cycle_pricing_cadence_n_positive CHECK (cadence_n IS NULL OR cadence_n > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- ---------------------------------------------------------------------------
-- 4. cyc.cycle_scope_item — item-level participation (D9). `participates` is the manual
--    signal-from-noise switch: heterogeneous products are scoped in/out here, not by forking the
--    pricing structure. GTIN-grain rows carry a gtin_code; subcommodity-grain rows do not, so the
--    PK coalesces gtin to a sentinel for uniqueness.
--    lot_id is left unconstrained (varchar): persistent norm.lot is a LATER migration (M2/G8); the
--    column is here now so participation can reference a lot once that table lands.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_scope_item (
    cycle_id          varchar(36)  NOT NULL,
    subcommodity_code text         NOT NULL,
    gtin_code         text         NOT NULL DEFAULT '',
    participates      boolean      NOT NULL DEFAULT false,
    lot_id            varchar(36),
    projected_volume  numeric(18, 3),
    PRIMARY KEY (cycle_id, subcommodity_code, gtin_code),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
CREATE INDEX IF NOT EXISTS ix_cycle_scope_item_participates
    ON cyc.cycle_scope_item (cycle_id, participates);

-- ---------------------------------------------------------------------------
-- 5. cyc.cycle_pba_term — PBA governance.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_pba_term (
    cycle_id    varchar(36) NOT NULL,
    metric      text        NOT NULL,
    threshold   text        NOT NULL,
    enforcement text,
    PRIMARY KEY (cycle_id, metric),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- ---------------------------------------------------------------------------
-- 6. cyc.cycle_commercial_term — working capital / KPM / other.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_commercial_term (
    cycle_id      varchar(36)    NOT NULL,
    term_type     text           NOT NULL,
    target_value  text,
    benefit_value numeric(18, 2),
    treatment     text,
    note          text,
    PRIMARY KEY (cycle_id, term_type),
    CONSTRAINT ck_cycle_commercial_term_type CHECK (
        term_type IN ('WORKING_CAPITAL', 'KPM', 'OTHER')),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- ---------------------------------------------------------------------------
-- 7. cyc.cycle_rfi_question — configurable RFI set; stable codes for cross-cycle comparability.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_rfi_question (
    cycle_id      varchar(36) NOT NULL,
    question_code text        NOT NULL,
    question_text text        NOT NULL,
    answer_type   text,
    seq           integer     NOT NULL,
    PRIMARY KEY (cycle_id, question_code),
    CONSTRAINT ck_cycle_rfi_answer_type CHECK (
        answer_type IS NULL OR answer_type IN ('TEXT', 'PCT', 'BOOL', 'ENUM')),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- ---------------------------------------------------------------------------
-- 8. cyc.cycle_timeline_event — the "Next Steps" rail (E-16). Drives the rendered process.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_timeline_event (
    cycle_id           varchar(36) NOT NULL,
    event_seq          integer     NOT NULL,
    event_name         text        NOT NULL,
    event_date         date,
    is_leadership_gate boolean     NOT NULL DEFAULT false,
    round_no           integer,
    bcg_support_needed boolean     NOT NULL DEFAULT false,
    PRIMARY KEY (cycle_id, event_seq),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- ---------------------------------------------------------------------------
-- 9. cyc.cycle_narrative — versioned rich text; never field-ified.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyc.cycle_narrative (
    cycle_id       varchar(36) NOT NULL,
    narrative_type text        NOT NULL,
    version        integer     NOT NULL DEFAULT 1,
    body_richtext  text        NOT NULL,
    authored_by    varchar(120),
    authored_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (cycle_id, narrative_type, version),
    CONSTRAINT ck_cycle_narrative_type CHECK (narrative_type IN (
        'BACKGROUND', 'DATA_DIVE', 'INDUSTRY_INSIGHTS', 'CATEGORY_STRATEGY',
        'SOURCING_STRATEGY', 'GENERAL_GOALS', 'APPENDIX_LINK')),
    CONSTRAINT ck_cycle_narrative_version_positive CHECK (version > 0),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);

-- ---------------------------------------------------------------------------
-- 10. EXTEND the existing cyc.cycle_invited_supplier with is_incumbent (denominator: N total,
--     X incumbent, Y non-incumbent). The table already exists in the M0 baseline.
-- ---------------------------------------------------------------------------
ALTER TABLE cyc.cycle_invited_supplier
    ADD COLUMN IF NOT EXISTS is_incumbent boolean NOT NULL DEFAULT false;
"""


DOWNGRADE_SQL = """
ALTER TABLE cyc.cycle_invited_supplier DROP COLUMN IF EXISTS is_incumbent;

DROP TABLE IF EXISTS cyc.cycle_narrative;
DROP TABLE IF EXISTS cyc.cycle_timeline_event;
DROP TABLE IF EXISTS cyc.cycle_rfi_question;
DROP TABLE IF EXISTS cyc.cycle_commercial_term;
DROP TABLE IF EXISTS cyc.cycle_pba_term;
DROP TABLE IF EXISTS cyc.cycle_scope_item;
DROP TABLE IF EXISTS cyc.cycle_pricing;
DROP TABLE IF EXISTS cyc.cycle_objective;

ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS dcs_scope;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS prior_structure_note;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS tf_end_calendar;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS tf_start_calendar;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS tf_end_fiscal;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS tf_start_fiscal;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS horizon_label;
ALTER TABLE cyc.cycle DROP COLUMN IF EXISTS annual_spend;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
