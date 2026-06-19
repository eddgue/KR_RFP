"""The SYNTHETIC, committable golden fixture (GOLDEN_MASTER.md §4).

100% placeholder data — suppliers S.., DCs DC.., lots LT.., TFs TF1/TF2. NO real prices,
supplier names, volumes, or award values. Engineered so that every band edge and every branch
of V3_ENGINE_LOGIC.md fires at least once, so passing it proves the lifted logic without
exposing data (the Phase-D exit gate, ADR-0006 / S2).

The expected outputs live in `golden_expectations.json`, derived independently from the spec's
band TABLES (logic, exactly reproduced in our spec) — NOT from our engine and NOT from the
quarantined v3 (clean-room, ADR-0001). The test asserts our engine reproduces them.

DESIGN — band isolation. Each band-edge bid sits in its OWN 2-bid group: an "anchor" bid that
fixes the group min/avg and the edge bid at the target premium. With exactly two bids the
Z-score is +/-1.0 (in [-1,1] -> z-risk 100), and coverage is held at 100, so the edge bid's
RecScore isolates the factor under test. (The 2-bidder group raises the advisory
"Low bidder count" flag — advisory only, it never changes eligibility.) Separate cells exercise
the split allocator (D), concentration, the cost-construction paths, and the scenario rules.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.interface import (
    BidComponents,
    BidInput,
    CustomOverrideRule,
    EngineConfig,
    EngineInputs,
    ExclusionRule,
    IncumbentBaseline,
    PreferredRule,
    ScenarioCode,
    VolumeRequirement,
    WeightPreset,
)

_D = Decimal


def _bid(
    bid_id: str,
    supplier: str,
    dc: str,
    lot: str,
    tf: str,
    price: str | None,
    *,
    total_vol: str | None = "100",
    is_incumbent: bool = False,
    is_as_needed: bool = False,
    components: BidComponents | None = None,
) -> BidInput:
    return BidInput(
        bid_id=bid_id,
        supplier_id=supplier,
        dc_no=dc,
        lot_id=lot,
        tf_code=tf,
        landed_cost_per_case=_D(price) if price is not None else _D("0"),
        total_vol_offered=_D(total_vol) if total_vol is not None else None,
        is_incumbent=is_incumbent,
        is_as_needed=is_as_needed,
        components=components,
    )


def _config(*, single_round: bool = False) -> EngineConfig:
    return EngineConfig(
        preset=WeightPreset.BALANCED,
        weight_price=_D("0.35"),
        weight_coverage=_D("0.25"),
        weight_historical=_D("0.20"),
        weight_zrisk=_D("0.10"),
        weight_continuity=_D("0.10"),
        max_sup_dc=2,
        conc_thresh=_D("0.40"),
        global_premium_threshold=_D("0.12"),
        coverage_floor=_D("0.80"),
        active_tf_codes=("TF1",),
        final_round_code="R1" if single_round else "R2",
        prior_round_code=None if single_round else "R1",
        lenses=(
            ScenarioCode.A,
            ScenarioCode.B,
            ScenarioCode.C,
            ScenarioCode.D,
            ScenarioCode.E,
            ScenarioCode.F,
            ScenarioCode.G,
        ),
        exclusions=(ExclusionRule(supplier_id="SX0"),),
        custom_overrides=(
            CustomOverrideRule(dc_no="DC20", lot_id="LT01", tf_code="TF1", supplier_id="S32"),
        ),
        preferred_rules=(
            PreferredRule(lot_id="LT01", supplier_id="S32", dc_no="DC20", tf_code="TF1"),
            # A preferred rule with NO eligible bid -> exception path, keeps B's pick.
            PreferredRule(lot_id="LT99", supplier_id="S_NONE"),
        ),
    )


def build_inputs(*, single_round: bool = False) -> EngineInputs:
    """Construct the synthetic golden EngineInputs (multi-round by default)."""

    bids: list[BidInput] = []
    volumes: list[VolumeRequirement] = []
    incumbents: list[IncumbentBaseline] = []

    def req(dc: str, lot: str, total: str = "100") -> None:
        volumes.append(
            VolumeRequirement(dc_no=dc, lot_id=lot, tf_code="TF1", total_volume=_D(total))
        )

    # === PRICE-band edges (anchor at 100, edge bid at the target premium). ========
    # Each in its own lot LP01..LP07 in DC10. anchor=100 -> group min 100;
    # PremVsLow = (edge-100)/100. cov=100, hist=50 (no baseline), z=+/-1 -> 100.
    price_edges = [
        ("LP01", "100.00", "S101"),  # 0%     -> 100
        ("LP02", "103.00", "S102"),  # 3%     -> 100
        ("LP03", "103.01", "S103"),  # 3.01%  -> 80
        ("LP04", "107.00", "S104"),  # 7%     -> 80
        ("LP05", "107.01", "S105"),  # 7.01%  -> 50
        ("LP06", "112.00", "S106"),  # 12%    -> 50
        ("LP07", "112.01", "S107"),  # 12.01% -> 20 (also breaches premium ceiling)
    ]
    for lot, edge_price, sup in price_edges:
        bids.append(_bid(f"b_pe_{lot}", "S100", "DC10", lot, "TF1", "100.00"))
        bids.append(_bid(f"b_pe_{lot}_e", sup, "DC10", lot, "TF1", edge_price))
        req("DC10", lot)

    # === COVERAGE-band edges (price held ~ at min -> price 100; vary vol vs 100). ==
    # anchor at exactly 100 (group min); edge bid at 100.00 too (PremVsLow 0 -> 100).
    cov_edges = [
        ("LC01", "49", 0),  # .49 -> 0
        ("LC02", "50", 40),  # .50 -> 40
        ("LC03", "79", 40),  # .79 -> 40
        ("LC04", "80", 70),  # .80 -> 70
        ("LC05", "99", 70),  # .99 -> 70
        ("LC06", "100", 100),  # 1.00 -> 100
        ("LC07", "120", 100),  # 1.20 -> 100
        ("LC08", "121", 95),  # 1.21 -> 95
    ]
    for lot, vol, _exp in cov_edges:
        bids.append(_bid(f"b_cov_{lot}", "S110", "DC11", lot, "TF1", "100.00", total_vol="100"))
        bids.append(_bid(f"b_cov_{lot}_e", "S111", "DC11", lot, "TF1", "100.00", total_vol=vol))
        req("DC11", lot)
    # NaN coverage (no vol offered) -> 30; As-Needed -> 70.
    bids.append(_bid("b_cov_nan_a", "S112", "DC11", "LC09", "TF1", "100.00", total_vol="100"))
    bids.append(_bid("b_cov_nan_e", "S113", "DC11", "LC09", "TF1", "100.00", total_vol=None))
    req("DC11", "LC09")
    bids.append(_bid("b_cov_an_a", "S114", "DC11", "LC10", "TF1", "100.00", total_vol="100"))
    bids.append(
        _bid("b_cov_an_e", "S115", "DC11", "LC10", "TF1", "100.00", is_as_needed=True)
    )
    req("DC11", "LC10")

    # === HISTORICAL-band edges vs incumbent routing baseline 100.00. ==============
    # anchor at 100 fixes group min; edge bid at the target delta. price score on the
    # edge bid follows PremVsLow off 100, so we pick prices that ALSO keep premium
    # under control (negative deltas have premium 0; positive deltas note premium).
    hist_edges = [
        ("LH01", "89.00", "S121"),  # -.11 -> 100 (edge below anchor: group min=89)
        ("LH02", "90.00", "S122"),  # -.10 -> 100
        ("LH03", "97.00", "S123"),  # -.03 -> 85
        ("LH04", "103.00", "S124"),  # +.03 -> 70
        ("LH05", "107.00", "S125"),  # +.07 -> 45
        ("LH06", "108.00", "S126"),  # +.08 -> 20
    ]
    for lot, edge_price, sup in hist_edges:
        # anchor equals the edge price so the group min == edge price => PremVsLow 0
        # (price 100) and Z=+/-... we make the anchor EQUAL so std=0 -> z None -> 100,
        # and premium 0 -> price 100, isolating the historical factor exactly.
        bids.append(_bid(f"b_h_{lot}", sup, "DC12", lot, "TF1", edge_price))
        bids.append(_bid(f"b_h_{lot}_t", f"{sup}b", "DC12", lot, "TF1", edge_price))
        incumbents.append(
            IncumbentBaseline(
                dc_no="DC12", lot_id=lot, supplier_id="INC", routing_cost_per_case=_D("100.00")
            )
        )
        req("DC12", lot)
    # No-baseline lot -> historical 50.
    bids.append(_bid("b_h_nobase", "S127", "DC12", "LH07", "TF1", "100.00"))
    bids.append(_bid("b_h_nobase2", "S128", "DC12", "LH07", "TF1", "100.00"))
    req("DC12", "LH07")

    # === Z-RISK outliers. A symmetric cluster caps |Z| at sqrt(7/2)~1.87, so we use
    # an ASYMMETRIC cluster (8 tight + 1 outlier) so the lone outlier clears |Z|>2.
    # LZ01: 8 @ 100 + 1 deep-low (60) -> Z_low ~ -2.83 -> 60.
    for i in range(1, 9):
        bids.append(_bid(f"b_zl{i}", f"S13{i:02d}", "DC13", "LZ01", "TF1", "100.00"))
    bids.append(_bid("b_zlow", "S1399", "DC13", "LZ01", "TF1", "60.00"))  # Z<-2 -> 60
    req("DC13", "LZ01")
    # LZ02: 8 @ 100 + 1 high (140) -> Z_high ~ +2.83 -> 40 (and premium breach).
    for i in range(1, 9):
        bids.append(_bid(f"b_zh{i}", f"S14{i:02d}", "DC13", "LZ02", "TF1", "100.00"))
    bids.append(_bid("b_zhigh", "S1499", "DC13", "LZ02", "TF1", "140.00"))  # Z>+2 -> 40
    req("DC13", "LZ02")

    # === SCENARIO D split: DC20/TF1, 3 suppliers across 4 lots. ===================
    # S31 strong on LT01/LT02, S32 strong on LT03; S33 ONLY covers LT04 -> top-2 =
    # {S31,S32}, LT04 is a FALLBACK-flagged fill from the wider field (S33).
    split = [
        ("b_d1", "S31", "LT01", "100.00"),
        ("b_d2", "S31", "LT02", "100.00"),
        ("b_d3", "S32", "LT03", "100.00"),
        ("b_d4", "S33", "LT04", "100.00"),
        ("b_d5", "S32", "LT01", "108.00"),  # weaker alt on LT01 (premium drags it down)
    ]
    for bid_id, sup, lot, price in split:
        bids.append(_bid(bid_id, sup, "DC20", lot, "TF1", price))
        req("DC20", lot)

    # === CONCENTRATION: S50 wins a very large lot so its B RecSpend >= 40% of the
    # whole category's B spend (the conc_thresh flag, computed over ALL B cells). ===
    bids.append(_bid("b_conc1", "S50", "DC30", "LT01", "TF1", "100.00", total_vol="6000"))
    bids.append(_bid("b_conc2", "S51", "DC30", "LT02", "TF1", "100.00", total_vol="100"))
    req("DC30", "LT01", "6000")
    req("DC30", "LT02")

    # === EXCLUSION (E): SX0 is the B-pick on DC40/LT01 but excluded -> SX1 wins E. =
    bids.append(_bid("b_ex0", "SX0", "DC40", "LT01", "TF1", "100.00"))
    bids.append(_bid("b_ex1", "SX1", "DC40", "LT01", "TF1", "101.00"))
    req("DC40", "LT01")

    # === CONTINUITY + SCENARIO C: incumbent S70 bids within 3% at full coverage. ===
    # Incumbent (continuity 100) at 100.00 (group min) vs a cheaper non-incumbent at
    # 99.00. B picks the higher RecScore; C retains the incumbent (within-3%, >=80%).
    bids.append(
        _bid("b_inc", "S70", "DC60", "LT01", "TF1", "100.00", is_incumbent=True)
    )
    bids.append(_bid("b_inc_rival", "S71", "DC60", "LT01", "TF1", "99.00"))
    req("DC60", "LT01")

    # === COST construction: fallback + double-subtract guard. =====================
    # Fallback: FOB 90 + Delivery 5 + VegCool 3 - LotDisc 2 - AllLotDisc 1 = 95.00.
    bids.append(
        _bid(
            "b_fallback",
            "S60",
            "DC50",
            "LT01",
            "TF1",
            None,
            components=BidComponents(
                all_in=None,
                fob=_D("90.00"),
                delivery_surcharge=_D("5.00"),
                vegcool_surcharge=_D("3.00"),
                lot_discount=_D("2.00"),
                all_lot_discount=_D("1.00"),
            ),
        )
    )
    # All-In present (95.00) WITH Lot_Discount populated -> must NOT subtract again.
    bids.append(
        _bid(
            "b_doublesub",
            "S61",
            "DC50",
            "LT02",
            "TF1",
            None,
            components=BidComponents(
                all_in=_D("95.00"),
                fob=_D("90.00"),
                delivery_surcharge=_D("5.00"),
                vegcool_surcharge=_D("3.00"),
                lot_discount=_D("2.00"),
            ),
        )
    )
    req("DC50", "LT01")
    req("DC50", "LT02")
    # No-valid-price row (price 0) -> dropped, `No valid price`.
    bids.append(_bid("b_zeroprice", "S62", "DC50", "LT03", "TF1", "0"))
    req("DC50", "LT03")

    return EngineInputs(
        cycle_id="cyc-golden",
        round_code="R1" if single_round else "R2",
        config=_config(single_round=single_round),
        bids=tuple(bids),
        volumes=tuple(volumes),
        incumbents=tuple(incumbents),
    )
