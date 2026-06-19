"""Build the bid-template `CycleScope` for one round from a resolved `CycleView`.

The inverse companion to `app.cycle.loader.load_cycle`: given the name-resolved `CycleView`
(reconstructed from the governed records, or the demo seed) and a 1-based round number, assemble
the intake `CycleScope` — one `ScopeRow` per DC × lot × item × TF × supplier cell, carrying the
system-owned surrogate KEY IDs (D21) the bid-template generator embeds and the ingester validates.

This recreates the demo's `build_scope(seeded, round_entity)` against a `CycleView`, so the bid
template generator runs identically whether the scope comes from the synthetic demo seed or from a
REAL persisted cycle. The lot↔item grain is one item per lot (`lots[i]` ↔ `items[i]`, the
index-alignment the loader guarantees).
"""

from __future__ import annotations

from app.domain.bid.template_schema import CycleScope, ScopeRow
from app.output.types import CycleView


def build_scope_from_cycle(cycle: CycleView, round_no: int) -> CycleScope:
    """Build the intake `CycleScope` (embedded keys) for ONE round across all cells × suppliers.

    `round_no` is 1-based (the buyer's "Round 1"); it selects `cycle.rounds[round_no - 1]`. Raises
    `ValueError` if the round number is out of range for the cycle (never silently picks a default).
    """

    if not (1 <= round_no <= len(cycle.rounds)):
        raise ValueError(
            f"round {round_no} out of range for cycle {cycle.cycle_code} "
            f"(has {len(cycle.rounds)} round(s))"
        )
    round_entity = cycle.rounds[round_no - 1]

    rows: list[ScopeRow] = []
    for dc in cycle.dcs:
        for li, item in enumerate(cycle.items):
            lot = cycle.lots[li]
            for tf in cycle.tfs:
                for sup in cycle.suppliers:
                    rows.append(
                        ScopeRow(
                            round_code=round_entity.code,
                            bid_type="STANDARD",
                            round_id=round_entity.id,
                            tf_id=tf.id,
                            supplier_id=sup.id,
                            dc_id=dc.id,
                            lot_id=lot.id,
                            item_id=item.id,
                            supplier_label=sup.name,
                            dc_label=dc.name,
                            lot_label=lot.name,
                            item_label=item.name,
                            tf_code=tf.code,
                        )
                    )
    return CycleScope(
        cycle_id=cycle.cycle_id,
        cycle_code=cycle.cycle_code,
        cycle_name=cycle.cycle_name,
        window_label=f"{round_entity.code} window",
        rows=tuple(rows),
    )
