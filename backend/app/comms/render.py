"""Structured email templates + the table-aware render for supplier comms (E-37).

`merge` (merge.py) fills scalar `[#Name]` placeholders. This layer adds the two structures the
buyer's authored templates use:

  * a SUBJECT line with machine-readable bracket tags first — e.g.
    `[RFP:[#CycleID]] [SUP:[#SupplierID]] Invitation – [#CycleName]`. The literal `[RFP:` / `[SUP:`
    wrappers and trailing `]` are kept; only the inner `[#...]` tokens merge, so a downstream parser
    (Power Automate) routes on a stable tag even if the human wording changes.
  * TABLE/block placeholders (e.g. `[#IncompleteBidTable]`) that expand to a header + one row per
    data record, each row built from a row-template (`[#DC] | [#Lot] | ...`).

A `CommsTemplate` is authored content (subject + body + its table specs); `render` fills it from a
scalar context + per-table row lists and reports any placeholder it couldn't fill (`missing`), so a
draft never goes out with an invisible hole.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.comms.merge import merge


@dataclass(frozen=True)
class TableSpec:
    """A table/block placeholder: its `[#name]`, the column headers, and the per-row template."""

    name: str  # the body placeholder name, e.g. "IncompleteBidTable"
    columns: tuple[str, ...]  # header labels
    row: str  # the per-row template, e.g. "[#DC] | [#Lot] | [#Item]"


@dataclass(frozen=True)
class CommsTemplate:
    """One touchpoint's authored email: machine tag + subject + body + its table specs."""

    email_type: str
    subject: str
    body: str
    tables: tuple[TableSpec, ...] = ()


@dataclass(frozen=True)
class EmailDraft:
    """A rendered draft: the filled subject + body, plus any placeholder left unfilled."""

    subject: str
    body: str
    missing: tuple[str, ...]


def _render_table(spec: TableSpec, rows: Sequence[Mapping[str, str]]) -> tuple[str, list[str]]:
    """Render a table block (header + separator + one merged row per record).

    Returns the text and the names of any per-row placeholder that couldn't be filled.
    """

    header = " | ".join(spec.columns)
    separator = "-" * len(header)
    missing: list[str] = []
    if not rows:
        return f"{header}\n{separator}\n(none)", missing
    lines = [header, separator]
    for row in rows:
        result = merge(spec.row, row)
        for name in result.missing:
            if name not in missing:
                missing.append(name)
        lines.append(result.text)
    return "\n".join(lines), missing


def render(
    template: CommsTemplate,
    context: Mapping[str, str],
    tables: Mapping[str, Sequence[Mapping[str, str]]] | None = None,
) -> EmailDraft:
    """Fill `template` from a scalar `context` + per-table row lists into a subject + body draft.

    Tables expand first (each `[#XxxTable]` -> a rendered block), then the scalar `[#Name]` tokens
    in the body + subject merge. Any placeholder with no value (scalar or row) is left visibly in
    place and collected in `missing`, so a draft never goes out with an invisible gap.
    """

    table_rows = tables or {}
    missing: list[str] = []

    body = template.body
    for spec in template.tables:
        rendered, table_missing = _render_table(spec, list(table_rows.get(spec.name, [])))
        for name in table_missing:
            if name not in missing:
                missing.append(name)
        body = body.replace(f"[#{spec.name}]", rendered)

    body_result = merge(body, context)
    subject_result = merge(template.subject, context)
    for name in (*subject_result.missing, *body_result.missing):
        if name not in missing:
            missing.append(name)

    return EmailDraft(subject=subject_result.text, body=body_result.text, missing=tuple(missing))
