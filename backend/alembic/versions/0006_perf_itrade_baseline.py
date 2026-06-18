"""perf.itrade_receipt reconciled to the real 43-col feed + actual-paid baseline view (E-08 / D11).

Revision ID: 0006_perf_itrade_baseline
Revises: 0005_eng_scenario_award_split
Create Date: 2026-06-18

ADDITIVE, on top of the M0 baseline (frozen).

perf.itrade_receipt is NOT in the M0 baseline (it is deferred to M4/G6), so this migration CREATEs
it at the real 43-column structure observed in FEEDS_ITRADE.md (a real iTrade export). Columns are
grouped per that doc: identity, lineage, the 7-date chain, vendor/origin, performance (qty
shipped/received, QC reject), cost components, flags, and fiscal stamping. (The ALTER ... ADD COLUMN
IF NOT EXISTS pattern in the prompt is honored too — the CREATE is guarded IF NOT EXISTS and a tail
block ADDs each column idempotently, so re-running against an already-present table reconciles it.)

D11 savings baseline — perf.v_itrade_actual_paid_baseline: a VIEW deriving the VOLUME-WEIGHTED
AVERAGE actual-paid per lot×DC×fiscal_period. iTrade receipts carry no RFP `lot_id` (lots are an RFP
construct); the receipt's natural anchor is `subcommodity_desc` (FEEDS_ITRADE.md col 2 — "the
anchor"), which is what lots are built over, so the view groups by subcommodity_desc × dc_no ×
fiscal_year × period and labels that grain the lot×DC×fiscal_period baseline. Actual-paid =
`cogs` (the cost actually booked), volume-weighted by `qty_received`; the view also keeps min/max
of cogs for the contracted-vs-paid context story (D11 keeps min/max too). Canceled / zero-cost /
zero-qty rows (the flag-first gate) are excluded.

Idempotent raw DDL; real downgrade drops the view then the table so up->down->up stays clean.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_perf_itrade_baseline"
down_revision: str | None = "0005_eng_scenario_award_split"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
-- ---------------------------------------------------------------------------
-- perf.itrade_receipt — the 43-column real iTrade "Data" structure (FEEDS_ITRADE.md).
-- One row per receipt line. Resolved identity FKs (commodity/dc/item/supplier) are NOT enforced
-- here: identity resolution is the importer's job (Vendor/UPC → alias → quarantine, never guess),
-- so the raw text columns are persisted and resolution happens downstream.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perf.itrade_receipt (
    receipt_id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    -- identity (cols 1-2, 12-21)
    commodity_desc          text,
    subcommodity_desc       text,                          -- col 2: the anchor (→ ref.subcommodity)
    dc_no                   varchar(40),                   -- col 12 (→ ref.dc)
    dc_name                 text,
    case_size               text,
    item_gross_weight       numeric(18, 6),
    case_net_weight         numeric(18, 6),
    ship_pack_qty           numeric(18, 3),
    warehouse_ship_pack_qty numeric(18, 3),
    upc                     varchar(40),                   -- col 20 (→ ref.item via alias)
    warehouse_desc          text,
    -- lineage (cols 3-4, 14, 31)
    po_number               varchar(80),
    po_purchase_order_no    varchar(80),
    line_no                 integer,
    field_buying_office     text,
    -- the 7-date chain (cols 5-11)
    po_creation_date        date,
    po_arrival_date         date,
    received_date           date,
    ship_date_request       date,
    p200_final_sent_date    date,
    ship_date_indicated     date,
    ship_date_recorded      date,
    -- vendor / origin (cols 22-26)
    supplier_name           text,                          -- col 22 (→ ref.supplier_alias)
    ship_from_address       text,
    ship_from_state         varchar(8),                    -- col 24: ship-from, NOT grow-origin
    ship_from_zip           varchar(16),                   -- col 25: freight proxy via ref.zip_centroid
    routing                 text,                          -- Delivered / FOB / ...
    -- performance (cols 27-29)
    qty_received            numeric(18, 3),
    qty_shipped             numeric(18, 3),
    qc_reject_qty           numeric(18, 3),
    -- cost (cols 30, 32-35, 43)
    final_price_fob         numeric(18, 6),                -- col 30 (FOB)
    freight                 numeric(18, 6),
    total_w_freight         numeric(18, 6),                -- delivered
    xdock_charges           numeric(18, 6),
    total_xdock             numeric(18, 6),
    cogs                    numeric(18, 6),                -- col 43: cost actually booked
    -- flags (cols 36-38) — the flag-first gate
    flag_canceled           boolean      NOT NULL DEFAULT false,
    flag_zero_cost          boolean      NOT NULL DEFAULT false,
    flag_zero_qty           boolean      NOT NULL DEFAULT false,
    -- fiscal stamping (cols 39-42)
    fiscal_ypw              varchar(40),                   -- composite Year/Period/Week
    fiscal_year             integer,
    period                  integer,
    week_of_year            integer,
    -- ingestion lineage
    ingestion_run_id        varchar(36),
    source_artifact         text,
    source_row              integer,
    created_at              timestamptz  NOT NULL DEFAULT now()
);

-- Reconcile pattern (idempotent): ensure each real column exists even if an earlier/partial
-- itrade_receipt was already present. ADD COLUMN IF NOT EXISTS is a no-op when present.
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS commodity_desc          text;
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS subcommodity_desc       text;
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS dc_no                   varchar(40);
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS qty_received            numeric(18, 3);
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS qty_shipped             numeric(18, 3);
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS qc_reject_qty           numeric(18, 3);
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS final_price_fob         numeric(18, 6);
ALTER TABLE perf.itrade_receipt ADD COLUMN IF NOT EXISTS cogs                    numeric(18, 6);

CREATE INDEX IF NOT EXISTS ix_itrade_receipt_grain
    ON perf.itrade_receipt (subcommodity_desc, dc_no, fiscal_year, period);
CREATE INDEX IF NOT EXISTS ix_itrade_receipt_supplier
    ON perf.itrade_receipt (supplier_name);
COMMENT ON TABLE perf.itrade_receipt IS
    'Real 43-col iTrade "Data" feed (FEEDS_ITRADE.md / E-08). One feed, two jobs: historical cost + scorecard.';

-- ---------------------------------------------------------------------------
-- perf.v_itrade_actual_paid_baseline — the D11 savings baseline.
-- Volume-weighted average ACTUAL-PAID (cogs) per lot×DC×fiscal_period, with min/max for context.
-- "lot" grain = subcommodity_desc (the iTrade anchor lots are built over). Flag-first exclusion.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW perf.v_itrade_actual_paid_baseline AS
SELECT
    r.subcommodity_desc                                   AS lot_anchor,
    r.dc_no,
    r.fiscal_year,
    r.period                                              AS fiscal_period,
    sum(r.qty_received)                                   AS total_qty_received,
    -- volume-weighted average actual-paid (the D11 savings baseline)
    sum(r.cogs * r.qty_received) / NULLIF(sum(r.qty_received), 0)
                                                          AS vwa_actual_paid_per_case,
    -- min/max kept too (D11: contracted-vs-paid context)
    min(r.cogs)                                           AS min_actual_paid_per_case,
    max(r.cogs)                                           AS max_actual_paid_per_case,
    count(*)                                              AS receipt_line_count
FROM perf.itrade_receipt r
WHERE r.flag_canceled = false
  AND r.flag_zero_cost = false
  AND r.flag_zero_qty  = false
  AND r.qty_received IS NOT NULL
  AND r.qty_received > 0
  AND r.cogs IS NOT NULL
GROUP BY r.subcommodity_desc, r.dc_no, r.fiscal_year, r.period;
COMMENT ON VIEW perf.v_itrade_actual_paid_baseline IS
    'D11 savings baseline: volume-weighted average actual-paid (cogs) per lot×DC×fiscal_period; min/max kept.';
"""


DOWNGRADE_SQL = """
DROP VIEW IF EXISTS perf.v_itrade_actual_paid_baseline;
DROP TABLE IF EXISTS perf.itrade_receipt;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
