"""DB-backed deliverable registry — every run output rendered on request (ADR-0018, NFS Slice 1).

The web console stores NO files server-side: each deliverable is generated from the governed DB on
request and streamed. This module is the single source of truth for WHAT a run can produce and HOW
each item renders. `enumerate_deliverables` reads ONLY the governed cycle state (`cyc.*`, `eng.*`,
`awd.*`) — never the vault folder — and returns one `Deliverable` per item the run would have
written to `outputs/`/`inputs/` today, with the SAME normalized filename (`stage_filename`/`_stage`)
and a deferred `render(session) -> bytes` callable that reproduces the exact workbook bytes.

It enumerates:
  * the Setup/Kickoff workbook (always — stage 1);
  * one bid template per `cyc.cycle_round` (stage 2/5/...);
  * one alignment workbook per SEALED `eng.analysis_run`, at its 1-based version seq (stage 4/7);
  * when an `awd.award` is FROZEN: the internal booking guide + the combined supplier guides + one
    per-supplier guide per awarded supplier (stage 8);
  * one post-award adjustments doc per `awd.award_adjustment` version (stage 9).

Names match exactly what `run_round`/`freeze_award`/`record_adjustment` write to disk today, so the
console's file list / download / archive (Slice 5) is a faithful projection of the on-disk runtime.

This module is READ-ONLY new surface: it renders via the Slice-0 bytes builders and reuses the
`PilotService` view helpers (scenario/frozen award views, version seq, effective config) so the
render path can never diverge from the harness write path. Provenance: `rehearsal` stamps SYNTHETIC.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.cycle.loader import load_cycle
from app.cycle.scope import build_scope_from_cycle
from app.domain.awd.read import list_awards
from app.domain.awd.service import award_versions
from app.domain.bid.template_generator import generate_template_bytes
from app.domain.eng.read import list_analyses
from app.output.booking_guide import (
    BookingAwardView,
    build_booking_guide_internal_bytes,
    build_supplier_award_guide_bytes,
    build_supplier_award_guides_bytes,
    supplier_guide_label,
)
from app.output.post_award_doc import build_post_award_adjustments_bytes
from app.output.scenario_workbook import build_scenario_workbook_bytes
from app.pilot.setup_template import build_setup_workbook
from app.pilot.vault import stage_filename

DeliverableKind = Literal["input", "output"]


@dataclass(frozen=True)
class Deliverable:
    """One render-on-request deliverable: its normalized filename, kind, and a deferred renderer.

    `name` is the SAME `stage_filename` the harness writes to disk today; `kind` is whether the
    harness wrote it to `inputs/` (setup, bid template) or `outputs/` (alignment, guides,
    post-award) — the console's file listing labels by this. `render(session)` produces the
    workbook bytes from the governed records; deferred so a listing can enumerate lazily.
    """

    name: str
    kind: DeliverableKind
    render: Callable[[Session], bytes]


# Stage numbers mirror `PilotService._stage` (the normalized workflow-stage numbering, §2). Kept
# here as a tiny standalone helper so the registry has no dependency on the service for naming.
def _stage(kind: str, round_no: int = 0) -> int:
    if kind == "bid_template":
        return 2 + (round_no - 1) * 3
    if kind == "alignment":
        return 4 + (round_no - 1) * 3
    if kind == "booking_guide":
        return 8
    if kind == "post_award":
        return 9
    raise ValueError(f"unknown stage kind {kind!r}")


def enumerate_deliverables(
    session: Session,
    *,
    cycle_id: str | None,
    slug: str,
    rehearsal: bool,
) -> list[Deliverable]:
    """Every deliverable the run can produce, derived from the governed DB state alone (no files).

    `cycle_id` None (setup not ingested yet) yields just the Setup/Kickoff workbook — the one thing
    a run can always produce. With a cycle, the bid templates, sealed-analysis alignment workbooks,
    frozen-award booking guides, and post-award adjustment docs are enumerated from `cyc.*`/`eng.*`/
    `awd.*`. `rehearsal` stamps the generated artifacts SYNTHETIC (mirrors `is_rehearsal`).
    """

    items: list[Deliverable] = []

    # Stage 1 — the Setup/Kickoff workbook is always producible (no cycle needed; it's the template
    # the buyer fills in to CREATE the cycle).
    items.append(
        Deliverable(
            name=stage_filename(1, "setup_kickoff"),
            kind="input",
            render=_render_setup,
        )
    )

    if cycle_id is None:
        return items

    cycle = load_cycle(session, cycle_id)

    # Stage 2/5/... — one owned bid template per round.
    for round_no, _round in enumerate(cycle.rounds, start=1):
        items.append(
            Deliverable(
                name=stage_filename(
                    _stage("bid_template", round_no), f"round{round_no}_bid_template"
                ),
                kind="input",
                render=partial(_render_bid_template, cycle_id=cycle_id, round_no=round_no),
            )
        )

    # Stage 4/7/... — one alignment workbook per SEALED analysis run, at its version seq. The
    # round_number + version ordinal come straight from the read layer (the same ordinal the
    # workbook heading carries), so the filename matches `run_round` exactly.
    for summary in list_analyses(session, cycle_id):
        items.append(
            Deliverable(
                name=stage_filename(
                    _stage("alignment", summary.round_number),
                    f"round{summary.round_number}_alignment",
                    version=summary.version,
                ),
                kind="output",
                render=partial(
                    _render_alignment,
                    cycle_id=cycle_id,
                    analysis_run_id=summary.analysis_run_id,
                    rehearsal=rehearsal,
                ),
            )
        )

    # Stage 8 — when an award is FROZEN: the internal booking guide, the combined supplier guides,
    # and one per-supplier guide per awarded supplier (the sendable artifacts).
    guide_stage = _stage("booking_guide")
    for award in list_awards(session, cycle_id):
        items.append(
            Deliverable(
                name=stage_filename(guide_stage, "award_booking_guide"),
                kind="output",
                render=partial(
                    _render_booking_internal,
                    cycle_id=cycle_id,
                    award_id=award.award_id,
                    scenario_code=award.scenario_code,
                    rehearsal=rehearsal,
                ),
            )
        )
        items.append(
            Deliverable(
                name=stage_filename(guide_stage, "award_supplier_guides"),
                kind="output",
                render=partial(
                    _render_supplier_guides,
                    cycle_id=cycle_id,
                    award_id=award.award_id,
                    scenario_code=award.scenario_code,
                    rehearsal=rehearsal,
                ),
            )
        )
        # One INDIVIDUAL file per awarded supplier — named exactly as `freeze_award` writes them
        # (award-id-stamped so a later freeze never shadows an earlier award's per-supplier file).
        awarded_supplier_ids = {
            sup_id
            for (sup_id,) in session.execute(
                text("SELECT DISTINCT supplier_id FROM awd.award_line WHERE award_id = :aid"),
                {"aid": award.award_id},
            ).all()
        }
        for sup in cycle.suppliers:
            if sup.id not in awarded_supplier_ids:
                continue
            items.append(
                Deliverable(
                    name=stage_filename(
                        guide_stage,
                        supplier_guide_label(award.award_id, award.award_code, sup.name, sup.id),
                    ),
                    kind="output",
                    render=partial(
                        _render_supplier_guide,
                        cycle_id=cycle_id,
                        award_id=award.award_id,
                        scenario_code=award.scenario_code,
                        supplier_id=sup.id,
                        rehearsal=rehearsal,
                    ),
                )
            )

        # Stage 9 — one post-award adjustments doc per ADJUSTMENT version (v1..vN; v0 is the frozen
        # baseline, which `record_adjustment` never writes a separate doc for).
        for version in award_versions(session, award_id=award.award_id):
            version_no = int(version["version_no"])
            if version_no == 0:
                continue
            items.append(
                Deliverable(
                    name=stage_filename(_stage("post_award"), "post_award", version=version_no),
                    kind="output",
                    render=partial(
                        _render_post_award, award_id=award.award_id, version_no=version_no
                    ),
                )
            )

    return items


# --------------------------------------------------------------------------- #
# render helpers — reconstruct the exact view inputs the harness write path uses
# --------------------------------------------------------------------------- #
def _render_setup(_session: Session) -> bytes:
    """The Setup/Kickoff workbook (no DB needed — the blank template the buyer fills in)."""

    return build_setup_workbook()


def _render_bid_template(session: Session, *, cycle_id: str, round_no: int) -> bytes:
    """A round's owned bid template — built from the cycle scope (per `generate_bid_template`)."""

    cycle = load_cycle(session, cycle_id)
    scope = build_scope_from_cycle(cycle, round_no)
    return generate_template_bytes(scope)


def _render_alignment(
    session: Session, *, cycle_id: str, analysis_run_id: str, rehearsal: bool
) -> bytes:
    """Render the alignment workbook for a sealed run — mirrors `PilotService.run_round`'s write.

    Rebuilds the run's effective config (the cycle's weight preset + the four engine safeties) and
    the in-flight Scenario-B award split exactly as `run_round` does, so the on-request bytes are
    data-identical to the workbook the harness saved at seal time (E-39).
    """

    from app.pilot.service import _DEFAULT_CONFIG, PilotService

    cycle = load_cycle(session, cycle_id)
    helper = PilotService.__new__(PilotService)  # view helpers only; no vault/db state needed
    config = PilotService._apply_cycle_preset(_DEFAULT_CONFIG, cycle)
    config = PilotService._apply_cycle_safeties(config, cycle)
    final_round_id = PilotService._analysis_round_id(session, analysis_run_id)
    award = helper._scenario_award_view(session, cycle, analysis_run_id, scenario_code="B")
    return build_scenario_workbook_bytes(
        session,
        cycle,
        config,
        analysis_run_id,
        final_round_id,
        award,
        synthetic=rehearsal,
    )


def _frozen_award_view(
    session: Session, cycle_id: str, award_id: str, scenario_code: str
) -> BookingAwardView:
    """The booking `AwardView` from a FROZEN award's baseline lines (mirrors the service helper)."""

    from app.pilot.service import PilotService

    cycle = load_cycle(session, cycle_id)
    helper = PilotService.__new__(PilotService)
    return helper._frozen_award_view(session, cycle, award_id, scenario_code)


def _render_booking_internal(
    session: Session, *, cycle_id: str, award_id: str, scenario_code: str, rehearsal: bool
) -> bytes:
    """The internal (buyers/pricing) booking guide for a frozen award."""

    cycle = load_cycle(session, cycle_id)
    award = _frozen_award_view(session, cycle_id, award_id, scenario_code)
    return build_booking_guide_internal_bytes(cycle, award, synthetic=rehearsal)


def _render_supplier_guides(
    session: Session, *, cycle_id: str, award_id: str, scenario_code: str, rehearsal: bool
) -> bytes:
    """The combined per-supplier award guides (a sheet per awarded supplier) for a frozen award."""

    cycle = load_cycle(session, cycle_id)
    award = _frozen_award_view(session, cycle_id, award_id, scenario_code)
    return build_supplier_award_guides_bytes(cycle, award, synthetic=rehearsal)


def _render_supplier_guide(
    session: Session,
    *,
    cycle_id: str,
    award_id: str,
    scenario_code: str,
    supplier_id: str,
    rehearsal: bool,
) -> bytes:
    """One supplier's individual award guide bytes (only that supplier's awarded cells)."""

    cycle = load_cycle(session, cycle_id)
    award = _frozen_award_view(session, cycle_id, award_id, scenario_code)
    data = build_supplier_award_guide_bytes(cycle, award, supplier_id, synthetic=rehearsal)
    # An awarded supplier always has cells (we only enumerate awarded suppliers), so bytes is not
    # None here; guard anyway so a render never returns None to the streaming layer.
    if data is None:  # pragma: no cover — awarded suppliers always have cells
        raise ValueError(f"supplier {supplier_id!r} has no awarded cells on award {award_id!r}")
    return data


def _render_post_award(session: Session, *, award_id: str, version_no: int) -> bytes:
    """The post-award adjustments doc as of a given version (mirrors `record_adjustment`)."""

    return build_post_award_adjustments_bytes(session, award_id=award_id, as_of_version=version_no)
