"""Deterministic template-merge for supplier communications (E-37).

The buyer authors plain-text email templates with placeholders written as `[#PlaceholderName]`
(square brackets, a leading `#`, then a name). This module PARSES those placeholders and FILLS them
from a context of governed-data values — a deterministic mail-merge, NOT AI/LLM generation: the same
reproducible, auditable pattern as the workbook generators, just emitting email text.

Strictness (no silent holes): a placeholder the context can't fill is REPORTED and LEFT IN PLACE —
the literal `[#Name]` stays in the output — so a draft never goes out with an invisible gap; the
caller can refuse to mark a draft ready/SENT while `missing` is non-empty.

Pure stdlib — no DB, no app imports — so it is trivially testable and reusable by every touchpoint.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

# A placeholder token: `[#Name]` — a leading `#` then letters/digits/underscore, inside square
# brackets, with the `]` immediately after the name. e.g. [#SupplierName], [#DueDate]. A bracketed
# run that isn't this exact shape (`[plain]`, `[# spaced]`, `[#]`) is NOT a token and is left as-is.
_TOKEN = re.compile(r"\[#([A-Za-z0-9_]+)\]")


@dataclass(frozen=True)
class MergeResult:
    """The filled text + an account of which placeholders were used and which couldn't be filled."""

    text: str
    # Placeholder names filled from the context, in first-seen order.
    used: tuple[str, ...]
    # Placeholder names present in the template but absent/blank in the context (left in the text).
    missing: tuple[str, ...]


def placeholders(template: str) -> list[str]:
    """The distinct placeholder names a template references, in first-seen order.

    Lets a caller show the buyer which `[#...]` fields a template needs (and check them against the
    available vocabulary) before any data is merged.
    """

    seen: list[str] = []
    for match in _TOKEN.finditer(template):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def merge(template: str, context: Mapping[str, str]) -> MergeResult:
    """Fill every `[#Name]` in `template` from `context[Name]`; report (and keep) the ones it can't.

    A placeholder is "filled" only when the context carries a non-empty value for its name; an
    unknown name, a `None`, or an empty string counts as MISSING — its literal `[#Name]` is left in
    the text so the gap is visible, and the name is collected in `missing`. Deterministic: the same
    template + context always yields the same result.
    """

    used: list[str] = []
    missing: list[str] = []

    def _fill(match: re.Match[str]) -> str:
        name = match.group(1)
        value = context.get(name)
        if value is not None and value != "":
            if name not in used:
                used.append(name)
            return value
        if name not in missing:
            missing.append(name)
        return match.group(0)  # leave `[#Name]` in place — a visible hole, not a silent blank

    text = _TOKEN.sub(_fill, template)
    return MergeResult(text=text, used=tuple(used), missing=tuple(missing))
