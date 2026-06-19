"""Scenarios A-G (§5), the deterministic tie-break sort (§6), and the max_two_per_dc split (§4).

Clean-room re-implementation of V3_ENGINE_LOGIC.md §4-§6 from our own spec. All controls
(max_sup_dc, single_supplier_per_lot, conc_thresh, lenses, scenario rules) come from the frozen
config (ADR-0016). Decision-support only: scenarios PROPOSE; the human selects.

Pure: stdlib only.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from app.engine.interface import (
    EngineConfig,
    ExclusionRule,
    PreferredRule,
    ScenarioAward,
    ScenarioCode,
)
from app.engine.scoring import ScoredBid

_ZERO = Decimal("0")
_ONE = Decimal("1")
Cell = tuple[str, str, str]  # (dc, lot, tf)


# ---------------------------------------------------------------------------
# §6 — Deterministic tie-break sort key (load-bearing for reproduction)
# ---------------------------------------------------------------------------
def _det_sort_key(sb: ScoredBid) -> tuple[Decimal, Decimal, Decimal, int, str]:
    """[RecScore desc, Price asc, TotalCovRatio desc, _IncBoost desc, Supplier asc].

    Implemented as a min-sort key by negating the descending Decimal/int components.
    """

    price = sb.price if sb.price is not None else Decimal("999999999")
    cov = sb.total_cov_ratio if sb.total_cov_ratio is not None else _ZERO
    inc_boost = 1 if sb.bid.is_incumbent else 0
    return (-sb.rec_score, price, -cov, -inc_boost, sb.bid.supplier_id)


def _best_per_cell(rows: list[ScoredBid]) -> dict[Cell, ScoredBid]:
    """First row per (dc,lot,tf) under the deterministic sort -> the cell winner."""

    by_cell: dict[Cell, list[ScoredBid]] = defaultdict(list)
    for sb in rows:
        by_cell[(sb.bid.dc_no, sb.bid.lot_id, sb.bid.tf_code)].append(sb)
    return {cell: min(group, key=_det_sort_key) for cell, group in by_cell.items()}


def _lowest_cost_per_cell(rows: list[ScoredBid]) -> dict[Cell, ScoredBid]:
    """Scenario A: cheapest eligible bid per cell — [Price asc, Supplier asc]."""

    by_cell: dict[Cell, list[ScoredBid]] = defaultdict(list)
    for sb in rows:
        by_cell[(sb.bid.dc_no, sb.bid.lot_id, sb.bid.tf_code)].append(sb)

    def cost_key(sb: ScoredBid) -> tuple[Decimal, str]:
        price = sb.price if sb.price is not None else Decimal("999999999")
        return (price, sb.bid.supplier_id)

    return {cell: min(group, key=cost_key) for cell, group in by_cell.items()}


def _award(
    sb: ScoredBid,
    code: ScenarioCode,
    *,
    is_recommended: bool = False,
    is_fallback: bool = False,
    cap_breach_flag: bool = False,
) -> ScenarioAward:
    return ScenarioAward(
        scenario_code=code,
        dc_no=sb.bid.dc_no,
        lot_id=sb.bid.lot_id,
        tf_code=sb.bid.tf_code,
        supplier_id=sb.bid.supplier_id,
        volume_share=_ONE,  # single-winner cells take the full share
        awarded_price=sb.price if sb.price is not None else _ZERO,
        is_recommended=is_recommended,
        is_fallback=is_fallback,
        cap_breach_flag=cap_breach_flag,
    )


# ---------------------------------------------------------------------------
# §5 — Scenario A (lowest-cost reference)
# ---------------------------------------------------------------------------
def scenario_a(eligible: list[ScoredBid]) -> list[ScoredBid]:
    return list(_lowest_cost_per_cell(eligible).values())


# ---------------------------------------------------------------------------
# §5 — Scenario B (risk-adjusted, the main recommendation)
# ---------------------------------------------------------------------------
def scenario_b(eligible: list[ScoredBid]) -> dict[Cell, ScoredBid]:
    return _best_per_cell(eligible)


def rec_type(sb: ScoredBid, config: EngineConfig) -> str:
    """The Scenario-B RecType label (§5, B). Config-driven thresholds; decision-support phrasing."""

    prem = sb.prem_vs_low
    cov = sb.total_cov_ratio
    if prem is not None and prem <= Decimal("0.02"):
        return "Lowest cost"
    if cov is not None and cov > Decimal("1.2"):
        return "Coverage advantage"
    if prem is not None and prem <= config.premium_band_comparable:
        return "Comparable premium"
    if prem is not None and prem <= config.premium_band_defensible:
        return "Defensible premium"
    return "Risk-adjusted"


# ---------------------------------------------------------------------------
# §5 — Scenario C (incumbent defense)
# ---------------------------------------------------------------------------
def scenario_c(
    eligible: list[ScoredBid], b_pick: dict[Cell, ScoredBid], config: EngineConfig
) -> dict[Cell, ScoredBid]:
    """Incumbent retained iff incumbent ∧ premium<=comparable ∧ coverage ok; else B's pick."""

    inc_by_cell: dict[Cell, ScoredBid] = {}
    for sb in eligible:
        if not sb.bid.is_incumbent:
            continue
        prem_ok = sb.prem_vs_low is not None and sb.prem_vs_low <= config.premium_band_comparable
        cov_ok = (
            sb.bid.is_as_needed
            or sb.total_cov_ratio is None
            or sb.total_cov_ratio >= config.coverage_floor
        )
        if prem_ok and cov_ok:
            cell = (sb.bid.dc_no, sb.bid.lot_id, sb.bid.tf_code)
            current = inc_by_cell.get(cell)
            if current is None or _det_sort_key(sb) < _det_sort_key(current):
                inc_by_cell[cell] = sb
    return {**b_pick, **inc_by_cell}


# ---------------------------------------------------------------------------
# §5 — Scenario E (exclusion), F (custom override), G (preferred)
# ---------------------------------------------------------------------------
def _excluded(sb: ScoredBid, rule: ExclusionRule) -> bool:
    if sb.bid.supplier_id != rule.supplier_id:
        return False
    return (
        (rule.dc_no is None or rule.dc_no == sb.bid.dc_no)
        and (rule.lot_id is None or rule.lot_id == sb.bid.lot_id)
        and (rule.tf_code is None or rule.tf_code == sb.bid.tf_code)
    )


def scenario_e(eligible: list[ScoredBid], config: EngineConfig) -> dict[Cell, ScoredBid]:
    """Drop excluded suppliers, then re-run B's selection. No exclusions => E == B."""

    if not config.exclusions:
        return _best_per_cell(eligible)
    kept = [sb for sb in eligible if not any(_excluded(sb, r) for r in config.exclusions)]
    return _best_per_cell(kept)


def scenario_f(
    eligible: list[ScoredBid], b_pick: dict[Cell, ScoredBid], config: EngineConfig
) -> dict[Cell, ScoredBid]:
    """Start from B; replace a cell's award with the named supplier IF they have an eligible bid."""

    result = dict(b_pick)
    by_cell_sup: dict[tuple[Cell, str], ScoredBid] = {}
    for sb in eligible:
        by_cell_sup[((sb.bid.dc_no, sb.bid.lot_id, sb.bid.tf_code), sb.bid.supplier_id)] = sb
    for rule in config.custom_overrides:
        cell: Cell = (rule.dc_no, rule.lot_id, rule.tf_code)
        override = by_cell_sup.get((cell, rule.supplier_id))
        if override is not None:  # else WARN + skip (silent here; runner logs)
            result[cell] = override
    return result


def _preferred_matches(sb: ScoredBid, rule: PreferredRule) -> bool:
    if sb.bid.lot_id != rule.lot_id:
        return False
    return (rule.dc_no is None or rule.dc_no == sb.bid.dc_no) and (
        rule.tf_code is None or rule.tf_code == sb.bid.tf_code
    )


def scenario_g(
    eligible: list[ScoredBid], b_pick: dict[Cell, ScoredBid], config: EngineConfig
) -> dict[Cell, ScoredBid]:
    """Start from B; force preferred supplier where they have an eligible bid; else keep B."""

    result = dict(b_pick)
    for rule in config.preferred_rules:
        for cell in list(result.keys()):
            matching = [
                sb
                for sb in eligible
                if (sb.bid.dc_no, sb.bid.lot_id, sb.bid.tf_code) == cell
                and sb.bid.supplier_id == rule.supplier_id
                and _preferred_matches(sb, rule)
            ]
            if matching:  # no eligible bid => log exception + keep B's pick
                result[cell] = min(matching, key=_det_sort_key)
    return result


# ---------------------------------------------------------------------------
# §4 — Scenario D: the max_two_per_dc split allocator
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SupplierStrength:
    supplier_id: str
    avg_score: Decimal
    lots_covered: int
    avg_price: Decimal
    avg_coverage: Decimal
    rank_score: Decimal


def _supplier_strength(rows: list[ScoredBid]) -> list[SupplierStrength]:
    """Aggregate per supplier within a DC×TF and compute SupRankScore (§4.1)."""

    by_sup: dict[str, list[ScoredBid]] = defaultdict(list)
    for sb in rows:
        by_sup[sb.bid.supplier_id].append(sb)

    out: list[SupplierStrength] = []
    for sup, group in by_sup.items():
        n = Decimal(len(group))
        avg_score = sum((g.rec_score for g in group), _ZERO) / n
        lots = len({g.bid.lot_id for g in group})
        prices = [g.price for g in group if g.price is not None]
        avg_price = sum(prices, _ZERO) / Decimal(len(prices)) if prices else _ZERO
        # AvgCoverage = mean of TotalCovRatio.fillna(1.0)
        cov_vals = [g.total_cov_ratio if g.total_cov_ratio is not None else _ONE for g in group]
        avg_cov = sum(cov_vals, _ZERO) / n
        clipped = max(_ZERO, min(avg_cov, Decimal("1.2")))
        rank = avg_score * Decimal("0.60") + Decimal(lots) * Decimal("5") + clipped * Decimal("10")
        out.append(SupplierStrength(sup, avg_score, lots, avg_price, avg_cov, rank))
    # Sort by [SupRankScore desc, AvgPrice asc].
    out.sort(key=lambda s: (-s.rank_score, s.avg_price))
    return out


def scenario_d(eligible: list[ScoredBid], config: EngineConfig) -> list[ScenarioAward]:
    """The split allocator (§4): top-N suppliers per DC×TF, best lot picks, flagged fallback."""

    by_dctf: dict[tuple[str, str], list[ScoredBid]] = defaultdict(list)
    for sb in eligible:
        by_dctf[(sb.bid.dc_no, sb.bid.tf_code)].append(sb)

    awards: list[ScenarioAward] = []
    for group in by_dctf.values():
        strengths = _supplier_strength(group)
        top_set = {s.supplier_id for s in strengths[: config.max_sup_dc]}

        kept = [sb for sb in group if sb.bid.supplier_id in top_set]
        if not kept:  # empty kept set -> fall back to the whole group (§4.2)
            kept = group

        # 4.2 per-lot award within the kept set.
        kept_by_cell = _best_per_cell(kept)
        covered_cells = set(kept_by_cell.keys())
        for sb in kept_by_cell.values():
            awards.append(_award(sb, ScenarioCode.D))

        # 4.3 fallback fill: lots the top-N cannot cover -> best from the WIDER field, flagged.
        wider_by_cell = _best_per_cell(group)
        for cell, sb in wider_by_cell.items():
            if cell not in covered_cells:
                awards.append(_award(sb, ScenarioCode.D, is_fallback=True))
    return awards


# ---------------------------------------------------------------------------
# §4.4 cap-breach + §4.5 concentration flags (computed on Scenario B)
# ---------------------------------------------------------------------------
def cap_breach_cells(
    b_pick: dict[Cell, ScoredBid], config: EngineConfig
) -> set[tuple[str, str]]:
    """Per (dc, tf): >max_sup_dc distinct suppliers across B's lot awards -> breach (§4.4)."""

    sups_by_dctf: dict[tuple[str, str], set[str]] = defaultdict(set)
    for (dc, _lot, tf), sb in b_pick.items():
        sups_by_dctf[(dc, tf)].add(sb.bid.supplier_id)
    return {
        dctf for dctf, sups in sups_by_dctf.items() if len(sups) > config.max_sup_dc
    }


def concentration_flags(
    b_pick: dict[Cell, ScoredBid],
    volumes_by_cell: dict[Cell, Decimal | None],
    config: EngineConfig,
) -> set[str]:
    """Suppliers with B RecSpend >= conc_thresh of total category spend (§4.5)."""

    spend_by_sup: dict[str, Decimal] = defaultdict(lambda: _ZERO)
    total = _ZERO
    for cell, sb in b_pick.items():
        if sb.price is None:
            continue
        vol = volumes_by_cell.get(cell) or _ONE  # As-Needed/missing -> per-case weight of 1
        spend = sb.price * vol
        spend_by_sup[sb.bid.supplier_id] += spend
        total += spend
    if total <= _ZERO:
        return set()
    return {sup for sup, sp in spend_by_sup.items() if sp / total >= config.conc_thresh}
