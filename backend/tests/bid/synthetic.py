"""SYNTHETIC scope + resolver builders for the bid intake tests.

100% placeholder data — suppliers SUP-*, DCs DC-*, lots LOT-*, items ITEM-*, TFs TF1/TF2. NO real
prices, supplier names, volumes, or award values (ADR-0001 §4). The scope is engineered so the
round-trip exercises: All-In rows, component-fallback rows, a no-bid row, and an incomplete row.
"""

from __future__ import annotations

from app.domain.bid.bid_ingester import StubIdentityResolver
from app.domain.bid.template_schema import CycleScope, ScopeRow

# Synthetic identity tables: (label written in the sheet) -> (canonical store id).
_SUPPLIERS = {"Acme Produce": "SUP-1", "Bravo Farms": "SUP-2", "Cresta Growers": "SUP-3"}
_DCS = {"Atlanta DC": "DC-1", "Memphis DC": "DC-2"}
_LOTS = {"Grape Lot": "LOT-1", "Roma Lot": "LOT-2"}
_ITEMS = {"Grape Tomato 1lb": "ITEM-1", "Roma XL 25lb": "ITEM-2"}
_TFS = {"TF1": "TF1", "TF2": "TF2"}


def build_resolver() -> StubIdentityResolver:
    """A resolver that knows the synthetic scope's labels (normalized, alias-layer style)."""

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
        supplier_id=_SUPPLIERS[supplier],
        supplier_label=supplier,
        dc_id=_DCS[dc],
        dc_label=dc,
        lot_id=_LOTS[lot],
        lot_label=lot,
        item_id=_ITEMS[item],
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
        cycle_id="cyc-syn-1",
        cycle_code="SYN-2026",
        cycle_name="Synthetic Tomato 2026",
        window_label="June 21 - August 15, 2026",
        rows=tuple(rows),
    )
