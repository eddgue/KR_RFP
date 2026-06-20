"""bid.bid_line — add supplier-stated lane transit days (standard column-set member).

Revision ID: 0011_bid_transit_days
Revises: 0010_awd_award_versioned
Create Date: 2026-06-20

ADDITIVE. Transit days (origin→DC lane) is a real bid attribute some submissions carry (e.g. the
booking guide records Transit Days per awarded cell). It is a HIDDEN COST surfaced in the analysis
(freshness / lead-time), not an engine scoring factor. Per the "full column set always available"
rule, transit is part of the standard bid column set; it is nullable because not every cycle or
supplier populates it — and when absent the analysis shows no transit (no synthetic proxy).

WHAT:
  * ADD transit_days integer  — supplier-stated lane transit (origin→DC), nullable.

Downgrade drops the column, so up->down->up is clean. Idempotent raw DDL (ADD COLUMN IF NOT EXISTS).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_bid_transit_days"
down_revision: str | None = "0010_awd_award_versioned"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
ALTER TABLE bid.bid_line
    ADD COLUMN IF NOT EXISTS transit_days integer;

COMMENT ON COLUMN bid.bid_line.transit_days IS
    'Supplier-stated lane transit days (origin->DC). Hidden-cost display, not a scoring factor; '
    'nullable — absent when the cycle/supplier did not provide it (no proxy shown).';
"""

DOWNGRADE_SQL = """
ALTER TABLE bid.bid_line DROP COLUMN IF EXISTS transit_days;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
