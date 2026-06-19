"""SYNTHETIC scope + resolver builders for the bid intake tests.

100% placeholder data — suppliers SUP-*, DCs DC-*, lots LOT-*, items ITEM-*, TFs TF1/TF2. NO real
prices, supplier names, volumes, or award values (ADR-0001 §4). The scope is engineered so the
round-trip exercises: All-In rows, component-fallback rows, a no-bid row, and an incomplete row.

D21: every grain carries a system-owned surrogate KEY ID (here synthetic, UUID-shaped). The
generated template embeds these keys; ingest validates them against the scope key set. The
display labels are attributes used only for the legacy name-resolver fallback + warn-only checks.
"""

from __future__ import annotations

from app.domain.bid.bid_ingester import StubIdentityResolver
from app.domain.bid.template_schema import CycleScope, ScopeRow

# Synthetic identity tables: (label written in the sheet) -> (system-owned surrogate key id).
_SUPPLIERS = {"Acme Produce": "SUP-1", "Bravo Farms": "SUP-2", "Cresta Growers": "SUP-3"}
_DCS = {"Atlanta DC": "DC-1", "Memphis DC": "DC-2"}
_LOTS = {"Grape Lot": "LOT-1", "Roma Lot": "LOT-2"}
_ITEMS = {"Grape Tomato 1lb": "ITEM-1", "Roma XL 25lb": "ITEM-2"}
_TFS = {"TF1": "TF1", "TF2": "TF2"}

# Cycle/round/TF surrogate key ids (system-owned; embedded in the template by the generator).
CYCLE_ID = "cyc-syn-1"
_ROUND_ID = "ROUND-R1"
_TF_ID = "TFID-1"


def build_resolver() -> StubIdentityResolver:
    """A resolver that knows the synthetic scope's labels (normalized, alias-layer style).

    LEGACY-ONLY (D21): the resolver maps human labels -> ids and is used solely by the legacy
    migration path. OUR template is key-validated and never name-resolved.
    """

    norm = StubIdentityResolver._norm
    return StubIdentityResolver(
        suppliers={norm(k): v for k, v in _SUPPLIERS.items()},
        dcs={norm(k): v for k, v in _DCS.items()},
        lots={norm(k): v for k, v in _LOTS.items()},
        items={norm(k): v for k, v in _ITEMS.items()},
        tfs={norm(k): v for k, v in _TFS.items()},
    )


def _scope_row(supplier: str, dc: str, lot: str, item: str, tf: str) -> ScopeRow:
    return ScopeRow(
        round_code="R1",
        bid_type="Initial FOB",
        round_id=_ROUND_ID,
        tf_id=_TF_ID,
        supplier_id=_SUPPLIERS[supplier],
        dc_id=_DCS[dc],
        lot_id=_LOTS[lot],
        item_id=_ITEMS[item],
        supplier_label=supplier,
        dc_label=dc,
        lot_label=lot,
        item_label=item,
        tf_code=tf,
    )


def build_scope() -> CycleScope:
    """A small synthetic cycle scope: 2 suppliers x 2 DCs x 2 lot/item pairs x 1 TF."""

    rows: list[ScopeRow] = []
    pairs = [("Grape Lot", "Grape Tomato 1lb"), ("Roma Lot", "Roma XL 25lb")]
    for supplier in ("Acme Produce", "Bravo Farms"):
        for dc in ("Atlanta DC", "Memphis DC"):
            for lot, item in pairs:
                rows.append(_scope_row(supplier, dc, lot, item, "TF1"))
    return CycleScope(
        cycle_id=CYCLE_ID,
        cycle_code="SYN-2026",
        cycle_name="Synthetic Tomato 2026",
        window_label="June 21 - August 15, 2026",
        rows=tuple(rows),
    )
