"""eng — the engine runner's sealed decision-support output spine (D19 prototype fidelity).

Revision ID: 0008_eng_analysis_run
Revises: 0007_bid_components
Create Date: 2026-06-19

ADDITIVE, on top of the M0 baseline (frozen). Owned by the Engine & Domain squad.

WHY (ENG-PLAN §3, ADR-0006, D19):
  The engine runner (`app/domain/eng/runner.py`) reads a cycle's bids + strategy config +
  incumbents/volumes from the governed store BY KEY, assembles the frozen `EngineInputs`, calls
  the pure `V3Engine.run`, and SEALS the result. The M0 baseline carries the heavyweight governed
  solver spine (`eng.calculation_run` + `eng.scenario` + `eng.scenario_award`) whose AWARDED rows
  require the full eligibility/landed-cost chain (`upstream_eligibility_result_id`, `cell_spend>0`,
  version-pin quads). For the decision-support prototype the runner needs a LIGHTWEIGHT sealed
  output spine that records the same audit-grade facts (a hashed input/output manifest, the engine
  version pin, is_sealed) plus the per-bid 5-factor scores and the A-G lenses with SPLIT awards —
  without the solver chain. These four tables are that spine, FK'd into the SAME governed cyc/ref
  keys so the outputs are real rows in the governed store, not a side file.

  Decision-support only (ADR-0006): an `analysis_scenario_award` row RECOMMENDS a split; it never
  asserts the award. The real award lands in `awd.*` only after a human selects a scenario.

WHAT (all additive, idempotent):
  * eng.analysis_run            — one sealed run per (cycle, round, engine call). Hashed
                                  input/output manifests (sha256 of the canonical inputs/outputs),
                                  engine version pin, is_sealed, run timestamps. FK -> cyc.cycle /
                                  cyc.cycle_round.
  * eng.bid_score               — the five banded factors -> rec_score per scored bid line, with
                                  eligibility + gate flags. FK -> eng.analysis_run.
  * eng.analysis_scenario       — the A-G lens headers (code + decision-support label). One row per
                                  lens per run. FK -> eng.analysis_run.
  * eng.analysis_scenario_award — the SPLIT award rows: a supplier's share of a (scenario, dc, lot,
                                  tf) cell, carrying volume_share / is_fallback / cap_breach_flag
                                  (G1/D10). Per-supplier grain so a cell may hold N suppliers. FK ->
                                  eng.analysis_scenario + the governed ref.dc / cyc.cycle_lot /
                                  cyc.cycle_timeframe / ref.supplier keys.

Downgrade drops the four tables (child-first), so up->down->up is clean. Idempotent raw DDL
(CREATE TABLE IF NOT EXISTS) so re-runs are no-ops.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_eng_analysis_run"
down_revision: str | None = "0007_bid_components"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
-- eng.analysis_run — the sealed decision-support run (hashed manifests + version pin + is_sealed).
CREATE TABLE IF NOT EXISTS eng.analysis_run (
    analysis_run_id      varchar(36)  NOT NULL,
    cycle_id             varchar(36)  NOT NULL,
    round_id             varchar(36)  NOT NULL,
    engine_version       varchar(60)  NOT NULL,
    config_preset        varchar(40)  NOT NULL,
    status               text         NOT NULL,
    is_sealed            boolean      NOT NULL DEFAULT false,
    input_hash_manifest  varchar(128) NOT NULL,
    output_hash_manifest varchar(128) NOT NULL,
    run_started_at       timestamp    NOT NULL,
    run_finished_at      timestamp    NOT NULL,
    run_by               varchar(120) NOT NULL,
    PRIMARY KEY (analysis_run_id),
    CONSTRAINT uq_analysis_run_identity UNIQUE (analysis_run_id, cycle_id, round_id),
    CONSTRAINT ck_analysis_run_input_hash_len  CHECK (length(input_hash_manifest)  >= 8),
    CONSTRAINT ck_analysis_run_output_hash_len CHECK (length(output_hash_manifest) >= 8),
    CONSTRAINT ck_analysis_run_sealed_finished CHECK (
        is_sealed = false OR run_finished_at IS NOT NULL),
    CONSTRAINT fk_analysis_run_round_in_cycle FOREIGN KEY (round_id, cycle_id)
        REFERENCES cyc.cycle_round (round_id, cycle_id),
    FOREIGN KEY (cycle_id) REFERENCES cyc.cycle (cycle_id)
);
COMMENT ON TABLE eng.analysis_run IS
    'Engine runner sealed decision-support run: hashed input/output manifest + engine version pin '
    '+ is_sealed. Append-only / immutable once sealed (ADR-0006).';

-- eng.bid_score — the five banded factors -> rec_score per scored bid (decision-support output).
CREATE TABLE IF NOT EXISTS eng.bid_score (
    bid_score_id      varchar(36)    NOT NULL,
    analysis_run_id   varchar(36)    NOT NULL,
    bid_line_id       varchar(36)    NOT NULL,
    supplier_id       varchar(36)    NOT NULL,
    dc_id             varchar(36)    NOT NULL,
    lot_id            varchar(36)    NOT NULL,
    tf_id             varchar(36)    NOT NULL,
    price_score       numeric(9, 4)  NOT NULL,
    coverage_score    numeric(9, 4)  NOT NULL,
    hist_score        numeric(9, 4)  NOT NULL,
    zrisk_score       numeric(9, 4)  NOT NULL,
    continuity_score  numeric(9, 4)  NOT NULL,
    rec_score         numeric(9, 4)  NOT NULL,
    is_eligible       boolean        NOT NULL,
    gate_flags        text,
    PRIMARY KEY (bid_score_id),
    CONSTRAINT uq_bid_score_per_run_line UNIQUE (analysis_run_id, bid_line_id),
    CONSTRAINT fk_bid_score_run FOREIGN KEY (analysis_run_id)
        REFERENCES eng.analysis_run (analysis_run_id)
);

-- eng.analysis_scenario — the A-G lens headers (decision-support label, never an assertion).
CREATE TABLE IF NOT EXISTS eng.analysis_scenario (
    analysis_scenario_id varchar(36)  NOT NULL,
    analysis_run_id      varchar(36)  NOT NULL,
    scenario_code        varchar(4)   NOT NULL,
    label                varchar(160) NOT NULL,
    description          text,
    objective_total_spend numeric(18, 6),
    PRIMARY KEY (analysis_scenario_id),
    CONSTRAINT uq_analysis_scenario_per_run_code UNIQUE (analysis_run_id, scenario_code),
    CONSTRAINT fk_analysis_scenario_run FOREIGN KEY (analysis_run_id)
        REFERENCES eng.analysis_run (analysis_run_id)
);

-- eng.analysis_scenario_award — the SPLIT award rows (per-supplier cell grain; G1/D10 columns).
CREATE TABLE IF NOT EXISTS eng.analysis_scenario_award (
    award_id             varchar(36)    NOT NULL,
    analysis_scenario_id varchar(36)    NOT NULL,
    dc_id                varchar(36)    NOT NULL,
    lot_id               varchar(36)    NOT NULL,
    tf_id                varchar(36)    NOT NULL,
    supplier_id          varchar(36)    NOT NULL,
    volume_share         numeric(9, 6)  NOT NULL,
    awarded_price        numeric(18, 6) NOT NULL,
    is_recommended       boolean        NOT NULL DEFAULT false,
    is_fallback          boolean        NOT NULL DEFAULT false,
    cap_breach_flag      boolean        NOT NULL DEFAULT false,
    PRIMARY KEY (award_id),
    CONSTRAINT uq_analysis_award_cell_supplier
        UNIQUE (analysis_scenario_id, dc_id, lot_id, tf_id, supplier_id),
    CONSTRAINT ck_analysis_award_volume_share_range
        CHECK (volume_share >= 0 AND volume_share <= 1),
    CONSTRAINT ck_analysis_award_price_positive CHECK (awarded_price > 0),
    CONSTRAINT fk_analysis_award_scenario FOREIGN KEY (analysis_scenario_id)
        REFERENCES eng.analysis_scenario (analysis_scenario_id),
    CONSTRAINT fk_analysis_award_lot_in_cycle FOREIGN KEY (lot_id)
        REFERENCES cyc.cycle_lot (lot_id),
    CONSTRAINT fk_analysis_award_tf_in_cycle FOREIGN KEY (tf_id)
        REFERENCES cyc.cycle_timeframe (tf_id),
    FOREIGN KEY (dc_id) REFERENCES ref.dc (dc_id),
    FOREIGN KEY (supplier_id) REFERENCES ref.supplier (supplier_id)
);
COMMENT ON COLUMN eng.analysis_scenario_award.volume_share IS
    'Per-supplier cell volume fraction (split allocation, V3 §4 / D10). RECOMMENDS a split; the '
    'award is asserted only in awd.* after a human selects a scenario (ADR-0006).';
"""


DOWNGRADE_SQL = """
DROP TABLE IF EXISTS eng.analysis_scenario_award;
DROP TABLE IF EXISTS eng.analysis_scenario;
DROP TABLE IF EXISTS eng.bid_score;
DROP TABLE IF EXISTS eng.analysis_run;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
