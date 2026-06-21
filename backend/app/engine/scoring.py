"""The five banded factors -> RecScore, plus cost construction, weights, and eligibility gates.

Clean-room re-implementation of V3_ENGINE_LOGIC.md §2, §3, §7 — written from our own spec, never
from the quarantined source. All band thresholds/weights are config-driven (ADR-0016); nothing
is hardcoded here except the band *score* outputs, which are logic, not strategy knobs.

Pure: stdlib only (Decimal for reproducible arithmetic; no float, no numpy, no I/O).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.engine.formulas import construct_price, premium_vs_low
from app.engine.interface import BidInput, EngineConfig

# --- Reason codes (eligibility gate flags, V3_ENGINE_LOGIC §3). Strings, exact. ---
GATE_NO_PRICE = "No valid price"
GATE_PREMIUM = "Price premium exceeds threshold"
GATE_COVERAGE = "Insufficient volume (<80%)"
GATE_LOW_OUTLIER = "Low price outlier: validate sustainability"
GATE_HIGH_OUTLIER = "High price outlier"
GATE_LOW_BIDDER = "Low bidder count (<3): Z-score less reliable"

_ZERO = Decimal("0")
_ONE = Decimal("1")


@dataclass(frozen=True)
class GroupStats:
    """Market stats for a (dc, lot, tf) group key: min/avg/std/bidder count over valid prices."""

    min_price: Decimal
    avg_price: Decimal
    std_price: Decimal
    bidder_count: int


@dataclass(frozen=True)
class ScoredBid:
    """An internal scored row: the bid, its derived Price, factor scores, gates, ratios."""

    bid: BidInput
    price: Decimal | None  # None => dropped (NaN/<=0 price)
    prem_vs_low: Decimal | None
    total_cov_ratio: Decimal | None  # None => As-Needed or missing requirement
    delta_vs_hist: Decimal | None
    z_score: Decimal | None
    price_score: Decimal
    coverage_score: Decimal
    hist_score: Decimal
    zrisk_score: Decimal
    continuity_score: Decimal
    rec_score: Decimal
    eligible: bool
    gate_flags: tuple[str, ...]


# §7 cost construction (`construct_price`) is a canonical formula — see `app.engine.formulas`.


# ---------------------------------------------------------------------------
# §2.6 — Weight resolution + normalization
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Weights:
    price: Decimal
    coverage: Decimal
    historical: Decimal
    zrisk: Decimal
    continuity: Decimal


def resolve_weights(config: EngineConfig) -> Weights:
    """Resolve the five weights from config and renormalize if |sum - 1.0| > 1% (§2.6).

    Strategy-agnostic: weights come straight from the (frozen) config. If they sum off by more
    than 1% they are each divided by the total so the composite stays a convex combination
    (cost is 35% of the decision, not 100%).
    """

    raw = (
        config.weight_price,
        config.weight_coverage,
        config.weight_historical,
        config.weight_zrisk,
        config.weight_continuity,
    )
    total = sum(raw, _ZERO)
    if total != _ZERO and abs(total - _ONE) > Decimal("0.01"):
        raw = tuple(w / total for w in raw)  # type: ignore[assignment]
    return Weights(raw[0], raw[1], raw[2], raw[3], raw[4])


# ---------------------------------------------------------------------------
# §2.1-2.5 — The five banded factors
# ---------------------------------------------------------------------------
def price_score(prem_vs_low: Decimal | None, config: EngineConfig) -> Decimal:
    """§2.1 banded on PremVsLow. NaN -> 0 (treated as 0 in the composite)."""

    if prem_vs_low is None:
        return _ZERO
    if prem_vs_low <= config.premium_band_comparable:
        return Decimal("100")
    if prem_vs_low <= config.premium_band_defensible:
        return Decimal("80")
    if prem_vs_low <= config.premium_band_max:
        return Decimal("50")
    return Decimal("20")


def coverage_score(ratio: Decimal | None, is_as_needed: bool) -> Decimal:
    """§2.2 banded on TotalCovRatio. As-Needed -> 70; NaN -> 30 (penalty)."""

    if is_as_needed:
        return Decimal("70")
    if ratio is None:
        return Decimal("30")
    if ratio < Decimal("0.50"):
        return _ZERO
    if ratio < Decimal("0.80"):
        return Decimal("40")
    if ratio < Decimal("1.00"):
        return Decimal("70")
    if ratio <= Decimal("1.20"):
        return Decimal("100")
    return Decimal("95")


def hist_score(delta_vs_hist: Decimal | None) -> Decimal:
    """§2.3 banded on DeltaVsHistPct. No baseline (None) -> 50."""

    if delta_vs_hist is None:
        return Decimal("50")
    if delta_vs_hist <= Decimal("-0.10"):
        return Decimal("100")
    if delta_vs_hist <= Decimal("-0.03"):
        return Decimal("85")
    if delta_vs_hist <= Decimal("0.03"):
        return Decimal("70")
    if delta_vs_hist <= Decimal("0.07"):
        return Decimal("45")
    return Decimal("20")


def zrisk_score(z_score: Decimal | None) -> Decimal:
    """§2.4 banded on ZScore. In [-1,1] -> 100; <-2 -> 60; >2 -> 40; else 80 (default)."""

    if z_score is None:
        return Decimal("100")  # no spread / single bidder -> not an outlier
    if Decimal("-1") <= z_score <= _ONE:
        return Decimal("100")
    if z_score < Decimal("-2"):
        return Decimal("60")
    if z_score > Decimal("2"):
        return Decimal("40")
    return Decimal("80")


def continuity_score(bid: BidInput) -> Decimal:
    """§2.5: incumbent -> 100, else 0 (marginal tie-break only)."""

    return Decimal("100") if bid.is_incumbent else _ZERO


# ---------------------------------------------------------------------------
# Market stats + sqrt helper (population std, Decimal — matches numpy ddof=0)
# ---------------------------------------------------------------------------
def _dec_sqrt(value: Decimal) -> Decimal:
    """Decimal square root via the context (reproducible, no float)."""

    if value <= _ZERO:
        return _ZERO
    return value.sqrt()


def compute_group_stats(prices: list[Decimal]) -> GroupStats:
    """Min/avg/population-std and bidder count over a group's valid prices."""

    n = len(prices)
    if n == 0:
        return GroupStats(_ZERO, _ZERO, _ZERO, 0)
    total = sum(prices, _ZERO)
    avg = total / Decimal(n)
    var = sum(((p - avg) ** 2 for p in prices), _ZERO) / Decimal(n)
    return GroupStats(min(prices), avg, _dec_sqrt(var), n)


# ---------------------------------------------------------------------------
# Full scoring pass: build group keys, derive ratios, apply factors + gates
# ---------------------------------------------------------------------------
def _cell(bid: BidInput) -> tuple[str, str, str]:
    return (bid.dc_no, bid.lot_id, bid.tf_code)


def score_bids(
    bids: tuple[BidInput, ...],
    volumes_by_cell: dict[tuple[str, str, str], Decimal | None],
    incumbent_routing: dict[tuple[str, str], Decimal | None],
    config: EngineConfig,
) -> list[ScoredBid]:
    """Score every valid-priced bid (§2, §3). Returns ScoredBid rows (price=None => dropped).

    `volumes_by_cell` maps (dc,lot,tf) -> total volume required (None if missing/0).
    `incumbent_routing` maps (dc,lot) -> incumbent routing baseline (None if no baseline).
    """

    weights = resolve_weights(config)
    lot_thresh = dict(config.lot_premium_thresholds)

    # 1) Construct Price; group valid-priced bids by cell for market stats.
    priced: list[tuple[BidInput, Decimal | None]] = [(b, construct_price(b)) for b in bids]
    cell_prices: dict[tuple[str, str, str], list[Decimal]] = defaultdict(list)
    for bid, price in priced:
        if price is not None:
            cell_prices[_cell(bid)].append(price)
    stats = {cell: compute_group_stats(ps) for cell, ps in cell_prices.items()}

    scored: list[ScoredBid] = []
    for bid, price in priced:
        cell = _cell(bid)
        gst = stats.get(cell)

        if price is None or gst is None:
            scored.append(_dropped_row(bid))
            continue

        # --- ratios ---
        prem_vs_low = premium_vs_low(price, gst.min_price)
        z_score: Decimal | None = None
        if gst.std_price > _ZERO:
            z_score = (price - gst.avg_price) / gst.std_price

        cov_ratio = _coverage_ratio(bid, volumes_by_cell.get(cell))
        routing = incumbent_routing.get((bid.dc_no, bid.lot_id))
        delta_vs_hist = (price - routing) / routing if routing and routing > _ZERO else None

        # --- factor scores ---
        ps = price_score(prem_vs_low, config)
        cs = coverage_score(cov_ratio, bid.is_as_needed)
        hs = hist_score(delta_vs_hist)
        zs = zrisk_score(z_score)
        cns = continuity_score(bid)

        rec = (
            ps * weights.price
            + cs * weights.coverage
            + hs * weights.historical
            + zs * weights.zrisk
            + cns * weights.continuity
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- eligibility gates + reason codes (§3) ---
        eligible, flags = _gates(
            bid=bid,
            prem_vs_low=prem_vs_low,
            cov_ratio=cov_ratio,
            z_score=z_score,
            bidder_count=gst.bidder_count,
            lot_thresh=lot_thresh,
            config=config,
        )

        scored.append(
            ScoredBid(
                bid=bid,
                price=price,
                prem_vs_low=prem_vs_low,
                total_cov_ratio=cov_ratio,
                delta_vs_hist=delta_vs_hist,
                z_score=z_score,
                price_score=ps,
                coverage_score=cs,
                hist_score=hs,
                zrisk_score=zs,
                continuity_score=cns,
                rec_score=rec,
                eligible=eligible,
                gate_flags=flags,
            )
        )
    return scored


def _coverage_ratio(bid: BidInput, total_required: Decimal | None) -> Decimal | None:
    """TotVolOffered / TotVolReq. None when As-Needed, or req/offered missing/0 (§2.2)."""

    if bid.is_as_needed:
        return None
    if total_required is None or total_required <= _ZERO:
        return None
    if bid.total_vol_offered is None:
        return None
    return bid.total_vol_offered / total_required


def _gates(
    *,
    bid: BidInput,
    prem_vs_low: Decimal | None,
    cov_ratio: Decimal | None,
    z_score: Decimal | None,
    bidder_count: int,
    lot_thresh: dict[str, Decimal],
    config: EngineConfig,
) -> tuple[bool, tuple[str, ...]]:
    """Apply the three hard gates + advisory flags (§3). Returns (eligible, flag tuple)."""

    flags: list[str] = []
    eligible = True

    # Gate 1: valid price. (Price=None handled by _dropped_row; here price is valid > 0.)
    # Gate 2: premium <= per-lot-or-global max threshold.
    max_thresh = lot_thresh.get(bid.lot_id, config.global_premium_threshold)
    if prem_vs_low is not None and prem_vs_low > max_thresh:
        flags.append(GATE_PREMIUM)
        eligible = False

    # Gate 3: coverage floor (skipped for As-Needed or when ratio is NaN/missing).
    if not bid.is_as_needed and cov_ratio is not None and cov_ratio < config.coverage_floor:
        flags.append(GATE_COVERAGE)
        eligible = False

    # Advisory flags (recorded, do NOT set Eligible=False on their own).
    if z_score is not None and z_score < Decimal("-2"):
        flags.append(GATE_LOW_OUTLIER)
    if z_score is not None and z_score > Decimal("2"):
        flags.append(GATE_HIGH_OUTLIER)
    if bidder_count < 3:
        flags.append(GATE_LOW_BIDDER)

    # Preserve any upstream (as-built eligibility-layer) flags the runner already attached.
    merged = tuple(bid.gate_flags) + tuple(flags)
    if not bid.eligible:
        eligible = False
    return eligible, merged


def _dropped_row(bid: BidInput) -> ScoredBid:
    """A bid with NaN/<=0 Price: dropped from scoring (§7 l.603), ineligible, `No valid price`.

    Such rows are not awardable; factor scores are zeroed and rec_score is 0 — they exist in
    the output only to surface the `No valid price` gate, never to be selected.
    """

    return ScoredBid(
        bid=bid,
        price=None,
        prem_vs_low=None,
        total_cov_ratio=None,
        delta_vs_hist=None,
        z_score=None,
        price_score=_ZERO,
        coverage_score=_ZERO,
        hist_score=_ZERO,
        zrisk_score=_ZERO,
        continuity_score=_ZERO,
        rec_score=_ZERO,
        eligible=False,
        gate_flags=tuple(bid.gate_flags) + (GATE_NO_PRICE,),
    )
