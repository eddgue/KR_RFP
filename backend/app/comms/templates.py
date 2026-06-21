"""The seven authored supplier-comms email templates (E-37) — buyer content, stored verbatim.

Each `CommsTemplate` pairs a machine-readable subject (bracket tags first, so a downstream router
parses on a stable tag) with the buyer's authored body — kept verbatim as a `.txt` data file under
`templates/` (NOT a Python string, so the prose is never reflowed by formatters and the buyer can
edit it directly) — plus the specs for the body's `[#XxxTable]` blocks. Filled by
`app.comms.render.render` from governed data.

Neutral, process-driven, fully data-backed. v1 lives in-repo (templates are versioned data, like the
workbook generators); making them buyer-editable at runtime is a later E-37 increment. NOTE: the
feedback `DCSummaryTable` columns are INFERRED (the author specified only the Hard/Soft ask tables).
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from app.comms.render import CommsTemplate, TableSpec

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Subject standard: machine-readable routing tags FIRST (RFP + supplier), then the human-readable
# infix + cycle name — so a downstream parser routes on the tags even if the wording moves.
_TAGS = "[RFP:[#CycleID]] [SUP:[#SupplierID]]"


def _subject(infix: str) -> str:
    """A subject line: the routing tags, the type infix (may carry `[#RoundNumber]`), the cycle."""

    return f"{_TAGS} {infix} – [#CycleName]"


def _body(filename: str) -> str:
    """Load an authored body verbatim from its `.txt` data file (trailing newline trimmed)."""

    return (_TEMPLATE_DIR / filename).read_text(encoding="utf-8").rstrip("\n")


class EmailType(StrEnum):
    """The seven supplier-comms touchpoints (the value is the machine tag used in the subject)."""

    INVITATION = "Invitation"
    TEMPLATE = "Template"
    INCOMPLETE_BID = "Incomplete Bid"
    ROUND_FEEDBACK = "Round Feedback"
    AWARD = "Award Notification"
    NON_SELECTION = "RFP Results"
    PBA = "PBA Transmittal"


_INVITATION = CommsTemplate(
    email_type=EmailType.INVITATION,
    subject=_subject("Invitation"),
    body=_body("invitation.txt"),
)

_TEMPLATE = CommsTemplate(
    email_type=EmailType.TEMPLATE,
    subject=_subject("Template – Round [#RoundNumber]"),
    body=_body("template.txt"),
)

_INCOMPLETE_BID = CommsTemplate(
    email_type=EmailType.INCOMPLETE_BID,
    subject=_subject("Incomplete Bid"),
    body=_body("incomplete_bid.txt"),
    tables=(
        TableSpec(
            name="IncompleteBidTable",
            columns=("DC", "Lot", "Item", "Timeframe", "Missing Fields"),
            row="[#DC] | [#Lot] | [#Item] | [#Timeframe] | [#MissingFields]",
        ),
    ),
)

_ROUND_FEEDBACK = CommsTemplate(
    email_type=EmailType.ROUND_FEEDBACK,
    subject=_subject("Round [#RoundNumber] Feedback"),
    body=_body("round_feedback.txt"),
    tables=(
        TableSpec(
            name="DCSummaryTable",
            columns=(
                "DC",
                "Lots Above Target",
                "Avg $ Premium",
                "Avg % Premium",
                "Estimated Weekly Impact",
            ),
            row="[#DC] | [#LotsAboveTarget] | [#AvgDollarPremium] | [#AvgPercentPremium] | [#EstWeeklyImpact]",  # noqa: E501
        ),
        TableSpec(
            name="HardAskTable",
            columns=("DC", "Lot", "Issue", "Current Value", "Required Improvement"),
            row="[#DC] | [#Lot] | [#IssueReason] | [#CurrentMetric] | [#TargetMetric]",
        ),
        TableSpec(
            name="SoftAskTable",
            columns=("DC", "Lot", "Premium %", "Market Benchmark", "Improvement Opportunity"),
            row="[#DC] | [#Lot] | [#PremiumPct] | [#BenchmarkPrice] | [#SuggestedTarget]",
        ),
    ),
)

_AWARD = CommsTemplate(
    email_type=EmailType.AWARD,
    subject=_subject("Award Notification"),
    body=_body("award.txt"),
)

_NON_SELECTION = CommsTemplate(
    email_type=EmailType.NON_SELECTION,
    subject=_subject("RFP Results"),
    body=_body("non_selection.txt"),
    tables=(
        TableSpec(
            name="RejectionReasonTable",
            columns=("DC", "Lot", "Submitted Price", "Benchmark Price", "Difference %", "Reason"),
            row="[#DC] | [#Lot] | [#BidPrice] | [#BenchmarkPrice] | [#PremiumPct] | [#ReasonCode]",
        ),
    ),
)

_PBA = CommsTemplate(
    email_type=EmailType.PBA,
    subject=_subject("PBA Transmittal"),
    body=_body("pba.txt"),
)


# The registry: every touchpoint -> its authored template.
REGISTRY: dict[EmailType, CommsTemplate] = {
    EmailType.INVITATION: _INVITATION,
    EmailType.TEMPLATE: _TEMPLATE,
    EmailType.INCOMPLETE_BID: _INCOMPLETE_BID,
    EmailType.ROUND_FEEDBACK: _ROUND_FEEDBACK,
    EmailType.AWARD: _AWARD,
    EmailType.NON_SELECTION: _NON_SELECTION,
    EmailType.PBA: _PBA,
}


def get_template(email_type: EmailType) -> CommsTemplate:
    """The authored template for a touchpoint."""

    return REGISTRY[email_type]
