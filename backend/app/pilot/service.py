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

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.cycle.loader import load_cycle
from app.cycle.scope import build_scope_from_cycle
from app.domain.awd import service as awd_service
from app.domain.awd.models import Award, AwardLine
from app.domain.bid.bid_ingester import Completeness, ParsedBidLine, ingest_template
from app.domain.bid.models import BidLine
from app.domain.bid.template_generator import generate_template_bytes
from app.domain.eng.models import AnalysisRun
from app.domain.eng.runner import EngineRunner, IncumbentRow
from app.engine.interface import EngineConfig, WeightPreset
from app.output.booking_guide import (
    BookingAwardView,
    write_booking_guide_internal_xlsx,
    write_supplier_award_guides_xlsx,
)
from app.output.post_award_doc import write_post_award_adjustments_xlsx
from app.output.scenario_workbook import write_scenario_workbook_xlsx
from app.output.types import CycleView
from app.pilot import status as status_mod
from app.pilot.flex_ingest import MappingProposal, apply_mapping, infer_bid_mapping
from app.pilot.setup_ingest import ingest_setup_workbook
from app.pilot.setup_template import build_setup_workbook
from app.pilot.vault import (
    SUBDIR_INPUTS,
    SUBDIR_MEMORY,
    RunPaths,
    archive_run,
    create_run,
    git_commit_run,
    list_runs,
    purge_run,
    run_paths,
    stage_filename,
    write_to_run,
)

# The default engine strategy for a pilot run when the caller passes no config — a balanced preset
# mirroring the demo's. The setup workbook also carries the strategy; this is the safe fallback.
_DEFAULT_CONFIG = EngineConfig(
    preset=WeightPreset.BALANCED,
    weight_price=Decimal("0.35"),
    weight_coverage=Decimal("0.25"),
    weight_historical=Decimal("0.20"),
    weight_zrisk=Decimal("0.10"),
    weight_continuity=Decimal("0.10"),
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

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = Path(vault_root)

    # ------------------------------------------------------------------ #
    # step 0 — start run + setup
    # ------------------------------------------------------------------ #
    def start_run(self, *, commodity: str, label: str) -> RunPaths:
        """Create the run scaffold, write the Setup/Kickoff workbook, update RUN.md, and commit.

        No DB touch — a cycle doesn't exist until the filled setup is ingested. The kanban's Next
        bucket points the sponsor at filling & uploading the setup doc.
        """

        paths = create_run(self.vault_root, commodity=commodity, label=label)
        setup_name = stage_filename(1, "setup_kickoff")
        write_to_run(paths, SUBDIR_INPUTS, setup_name, build_setup_workbook())

        board = status_mod.kanban(None, None, paths)
        status_mod.render_run_md(paths, board)
        git_commit_run(self.vault_root, paths.slug, "setup/kickoff workbook generated")
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
    def remember(
        self, runpaths: RunPaths, note: str, *, related_file: str | None = None
    ) -> None:
        """Append a dated entry to NOTES.md; if `related_file` given, record it lives in memory/."""

        self._append_note(runpaths, note, related_file=related_file)
        git_commit_run(self.vault_root, runpaths.slug, "note added")

    def add_memory(
        self, runpaths: RunPaths, filename: str, data: bytes, note: str
    ) -> Path:
        """Write `data` into memory/, append the linked NOTES.md entry, commit; return the path."""

        path = write_to_run(runpaths, SUBDIR_MEMORY, filename, data)
        self._append_note(runpaths, note, related_file=filename)
        git_commit_run(self.vault_root, runpaths.slug, f"memory file added: {filename}")
        return path

    def _append_note(
        self, runpaths: RunPaths, note: str, *, related_file: str | None
    ) -> None:
        today = datetime.now(UTC).date().isoformat()
        entry = f"- {today}: {note}"
        if related_file:
            entry += f" (file: `{related_file}` in memory/)"
        existing = (
            runpaths.notes_md.read_text(encoding="utf-8")
            if runpaths.notes_md.exists()
            else ""
        )
        runpaths.notes_md.write_text(
            existing.rstrip() + "\n" + entry + "\n", encoding="utf-8"
        )

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
    def generate_bid_template(
        self, session: Session, runpaths: RunPaths, round_no: int
    ) -> Path:
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
        git_commit_run(
            self.vault_root, runpaths.slug, f"round {round_no} bid template generated"
        )
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
        count = self._persist_bid_lines(session, cycle, round_id, result.lines)

        if result.quarantined:
            self._append_note(
                runpaths,
                f"Round {round_no} bids: {len(result.quarantined)} row(s) quarantined and not "
                "loaded (key mismatch / bad number) — review before re-uploading.",
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
    ) -> Path:
        """Run the engine on a round -> sealed eng.* + the VERSIONED alignment workbook (step 2).

        Builds the `IncumbentRow`s from the loaded cycle, runs `EngineRunner.run_analysis` on the
        round, then writes the versioned alignment workbook (`write_scenario_workbook_xlsx`, which
        computes the `Analysis v{seq}` heading) into outputs/ as
        `0X_round{n}_alignment_v{seq}.xlsx`. Updates the kanban (Done: Round n analysis v{seq}) and
        commits. Returns the written path.
        """

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

        runner = EngineRunner(session)
        run_result = runner.run_analysis(
            cycle_id=cycle.cycle_id,
            round_id=round_id,
            config=config or _DEFAULT_CONFIG,
            incumbents=incumbents,
            run_by="pilot-runner",
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
            config or _DEFAULT_CONFIG,
            run_result.analysis_run_id,
            round_id,
            award,
            output_path=out_path,
        )

        self._render_kanban(
            session,
            runpaths,
            extra_done=[f"Round {round_no} alignment analysis v{version_seq} ready"],
        )
        git_commit_run(
            self.vault_root,
            runpaths.slug,
            f"round {round_no} alignment analysis v{version_seq} sealed",
        )
        return out_path

    def freeze_award(
        self,
        session: Session,
        runpaths: RunPaths,
        *,
        analysis_run_id: str,
        scenario_code: str = "B",
        award_code: str,
    ) -> str:
        """Freeze a selected scenario into awd.* + the booking guide(s) (step 4); returns award_id.

        Promotes the human-selected scenario (default B — the risk-adjusted recommendation) to a
        FROZEN award (`awd.freeze_award`), then writes the two-audience booking guide into outputs/
        (`0X_award_booking_guide.xlsx` + the per-supplier guides). Decision-support: the HUMAN
        asserts the award (ADR-0006). Commits. Returns the award_id.
        """

        cycle = self._load_cycle(session, runpaths)
        award_id = awd_service.freeze_award(
            session,
            cycle_id=cycle.cycle_id,
            analysis_run_id=analysis_run_id,
            scenario_code=scenario_code,
            award_code=award_code,
            frozen_by="pilot",
        )

        booking = self._frozen_award_view(session, cycle, award_id, scenario_code)
        internal_name = stage_filename(self._stage("booking_guide"), "award_booking_guide")
        supplier_name = stage_filename(
            self._stage("booking_guide"), "award_supplier_guides"
        )
        write_booking_guide_internal_xlsx(
            cycle, booking, output_path=runpaths.outputs / internal_name
        )
        write_supplier_award_guides_xlsx(
            cycle, booking, output_path=runpaths.outputs / supplier_name
        )

        self._render_kanban(
            session, runpaths, extra_done=[f"Award {award_code} frozen — booking guides ready"]
        )
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
    ) -> Path:
        """Record a post-award adjustment as the next VERSION + its doc (step 5, ADR-0014).

        Appends the adjustment layer (`awd.add_adjustment`), then writes the versioned post-award
        workbook (`write_post_award_adjustments_xlsx`, which carries the `Version N · as of DATE`
        heading) into outputs/ as `0X_post_award_v{N}.xlsx`. Updates the kanban + commits. Returns
        the written path. `line_changes` are (dc_id, lot_id, tf_id, supplier_id, new_price) tuples.
        """

        version_no = awd_service.add_adjustment(
            session,
            award_id=award_id,
            adjustment_type=adjustment_type,
            effective_date=effective_date,
            reason=reason,
            created_by="pilot",
            line_changes=line_changes,
        )

        filename = stage_filename(
            self._stage("post_award"), "post_award", version=version_no
        )
        out_path = runpaths.outputs / filename
        write_post_award_adjustments_xlsx(
            session, award_id=award_id, as_of_version=version_no, output_path=out_path
        )

        self._render_kanban(
            session, runpaths, extra_done=[f"Post-award adjustment v{version_no} recorded"]
        )
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
                        "SELECT round_id, round_number FROM cyc.cycle_round "
                        "WHERE cycle_id = :cyc"
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
                    select(Award)
                    .where(Award.cycle_id == cycle_id)
                    .order_by(Award.frozen_at)
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
                        "versions": awd_service.award_versions(
                            session, award_id=award.award_id
                        ),
                    }
                )

        output_files = sorted(
            p.name for p in runpaths.outputs.glob("*.xlsx") if p.is_file()
        )
        return {
            "cycle_id": cycle_id,
            "analysis_runs": analysis_runs,
            "awards": awards,
            "output_files": output_files,
        }

    def close_run(self, runpaths: RunPaths) -> Path:
        """Archive the FULL normalized history of a run into a zip; return the zip path (step 10).

        Zips inputs/ + outputs/ + memory/ + NOTES.md + RUN.md + cycle_id.txt under the vault's
        `archives/` (so a later purge leaves the archive intact). This is the PRESENT step of the
        present→confirm→purge close-out; the skill confirms with the buyer, then calls `purge_run`.
        """

        return archive_run(runpaths)

    def purge_run(self, slug: str) -> None:
        """Remove a run's vault folder + commit the removal (after the buyer confirms the archive).

        The governed Postgres records for the cycle REMAIN — only the vault document folder is
        purged; `close_run`'s archive already preserves the full history.
        """

        purge_run(self.vault_root, slug)

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

    def _persist_bid_lines(
        self,
        session: Session,
        cycle: CycleView,
        round_id: str,
        lines: list[ParsedBidLine],
    ) -> int:
        """Persist priced ingest lines as bid.bid_line rows (one submission per supplier).

        Mirrors the demo's `ingest_and_persist`: one `norm.source_artifact` + `bid.bid_submission`
        per supplier for the round (the FK chain), then one `bid.bid_line` per priced line. Only
        `Completeness.BID` lines persist (no-bid / incomplete are not scoreable). Returns the count.
        """

        now = datetime.now(UTC).replace(tzinfo=None)
        submission_by_sup: dict[str, str] = {}

        def _submission_for(supplier_id: str) -> str:
            existing = submission_by_sup.get(supplier_id)
            if existing is not None:
                return existing
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
            submission_by_sup[supplier_id] = submission_id
            return submission_id

        count = 0
        for line in lines:
            if line.completeness is not Completeness.BID:
                continue
            ident = line.identity
            session.add(
                BidLine(
                    bid_line_id=_new_id(),
                    submission_id=_submission_for(ident.supplier_id),
                    cycle_id=cycle.cycle_id,
                    round_id=round_id,
                    supplier_id=ident.supplier_id,
                    dc_id=ident.dc_id,
                    lot_id=ident.lot_id,
                    item_id=ident.item_id,
                    tf_id=ident.tf_id,
                    currency_code="USD",
                    price_basis=line.price_basis or "ALL_IN",
                    submitted_all_in_case=line.components.all_in,
                    fob_case=line.components.fob,
                    delivery_surcharge_case=line.components.delivery_surcharge or None,
                    vegcool_surcharge_case=line.components.vegcool_surcharge or None,
                    lot_discount_case=line.components.lot_discount or None,
                    price_basis_resolved=line.price_basis or None,
                    volume_minimum_cases=line.total_vol_offered,
                    exclusivity_required_flag=False,
                    validity_status="VALID",
                    source_row_number=line.source_row_number,
                    created_at=now,
                    is_scoreable=True,
                    is_awardable=True,
                )
            )
            count += 1
        session.flush()
        return count

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

        item_for_lot = {
            cycle.lots[i].id: cycle.items[i].id for i in range(len(cycle.lots))
        }
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
                    routing_baseline=cycle.incumbent_routing.get(
                        (dc_id, lot_id), Decimal("0")
                    ),
                )
            )
        return tuple(cells)

    @staticmethod
    def _run_version_seq(session: Session, cycle_id: str, analysis_run_id: str) -> int:
        """The 1-based ordinal of THIS sealed run among the cycle's runs (matches the doc)."""

        this_run = session.execute(
            select(AnalysisRun.run_started_at).where(
                AnalysisRun.analysis_run_id == analysis_run_id
            )
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
