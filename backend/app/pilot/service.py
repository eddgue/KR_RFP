"""`PilotService` — the pilot core's orchestration surface (PILOT_SYSTEM_DESIGN §3, §7).

Constructed with a `vault_root: Path`, the service drives the run-vault files directly and takes a
`session` on the methods that touch the governed Postgres store (the simplest of the two patterns in
the brief: vault files are managed here; DB writes ride the caller's unit of work, PLAN §7). It is
the thin layer the MCP server (PART B) will wrap.

Implemented here (PART A — pilot core, step 0):
  * `start_run`     — create the identical run folder + write the Setup/Kickoff workbook + commit.
  * `ingest_setup`  — ingest the uploaded setup workbook into the cycle, link cycle_id.txt, commit.
  * `remember`      — append a dated note to NOTES.md (optionally linking a memory file) + commit.
  * `add_memory`    — write a file into memory/ + link it from NOTES.md + commit.
  * `status`        — the kanban dict (Done/Doing/Next/Waiting).
  * `list_runs`     — every run in the vault.

PART B (the rest of the loop) is left as clearly-marked NotImplementedError stubs at the bottom:
generate_bid_template, ingest_bids, ingest_any, run_round, freeze_award, record_adjustment, history.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.comms.resolvers import (
    SupplierEmailDraft,
    award_drafts,
    feedback_drafts,
    rejection_drafts,
)
from app.core.audit.events import DomainEvent, EventType
from app.core.audit.recorder import client_id_for_cycle
from app.core.audit.writer import AuditWriter
from app.cycle.loader import load_cycle
from app.cycle.scope import build_scope_from_cycle
from app.domain.awd import service as awd_service
from app.domain.awd.models import Award, AwardLine
from app.domain.awd.read import (
    AwardDetail,
    AwardSummary,
)
from app.domain.awd.read import (
    award_detail as read_award_detail,
)
from app.domain.awd.read import (
    list_awards as read_list_awards,
)
from app.domain.bid.bid_ingester import (
    Completeness,
    ParsedBidLine,
    ParsedCapacityLine,
    ingest_capacity,
    ingest_template,
)
from app.domain.bid.models import BidLine, CapacityConstraint, CapacityStatement
from app.domain.bid.template_generator import generate_template_bytes
from app.domain.eng.models import AnalysisRun
from app.domain.eng.read import (
    AnalysisSummary,
    ScenarioComparisonRow,
    ScenarioDetail,
)
from app.domain.eng.read import (
    list_analyses as read_list_analyses,
)
from app.domain.eng.read import (
    scenario_comparison as read_scenario_comparison,
)
from app.domain.eng.read import (
    scenario_detail as read_scenario_detail,
)
from app.domain.eng.runner import EngineRunner, IncumbentRow
from app.engine.interface import PRESET_WEIGHTS, EngineConfig, WeightPreset
from app.fiscal.calendar import FiscalPeriod, all_periods, period_for_date
from app.output.booking_guide import (
    BookingAwardView,
    supplier_guide_label,
    write_booking_guide_internal_xlsx,
    write_supplier_award_guide_files,
    write_supplier_award_guides_xlsx,
)
from app.output.post_award_doc import write_post_award_adjustments_xlsx
from app.output.scenario_workbook import write_scenario_workbook_xlsx
from app.output.types import CycleView
from app.pilot import status as status_mod
from app.pilot.flex_ingest import MappingProposal, apply_mapping, infer_bid_mapping
from app.pilot.run_db import (
    drop_run_database,
    dump_run_database,
    provision_run_database,
    restore_run_database,
)
from app.pilot.setup_ingest import ingest_setup_workbook
from app.pilot.setup_template import build_setup_workbook
from app.pilot.vault import (
    SUBDIR_INPUTS,
    SUBDIR_MEMORY,
    RunPaths,
    archive_run,
    create_run,
    git_commit_run,
    is_rehearsal,
    list_runs,
    purge_run,
    run_paths,
    stage_filename,
    write_to_run,
)

# The default engine strategy for a pilot run when the caller passes no config — a balanced preset
# mirroring the demo's. The setup workbook also carries the strategy; this is the safe fallback.
# Continuity is weighted at 0.20 (raised from 0.10): in a relationship-heavy, repeated-game
# category the engine should prefer the incumbent on a near-tie. It only retains a *price-eligible*
# incumbent — one over the premium ceiling is still gated, and that premium is surfaced for the
# human to decide (Incumbent Retention tab), never silently paid.
_BALANCED_WEIGHTS = PRESET_WEIGHTS[WeightPreset.BALANCED]  # single source of truth for the weights
_DEFAULT_CONFIG = EngineConfig(
    preset=WeightPreset.BALANCED,
    weight_price=_BALANCED_WEIGHTS["weight_price"],
    weight_coverage=_BALANCED_WEIGHTS["weight_coverage"],
    weight_historical=_BALANCED_WEIGHTS["weight_historical"],
    weight_zrisk=_BALANCED_WEIGHTS["weight_zrisk"],
    weight_continuity=_BALANCED_WEIGHTS["weight_continuity"],
    max_sup_dc=2,
    conc_thresh=Decimal("0.40"),
    global_premium_threshold=Decimal("0.12"),
    coverage_floor=Decimal("0.80"),
)


@dataclass(frozen=True)
class _BookingCell:
    """A booking-guide cell assembled from the FROZEN award + the cycle scope (BookingCellView)."""

    dc_id: str
    lot_id: str
    item_id: str
    tf_id: str
    supplier_id: str
    volume_share: Decimal
    awarded_price: Decimal
    period_cases: Decimal
    routing_baseline: Decimal


@dataclass(frozen=True)
class _BookingAward:
    """The frozen award shaped for the booking-guide generators (BookingAwardView)."""

    scenario_code: str
    scenario_label: str
    cells: tuple[_BookingCell, ...]


class PilotService:
    """Orchestrates the per-RFP run vault + the governed cycle store for the pilot loop."""

    def __init__(self, vault_root: Path, *, isolate_db: bool = True) -> None:
        self.vault_root = Path(vault_root)
        # D30: each run gets its OWN blank database. On by default (the compliant runtime); unit
        # tests that share a rolled-back session pass isolate_db=False.
        self.isolate_db = isolate_db

    # ------------------------------------------------------------------ #
    # step 0 — start run + setup
    # ------------------------------------------------------------------ #
    def start_run(self, *, commodity: str, label: str, rehearsal: bool = False) -> RunPaths:
        """Create the run scaffold + its OWN blank database, write the Setup/Kickoff workbook.

        D30: when `isolate_db` is on, the run is born with a freshly created + migrated database of
        its own — blank, no demo data, invisible to other runs. Callers then operate on this run
        via `run_unit_of_work(paths.slug)`. The kanban Next bucket points the sponsor at the setup.

        `rehearsal=True` marks the run SYNTHETIC (every artifact is stamped so, never "LIVE CYCLE
        DATA") — see `is_rehearsal`. If any step after the scaffold/DB is created fails, the partial
        run is torn down (folder removed + DB dropped) so a failed start never leaves an orphan.
        """

        paths = create_run(self.vault_root, commodity=commodity, label=label, rehearsal=rehearsal)
        try:
            if self.isolate_db:
                provision_run_database(paths.slug)
            setup_name = stage_filename(1, "setup_kickoff")
            write_to_run(paths, SUBDIR_INPUTS, setup_name, build_setup_workbook())

            board = status_mod.kanban(None, None, paths)
            status_mod.render_run_md(paths, board)
            git_commit_run(self.vault_root, paths.slug, "setup/kickoff workbook generated")
        except Exception:
            # A failed start must not leave an orphan run (vault folder + provisioned database).
            if self.isolate_db:
                drop_run_database(paths.slug)
            purge_run(self.vault_root, paths.slug)
            raise
        return paths

    def ingest_setup(self, session: Session, runpaths: RunPaths, uploaded: Path) -> str:
        """Ingest the uploaded (already-in-inputs/) setup workbook -> cycle; link + commit.

        Returns the new cycle_id. Writes it to cycle_id.txt and the RUN.md header, recomputes the
        kanban from the freshly-created cycle, and commits the vault.
        """

        data = Path(uploaded).read_bytes()
        cycle_id = ingest_setup_workbook(session, data)

        runpaths.cycle_id_file.write_text(cycle_id, encoding="utf-8")
        status_mod.set_header_field(runpaths, "Cycle", cycle_id)
        board = status_mod.kanban(session, cycle_id, runpaths)
        status_mod.render_run_md(runpaths, board)
        git_commit_run(self.vault_root, runpaths.slug, "setup ingested → cycle created")
        return cycle_id

    # ------------------------------------------------------------------ #
    # notes + memory
    # ------------------------------------------------------------------ #
    def remember(self, runpaths: RunPaths, note: str, *, related_file: str | None = None) -> None:
        """Append a dated entry to NOTES.md; if `related_file` given, record it lives in memory/."""

        self._append_note(runpaths, note, related_file=related_file)
        git_commit_run(self.vault_root, runpaths.slug, "note added")

    def add_memory(self, runpaths: RunPaths, filename: str, data: bytes, note: str) -> Path:
        """Write `data` into memory/, append the linked NOTES.md entry, commit; return the path."""

        path = write_to_run(runpaths, SUBDIR_MEMORY, filename, data)
        self._append_note(runpaths, note, related_file=filename)
        git_commit_run(self.vault_root, runpaths.slug, f"memory file added: {filename}")
        return path

    def _append_note(self, runpaths: RunPaths, note: str, *, related_file: str | None) -> None:
        today = datetime.now(UTC).date().isoformat()
        entry = f"- {today}: {note}"
        if related_file:
            entry += f" (file: `{related_file}` in memory/)"
        existing = (
            runpaths.notes_md.read_text(encoding="utf-8") if runpaths.notes_md.exists() else ""
        )
        runpaths.notes_md.write_text(existing.rstrip() + "\n" + entry + "\n", encoding="utf-8")

    # ------------------------------------------------------------------ #
    # status + listing
    # ------------------------------------------------------------------ #
    def status(self, session: Session, runpaths: RunPaths) -> dict[str, list[str]]:
        """The kanban dict for a run (reads its cycle id from cycle_id.txt if present)."""

        cycle_id = self._cycle_id(runpaths)
        return status_mod.kanban(session, cycle_id, runpaths)

    def list_runs(self) -> list[RunPaths]:
        """Every run folder in the vault (ordered by slug)."""

        return list_runs(self.vault_root)

    def run_paths(self, slug: str) -> RunPaths:
        """The `RunPaths` for an existing run slug."""

        return run_paths(self.vault_root, slug)

    def _cycle_id(self, runpaths: RunPaths) -> str | None:
        if not runpaths.cycle_id_file.exists():
            return None
        value = runpaths.cycle_id_file.read_text(encoding="utf-8").strip()
        return value or None

    # ================================================================== #
    # PART B — the rest of the cycle loop
    # ================================================================== #
    def generate_bid_template(self, session: Session, runpaths: RunPaths, round_no: int) -> Path:
        """Generate the owned bid template for a round into inputs/ (step 1, D21 key-validated).

        Loads the persisted cycle (`load_cycle`), builds the round's `CycleScope`
        (`build_scope_from_cycle`), runs the bid-template generator, writes the normalized
        `0X_round{n}_bid_template.xlsx` into inputs/, updates the kanban (Waiting: upload the
        round's bids), and commits the vault. Returns the written path.
        """

        cycle = self._load_cycle(session, runpaths)
        scope = build_scope_from_cycle(cycle, round_no)
        data = generate_template_bytes(scope)

        filename = stage_filename(
            self._stage("bid_template", round_no), f"round{round_no}_bid_template"
        )
        path = write_to_run(runpaths, SUBDIR_INPUTS, filename, data)

        self._render_kanban(
            session,
            runpaths,
            extra_waiting=[f"Fill in and upload the Round {round_no} bids (file `{filename}`)"],
        )
        git_commit_run(self.vault_root, runpaths.slug, f"round {round_no} bid template generated")
        return path

    def ingest_bids(
        self, session: Session, runpaths: RunPaths, round_no: int, uploaded: Path
    ) -> int:
        """Key-validated ingest of a returned bid file -> `bid.bid_line` rows (step 1); returns N.

        The file is already uploaded into inputs/ (the formal request→upload→ingest gate). Rebuilds
        the round scope, ingests OUR template via the strict KEY-VALIDATED path, persists one
        `bid.bid_line` per priced line (mirrors the demo's submission/source_artifact + bid_line
        pattern), records any quarantined rows in NOTES.md (surfaced, never silently dropped), and
        commits.
        """

        cycle = self._load_cycle(session, runpaths)
        scope = build_scope_from_cycle(cycle, round_no)
        round_id = cycle.rounds[round_no - 1].id

        data = Path(uploaded).read_bytes()
        result = ingest_template(data, scope)
        capacity = ingest_capacity(data, scope)
        count, superseded, cap_count = self._persist_bid_lines(
            session, cycle, round_id, result.lines, capacity.lines
        )

        if result.quarantined:
            self._append_note(
                runpaths,
                f"Round {round_no} bids: {len(result.quarantined)} row(s) quarantined and not "
                "loaded (key mismatch / bad number) — review before re-uploading.",
                related_file=None,
            )
        if capacity.quarantined:
            self._append_note(
                runpaths,
                f"Round {round_no} capacity: {len(capacity.quarantined)} row(s) quarantined and "
                "not loaded (key mismatch / bad number) — review before re-uploading.",
                related_file=None,
            )
        if cap_count:
            self._append_note(
                runpaths,
                f"Round {round_no} capacity: {cap_count} stated per-cell ceiling(s) loaded "
                "and stored. Allocation-vs-capacity is not yet surfaced in outputs "
                "(tracked as G-G / E-38b).",
                related_file=None,
            )
        if superseded:
            self._append_note(
                runpaths,
                f"Round {round_no} bids: superseded {superseded} prior bid line(s) — a newer "
                "submission replaced an earlier one for the same supplier(s) (no double-counting).",
                related_file=None,
            )
        self._render_kanban(session, runpaths)
        git_commit_run(
            self.vault_root,
            runpaths.slug,
            f"round {round_no} bids ingested → {count} bid line(s)",
        )
        return count

    def ingest_any(
        self,
        session: Session,
        runpaths: RunPaths,
        round_no: int,
        uploaded: Path,
        *,
        confirm: bool = False,
    ) -> MappingProposal | int:
        """Flexible "take my file as-is" ingest (PILOT_SYSTEM_DESIGN §4).

        `confirm=False` (default): INFER the messy file's column mapping against the cycle's known
        scope and RETURN the `MappingProposal` for the skill to show the buyer — nothing is written.
        `confirm=True`: APPLY the (confirmed) mapping to a clean key-stamped owned template, write
        it to inputs/ as the normalized `0X_round{n}_bids_normalized.xlsx`, then ingest it via the
        strict key-validated path (returns the bid-line count). Ambiguity surfaced, never guessed.
        """

        cycle = self._load_cycle(session, runpaths)
        scope = build_scope_from_cycle(cycle, round_no)
        data = Path(uploaded).read_bytes()

        proposal = infer_bid_mapping(data, cycle)
        if not confirm:
            return proposal

        cleaned = apply_mapping(data, proposal, scope)
        filename = stage_filename(
            self._stage("bids_normalized", round_no), f"round{round_no}_bids_normalized"
        )
        normalized_path = write_to_run(runpaths, SUBDIR_INPUTS, filename, cleaned)
        git_commit_run(
            self.vault_root,
            runpaths.slug,
            f"round {round_no} messy file normalized → owned template",
        )
        return self.ingest_bids(session, runpaths, round_no, normalized_path)

    def run_round(
        self,
        session: Session,
        runpaths: RunPaths,
        round_no: int,
        config: EngineConfig | None = None,
        *,
        synthetic: bool = False,
    ) -> Path:
        """Run the engine on a round -> sealed eng.* + the VERSIONED alignment workbook (step 2).

        Builds the `IncumbentRow`s from the loaded cycle, runs `EngineRunner.run_analysis` on the
        round, then writes the versioned alignment workbook (`write_scenario_workbook_xlsx`, which
        computes the `Analysis v{seq}` heading) into outputs/ as
        `0X_round{n}_alignment_v{seq}.xlsx`. Updates the kanban (Done: Round n analysis v{seq}) and
        commits. Returns the written path.
        """

        # A rehearsal run stamps every artifact SYNTHETIC regardless of the caller's flag, so its
        # output can never be mislabelled "LIVE CYCLE DATA — real names & prices".
        synthetic = synthetic or is_rehearsal(runpaths)

        cycle = self._load_cycle(session, runpaths)
        round_id = cycle.rounds[round_no - 1].id
        incumbents = tuple(
            IncumbentRow(
                dc_id=dc_id,
                lot_id=lot_id,
                supplier_id=sup_id,
                routing_cost_per_case=cycle.incumbent_routing.get((dc_id, lot_id)),
            )
            for (dc_id, lot_id), sup_id in cycle.incumbent_by_dc_lot.items()
        )

        # Honour the per-RFP strategy the buyer set at kickoff: the named weight preset (remaps the
        # five scoring weights) AND the four engine safeties (premium ceiling, coverage floor,
        # concentration threshold, max suppliers/DC) — each over the default, blank fields falling
        # back. EngineConfig is frozen, so both layers go on via model_copy.
        effective_config = self._apply_cycle_preset(config or _DEFAULT_CONFIG, cycle)
        effective_config = self._apply_cycle_safeties(effective_config, cycle)

        runner = EngineRunner(session)
        run_result = runner.run_analysis(
            cycle_id=cycle.cycle_id,
            round_id=round_id,
            config=effective_config,
            incumbents=incumbents,
            run_by="pilot-runner",
        )

        # Governed decision: the analysis run is sealed. Land a tamper-evident event in the same
        # transaction as the seal (Gap G-B) — identifiers + status only, no commercial values.
        AuditWriter(session).append(
            DomainEvent(
                event_type=EventType.SEALED,
                client_id=client_id_for_cycle(session, cycle.cycle_id),
                entity_type="eng.analysis_run",
                entity_id=uuid.UUID(run_result.analysis_run_id),
                cycle_id=uuid.UUID(cycle.cycle_id),
                actor="pilot-runner",
                source="worker",
                after={"round_id": round_id},
            )
        )

        # The booking-guide award isn't frozen yet; the alignment workbook needs an AwardView. Use
        # the engine's Scenario B split (the risk-adjusted recommendation) as the in-flight award.
        award = self._scenario_award_view(
            session, cycle, run_result.analysis_run_id, scenario_code="B"
        )
        version_seq = self._run_version_seq(session, cycle.cycle_id, run_result.analysis_run_id)
        filename = stage_filename(
            self._stage("alignment", round_no),
            f"round{round_no}_alignment",
            version=version_seq,
        )
        out_path = runpaths.outputs / filename
        write_scenario_workbook_xlsx(
            session,
            cycle,
            effective_config,
            run_result.analysis_run_id,
            round_id,
            award,
            output_path=out_path,
            synthetic=synthetic,
        )

        self._render_kanban(
            session,
            runpaths,
            extra_done=[f"Round {round_no} alignment analysis v{version_seq} ready"],
        )
        self.export_run_data(session, runpaths)
        self.feedback_file(session, runpaths)
        git_commit_run(
            self.vault_root,
            runpaths.slug,
            f"round {round_no} alignment analysis v{version_seq} sealed",
        )
        return out_path

    @staticmethod
    def _apply_cycle_preset(config: EngineConfig, cycle: CycleView) -> EngineConfig:
        """Remap the five scoring weights to the buyer's named preset (blank/unknown → unchanged).

        The setup workbook's "Weight Preset" is authoritative for the run. A named preset
        (balanced/price_focus/coverage_focus/risk_averse) swaps in its canonical weight vector;
        CUSTOM keeps the explicit weights as given (only the preset label is recorded). The ingester
        already rejects an unrecognized preset, so an unparseable value here is treated as "leave as
        is" rather than guessed.
        """

        if not cycle.weight_preset:
            return config
        try:
            preset = WeightPreset(cycle.weight_preset.strip().lower())
        except ValueError:
            return config
        weights = PRESET_WEIGHTS.get(preset)
        if weights is None:  # CUSTOM — keep the explicit weights, just record the label
            return config.model_copy(update={"preset": preset})
        return config.model_copy(update={"preset": preset, **weights})

    @staticmethod
    def _apply_cycle_safeties(config: EngineConfig, cycle: CycleView) -> EngineConfig:
        """Layer the cycle's per-RFP engine safeties over `config` (blank fields keep the preset).

        The buyer sets these at kickoff (setup workbook); they are authoritative for the run, so a
        value present on the cycle overrides the strategy-preset default. EngineConfig is frozen, so
        the override is applied via `model_copy`.
        """

        overrides: dict[str, object] = {}
        if cycle.premium_ceiling is not None:
            overrides["global_premium_threshold"] = cycle.premium_ceiling
        if cycle.coverage_floor is not None:
            overrides["coverage_floor"] = cycle.coverage_floor
        if cycle.conc_thresh is not None:
            overrides["conc_thresh"] = cycle.conc_thresh
        if cycle.max_sup_dc is not None:
            overrides["max_sup_dc"] = cycle.max_sup_dc
        return config.model_copy(update=overrides) if overrides else config

    def freeze_award(
        self,
        session: Session,
        runpaths: RunPaths,
        *,
        analysis_run_id: str,
        scenario_code: str = "B",
        award_code: str,
        actor: str = "pilot",
    ) -> str:
        """Freeze a selected scenario into awd.* + the booking guide(s) (step 4); returns award_id.

        Promotes the human-selected scenario (default B — the risk-adjusted recommendation) to a
        FROZEN award (`awd.freeze_award`), then writes the two-audience booking guide into outputs/
        (`0X_award_booking_guide.xlsx` + the per-supplier guides). Decision-support: the HUMAN
        asserts the award (ADR-0006). `actor` is who froze it — recorded as `frozen_by` and on the
        FROZEN audit event (the HTTP path passes the authenticated user; the MCP path defaults to
        "pilot"). Commits. Returns the award_id.
        """

        cycle = self._load_cycle(session, runpaths)
        award_id = awd_service.freeze_award(
            session,
            cycle_id=cycle.cycle_id,
            analysis_run_id=analysis_run_id,
            scenario_code=scenario_code,
            award_code=award_code,
            frozen_by=actor,
        )

        booking = self._frozen_award_view(session, cycle, award_id, scenario_code)
        internal_name = stage_filename(self._stage("booking_guide"), "award_booking_guide")
        supplier_name = stage_filename(self._stage("booking_guide"), "award_supplier_guides")
        synthetic = is_rehearsal(runpaths)
        write_booking_guide_internal_xlsx(
            cycle, booking, output_path=runpaths.outputs / internal_name, synthetic=synthetic
        )
        write_supplier_award_guides_xlsx(
            cycle, booking, output_path=runpaths.outputs / supplier_name, synthetic=synthetic
        )
        # Individual per-supplier files (the sendable artifacts — only that supplier's data), so the
        # award notification (E-37) can attach a supplier's OWN guide, never the combined workbook.
        guide_stage = self._stage("booking_guide")
        awarded_ids = {cell.supplier_id for cell in booking.cells}
        write_supplier_award_guide_files(
            cycle,
            booking,
            paths_by_supplier={
                sup.id: runpaths.outputs
                / stage_filename(
                    guide_stage, supplier_guide_label(award_id, award_code, sup.name, sup.id)
                )
                for sup in cycle.suppliers
                if sup.id in awarded_ids
            },
            synthetic=synthetic,
        )

        self._render_kanban(
            session, runpaths, extra_done=[f"Award {award_code} frozen — booking guides ready"]
        )
        self.export_run_data(session, runpaths)
        self.feedback_file(session, runpaths)
        git_commit_run(
            self.vault_root, runpaths.slug, f"award {award_code} frozen → booking guides"
        )
        return award_id

    def record_adjustment(
        self,
        session: Session,
        runpaths: RunPaths,
        *,
        award_id: str,
        adjustment_type: str,
        effective_date: date,
        reason: str,
        line_changes: list[tuple[str, str, str, str, Decimal]],
        actor: str = "pilot",
    ) -> Path:
        """Record a post-award adjustment as the next VERSION + its doc (step 5, ADR-0014).

        Appends the adjustment layer (`awd.add_adjustment`), then writes the versioned post-award
        workbook (`write_post_award_adjustments_xlsx`, which carries the `Version N · as of DATE`
        heading) into outputs/ as `0X_post_award_v{N}.xlsx`. Updates the kanban + commits. Returns
        the written path. `line_changes` are (dc_id, lot_id, tf_id, supplier_id, new_price) tuples.
        `actor` is who recorded it — stored as the version's `created_by` and on the CREATED audit
        event (the HTTP path passes the authenticated user; the MCP path defaults to "pilot").
        """

        version_no = awd_service.add_adjustment(
            session,
            award_id=award_id,
            adjustment_type=adjustment_type,
            effective_date=effective_date,
            reason=reason,
            created_by=actor,
            line_changes=line_changes,
        )

        filename = stage_filename(self._stage("post_award"), "post_award", version=version_no)
        out_path = runpaths.outputs / filename
        write_post_award_adjustments_xlsx(
            session, award_id=award_id, as_of_version=version_no, output_path=out_path
        )

        self._render_kanban(
            session, runpaths, extra_done=[f"Post-award adjustment v{version_no} recorded"]
        )
        self.export_run_data(session, runpaths)
        self.feedback_file(session, runpaths)
        git_commit_run(
            self.vault_root, runpaths.slug, f"post-award adjustment v{version_no} recorded"
        )
        return out_path

    def history(self, session: Session, runpaths: RunPaths) -> dict[str, object]:
        """The run's versions: sealed analysis runs + award adjustment versions + the output files.

        Returns a plain dict the skill can render: `analysis_runs` (each sealed `eng.analysis_run`
        with its 1-based version ordinal + round + sealed time), `awards` (each frozen award with
        its full version history v0→vN), and `output_files` (the versioned workbooks in outputs/).
        Any historical version's records/doc can be re-pulled from these handles.
        """

        cycle_id = self._cycle_id(runpaths)
        analysis_runs: list[dict[str, object]] = []
        awards: list[dict[str, object]] = []
        if cycle_id is not None:
            runs = list(
                session.execute(
                    select(AnalysisRun)
                    .where(AnalysisRun.cycle_id == cycle_id, AnalysisRun.is_sealed.is_(True))
                    .order_by(AnalysisRun.run_started_at)
                )
                .scalars()
                .all()
            )
            round_number_by_id: dict[str, int] = {
                row[0]: int(row[1])
                for row in session.execute(
                    text(
                        "SELECT round_id, round_number FROM cyc.cycle_round WHERE cycle_id = :cyc"
                    ),
                    {"cyc": cycle_id},
                ).all()
            }
            for seq, run in enumerate(runs, start=1):
                analysis_runs.append(
                    {
                        "version": seq,
                        "analysis_run_id": run.analysis_run_id,
                        "round_number": round_number_by_id.get(run.round_id, 0),
                        "engine_version": run.engine_version,
                        "sealed_at": run.run_finished_at,
                    }
                )

            award_rows = list(
                session.execute(
                    select(Award).where(Award.cycle_id == cycle_id).order_by(Award.frozen_at)
                )
                .scalars()
                .all()
            )
            for award in award_rows:
                awards.append(
                    {
                        "award_id": award.award_id,
                        "award_code": award.award_code,
                        "scenario_code": award.scenario_code,
                        "versions": awd_service.award_versions(session, award_id=award.award_id),
                    }
                )

        output_files = sorted(p.name for p in runpaths.outputs.glob("*.xlsx") if p.is_file())
        return {
            "cycle_id": cycle_id,
            "analysis_runs": analysis_runs,
            "awards": awards,
            "output_files": output_files,
        }

    def export_run_data(self, session: Session, runpaths: RunPaths) -> Path:
        """Write `<run>/run_data.json` — a git-versioned snapshot of THIS run's governed records.

        The sponsor's "data in git per run" requirement, on Postgres (NOT Dolt): a JSON snapshot of
        the run's governed DATA so the run folder's git history carries the data alongside the
        documents. NAMES not keys (D23): every dc/lot/timeframe/supplier is rendered by its display
        name. Captures the cycle + scope, bid-line counts per round, the sealed `eng.analysis_run`
        versions, and the frozen `awd.award` + its adjustment version history. Does NOT commit here
        (the calling op commits the whole step so run_data.json rides the same commit). Returns the
        written path. Called at the end of run_round / freeze_award / record_adjustment so the
        snapshot stays current, and it is included in the close-out archive (it lives in the run
        root, which `archive_run` zips).
        """

        cycle_id = self._cycle_id(runpaths)
        if cycle_id is None:
            snapshot: dict[str, object] = {
                "run": runpaths.slug,
                "status": "no cycle yet — run setup ingest to create the governed cycle",
            }
            self._write_run_data(runpaths, snapshot)
            return runpaths.run_data_file

        cycle = self._load_cycle(session, runpaths)
        name_by_id = self._name_index(cycle)

        round_number_by_id = {
            row[0]: int(row[1])
            for row in session.execute(
                text("SELECT round_id, round_number FROM cyc.cycle_round WHERE cycle_id = :cyc"),
                {"cyc": cycle_id},
            ).all()
        }

        # bid_line counts per round (names not keys: rounds reported by their number).
        # OPTION B (INTAKE §1a): bids are STORED flat at the 13 fiscal periods, so count the LOGICAL
        # lines (DISTINCT identity cells) — NOT the fanned storage rows — so this stays the priced
        # count the buyer ingested (matches `ingest_bids`'s returned N and the API contract). Only
        # ACTIVE (`is_scoreable`) rows are counted — mirrors the engine's `_read_bid_lines` filter,
        # so a re-submission that drops a cell (prior rows superseded) doesn't overcount this round.
        bid_counts = [
            {
                "round": round_number_by_id.get(round_id, 0),
                "bid_lines": int(count),
            }
            for round_id, count in session.execute(
                text(
                    "SELECT round_id, "
                    "count(DISTINCT (supplier_id, dc_id, lot_id, item_id, tf_id)) "
                    "FROM bid.bid_line WHERE cycle_id = :cyc AND is_scoreable = true "
                    "GROUP BY round_id"
                ),
                {"cyc": cycle_id},
            ).all()
        ]
        bid_counts.sort(key=lambda r: r["round"])

        hist = self.history(session, runpaths)
        hist_runs = cast(list[dict[str, object]], hist["analysis_runs"])
        hist_awards = cast(list[dict[str, object]], hist["awards"])
        analysis_versions = [
            {
                "version": run["version"],
                "round": run["round_number"],
                "engine_version": run["engine_version"],
                "sealed_at": self._iso(run["sealed_at"]),
            }
            for run in hist_runs
        ]

        awards: list[dict[str, object]] = []
        for award in hist_awards:
            versions = cast(list[dict[str, object]], award["versions"])
            awards.append(
                {
                    "award_code": award["award_code"],
                    "scenario": award["scenario_code"],
                    "lines": self._award_lines_by_name(session, str(award["award_id"]), name_by_id),
                    "versions": [
                        {
                            "version": v["version_no"],
                            "type": v["adjustment_type"],
                            "effective_date": self._iso(v["effective_date"]),
                            "reason": v["reason"],
                            "cells_changed": v["n_lines"],
                            "recorded_by": v["created_by"],
                        }
                        for v in versions
                    ],
                }
            )

        snapshot = {
            "run": runpaths.slug,
            "exported_at": self._iso(datetime.now(UTC)),
            "cycle": {
                "name": cycle.cycle_name,
                "commodity_id": cycle.commodity_id,
            },
            "scope": {
                "dcs": [dc.name for dc in cycle.dcs],
                "lots": [lot.name for lot in cycle.lots],
                "timeframes": [tf.name for tf in cycle.tfs],
                "suppliers": [sup.name for sup in cycle.suppliers],
                "rounds": [rnd.name for rnd in cycle.rounds],
            },
            "bid_lines_by_round": bid_counts,
            "analysis_versions": analysis_versions,
            "awards": awards,
        }
        self._write_run_data(runpaths, snapshot)
        return runpaths.run_data_file

    def feedback_file(self, session: Session, runpaths: RunPaths) -> Path:
        """Write `<run>/FEEDBACK.md` — dev-facing signals distilled from THIS run's sealed records.

        Closes the development feedback loop (PILOT_SYSTEM_DESIGN feedback note): a real run leaves
        a clean trail, and this file turns it into a structured, DATA-DERIVED (D28) review for the
        platform team — data-quality + competition gaps (gate flags, no-bids, thin competition,
        coverage), concentration/cap-breach risk, template fit (where flexible ingest had to adapt),
        process friction (alignment re-runs, renegotiations, the premium the recommendation paid),
        and the sponsor's own notes. Names not keys (D23). Refreshed after each
        run/freeze/adjustment and included in the close-out archive. Does NOT commit (the caller
        commits the step).
        """

        cycle_id = self._cycle_id(runpaths)
        if cycle_id is None:
            runpaths.feedback_file.write_text(
                f"# Development feedback — {runpaths.slug}\n\n_No run yet._\n", encoding="utf-8"
            )
            return runpaths.feedback_file

        cycle = self._load_cycle(session, runpaths)
        latest_run = session.execute(
            text(
                "SELECT analysis_run_id FROM eng.analysis_run WHERE cycle_id = :cyc "
                "ORDER BY run_started_at DESC LIMIT 1"
            ),
            {"cyc": cycle_id},
        ).scalar_one_or_none()
        # Signals reflect the round actually SCORED (the latest analysis run's round), not the
        # cycle's last round — a Round-1 review must read Round 1's bids, not an empty final round.
        scored_round_id = None
        scored_round_no = None
        if latest_run is not None:
            row = session.execute(
                text(
                    "SELECT a.round_id, r.round_number FROM eng.analysis_run a "
                    "JOIN cyc.cycle_round r ON r.round_id = a.round_id "
                    "WHERE a.analysis_run_id = :run"
                ),
                {"run": latest_run},
            ).one()
            scored_round_id = row[0]
            scored_round_no = int(row[1])

        lines: list[str] = [f"# Development feedback — {runpaths.slug}", ""]
        lines.append(f"_Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC from the sealed records._")
        lines.append("")
        lines.append(
            f"**Cycle:** {cycle.cycle_name} — {len(cycle.dcs)} DCs, {len(cycle.lots)} "
            f"lots, {len(cycle.suppliers)} suppliers, {len(cycle.rounds)} rounds."
        )
        lines.append("")

        # --- Data quality & competition (the signals that improve the engine/invite list) ---
        lines.append("## Data quality & competition")
        if latest_run is None or scored_round_id is None:
            lines.append("- No alignment has run yet — no scoring signals.")
        else:
            lines.append(f"_Signals from the latest scored round: **Round {scored_round_no}**._")
            flag_tally: dict[str, int] = {}
            for (gf,) in session.execute(
                text(
                    "SELECT gate_flags FROM eng.bid_score WHERE analysis_run_id = :run "
                    "AND gate_flags IS NOT NULL AND gate_flags <> ''"
                ),
                {"run": latest_run},
            ).all():
                for reason in str(gf).split(";"):
                    reason = reason.strip()
                    if reason:
                        flag_tally[reason] = flag_tally.get(reason, 0) + 1
            # scope cells vs cells with a scoreable bid in the SCORED round (not the cycle's last).
            scope_cells = {(dc, lot) for (dc, lot, _tf) in cycle.period_cases_by_cell}
            covered = {
                (r[0], r[1])
                for r in session.execute(
                    text(
                        "SELECT dc_id, lot_id, count(DISTINCT supplier_id) FROM bid.bid_line "
                        "WHERE cycle_id = :cyc AND round_id = :rnd AND is_scoreable = true "
                        "GROUP BY dc_id, lot_id"
                    ),
                    {"cyc": cycle_id, "rnd": scored_round_id},
                ).all()
            }
            thin = {
                (r[0], r[1])
                for r in session.execute(
                    text(
                        "SELECT dc_id, lot_id, count(DISTINCT supplier_id) AS n FROM bid.bid_line "
                        "WHERE cycle_id = :cyc AND round_id = :rnd AND is_scoreable = true "
                        "GROUP BY dc_id, lot_id HAVING count(DISTINCT supplier_id) < 3"
                    ),
                    {"cyc": cycle_id, "rnd": scored_round_id},
                ).all()
            }
            no_bid = scope_cells - covered
            lines.append(
                f"- **No-bid lots:** {len(no_bid)} of {len(scope_cells)} (DC × lot) had "
                f"no priced bid in Round {scored_round_no} — coverage gaps to chase."
            )
            lines.append(
                f"- **Thin competition (<3 bidders):** {len(thin)} (DC × lot) — consider "
                "widening the invite list there; Z-scores are less reliable."
            )
            if flag_tally:
                lines.append(f"- **Eligibility/gate flags raised (Round {scored_round_no}):**")
                for reason, n in sorted(flag_tally.items(), key=lambda kv: -kv[1]):
                    lines.append(f"    - {reason}: {n}")
            else:
                lines.append("- No eligibility/gate flags raised.")
        lines.append("")

        # --- Concentration / cap-breach (supply-risk to weigh against savings) ---
        lines.append("## Concentration & split")
        if latest_run is not None:
            breaches = session.execute(
                text(
                    "SELECT count(*) FROM eng.analysis_scenario_award a "
                    "JOIN eng.analysis_scenario s "
                    "ON s.analysis_scenario_id = a.analysis_scenario_id "
                    "WHERE s.analysis_run_id = :run AND s.scenario_code = 'B' "
                    "AND a.cap_breach_flag = true"
                ),
                {"run": latest_run},
            ).scalar_one()
            lines.append(
                f"- Recommended (Scenario B) cap-breach cells: {int(breaches)} "
                "(a DC carrying more than the max suppliers)."
            )
        else:
            lines.append("- No recommendation yet.")
        lines.append("")

        # --- Template fit — where flexible ingest had to adapt (improve the template/guidance) ---
        normalized = sorted(p.name for p in runpaths.inputs.glob("*bids_normalized*"))
        lines.append("## Template fit")
        if normalized:
            lines.append(
                f"- Flexible ingest was used {len(normalized)} time(s) — a supplier file "
                "didn't match the owned template and had to be re-mapped:"
            )
            for nm in normalized:
                lines.append(f"    - `{nm}`")
            lines.append("  → recurring re-mappings signal a template/guidance gap worth closing.")
        else:
            lines.append("- All bids came in on the owned template (no re-mapping needed).")
        lines.append("")

        # --- Process — re-runs, renegotiations, the premium the recommendation paid ---
        hist = self.history(session, runpaths)
        hist_runs = cast(list[dict[str, object]], hist["analysis_runs"])
        hist_awards = cast(list[dict[str, object]], hist["awards"])
        n_adj = sum(len(cast(list[object], a["versions"])) - 1 for a in hist_awards)
        lines.append("## Process")
        lines.append(
            f"- Alignment runs sealed: {len(hist_runs)} "
            f"(re-runs beyond one per round = mid-cycle iterations)."
        )
        lines.append(
            f"- Awards frozen: {len(hist_awards)}; post-award renegotiation versions: {n_adj}."
        )
        lines.append("")

        # --- Sponsor notes (their own feedback captured during the run) ---
        lines.append("## Sponsor notes (from NOTES.md)")
        notes_text = (
            runpaths.notes_md.read_text(encoding="utf-8") if runpaths.notes_md.exists() else ""
        )
        note_lines = [ln.strip() for ln in notes_text.splitlines() if ln.strip().startswith("- ")]
        if note_lines:
            lines.extend(note_lines[-12:])
        else:
            lines.append("- (none recorded)")
        lines.append("")
        lines.append(
            "_Data stays in the private vault (clean-room); the platform team reviews "
            "STRUCTURE + these signals to adapt the engine, templates, and analysis._"
        )

        runpaths.feedback_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return runpaths.feedback_file

    def close_run(self, runpaths: RunPaths) -> Path:
        """Archive the FULL normalized history of a run into a zip; return the zip path (step 10).

        Zips inputs/ + outputs/ + memory/ + NOTES.md + RUN.md + cycle_id.txt under the vault's
        `archives/` (so a later purge leaves the archive intact). This is the PRESENT step of the
        present→confirm→purge close-out; the skill confirms with the buyer, then calls `purge_run`.
        """

        return archive_run(runpaths)

    def purge_run(self, slug: str) -> None:
        """Remove a run's vault folder AND drop its isolated database (after the buyer confirms).

        `close_run`'s archive already preserves the full history (files + the run_data.json),
        so purge is a clean teardown: the vault folder is removed and — under D30 isolation — the
        run's own database is dropped. Nothing of this run lingers to contaminate another.
        """

        purge_run(self.vault_root, slug)
        if self.isolate_db:
            drop_run_database(slug)

    # ------------------------------------------------------------------ #
    # vault-carried DB persistence (resume across ephemeral containers)
    # ------------------------------------------------------------------ #
    _DB_SNAPSHOT = (
        "db/run_db.sql"  # the run's governed-DB dump under the run folder (git-versioned)
    )

    def snapshot_run(self, runpaths: RunPaths) -> Path | None:
        """Dump the run's isolated DB into the vault (git-committed) so it survives a wiped box.

        Called after a governed write commits. The dump rides the vault's git history alongside the
        documents + run_data.json, so a fresh (web) session can rehydrate the exact governed state.
        No-op when DB isolation is off (the shared-DB test mode has nothing per-run to dump).
        """

        if not self.isolate_db:
            return None
        out_path = runpaths.root / self._DB_SNAPSHOT
        dump_run_database(runpaths.slug, out_path)
        git_commit_run(self.vault_root, runpaths.slug, "run DB snapshot")
        return out_path

    def rehydrate_runs(self) -> list[str]:
        """Restore every vault run's DB from its committed snapshot (session start in a fresh box).

        Iterates the vault's runs; for each that carries a `db/run_db.sql` snapshot, recreates the
        run's isolated database and loads it. Returns the slugs restored. The inverse of the
        per-step `snapshot_run` — together they make a run fully resumable from git alone (D30/D32).
        """

        restored: list[str] = []
        for paths in list_runs(self.vault_root):
            snapshot = paths.root / self._DB_SNAPSHOT
            if snapshot.is_file():
                restore_run_database(paths.slug, snapshot)
                restored.append(paths.slug)
        return restored

    # ================================================================== #
    # PART B — internal helpers
    # ================================================================== #
    def _load_cycle(self, session: Session, runpaths: RunPaths) -> CycleView:
        """Load the run's persisted cycle (raises if the run hasn't ingested its setup yet)."""

        cycle_id = self._cycle_id(runpaths)
        if cycle_id is None:
            raise ValueError(
                f"run {runpaths.slug} has no cycle yet — ingest the setup workbook first"
            )
        return load_cycle(session, cycle_id)

    @staticmethod
    def _name_index(cycle: CycleView) -> dict[str, str]:
        """A flat id -> display-name index over every scope entity (for names-not-keys output)."""

        index: dict[str, str] = {}
        for entity in (
            *cycle.dcs,
            *cycle.lots,
            *cycle.tfs,
            *cycle.suppliers,
            *cycle.rounds,
        ):
            index[entity.id] = entity.name
        return index

    @staticmethod
    def _iso(value: object) -> str | None:
        """ISO-8601 a datetime/date for JSON (None passes through)."""

        if isinstance(value, datetime | date):
            return value.isoformat()
        return None if value is None else str(value)

    def _award_lines_by_name(
        self, session: Session, award_id: str, name_by_id: dict[str, str]
    ) -> list[dict[str, object]]:
        """The frozen award's baseline lines by name (dc/lot/timeframe/supplier + price)."""

        rows = session.execute(
            select(
                AwardLine.dc_id,
                AwardLine.lot_id,
                AwardLine.tf_id,
                AwardLine.supplier_id,
                AwardLine.volume_share,
                AwardLine.frozen_price,
            ).where(AwardLine.award_id == award_id)
        ).all()
        lines = [
            {
                "dc": name_by_id.get(dc_id, dc_id),
                "lot": name_by_id.get(lot_id, lot_id),
                "timeframe": name_by_id.get(tf_id, tf_id),
                "supplier": name_by_id.get(sup_id, sup_id),
                "volume_share": str(share),
                "frozen_price": str(price),
            }
            for dc_id, lot_id, tf_id, sup_id, share, price in rows
        ]
        lines.sort(key=lambda r: (r["dc"], r["lot"], r["supplier"]))
        return lines

    @staticmethod
    def _write_run_data(runpaths: RunPaths, snapshot: dict[str, object]) -> None:
        """Serialize the governed-data snapshot to `<run>/run_data.json` (stable, pretty JSON)."""

        runpaths.run_data_file.write_text(
            json.dumps(snapshot, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )

    def _render_kanban(
        self,
        session: Session,
        runpaths: RunPaths,
        *,
        extra_done: list[str] | None = None,
        extra_waiting: list[str] | None = None,
    ) -> None:
        """Recompute + write the kanban, appending any explicit Done/Waiting lines for this step."""

        cycle_id = self._cycle_id(runpaths)
        board = status_mod.kanban(session, cycle_id, runpaths)
        for line in extra_done or []:
            if line not in board["Done"]:
                board["Done"].append(line)
        for line in extra_waiting or []:
            if line not in board["Waiting on you"]:
                board["Waiting on you"].append(line)
        status_mod.render_run_md(runpaths, board)

    def _period_ids_by_timeframe(
        self, session: Session, cycle_id: str
    ) -> dict[str, list[str | None]]:
        """Resolve each cycle timeframe to its flat-13 fiscal-period span (INTAKE §1a / Option B).

        Maps `tf_id -> [fiscal_period_id, ...]` by reading the timeframe's stored calendar dates
        (`cyc.cycle_timeframe.start_date/end_date`), walking them to the covering
        `ref.fiscal_period` rows (`period_for_date`), and collecting each period's id as TEXT (the
        `bid_line` column is varchar; `ref.fiscal_period.id` is uuid — store via `str()`/`::text`).

        GRACEFUL FALLBACK: a timeframe whose dates fall OUTSIDE the seeded FY16–36 calendar (a
        synthetic/placeholder cycle) cannot be resolved to periods — it maps to `[None]`, so the
        caller writes the single tf-grain row with `fiscal_period_id` NULL exactly as before. The
        supersede logic + the two filtered unique indexes (migration 0016) cover both grains.
        """

        rows = session.execute(
            text(
                "SELECT tf_id, start_date, end_date FROM cyc.cycle_timeframe WHERE cycle_id = :cyc"
            ),
            {"cyc": cycle_id},
        ).all()
        # fiscal_period (fiscal_year, period) -> id::text, for the years the calendar seeds.
        fp_id_by_year_period = {
            (int(fy), int(p)): str(fid)
            for fy, p, fid in session.execute(
                text("SELECT fiscal_year, period, id FROM ref.fiscal_period")
            ).all()
        }

        spans: dict[str, list[str | None]] = {}
        for tf_id, start, end in rows:
            try:
                first, last = period_for_date(start), period_for_date(end)
            except ValueError:
                spans[tf_id] = [None]  # dates outside the seeded calendar -> tf-grain fallback
                continue
            period_ids: list[str | None] = []
            ok = True
            # Walk the contiguous span first..last (inclusive) across (possibly) two FYs.
            for fp in self._period_walk(first, last):
                fid = fp_id_by_year_period.get((fp.fiscal_year, fp.period))
                if fid is None:
                    ok = False
                    break
                period_ids.append(fid)
            spans[tf_id] = period_ids if (ok and period_ids) else [None]
        return spans

    @staticmethod
    def _period_walk(first: FiscalPeriod, last: FiscalPeriod) -> list[FiscalPeriod]:
        """The inclusive fiscal-period span from `first` to `last`, ordered by (FY, period)."""

        ordered = sorted(all_periods(), key=lambda p: (p.fiscal_year, p.period))
        out: list[FiscalPeriod] = []
        collecting = False
        for fp in ordered:
            if fp.fiscal_year == first.fiscal_year and fp.period == first.period:
                collecting = True
            if collecting:
                out.append(fp)
            if fp.fiscal_year == last.fiscal_year and fp.period == last.period:
                break
        return out

    def _persist_bid_lines(
        self,
        session: Session,
        cycle: CycleView,
        round_id: str,
        lines: list[ParsedBidLine],
        capacity_lines: list[ParsedCapacityLine] | None = None,
    ) -> tuple[int, int, int]:
        """Persist priced ingest lines as bid.bid_line rows (one submission per supplier).

        Mirrors the demo's `ingest_and_persist`: one `norm.source_artifact` + `bid.bid_submission`
        per supplier for the round (the FK chain), then one `bid.bid_line` per priced line. Only
        `Completeness.BID` lines persist (no-bid / incomplete are not scoreable). A prior submission
        for the same (cycle, round, supplier) is SUPERSEDED (its lines marked non-scoreable) so a
        re-send never double-counts.

        E-38: the supplier's stated capacity (`capacity_lines`, from the SAME returned file) is
        persisted in the same pass — one `bid.capacity_statement` per supplier riding that
        supplier's SAME submission/artifact, with one CELL-scoped `bid.capacity_constraint` per
        stated cell. A re-send supersedes the prior capacity statement too (status -> SUPERSEDED),
        so the cap never reads a stale ceiling. Returns (count, superseded_lines, capacity_count).
        """

        now = datetime.now(UTC).replace(tzinfo=None)
        submission_by_sup: dict[str, str] = {}
        artifact_by_sup: dict[str, str] = {}
        superseded_total = 0

        # Resolve the owning tenant once for this ingest; reused for the IMPORTED + SUPERSEDED
        # events appended on the caller's transaction (Gap G-B).
        audit = AuditWriter(session)
        client_id = client_id_for_cycle(session, cycle.cycle_id)

        def _submission_for(supplier_id: str) -> str:
            nonlocal superseded_total
            existing = submission_by_sup.get(supplier_id)
            if existing is not None:
                return existing
            # Supersede any PRIOR submission for this (cycle, round, supplier): a re-send or a
            # second file for the same supplier in the round REPLACES the earlier one, so the
            # engine never double-counts. Supersede, never hard-delete (ADR-0006): mark the prior
            # lines non-scoreable and the prior submission SUPERSEDED.
            keys = {"cyc": cycle.cycle_id, "rnd": round_id, "sup": supplier_id}
            superseded_total += int(
                session.execute(
                    text(
                        "SELECT count(*) FROM bid.bid_line WHERE cycle_id = :cyc "
                        "AND round_id = :rnd AND supplier_id = :sup AND is_scoreable = true"
                    ),
                    keys,
                ).scalar_one()
            )
            session.execute(
                text(
                    "UPDATE bid.bid_line SET is_scoreable = false WHERE cycle_id = :cyc "
                    "AND round_id = :rnd AND supplier_id = :sup AND is_scoreable = true"
                ),
                keys,
            )
            # Governed decision: each prior submission is being superseded. Emit one tamper-evident
            # SUPERSEDED event per prior id BEFORE the status flip, in the same transaction.
            prior_ids = [
                pid
                for (pid,) in session.execute(
                    text(
                        "SELECT submission_id FROM bid.bid_submission "
                        "WHERE cycle_id = :cyc AND round_id = :rnd AND supplier_id = :sup "
                        "AND overall_status <> 'SUPERSEDED'"
                    ),
                    {"cyc": cycle.cycle_id, "rnd": round_id, "sup": supplier_id},
                ).all()
            ]
            for prior_id in prior_ids:
                audit.append(
                    DomainEvent(
                        event_type=EventType.SUPERSEDED,
                        client_id=client_id,
                        entity_type="bid.bid_submission",
                        entity_id=uuid.UUID(prior_id),
                        cycle_id=uuid.UUID(cycle.cycle_id),
                        actor="pilot",
                        source="import",
                        before={"overall_status": "SUBMITTED"},
                        after={"overall_status": "SUPERSEDED"},
                    )
                )
            session.execute(
                text(
                    "UPDATE bid.bid_submission SET overall_status = 'SUPERSEDED' "
                    "WHERE cycle_id = :cyc AND round_id = :rnd AND supplier_id = :sup "
                    "AND overall_status <> 'SUPERSEDED'"
                ),
                {"cyc": cycle.cycle_id, "rnd": round_id, "sup": supplier_id},
            )
            # E-38: supersede this supplier's PRIOR capacity statement for the round too, so the
            # cap check reads only the latest ceilings (append-only — status flip, rows retained).
            session.execute(
                text(
                    "UPDATE bid.capacity_statement SET status = 'SUPERSEDED' "
                    "WHERE cycle_id = :cyc AND round_id = :rnd AND supplier_id = :sup "
                    "AND status <> 'SUPERSEDED'"
                ),
                {"cyc": cycle.cycle_id, "rnd": round_id, "sup": supplier_id},
            )
            artifact_id = _new_id()
            session.execute(
                text(
                    "INSERT INTO norm.source_artifact (artifact_id, artifact_type, file_name, "
                    "file_hash_sha256, received_at, status, cycle_id, round_id, supplier_id, "
                    "created_by) VALUES (:aid, 'BID_SUBMISSION', :fn, :hash, :now, 'RECEIVED', "
                    ":cyc, :rnd, :sup, 'pilot')"
                ),
                {
                    "aid": artifact_id,
                    "fn": f"bids_{supplier_id[:8]}_{round_id[:8]}.xlsx",
                    "hash": _new_id().replace("-", "")[:64].ljust(64, "0"),
                    "now": now,
                    "cyc": cycle.cycle_id,
                    "rnd": round_id,
                    "sup": supplier_id,
                },
            )
            submission_id = _new_id()
            session.execute(
                text(
                    "INSERT INTO bid.bid_submission (submission_id, cycle_id, round_id, "
                    "supplier_id, source_artifact_id, submitted_at, version_number, "
                    "overall_status, standard_terms_accepted) VALUES (:sid, :cyc, :rnd, :sup, "
                    ":aid, :now, 1, 'SUBMITTED', true)"
                ),
                {
                    "sid": submission_id,
                    "cyc": cycle.cycle_id,
                    "rnd": round_id,
                    "sup": supplier_id,
                    "aid": artifact_id,
                    "now": now,
                },
            )
            # Governed decision: a bid submission has been imported. Land its tamper-evident event
            # in the same transaction as the INSERT (Gap G-B) — ids only, no commercial values.
            audit.append(
                DomainEvent(
                    event_type=EventType.IMPORTED,
                    client_id=client_id,
                    entity_type="bid.bid_submission",
                    entity_id=uuid.UUID(submission_id),
                    cycle_id=uuid.UUID(cycle.cycle_id),
                    actor="pilot",
                    source="import",
                    after={"round_id": round_id, "supplier_id": supplier_id},
                )
            )
            submission_by_sup[supplier_id] = submission_id
            artifact_by_sup[supplier_id] = artifact_id
            return submission_id

        # Option B (INTAKE §1a): store bids FLAT at the 13 fiscal periods. Each priced tf-grain line
        # is FANNED OUT to one bid.bid_line per fiscal period in its timeframe's span — the payload
        # is replicated verbatim, only `fiscal_period_id` differs. The engine/scenarios/awards stay
        # timeframe-grain via a representative-row collapse downstream; the storage row count grows
        # (≤13×) but `count` keeps the LOGICAL line semantics (the API contract: `ingested == N`).
        period_ids_by_tf = self._period_ids_by_timeframe(session, cycle.cycle_id)

        count = 0
        for line in lines:
            if line.completeness is not Completeness.BID:
                continue
            ident = line.identity
            submission_id = _submission_for(ident.supplier_id)
            # The timeframe's fiscal-period span; `[None]` for a tf that doesn't map (fallback) ->
            # a single tf-grain row exactly as before.
            period_ids = period_ids_by_tf.get(ident.tf_id) or [None]
            for fiscal_period_id in period_ids:
                session.add(
                    BidLine(
                        bid_line_id=_new_id(),
                        submission_id=submission_id,
                        cycle_id=cycle.cycle_id,
                        round_id=round_id,
                        supplier_id=ident.supplier_id,
                        dc_id=ident.dc_id,
                        lot_id=ident.lot_id,
                        item_id=ident.item_id,
                        tf_id=ident.tf_id,
                        fiscal_period_id=fiscal_period_id,
                        currency_code="USD",
                        price_basis=line.price_basis or "ALL_IN",
                        submitted_all_in_case=line.components.all_in,
                        fob_case=line.components.fob,
                        delivery_surcharge_case=line.components.delivery_surcharge or None,
                        vegcool_surcharge_case=line.components.vegcool_surcharge or None,
                        lot_discount_case=line.components.lot_discount or None,
                        price_basis_resolved=line.price_basis or None,
                        transit_days=line.transit_days,
                        volume_minimum_cases=line.total_vol_offered,
                        exclusivity_required_flag=False,
                        validity_status="VALID",
                        source_row_number=line.source_row_number,
                        created_at=now,
                        is_scoreable=True,
                        is_awardable=True,
                    )
                )
            count += 1  # LOGICAL priced lines, NOT the fanned storage rows (API contract).

        # E-38: persist stated capacity from the SAME file. One capacity_statement per supplier
        # (lazily, riding that supplier's submission + source_artifact via `_submission_for`), then
        # one CELL-scoped capacity_constraint per stated cell (dc x lot x tf — the award's grain).
        cap_count = 0
        cap_stmt_by_sup: dict[str, str] = {}
        for cap in capacity_lines or ():
            if cap.max_weekly_cases is None and cap.max_period_cases is None:
                continue  # belt-and-suspenders: the ingester already drops no-max rows
            submission_id = _submission_for(cap.supplier_id)
            stmt_id = cap_stmt_by_sup.get(cap.supplier_id)
            if stmt_id is None:
                stmt_id = _new_id()
                session.add(
                    CapacityStatement(
                        capacity_statement_id=stmt_id,
                        cycle_id=cycle.cycle_id,
                        round_id=round_id,
                        supplier_id=cap.supplier_id,
                        submission_id=submission_id,
                        source_artifact_id=artifact_by_sup[cap.supplier_id],
                        status="SUBMITTED",
                        effective_at=now,
                        notes=None,
                    )
                )
                # Flush the parent now: the constraint FK is composite (statement_id, cycle_id) and
                # the ORM has no declared relationship to order the inserts, so the statement row
                # must exist before its CELL constraints are inserted below.
                session.flush()
                cap_stmt_by_sup[cap.supplier_id] = stmt_id
            session.add(
                CapacityConstraint(
                    capacity_constraint_id=_new_id(),
                    capacity_statement_id=stmt_id,
                    cycle_id=cycle.cycle_id,
                    scope_type="CELL",
                    dc_id=cap.dc_id,
                    lot_id=cap.lot_id,
                    tf_id=cap.tf_id,
                    max_weekly_cases=cap.max_weekly_cases,
                    max_period_cases=cap.max_period_cases,
                    conditions_text=cap.notes,
                )
            )
            cap_count += 1
        session.flush()
        return count, superseded_total, cap_count

    def _scenario_award_view(
        self,
        session: Session,
        cycle: CycleView,
        analysis_run_id: str,
        *,
        scenario_code: str,
    ) -> BookingAwardView:
        """An in-flight AwardView built from a scenario's `eng.analysis_scenario_award` split rows.

        Used for the alignment workbook BEFORE an award is frozen — it needs an `AwardView`. The
        booking-cell economics (period cases, routing baseline) come from the cycle scope (D23).
        """

        rows = session.execute(
            text(
                "SELECT a.dc_id, a.lot_id, a.tf_id, a.supplier_id, a.volume_share, a.awarded_price "
                "FROM eng.analysis_scenario_award a "
                "JOIN eng.analysis_scenario s "
                "  ON s.analysis_scenario_id = a.analysis_scenario_id "
                "WHERE s.analysis_run_id = :run AND s.scenario_code = :code "
                "ORDER BY a.dc_id, a.lot_id, a.tf_id"
            ),
            {"run": analysis_run_id, "code": scenario_code},
        ).all()
        label = (
            session.execute(
                text(
                    "SELECT label FROM eng.analysis_scenario "
                    "WHERE analysis_run_id = :run AND scenario_code = :code"
                ),
                {"run": analysis_run_id, "code": scenario_code},
            ).scalar()
            or scenario_code
        )
        cells = self._booking_cells(
            cycle,
            [
                (dc_id, lot_id, tf_id, sup_id, share, price)
                for dc_id, lot_id, tf_id, sup_id, share, price in rows
            ],
        )
        return _BookingAward(scenario_code=scenario_code, scenario_label=label, cells=cells)

    def _frozen_award_view(
        self,
        session: Session,
        cycle: CycleView,
        award_id: str,
        scenario_code: str,
    ) -> BookingAwardView:
        """An AwardView from the FROZEN award's `awd.award_line` baseline (the booking basis)."""

        rows = session.execute(
            select(
                AwardLine.dc_id,
                AwardLine.lot_id,
                AwardLine.tf_id,
                AwardLine.supplier_id,
                AwardLine.volume_share,
                AwardLine.frozen_price,
            ).where(AwardLine.award_id == award_id)
        ).all()
        cells = self._booking_cells(
            cycle,
            [(dc, lot, tf, sup, share, price) for dc, lot, tf, sup, share, price in rows],
        )
        return _BookingAward(
            scenario_code=scenario_code,
            scenario_label=f"Scenario {scenario_code} (frozen award)",
            cells=cells,
        )

    def _booking_cells(
        self,
        cycle: CycleView,
        rows: list[tuple[str, str, str, str, Decimal, Decimal]],
    ) -> tuple[_BookingCell, ...]:
        """Build booking cells from (dc, lot, tf, supplier, share, price) + the cycle economics."""

        item_for_lot = {cycle.lots[i].id: cycle.items[i].id for i in range(len(cycle.lots))}
        cells: list[_BookingCell] = []
        for dc_id, lot_id, tf_id, supplier_id, volume_share, awarded_price in rows:
            cells.append(
                _BookingCell(
                    dc_id=dc_id,
                    lot_id=lot_id,
                    item_id=item_for_lot.get(lot_id, lot_id),
                    tf_id=tf_id,
                    supplier_id=supplier_id,
                    volume_share=Decimal(str(volume_share)),
                    awarded_price=Decimal(str(awarded_price)),
                    period_cases=cycle.period_cases_by_cell.get(
                        (dc_id, lot_id, tf_id), Decimal("0")
                    ),
                    routing_baseline=cycle.incumbent_routing.get((dc_id, lot_id), Decimal("0")),
                )
            )
        return tuple(cells)

    # ------------------------------------------------------------------ #
    # web alignment read surface — the scenario/award reads the console renders
    # ------------------------------------------------------------------ #
    def list_analyses(self, session: Session, runpaths: RunPaths) -> list[AnalysisSummary]:
        """The run's cycle's SEALED analysis runs (typed views), or [] if no cycle yet.

        Thin wrapper over `read_views.list_analyses` scoped to THIS run's cycle, so the web lists
        exactly this run's sealed analyses (never another run's).
        """

        cycle_id = self._cycle_id(runpaths)
        if cycle_id is None:
            return []
        return read_list_analyses(session, cycle_id)

    def list_awards(self, session: Session, runpaths: RunPaths) -> list[AwardSummary]:
        """The run's cycle's FROZEN awards (typed views), or [] if no cycle yet.

        Thin wrapper over `awd.read.list_awards` scoped to THIS run's cycle.
        """

        cycle_id = self._cycle_id(runpaths)
        if cycle_id is None:
            return []
        return read_list_awards(session, cycle_id)

    def award_detail(self, session: Session, runpaths: RunPaths, award_id: str) -> AwardDetail:
        """One frozen award: baseline + effective lines + the version history (v0 → vN).

        Resolves THIS run's cycle (for names, D23) and hands off to `awd.read.award_detail`. Raises
        ValueError on an unknown award id (mapped to a clean 404 by the router).
        """

        cycle = self._load_cycle(session, runpaths)
        return read_award_detail(session, cycle, award_id)

    def award_email_drafts(
        self,
        session: Session,
        runpaths: RunPaths,
        award_id: str,
        *,
        buyer_name: str = "",
        buyer_title: str = "",
    ) -> list[SupplierEmailDraft]:
        """One award-notification email DRAFT per awarded supplier (E-37; template-merge).

        Loads the run's cycle (for names + the delivery window) and renders the award template per
        awarded supplier. Raises ValueError on an unknown award (router -> 404).

        Each draft attaches the supplier's OWN individual award guide (`write_supplier_award_guide_
        files`, written at freeze, award-code-stamped so a later freeze can't shadow it) — never the
        combined all-suppliers workbook. The filename per supplier is recomputed deterministically
        and only named when the file is actually present (otherwise `[#AwardFileName]` is left for
        the buyer to attach).
        """

        cycle = self._load_cycle(session, runpaths)
        award = next(
            (a for a in self.list_awards(session, runpaths) if a.award_id == award_id), None
        )
        award_files: dict[str, str] = {}
        if award is not None:
            guide_stage = self._stage("booking_guide")
            for sup in cycle.suppliers:
                fname = stage_filename(
                    guide_stage,
                    supplier_guide_label(award.award_id, award.award_code, sup.name, sup.id),
                )
                if (runpaths.outputs / fname).is_file():
                    award_files[sup.id] = fname
        return award_drafts(
            session,
            cycle,
            award_id,
            buyer_name=buyer_name,
            buyer_title=buyer_title,
            award_files=award_files,
        )

    def feedback_email_drafts(
        self,
        session: Session,
        runpaths: RunPaths,
        analysis_run_id: str,
        *,
        buyer_name: str = "",
        buyer_title: str = "",
    ) -> list[SupplierEmailDraft]:
        """One round-feedback email DRAFT per supplier with above-benchmark lots (E-37).

        Loads the run's cycle (names + the eligibility overrides) and renders the round-feedback
        template per supplier whose round bid sits above the market-low benchmark on any cell —
        with hard asks (ineligible) and soft asks (eligible but above) split into separate tables.
        Raises ValueError on an unknown analysis run (router -> 404).
        """

        cycle = self._load_cycle(session, runpaths)
        return feedback_drafts(
            session,
            cycle,
            analysis_run_id,
            buyer_name=buyer_name,
            buyer_title=buyer_title,
        )

    def rejection_email_drafts(
        self,
        session: Session,
        runpaths: RunPaths,
        award_id: str,
        *,
        buyer_name: str = "",
        buyer_title: str = "",
    ) -> list[SupplierEmailDraft]:
        """One non-selection ("RFP Results") email DRAFT per supplier with a lost lot (E-37).

        Keyed on the frozen award: loads the run's cycle (for names) and renders the non-selection
        template per supplier who bid the award's round but was not awarded every cell — each lost
        lot itemized with their price, the market-low benchmark, the % gap, and a data-centered
        reason. Raises ValueError on an unknown award (router -> 404).
        """

        cycle = self._load_cycle(session, runpaths)
        return rejection_drafts(
            session,
            cycle,
            award_id,
            buyer_name=buyer_name,
            buyer_title=buyer_title,
        )

    def scenario_comparison(
        self, session: Session, runpaths: RunPaths, analysis_run_id: str
    ) -> list[ScenarioComparisonRow]:
        """The seven lenses side by side for a sealed run (numbers match the alignment workbook)."""

        cycle = self._load_cycle(session, runpaths)
        return read_scenario_comparison(session, cycle, analysis_run_id)

    def scenario_detail(
        self, session: Session, runpaths: RunPaths, analysis_run_id: str, scenario_code: str
    ) -> ScenarioDetail:
        """One lens cell-by-cell for a sealed run: the competitive grid + the savings headline.

        Builds the chosen lens's in-flight `AwardView` from `eng.analysis_scenario_award`
        (`_scenario_award_view`) and resolves the run's round, then hands both to the read layer so
        the per-cell awarded supplier + share reflect THIS lens. Raises ValueError on unknown
        scenario (mapped to a clean 400 by the router).
        """

        cycle = self._load_cycle(session, runpaths)
        final_round_id = self._analysis_round_id(session, analysis_run_id)
        award = self._scenario_award_view(
            session, cycle, analysis_run_id, scenario_code=scenario_code
        )
        return read_scenario_detail(
            session,
            cycle,
            analysis_run_id,
            scenario_code,
            final_round_id=final_round_id,
            award_view=award,
        )

    @staticmethod
    def _analysis_round_id(session: Session, analysis_run_id: str) -> str:
        """The `round_id` a sealed analysis run scored (its final round), or raise if unknown."""

        round_id = session.execute(
            select(AnalysisRun.round_id).where(AnalysisRun.analysis_run_id == analysis_run_id)
        ).scalar_one_or_none()
        if round_id is None:
            raise ValueError(f"no sealed analysis run {analysis_run_id!r}")
        return round_id

    @staticmethod
    def _run_version_seq(session: Session, cycle_id: str, analysis_run_id: str) -> int:
        """The 1-based ordinal of THIS sealed run among the cycle's runs (matches the doc)."""

        this_run = session.execute(
            select(AnalysisRun.run_started_at).where(AnalysisRun.analysis_run_id == analysis_run_id)
        ).scalar_one()
        return int(
            session.execute(
                select(func.count())
                .select_from(AnalysisRun)
                .where(
                    AnalysisRun.cycle_id == cycle_id,
                    AnalysisRun.run_started_at <= this_run,
                )
            ).scalar_one()
        )

    # --- Normalized workflow-stage numbering (PILOT_SYSTEM_DESIGN §2). Files sort by workflow:
    #     01 setup · 02/05/.. bid template · 03/06/.. bids · 04/07/.. alignment · 08 booking ·
    #     09 post-award. Per-round stages step by 3 so a round's template/bids/alignment group. ---
    @staticmethod
    def _stage(kind: str, round_no: int = 0) -> int:
        if kind == "bid_template":
            return 2 + (round_no - 1) * 3
        if kind in ("bids_uploaded", "bids_normalized"):
            return 3 + (round_no - 1) * 3
        if kind == "alignment":
            return 4 + (round_no - 1) * 3
        if kind == "booking_guide":
            return 8
        if kind == "post_award":
            return 9
        raise ValueError(f"unknown stage kind {kind!r}")


def _new_id() -> str:
    return str(uuid.uuid4())
