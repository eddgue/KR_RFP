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

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.pilot import status as status_mod
from app.pilot.setup_ingest import ingest_setup_workbook
from app.pilot.setup_template import build_setup_workbook
from app.pilot.vault import (
    SUBDIR_INPUTS,
    SUBDIR_MEMORY,
    RunPaths,
    create_run,
    git_commit_run,
    list_runs,
    run_paths,
    stage_filename,
    write_to_run,
)


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
    # PART B — the rest of the cycle loop (stubs; raise NotImplementedError)
    # ================================================================== #
    def generate_bid_template(
        self, session: Session, runpaths: RunPaths, round_number: int
    ) -> Path:
        """PART B: generate the owned bid template for a round into inputs/ (D21, key-validated).

        Builds the `CycleScope` from the persisted cycle (via load_cycle), runs the bid template
        generator (`app.domain.bid.template_generator`), writes `0N_round{n}_bid_template.xlsx` into
        inputs/, updates the kanban, and commits.
        """

        raise NotImplementedError("PART B: generate_bid_template — bid template per round (step 1)")

    def ingest_bids(
        self, session: Session, runpaths: RunPaths, round_number: int, uploaded: list[Path]
    ) -> int:
        """PART B: key-validated ingest of returned bid files -> bid.bid_line (step 1).

        Mirrors the demo's key-validated ingest path; quarantines MISSING_KEY/UNKNOWN_KEY rows and
        reports counts; no-bid = blank price (recorded, not dropped).
        """

        raise NotImplementedError("PART B: ingest_bids — key-validated bid ingest (step 1)")

    def ingest_any(
        self, session: Session, runpaths: RunPaths, uploaded: Path, hint: str | None = None
    ) -> Path:
        """PART B: flexible "take my file as-is" ingest (PILOT_SYSTEM_DESIGN §4).

        Infers the file's structure against the cycle's known scope, shows the inferred mapping for
        confirm, writes a clean key-stamped input file into inputs/, then ingests that. Ambiguity is
        surfaced (quarantine + ask), never guessed silently.
        """

        raise NotImplementedError("PART B: ingest_any — flexible file ingest (§4)")

    def run_round(
        self, session: Session, runpaths: RunPaths, round_number: int
    ) -> Path:
        """PART B: run the engine on a round -> sealed eng.* + versioned alignment file (step 2).

        Reads by key -> EngineInputs -> V3Engine.run -> seals eng.analysis_run; generates the
        18-tab alignment workbook with the `MID-CYCLE ALIGNMENT … Analysis v{seq}` heading into
        outputs/ as `0N_round{n}_alignment_v{seq}.xlsx`; commits.
        """

        raise NotImplementedError("PART B: run_round — run + versioned alignment file (step 2)")

    def freeze_award(
        self, session: Session, runpaths: RunPaths, scenario_code: str
    ) -> Path:
        """PART B: freeze a selected scenario into awd.* + generate the booking guide (step 4).

        Uses `app.domain.awd.service.freeze_award`; generates the two-audience booking guide
        (D22) into outputs/ as `0N_award_booking_guide.xlsx`; commits. Decision-support: the human
        asserts the award (ADR-0006).
        """

        raise NotImplementedError("PART B: freeze_award — select & freeze + booking guide (step 4)")

    def record_adjustment(
        self, session: Session, runpaths: RunPaths, uploaded: Path
    ) -> Path:
        """PART B: record a post-award adjustment as the next version (step 5, ADR-0014).

        Ingests the adjustment intake doc as the next `awd.award_adjustment` version and generates
        the post-award workbook with the `POST-AWARD ADJUSTMENTS … Version N` heading into outputs/
        as `0N_post_award_v{N}.xlsx`; commits.
        """

        raise NotImplementedError("PART B: record_adjustment — versioned post-award layer (step 5)")

    def history(self, session: Session, runpaths: RunPaths) -> dict[str, object]:
        """PART B: history queries for the run (step 6).

        Lists the cycle's rounds + sealed analysis versions, the frozen award, and every post-award
        adjustment version so any historical version's records/document can be re-pulled.
        """

        raise NotImplementedError("PART B: history — version/history queries (step 6)")
