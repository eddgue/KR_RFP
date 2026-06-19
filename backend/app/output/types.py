"""Resolved cycle scope the output/generator layer is built on.

`CycleView` is the in-memory, name-resolved view of a cycle's scope (DCs, lots, items,
timeframes, rounds, suppliers, incumbents, projected volumes) that every gather/write step
in the scenario-workbook generator reads. It can be built two ways:

  * the demo's `seed_cycle` (synthetic, in-memory), or
  * `app.cycle.loader.load_cycle` (reconstructed from the governed persisted records),

so the generator runs identically for a synthetic demo cycle and for a REAL persisted cycle.

`SeededCycle` is kept as an alias so the demo's existing call sites keep working.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# ---------------------------------------------------------------------------
# Resolved identity holders
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Entity:
    id: str
    code: str
    name: str


@dataclass
class CycleView:
    cycle_id: str
    cycle_code: str
    cycle_name: str
    client_id: str
    commodity_id: str
    dcs: list[Entity]
    lots: list[Entity]
    items: list[Entity]  # items[i] belongs to lots[i]
    tfs: list[Entity]
    rounds: list[Entity]  # rounds[i].code == "R{i+1}"
    suppliers: list[Entity]
    incumbent_by_dc_lot: dict[tuple[str, str], str]  # (dc_id, lot_id) -> supplier_id
    incumbent_routing: dict[tuple[str, str], Decimal]  # (dc_id, lot_id) -> routing baseline
    period_cases_by_cell: dict[tuple[str, str, str], Decimal]  # (dc_id, lot_id, tf_id) -> cases


# Back-compat alias: the demo seeded this view, so the historical name is kept.
SeededCycle = CycleView
