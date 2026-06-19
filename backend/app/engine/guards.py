"""Decision-support restraint: the BANNED_DECISION_WORDS guard (ADR-0006, SPIKE_D2 §4).

The engine computes, scores, compares, and *proposes* — a human selects. It must never emit a
human-facing label that reads as an asserted award verdict. Any label the engine attaches to a
scenario or a recommendation surface is screened here; an asserted decision verb RAISES rather
than ships. This is the same restraint the as-built carried, preserved through the rebuild.

Pure: stdlib only.
"""

from __future__ import annotations

import re

#: Verbs/phrases that would assert an award decision instead of proposing one. Non-empty by
#: contract (the quality suite asserts this list is non-empty and enforced, S3).
BANNED_DECISION_WORDS: tuple[str, ...] = (
    "awarded",
    "award to",
    "won",
    "winner",
    "selected",
    "final decision",
    "must award",
    "shall award",
    "you will award",
    "is awarded",
    "contract granted",
    "approved for award",
)


class BannedDecisionWordError(ValueError):
    """Raised when a human-facing engine label asserts an award decision."""


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def assert_decision_support(label: str) -> str:
    """Return `label` unchanged iff it carries no banned decision verb; else RAISE.

    Word-boundary aware so benign substrings (e.g. "reward", "lawned") do not trip it, while
    phrases ("award to") still match. Used to screen every scenario label/description.
    """

    haystack = _normalize(label)
    for banned in BANNED_DECISION_WORDS:
        phrase = _normalize(banned)
        pattern = r"\b" + re.escape(phrase).replace(r"\ ", r"\s+") + r"\b"
        if re.search(pattern, haystack):
            raise BannedDecisionWordError(
                f"Decision-support violation: label {label!r} asserts an award "
                f"(matched banned phrase {banned!r}). The engine proposes; a human decides."
            )
    return label
