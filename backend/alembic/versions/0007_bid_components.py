"""bid.bid_line — carry the engine's IN_Bids cost-component set cleanly (D20 round-trip).

Revision ID: 0007_bid_components
Revises: 0006_perf_itrade_baseline
Create Date: 2026-06-19

ADDITIVE, on top of the M0 baseline (frozen). Owned by Platform & Data (the DDL); the bid
intake module owns the contract.

WHY (V3_ENGINE_LOGIC.md §7, CYCLE_FIELDTOMATO_STRUCTURE.md §1.2):
  The engine's IN_Bids cost stack is All-In + { FOB, Delivery Surcharge, VegCool Surcharge,
  Lot Discount }. The baseline bid.bid_line already carries `submitted_all_in_case` and
  `fob_case`, but its other component columns (`freight_case`, `fuel_case`, `accessorial_case`,
  `item_discount_case`, `shrink_case`) are a DIFFERENT, generic landed-cost vocabulary — there is
  no clean home for the engine's *Delivery Surcharge*, *VegCool Surcharge*, or *Lot Discount*.
  Overloading `freight`/`accessorial`/`item_discount` would silently re-map the engine's named
  components and break the round-trip's "components round-trip exactly" guarantee (D20). So this
  migration adds the three missing engine components as their OWN columns, plus a resolved
  price-basis column to record which §7 branch produced the price.

WHAT (all additive, idempotent):
  * ADD delivery_surcharge_case   numeric(18,6)  — engine Delivery Surcharge.
  * ADD vegcool_surcharge_case    numeric(18,6)  — engine VegCool (cold-chain) Surcharge.
  * ADD lot_discount_case         numeric(18,6)  — engine Lot Discount (fallback-only, §7).
  * ADD price_basis_resolved      text           — 'ALL_IN' | 'COMPONENT_FALLBACK' (provenance).
  * ADD CONSTRAINT ck_bid_line_no_double_discount — the §7 double-subtract guard, in the DB:
        when a submitted All-In is present, a Lot Discount must NOT also be populated (the
        ambiguous double-subtract case the ingester quarantines is also a hard CHECK at rest).

Downgrade drops the four columns + the CHECK, so up->down->up is clean. Idempotent raw DDL
(ADD COLUMN IF NOT EXISTS / guarded CHECK add) so re-runs are no-ops.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_bid_components"
down_revision: str | None = "0006_perf_itrade_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE bid.bid_line
    ADD COLUMN IF NOT EXISTS delivery_surcharge_case numeric(18, 6);
ALTER TABLE bid.bid_line
    ADD COLUMN IF NOT EXISTS vegcool_surcharge_case  numeric(18, 6);
ALTER TABLE bid.bid_line
    ADD COLUMN IF NOT EXISTS lot_discount_case       numeric(18, 6);
ALTER TABLE bid.bid_line
    ADD COLUMN IF NOT EXISTS price_basis_resolved    text;

-- The §7 double-subtract guard, enforced at rest: a submitted All-In already net of discounts
-- must not also carry a Lot Discount (the ambiguous recompute). Guarded so re-run is a no-op.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_bid_line_no_double_discount'
    ) THEN
        ALTER TABLE bid.bid_line
            ADD CONSTRAINT ck_bid_line_no_double_discount
            CHECK (
                submitted_all_in_case IS NULL
             OR lot_discount_case IS NULL
             OR lot_discount_case = 0
            );
    END IF;
END
$$;

COMMENT ON COLUMN bid.bid_line.delivery_surcharge_case IS
    'Engine IN_Bids Delivery Surcharge (§7 fallback component).';
COMMENT ON COLUMN bid.bid_line.vegcool_surcharge_case IS
    'Engine IN_Bids VegCool (cold-chain) Surcharge (§7 fallback component).';
COMMENT ON COLUMN bid.bid_line.lot_discount_case IS
    'Engine IN_Bids Lot Discount (§7 fallback-only; never applied when All-In is present).';
COMMENT ON COLUMN bid.bid_line.price_basis_resolved IS
    'Which §7 branch produced Price: ALL_IN (verbatim) or COMPONENT_FALLBACK.';
"""


DOWNGRADE_SQL = """
ALTER TABLE bid.bid_line DROP CONSTRAINT IF EXISTS ck_bid_line_no_double_discount;
ALTER TABLE bid.bid_line DROP COLUMN IF EXISTS price_basis_resolved;
ALTER TABLE bid.bid_line DROP COLUMN IF EXISTS lot_discount_case;
ALTER TABLE bid.bid_line DROP COLUMN IF EXISTS vegcool_surcharge_case;
ALTER TABLE bid.bid_line DROP COLUMN IF EXISTS delivery_surcharge_case;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
