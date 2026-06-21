"""Per-touchpoint field resolvers (E-37): pull governed data into a rendered comms draft.

The pure render core (`merge`/`render`/`templates`) fills placeholders from a context; these
resolvers BUILD that context from the governed store for a given touchpoint, then render one draft
per supplier. Draft-only — the buyer reviews/edits/sends; nothing here sends.

Routing tags use the canonical machine ids (`cycle_id` / `supplier_id`) so a downstream parser
(Power Automate) matches a stable key; the human-readable cycle/supplier NAMES are carried
separately in the body.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.comms.render import render
from app.comms.templates import EmailType, get_template
from app.domain.awd.models import Award, AwardLine
from app.domain.awd.read import award_detail
from app.domain.cyc.models import CycleTimeframe
from app.engine.scoring import GATE_COVERAGE, GATE_NO_PRICE, GATE_PREMIUM
from app.output.types import CycleView

# Engine eligibility defaults (mirror the pilot wiring) when the cycle sets no override.
_DEFAULT_PREMIUM_CEILING = Decimal("0.12")
_DEFAULT_COVERAGE_FLOOR = Decimal("0.80")

_Cell = tuple[str, str, str]  # (dc_id, lot_id, tf_id)


class SupplierEmailDraft(BaseModel):
    """One rendered, editable email draft for one supplier at a touchpoint."""

    supplier_id: str
    supplier_name: str
    email_type: str
    subject: str
    body: str
    missing: list[str] = Field(
        description="Placeholders left unfilled (visible `[#Name]` holes the buyer completes)."
    )


def _fmt_date(value: date | None) -> str:
    return value.strftime("%b %d, %Y") if value is not None else ""


def _delivery_window(session: Session, cycle_id: str) -> tuple[str, str]:
    """The cycle's overall delivery window: earliest timeframe start → latest timeframe end."""

    rows = session.execute(
        select(CycleTimeframe.start_date, CycleTimeframe.end_date).where(
            CycleTimeframe.cycle_id == cycle_id
        )
    ).all()
    if not rows:
        return "", ""
    return _fmt_date(min(r[0] for r in rows)), _fmt_date(max(r[1] for r in rows))


def award_drafts(
    session: Session,
    cycle_view: CycleView,
    award_id: str,
    *,
    buyer_name: str = "",
    buyer_title: str = "",
    award_file_name: str = "",
) -> list[SupplierEmailDraft]:
    """One AWARD-notification draft per awarded supplier (those with cells on the frozen award).

    Reuses the cycle-scoped `award_detail` (raises ValueError if the award isn't this run's), groups
    its lines by supplier to count distinct DCs + lots won, and renders the award template. A
    not-awarded supplier never appears here — that is the non-selection touchpoint.
    """

    detail = award_detail(session, cycle_view, award_id)
    name_by_supplier = {s.id: s.name for s in cycle_view.suppliers}

    won_dcs: dict[str, set[str]] = {}
    won_lots: dict[str, set[str]] = {}
    for line in detail.lines:
        won_dcs.setdefault(line.supplier_id, set()).add(line.dc_id)
        won_lots.setdefault(line.supplier_id, set()).add(line.lot_id)

    start, end = _delivery_window(session, cycle_view.cycle_id)
    template = get_template(EmailType.AWARD)

    drafts: list[SupplierEmailDraft] = []
    for supplier_id in won_dcs:
        supplier_name = name_by_supplier.get(supplier_id, supplier_id[:8])
        context = {
            "SupplierName": supplier_name,
            "SupplierID": supplier_id,
            "CycleName": cycle_view.cycle_name,
            "CycleID": cycle_view.cycle_id,
            "AwardedDCCount": str(len(won_dcs[supplier_id])),
            "AwardedLotCount": str(len(won_lots[supplier_id])),
            "DeliveryStartDate": start,
            "DeliveryEndDate": end,
            "AwardFileName": award_file_name,
            "BuyerName": buyer_name,
            "BuyerTitle": buyer_title,
        }
        rendered = render(template, context)
        drafts.append(
            SupplierEmailDraft(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                email_type=template.email_type,
                subject=rendered.subject,
                body=rendered.body,
                missing=list(rendered.missing),
            )
        )
    drafts.sort(key=lambda d: d.supplier_name)
    return drafts


# --------------------------------------------------------------------------- #
# Round feedback (E-37): per-supplier standing vs the market-low benchmark.
# --------------------------------------------------------------------------- #
def _money(value: Decimal, *, cents: bool = True) -> str:
    return f"${value:,.2f}" if cents else f"${value:,.0f}"


def _pct(value: Decimal) -> str:
    return f"{value * 100:.1f}%"


def _round_id_and_number(session: Session, analysis_run_id: str) -> tuple[str, int]:
    """The round this analysis scored: its id + 1-based number. Raises ValueError if unknown."""

    row = session.execute(
        text(
            "SELECT r.round_id, cr.round_number FROM eng.analysis_run r "
            "JOIN cyc.cycle_round cr ON cr.round_id = r.round_id "
            "WHERE r.analysis_run_id = :run"
        ),
        {"run": analysis_run_id},
    ).first()
    if row is None:
        raise ValueError(f"analysis run {analysis_run_id!r} not found")
    return str(row[0]), int(row[1])


def _round_prices(
    session: Session, cycle_id: str, round_id: str
) -> dict[_Cell, dict[str, Decimal]]:
    """The round's ACTIVE all-in price per cell -> {supplier_id: price} (one per supplier×cell)."""

    rows = session.execute(
        text(
            "SELECT DISTINCT ON (supplier_id, dc_id, lot_id, tf_id) "
            "supplier_id, dc_id, lot_id, tf_id, submitted_all_in_case "
            "FROM bid.bid_line WHERE cycle_id = :cyc AND round_id = :rnd "
            "AND is_scoreable = true AND submitted_all_in_case IS NOT NULL "
            "ORDER BY supplier_id, dc_id, lot_id, tf_id, fiscal_period_id NULLS LAST, bid_line_id"
        ),
        {"cyc": cycle_id, "rnd": round_id},
    ).all()
    by_cell: dict[_Cell, dict[str, Decimal]] = defaultdict(dict)
    for supplier_id, dc_id, lot_id, tf_id, price in rows:
        by_cell[(dc_id, lot_id, tf_id)][supplier_id] = Decimal(str(price))
    return by_cell


def _eligibility(
    session: Session, analysis_run_id: str
) -> dict[tuple[str, str, str, str], tuple[bool, str]]:
    """Per (supplier, dc, lot, tf): the sealed (is_eligible, gate_flags) from the bid_score."""

    rows = session.execute(
        text(
            "SELECT supplier_id, dc_id, lot_id, tf_id, is_eligible, COALESCE(gate_flags, '') "
            "FROM eng.bid_score WHERE analysis_run_id = :run"
        ),
        {"run": analysis_run_id},
    ).all()
    return {(s, d, lo, t): (bool(e), g) for s, d, lo, t, e, g in rows}


def _weekly_volume(session: Session, cycle_id: str) -> dict[_Cell, Decimal]:
    """Weekly required cases per (dc, lot, tf): projected weekly volume aggregated item -> lot."""

    rows = session.execute(
        text(
            "SELECT pv.dc_id, li.lot_id, pv.tf_id, COALESCE(SUM(pv.projected_weekly_cases), 0) "
            "FROM cyc.cycle_projected_volume pv "
            "JOIN cyc.cycle_lot_item li ON li.cycle_id = pv.cycle_id AND li.item_id = pv.item_id "
            "WHERE pv.cycle_id = :cyc GROUP BY pv.dc_id, li.lot_id, pv.tf_id"
        ),
        {"cyc": cycle_id},
    ).all()
    return {(d, lo, t): Decimal(str(v)) for d, lo, t, v in rows}


def _hard_ask_reason(
    flags: str, prem_pct: Decimal, ceiling: Decimal, floor: Decimal
) -> tuple[str, str, str]:
    """(Issue, Current Value, Required Improvement) for an INELIGIBLE lot, from its gate flags."""

    if GATE_PREMIUM in flags:
        return ("Price premium exceeds threshold", _pct(prem_pct), f"at or below {_pct(ceiling)}")
    if GATE_COVERAGE in flags:
        return (
            "Insufficient volume offered",
            f"below {_pct(floor)} of requirement",
            f"at least {_pct(floor)}",
        )
    return ("Not eligible for award", _pct(prem_pct), "review submission")


def feedback_drafts(
    session: Session,
    cycle_view: CycleView,
    analysis_run_id: str,
    *,
    buyer_name: str = "",
    buyer_title: str = "",
) -> list[SupplierEmailDraft]:
    """One ROUND-FEEDBACK draft per supplier with lots ABOVE the market-low benchmark (E-37).

    Per supplier, per cell they bid where their price is above the cell's market low: classify the
    lot HARD (ineligible — premium over the ceiling or coverage under the floor: "fix to keep
    participating") vs SOFT (eligible but above the benchmark: "improve your position"), and roll up
    the per-DC summary ($ / % premium + estimated weekly impact). Only suppliers with at least one
    above-benchmark lot get a draft. Draft-only; the supplier's OWN data only (no competitor names).
    """

    cycle_id = cycle_view.cycle_id
    round_id, round_number = _round_id_and_number(session, analysis_run_id)
    prices = _round_prices(session, cycle_id, round_id)
    eligibility = _eligibility(session, analysis_run_id)
    weekly = _weekly_volume(session, cycle_id)
    ceiling = cycle_view.premium_ceiling or _DEFAULT_PREMIUM_CEILING
    floor = cycle_view.coverage_floor or _DEFAULT_COVERAGE_FLOOR

    dc_name = {d.id: d.name for d in cycle_view.dcs}
    lot_name = {lot.id: lot.name for lot in cycle_view.lots}
    sup_name = {s.id: s.name for s in cycle_view.suppliers}

    # Per supplier: the hard/soft ask rows + per-DC aggregates over above-benchmark lots.
    hard: dict[str, list[dict[str, str]]] = defaultdict(list)
    soft: dict[str, list[dict[str, str]]] = defaultdict(list)
    dc_agg: dict[str, dict[str, dict[str, Decimal]]] = defaultdict(lambda: defaultdict(dict))

    for (dc_id, lot_id, tf_id), sup_prices in prices.items():
        if not sup_prices:
            continue
        market_low = min(sup_prices.values())
        if market_low <= 0:
            continue
        weekly_cases = weekly.get((dc_id, lot_id, tf_id), Decimal("0"))
        for supplier_id, price in sup_prices.items():
            if price <= market_low:  # at or below benchmark -> no ask (only include lots above)
                continue
            prem_dollar = price - market_low
            prem_pct = prem_dollar / market_low
            impact = prem_dollar * weekly_cases
            agg = dc_agg[supplier_id].setdefault(
                dc_id,
                {
                    "count": Decimal("0"),
                    "dollar": Decimal("0"),
                    "pct": Decimal("0"),
                    "impact": Decimal("0"),
                },
            )
            agg["count"] += Decimal("1")
            agg["dollar"] += prem_dollar
            agg["pct"] += prem_pct
            agg["impact"] += impact

            is_elig, flags = eligibility.get((supplier_id, dc_id, lot_id, tf_id), (True, ""))
            dc_label = dc_name.get(dc_id, dc_id[:6])
            lot_label = lot_name.get(lot_id, lot_id[:6])
            if not is_elig:
                issue, current, target = _hard_ask_reason(flags, prem_pct, ceiling, floor)
                hard[supplier_id].append(
                    {
                        "DC": dc_label,
                        "Lot": lot_label,
                        "IssueReason": issue,
                        "CurrentMetric": current,
                        "TargetMetric": target,
                    }
                )
            else:
                soft[supplier_id].append(
                    {
                        "DC": dc_label,
                        "Lot": lot_label,
                        "PremiumPct": _pct(prem_pct),
                        "BenchmarkPrice": _money(market_low),
                        "SuggestedTarget": f"match {_money(market_low)} to compete",
                    }
                )

    template = get_template(EmailType.ROUND_FEEDBACK)
    drafts: list[SupplierEmailDraft] = []
    for supplier_id, agg_by_dc in dc_agg.items():
        supplier_name = sup_name.get(supplier_id, supplier_id[:8])
        dc_rows = [
            {
                "DC": dc_name.get(dc_id, dc_id[:6]),
                "LotsAboveTarget": str(int(a["count"])),
                "AvgDollarPremium": _money(a["dollar"] / a["count"]),
                "AvgPercentPremium": _pct(a["pct"] / a["count"]),
                "EstWeeklyImpact": _money(a["impact"], cents=False),
            }
            for dc_id, a in sorted(agg_by_dc.items(), key=lambda kv: dc_name.get(kv[0], kv[0]))
        ]
        context = {
            "SupplierName": supplier_name,
            "SupplierID": supplier_id,
            "CycleName": cycle_view.cycle_name,
            "CycleID": cycle_view.cycle_id,
            "RoundNumber": str(round_number),
            "BuyerName": buyer_name,
            "BuyerTitle": buyer_title,
        }
        rendered = render(
            template,
            context,
            tables={
                "DCSummaryTable": dc_rows,
                "HardAskTable": sorted(hard[supplier_id], key=lambda r: (r["DC"], r["Lot"])),
                "SoftAskTable": sorted(soft[supplier_id], key=lambda r: (r["DC"], r["Lot"])),
            },
        )
        drafts.append(
            SupplierEmailDraft(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                email_type=template.email_type,
                subject=rendered.subject,
                body=rendered.body,
                missing=list(rendered.missing),
            )
        )
    drafts.sort(key=lambda d: d.supplier_name)
    return drafts


# --------------------------------------------------------------------------- #
# Non-selection / "RFP Results" (E-37): per-lot reasons a participant didn't win.
# --------------------------------------------------------------------------- #
@dataclass
class _LostLot:
    """A supplier's averaged standing on one (dc, lot) they did NOT win, across its timeframes."""

    bid_sum: Decimal = Decimal("0")
    low_sum: Decimal = Decimal("0")
    count: int = 0
    ineligible: bool = False
    flags: str = field(default="")


def _rejection_reason(ineligible: bool, flags: str) -> str:
    """A data-centered reason for a lost lot: the eligibility gate if any, else competitive rank."""

    if ineligible:
        if GATE_NO_PRICE in flags:
            return "No valid price submitted"
        if GATE_PREMIUM in flags:
            return "Price premium above ceiling"
        if GATE_COVERAGE in flags:
            return "Insufficient volume offered"
        return "Did not meet eligibility criteria"
    return "Not selected (lower competitive rank)"


def rejection_drafts(
    session: Session,
    cycle_view: CycleView,
    award_id: str,
    *,
    buyer_name: str = "",
    buyer_title: str = "",
) -> list[SupplierEmailDraft]:
    """One NON-SELECTION ("RFP Results") draft per supplier with a lot they did NOT win (E-37).

    Keyed on the frozen award (the decision that settles who won what): over the round the award
    scored, each supplier's cells NOT awarded to them (lost outright, or a split cell that went to
    others) become an itemized, data-centered row — their submitted price, the cell's market-low
    benchmark, the % difference, and a reason (an eligibility gate, else competitive rank). A
    supplier awarded every cell they bid gets no draft (they got the award notice). Raises a
    ValueError if the award isn't this run's (router -> 404). The supplier's OWN bid + an anonymous
    benchmark only — never a competitor's name or price.
    """

    award = session.execute(
        select(Award).where(Award.award_id == award_id, Award.cycle_id == cycle_view.cycle_id)
    ).scalar_one_or_none()
    if award is None:
        raise ValueError(f"award {award_id!r} not found")

    round_id, _ = _round_id_and_number(session, award.analysis_run_id)
    prices = _round_prices(session, cycle_view.cycle_id, round_id)
    eligibility = _eligibility(session, award.analysis_run_id)
    awarded: set[tuple[str, str, str, str]] = {
        (dc, lot, tf, sup)
        for dc, lot, tf, sup in session.execute(
            select(AwardLine.dc_id, AwardLine.lot_id, AwardLine.tf_id, AwardLine.supplier_id).where(
                AwardLine.award_id == award_id
            )
        ).all()
    }

    dc_name = {d.id: d.name for d in cycle_view.dcs}
    lot_name = {lot.id: lot.name for lot in cycle_view.lots}
    sup_name = {s.id: s.name for s in cycle_view.suppliers}

    # Per supplier, per (dc, lot) they lost: accumulate bid + benchmark + eligibility over its TFs.
    lost: dict[str, dict[tuple[str, str], _LostLot]] = defaultdict(dict)
    for (dc_id, lot_id, tf_id), sup_prices in prices.items():
        if not sup_prices:
            continue
        market_low = min(sup_prices.values())
        if market_low <= 0:
            continue
        for supplier_id, price in sup_prices.items():
            if (dc_id, lot_id, tf_id, supplier_id) in awarded:
                continue  # they won this cell — never a rejection row
            agg = lost[supplier_id].setdefault((dc_id, lot_id), _LostLot())
            agg.bid_sum += price
            agg.low_sum += market_low
            agg.count += 1
            is_elig, flags = eligibility.get((supplier_id, dc_id, lot_id, tf_id), (True, ""))
            if not is_elig:
                agg.ineligible = True
            agg.flags += flags

    template = get_template(EmailType.NON_SELECTION)
    drafts: list[SupplierEmailDraft] = []
    for supplier_id, by_lot in lost.items():
        supplier_name = sup_name.get(supplier_id, supplier_id[:8])
        rows = []
        for (dc_id, lot_id), agg in sorted(
            by_lot.items(),
            key=lambda kv: (dc_name.get(kv[0][0], kv[0][0]), lot_name.get(kv[0][1], kv[0][1])),
        ):
            count = Decimal(agg.count)
            avg_bid = agg.bid_sum / count
            avg_low = agg.low_sum / count
            prem_pct = (avg_bid - avg_low) / avg_low if avg_low > 0 else Decimal("0")
            rows.append(
                {
                    "DC": dc_name.get(dc_id, dc_id[:6]),
                    "Lot": lot_name.get(lot_id, lot_id[:6]),
                    "BidPrice": _money(avg_bid),
                    "BenchmarkPrice": _money(avg_low),
                    "PremiumPct": _pct(prem_pct),
                    "ReasonCode": _rejection_reason(agg.ineligible, agg.flags),
                }
            )
        context = {
            "SupplierName": supplier_name,
            "SupplierID": supplier_id,
            "CycleName": cycle_view.cycle_name,
            "CycleID": cycle_view.cycle_id,
            "BuyerName": buyer_name,
            "BuyerTitle": buyer_title,
        }
        rendered = render(template, context, tables={"RejectionReasonTable": rows})
        drafts.append(
            SupplierEmailDraft(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                email_type=template.email_type,
                subject=rendered.subject,
                body=rendered.body,
                missing=list(rendered.missing),
            )
        )
    drafts.sort(key=lambda d: d.supplier_name)
    return drafts
