"""Synthetic region / transit / freight model shared by the demo seed AND the generator.

These DEMO-illustrative attributes (no schema column yet) are derived deterministically so
BOTH the demo's seeding/template-fill AND the scenario-workbook generator read them from ONE
place and produce identical results. SYNTHETIC ONLY (placeholders; no real data).
"""

from __future__ import annotations

from decimal import Decimal

# Synthetic horizon: weeks per timeframe (drives projected volumes AND the Controls horizon).
WEEKS_PER_TF = 13

# DC display name carries a short demo airport-style code in parens (readable + locatable).
DC_NAMES: tuple[tuple[str, str], ...] = (
    ("Atlanta DC (ATL)", "ATL"),
    ("Dallas DC (DAL)", "DAL"),
    ("Denver DC (DEN)", "DEN"),
)


# Product type per lot (Conventional / Organic). The real allocation models segment the sign-off by
# product type (a Conventional | Organic split per DC); we mirror that as a DEMO-illustrative lot
# attribute (no schema column yet — derived here for the segmentation surface, clearly labelled).
LOT_PRODUCT_TYPE: tuple[str, ...] = ("Conventional", "Conventional", "Organic", "Organic")

# Broad shipping region per DC region-code, and a per-region freight (delivery) rate. The real FOB
# analysis tab strips freight off the landed price and shows a regional min; we decompose the
# synthetic All-In into FOB (farm-gate) + Delivery (lane freight, by region) + VegCool (cold-chain)
# so the landed price (All-In) the engine scores is UNCHANGED, but the freight is now transparent.
DC_REGION_GROUP: dict[str, str] = {"ATL": "East", "DAL": "South", "DEN": "West"}
REGION_FREIGHT: dict[str, Decimal] = {
    "East": Decimal("1.40"),
    "South": Decimal("1.85"),
    "West": Decimal("2.40"),
}
VEGCOOL_SURCHARGE_CASE = Decimal("0.35")  # cold-chain surcharge (constant in the demo)


def _dc_region(dc_index: int) -> str:
    """Broad shipping region (East/South/West) for a DC by its seed index."""

    region_code = DC_NAMES[dc_index % len(DC_NAMES)][1]
    return DC_REGION_GROUP.get(region_code, "East")


def _transit_days(sup_index: int, dc_index: int) -> int:
    """Lane transit time (days) supplier→DC — a HIDDEN COST (freshness/lead-time risk for produce).

    DEMO-illustrative: deterministic by (supplier origin, DC) so it varies per lane (2–6 days).
    Longer transit = more shrink/freshness risk on perishable produce — a non-price consideration
    the team weighs alongside landed cost. No schema column yet; derived here, clearly labelled.
    """

    return 2 + (sup_index * 2 + dc_index * 3) % 5


FRESHNESS_WATCH_DAYS = 4  # transit beyond this flags a freshness/lead-time watch (hidden cost)
