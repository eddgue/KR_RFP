"""Table-aware render over the seven authored supplier-comms templates (E-37)."""

from __future__ import annotations

from app.comms.render import render
from app.comms.templates import REGISTRY, EmailType, get_template

# A full scalar context for the invitation (every placeholder it needs).
_INVITE_CTX = {
    "SupplierName": "Acme Produce",
    "CycleName": "Tomato 2026",
    "CycleID": "KR-2026-TOM",
    "SupplierID": "DIVINE",
    "ProcessStartDate": "2026-05-01",
    "BidDueDate": "2026-05-15",
    "RoundCount": "2",
    "EstimatedAwardDate": "2026-06-01",
    "DeliveryStartDate": "2026-05-24",
    "DeliveryEndDate": "2026-10-10",
    "BuyerName": "J. Buyer",
    "BuyerTitle": "Sourcing Manager",
}


def test_subject_keeps_machine_tags_and_merges_inner_tokens() -> None:
    draft = render(
        get_template(EmailType.INVITATION),
        {"CycleID": "KR-2026-TOM", "SupplierID": "DIVINE", "CycleName": "Tomato 2026"},
    )
    # The literal [RFP:...] / [SUP:...] wrappers survive; only the inner tokens merge.
    assert draft.subject == "[RFP:KR-2026-TOM] [SUP:DIVINE] Invitation – Tomato 2026"


def test_scalar_body_fills_and_reports_nothing_missing() -> None:
    draft = render(get_template(EmailType.INVITATION), _INVITE_CTX)
    assert "Dear Acme Produce," in draft.body
    assert "Bid Submission Deadline: 2026-05-15" in draft.body
    assert "Estimated Number of Rounds: 2" in draft.body
    assert "J. Buyer" in draft.body
    assert draft.missing == ()


def test_missing_scalar_is_left_in_place_and_reported() -> None:
    draft = render(get_template(EmailType.INVITATION), {"SupplierName": "Acme"})
    assert "Dear Acme," in draft.body
    assert "[#BidDueDate]" in draft.body  # a visible hole, not a silent blank
    assert "BidDueDate" in draft.missing


def test_table_expands_to_header_plus_rows() -> None:
    draft = render(
        get_template(EmailType.INCOMPLETE_BID),
        {
            "SupplierName": "Acme",
            "CycleName": "Tomato",
            "CycleID": "K",
            "SupplierID": "S",
            "CorrectionDueDate": "2026-05-20",
            "BuyerName": "B",
            "BuyerTitle": "T",
        },
        tables={
            "IncompleteBidTable": [
                {
                    "DC": "Dallas",
                    "Lot": "Roma",
                    "Item": "Roma 25lb",
                    "Timeframe": "Spring",
                    "MissingFields": "All-In $/case",
                },
                {
                    "DC": "Atlanta",
                    "Lot": "Grape",
                    "Item": "Grape pint",
                    "Timeframe": "Spring",
                    "MissingFields": "FOB $/case, Weekly Vol",
                },
            ]
        },
    )
    assert "DC | Lot | Item | Timeframe | Missing Fields" in draft.body
    assert "Dallas | Roma | Roma 25lb | Spring | All-In $/case" in draft.body
    assert "Atlanta | Grape | Grape pint | Spring | FOB $/case, Weekly Vol" in draft.body
    assert "[#IncompleteBidTable]" not in draft.body  # the placeholder was expanded
    assert draft.missing == ()


def test_table_row_missing_field_is_reported() -> None:
    draft = render(
        get_template(EmailType.INCOMPLETE_BID),
        {"SupplierName": "Acme", "CycleName": "T", "CycleID": "K", "SupplierID": "S"},
        tables={"IncompleteBidTable": [{"DC": "Dallas", "Lot": "Roma"}]},
    )
    assert "MissingFields" in draft.missing
    assert "[#Item]" in draft.body  # the row's unfilled cell stays visible


def test_empty_table_renders_none_placeholder_block() -> None:
    draft = render(
        get_template(EmailType.INCOMPLETE_BID),
        {"SupplierName": "Acme"},
        tables={"IncompleteBidTable": []},
    )
    assert "(none)" in draft.body


def test_registry_covers_all_seven_touchpoints() -> None:
    assert set(REGISTRY) == set(EmailType)
    assert len(REGISTRY) == 7


def test_every_declared_table_placeholder_is_expanded() -> None:
    # Rendering with empty data must leave NO declared `[#XxxTable]` placeholder in any template.
    for email_type, tpl in REGISTRY.items():
        draft = render(tpl, {}, tables={})
        for spec in tpl.tables:
            assert f"[#{spec.name}]" not in draft.body, f"{email_type}: {spec.name} not expanded"
