"""norm attribute taxonomy — one shared catalog + sparse per-lot attributes (D14 / G8).

Revision ID: 0004_norm_attribute_taxonomy
Revises: 0003_cyc_cycle_safety
Create Date: 2026-06-18

ADDITIVE, on top of the M0 baseline (frozen).

D14: it is ONE shared attribute taxonomy (not separate per-commodity schemas). The CATALOG of
attributes is common; which fields are populated varies by item ("not every item has data in every
column"). So:
  * norm.attribute_def  — one superset catalog of attribute definitions (code, label, data type,
                          optional unit + allowed-values + commodity hint). The shared catalog is
                          extended only when a genuinely new attribute appears.
  * norm.lot_attribute  — SPARSE: a lot carries only its applicable attributes (one row per
                          (lot, attribute), value stored in the column matching the def's datatype).

lot_id linkage: the persistent norm.lot store is a LATER migration (M2/G8 — not in the M0 baseline),
so norm.lot_attribute.lot_id is an unconstrained varchar(36) for now. When norm.lot lands, a
follow-up migration can add the FK (additive). attribute_code FKs the catalog so a lot attribute
must reference a defined attribute.

Idempotent raw DDL; real downgrade drops both tables (child first) so up->down->up stays clean.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_norm_attribute_taxonomy"
down_revision: str | None = "0003_cyc_cycle_safety"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_SQL = """
-- ---------------------------------------------------------------------------
-- norm.attribute_def — the one shared superset catalog (D14).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS norm.attribute_def (
    attribute_code  varchar(60)  NOT NULL,
    label           varchar(160) NOT NULL,
    data_type       text         NOT NULL,
    unit            varchar(40),
    allowed_values  text,                    -- for ENUM data_type: delimited/JSON value set
    commodity_hint  varchar(120),            -- optional: where this attribute typically applies
    active_flag     boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    PRIMARY KEY (attribute_code),
    CONSTRAINT ck_attribute_def_data_type CHECK (
        data_type IN ('TEXT', 'NUMERIC', 'BOOL', 'ENUM', 'DATE')),
    CONSTRAINT ck_attribute_def_label_not_empty CHECK (length(label) > 0)
);
COMMENT ON TABLE norm.attribute_def IS
    'One shared, superset attribute catalog (D14). Extended only when a new attribute appears.';

-- ---------------------------------------------------------------------------
-- norm.lot_attribute — SPARSE per-lot attributes (a lot carries only its applicable ones).
-- The value lands in the column matching the attribute_def data_type; all value columns nullable.
-- lot_id is unconstrained (persistent norm.lot is M2/G8; FK added additively when it lands).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS norm.lot_attribute (
    lot_id          varchar(36)  NOT NULL,
    attribute_code  varchar(60)  NOT NULL,
    value_text      text,
    value_numeric   numeric(18, 6),
    value_bool      boolean,
    value_date      date,
    source          text,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    PRIMARY KEY (lot_id, attribute_code),
    FOREIGN KEY (attribute_code) REFERENCES norm.attribute_def (attribute_code)
);
CREATE INDEX IF NOT EXISTS ix_lot_attribute_attribute_code
    ON norm.lot_attribute (attribute_code);
COMMENT ON TABLE norm.lot_attribute IS
    'Sparse per-lot attributes (D14): a lot carries only its applicable shared-catalog attributes.';
"""


DOWNGRADE_SQL = """
DROP TABLE IF EXISTS norm.lot_attribute;
DROP TABLE IF EXISTS norm.attribute_def;
"""


def upgrade() -> None:
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
