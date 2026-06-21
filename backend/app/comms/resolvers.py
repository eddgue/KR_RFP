"""Per-touchpoint field resolvers (E-37): pull governed data into a rendered comms draft.

The pure render core (`merge`/`render`/`templates`) fills placeholders from a context; these
resolvers BUILD that context from the governed store for a given touchpoint, then render one draft
per supplier. Draft-only — the buyer reviews/edits/sends; nothing here sends.

Routing tags use the canonical machine ids (`cycle_id` / `supplier_id`) so a downstream parser
(Power Automate) matches a stable key; the human-readable cycle/supplier NAMES are carried
separately in the body.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comms.render import render
from app.comms.templates import EmailType, get_template
from app.domain.awd.read import award_detail
from app.domain.cyc.models import CycleTimeframe
from app.output.types import CycleView


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
