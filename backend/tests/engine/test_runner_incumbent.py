"""Regression test for incumbent flagging in the engine runner.

The runner used to hardcode `is_incumbent=False` on every assembled bid, so the §2.5 continuity
factor (incumbent -> 100) was inert no matter the weight. This test pins the fix: a bid whose
(dc, lot, supplier) matches a cycle incumbent is flagged `is_incumbent`, and others are not.

Pure test — `_assemble_bids` reads only its arguments (no DB), so we drive it with lightweight
stand-ins for the persisted bid lines.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from app.domain.eng.runner import EngineRunner


def _line(bid_id: str, supplier: str, dc: str, item: str) -> SimpleNamespace:
    return SimpleNamespace(
        bid_line_id=bid_id,
        supplier_id=supplier,
        dc_id=dc,
        lot_id="LOT_FALLBACK",
        item_id=item,
        tf_id="TFID1",
        submitted_all_in_case=Decimal("10.00"),
        fob_case=None,
        delivery_surcharge_case=None,
        vegcool_surcharge_case=None,
        lot_discount_case=None,
        is_scoreable=True,
        volume_minimum_cases=None,
    )


def test_assemble_bids_flags_only_the_incumbent_cell() -> None:
    runner = EngineRunner.__new__(EngineRunner)  # no session needed for _assemble_bids
    lines = [
        _line("b-inc", "SUP_INCUMBENT", "DC1", "ITEM1"),
        _line("b-chal", "SUP_CHALLENGER", "DC1", "ITEM1"),
        _line("b-other-dc", "SUP_INCUMBENT", "DC2", "ITEM1"),  # same supplier, different cell
    ]
    tf_code_by_id = {"TFID1": "TF1"}
    lot_by_item = {"ITEM1": "LT1"}
    incumbent_keys = {("DC1", "LT1", "SUP_INCUMBENT")}

    assembled = runner._assemble_bids(lines, tf_code_by_id, lot_by_item, incumbent_keys)  # type: ignore[arg-type]
    bids = {b.bid_id: b for b in assembled}

    assert bids["b-inc"].is_incumbent is True
    assert bids["b-chal"].is_incumbent is False
    # same supplier but a DC that is NOT its incumbent cell -> not flagged
    assert bids["b-other-dc"].is_incumbent is False


def test_assemble_bids_no_incumbents_flags_nothing() -> None:
    runner = EngineRunner.__new__(EngineRunner)
    lines = [_line("b1", "SUP_A", "DC1", "ITEM1")]
    bids = runner._assemble_bids(lines, {"TFID1": "TF1"}, {"ITEM1": "LT1"}, set())  # type: ignore[arg-type]
    assert bids[0].is_incumbent is False
