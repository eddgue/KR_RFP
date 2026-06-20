"""Reconstruct a `CycleView` from the governed persisted records — the inverse of the demo seed.

`load_cycle` reads the SAME governed tables the demo's `seed_cycle` writes (ref.dc / ref.supplier /
ref.item, cyc.cycle / cyc.cycle_lot / cyc.cycle_lot_item / cyc.cycle_timeframe / cyc.cycle_round /
cyc.cycle_projected_volume, perf.historical_award_assignment / perf.historical_awarded_price_basis)
and assembles the name-resolved `CycleView` the scenario-workbook generator is built on. This makes
the generator runnable for a REAL persisted cycle, not just the synthetic in-memory demo seed.

Names are DISPLAY names (D23): `dc_name`, `canonical_name`, item `description`, `lot_name`, and
`tf_name`. Keys (`*_code`) JOIN; names DISPLAY. The lot↔item grain is one item per lot (the
cyc.cycle_lot_item link), so
`lots[i]` and `items[i]` line up by lot order — the index alignment the generator relies on.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.output.types import CycleView, Entity


def load_cycle(session: Session, cycle_id: str) -> CycleView:
    """Reconstruct the resolved `CycleView` for a persisted cycle from its governed records."""

    cycle_row = session.execute(
        text(
            "SELECT c.cycle_code, c.cycle_name, c.commodity_id, m.commodity_name "
            "FROM cyc.cycle c "
            "LEFT JOIN ref.commodity m ON m.id::text = c.commodity_id "
            "WHERE c.cycle_id = :cyc"
        ),
        {"cyc": cycle_id},
    ).one()
    cycle_code, cycle_name, commodity_id, commodity_name = cycle_row

    # DCs in scope — the DCs the cycle carries projected volume for (ref.dc display names, D23).
    dc_rows = session.execute(
        text(
            "SELECT DISTINCT d.dc_id, d.dc_code, d.dc_name "
            "FROM ref.dc d "
            "JOIN cyc.cycle_projected_volume v ON v.dc_id = d.dc_id "
            "WHERE v.cycle_id = :cyc "
            "ORDER BY d.dc_code"
        ),
        {"cyc": cycle_id},
    ).all()
    dcs = [Entity(dc_id, dc_code, dc_name) for dc_id, dc_code, dc_name in dc_rows]

    # Lots + their one item (cyc.cycle_lot_item), ordered by lot_code so lots[i] ↔ items[i].
    lot_rows = session.execute(
        text(
            "SELECT l.lot_id, l.lot_code, l.lot_name, i.item_id, i.item_code, i.description "
            "FROM cyc.cycle_lot l "
            "JOIN cyc.cycle_lot_item li ON li.lot_id = l.lot_id AND li.cycle_id = l.cycle_id "
            "JOIN ref.item i ON i.item_id = li.item_id "
            "WHERE l.cycle_id = :cyc "
            "ORDER BY l.lot_code"
        ),
        {"cyc": cycle_id},
    ).all()
    lots: list[Entity] = []
    items: list[Entity] = []
    item_to_lot: dict[str, str] = {}
    for lot_id, lot_code, lot_name, item_id, item_code, description in lot_rows:
        lots.append(Entity(lot_id, lot_code, lot_name))
        items.append(Entity(item_id, item_code, description))
        item_to_lot[item_id] = lot_id

    # Timeframes (cyc.cycle_timeframe display season names), ordered by tf_code.
    tf_rows = session.execute(
        text(
            "SELECT tf_id, tf_code, tf_name, week_count FROM cyc.cycle_timeframe "
            "WHERE cycle_id = :cyc ORDER BY tf_code"
        ),
        {"cyc": cycle_id},
    ).all()
    tfs = [Entity(tf_id, tf_code, tf_name) for tf_id, tf_code, tf_name, _wc in tf_rows]
    horizon_weeks = sum(int(wc) for *_rest, wc in tf_rows if wc is not None)

    # Rounds (cyc.cycle_round), ordered by round_number; round name synthesized (no name column).
    round_rows = session.execute(
        text(
            "SELECT round_id, round_number, is_final FROM cyc.cycle_round "
            "WHERE cycle_id = :cyc ORDER BY round_number"
        ),
        {"cyc": cycle_id},
    ).all()
    rounds = [
        Entity(
            round_id,
            f"R{round_number}",
            f"Round {round_number}" + (" — Final" if is_final else ""),
        )
        for round_id, round_number, is_final in round_rows
    ]

    # Suppliers invited to the cycle (the submitted-vs-missing denominator), by canonical name.
    sup_rows = session.execute(
        text(
            "SELECT s.supplier_id, s.canonical_name "
            "FROM cyc.cycle_invited_supplier cis "
            "JOIN ref.supplier s ON s.supplier_id = cis.supplier_id "
            "WHERE cis.cycle_id = :cyc "
            "ORDER BY s.canonical_name"
        ),
        {"cyc": cycle_id},
    ).all()
    suppliers = [
        Entity(supplier_id, f"SUP-{i:02d}", canonical_name)
        for i, (supplier_id, canonical_name) in enumerate(sup_rows, start=1)
    ]

    # Projected volumes keyed at (dc, item, tf) -> remap to the engine's (dc, lot, tf) cell grain.
    vol_rows = session.execute(
        text(
            "SELECT dc_id, item_id, tf_id, projected_period_cases "
            "FROM cyc.cycle_projected_volume WHERE cycle_id = :cyc"
        ),
        {"cyc": cycle_id},
    ).all()
    period_cases_by_cell: dict[tuple[str, str, str], Decimal] = {}
    for dc_id, item_id, tf_id, period_cases in vol_rows:
        lot_id = item_to_lot.get(item_id)
        if lot_id is None:
            continue  # item not in any in-scope lot (shouldn't happen for a well-formed cycle)
        period_cases_by_cell[(dc_id, lot_id, tf_id)] = Decimal(str(period_cases))

    # Incumbents (perf.historical_award_assignment, incumbent_flag) -> (dc, lot) -> supplier; and
    # the routing baseline from the preferred perf.historical_awarded_price_basis row (the iTrade
    # baseline, D11). Item -> lot via cycle_lot_item so the incumbent keys land on the engine grain.
    inc_rows = session.execute(
        text(
            "SELECT a.dc_id, a.item_id, a.supplier_id, b.awarded_price_per_case "
            "FROM perf.historical_award_assignment a "
            "LEFT JOIN perf.historical_awarded_price_basis b "
            "  ON b.assignment_id = a.assignment_id AND b.preferred_basis_flag = true "
            "WHERE a.cycle_id = :cyc AND a.incumbent_flag = true"
        ),
        {"cyc": cycle_id},
    ).all()
    incumbent_by_dc_lot: dict[tuple[str, str], str] = {}
    incumbent_routing: dict[tuple[str, str], Decimal] = {}
    for dc_id, item_id, supplier_id, routing in inc_rows:
        lot_id = item_to_lot.get(item_id)
        if lot_id is None:
            continue
        incumbent_by_dc_lot[(dc_id, lot_id)] = supplier_id
        incumbent_routing[(dc_id, lot_id)] = (
            Decimal(str(routing)) if routing is not None else Decimal("0")
        )

    return CycleView(
        cycle_id=cycle_id,
        cycle_code=cycle_code,
        cycle_name=cycle_name,
        client_id="",  # not needed by the generator; left blank for a reconstructed view
        commodity_id=commodity_id,
        dcs=dcs,
        lots=lots,
        items=items,
        tfs=tfs,
        rounds=rounds,
        suppliers=suppliers,
        incumbent_by_dc_lot=incumbent_by_dc_lot,
        incumbent_routing=incumbent_routing,
        period_cases_by_cell=period_cases_by_cell,
        commodity_name=commodity_name or "",
        horizon_weeks=horizon_weeks,
    )
