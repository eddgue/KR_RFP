"""RUN.md as the kanban manifest (PILOT_SYSTEM_DESIGN §6 — proactive kanban).

The kanban is computed from TWO sources and rendered into RUN.md:

  * the governed Postgres state for the run's cycle (rounds with bids ingested, sealed analysis
    versions in `eng.analysis_run`, whether an award is frozen in `awd.award`, open post-award
    adjustments in `awd.award_adjustment`), and
  * the FILE presence in the run folder (was the setup workbook generated/uploaded, etc.).

`kanban(...)` returns a plain dict with four buckets — Done / Doing / Next / Waiting — each a list
of plain-language step labels (the buyer's vocabulary, never platform jargon, §5). `read_status`
parses RUN.md's existing header fields; `render_run_md` writes the kanban back into RUN.md.

DB access is read-only here (no writes); when `cycle_id` is None (a run that hasn't ingested its
setup yet) the kanban is computed from files alone.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.pilot.vault import RunPaths, stage_filename

_DONE = "Done"
_DOING = "Doing"
_NEXT = "Next"
_WAITING = "Waiting on you"
_BUCKETS = (_DONE, _DOING, _NEXT, _WAITING)

# The stage-1 setup workbook the pilot writes into inputs/ at start_run.
SETUP_FILENAME = stage_filename(1, "setup_kickoff")


# ---------------------------------------------------------------------------
# reading RUN.md
# ---------------------------------------------------------------------------
def read_status(runpaths: RunPaths) -> dict[str, str]:
    """Parse the RUN.md header bullet fields (`- **Key:** value`) into a flat dict.

    Returns e.g. {"Run": "...", "Commodity": "...", "Cycle": "...", "Created": "..."}.
    A missing RUN.md yields an empty dict (the run hasn't been scaffolded yet).
    """

    out: dict[str, str] = {}
    if not runpaths.run_md.exists():
        return out
    for line in runpaths.run_md.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- **") and ":**" in stripped:
            key, _, value = stripped[len("- **") :].partition(":**")
            out[key.strip()] = value.strip()
    return out


# ---------------------------------------------------------------------------
# computing the kanban
# ---------------------------------------------------------------------------
def kanban(
    session: Session | None, cycle_id: str | None, runpaths: RunPaths
) -> dict[str, list[str]]:
    """Compute the Done / Doing / Next / Waiting board from run state + file presence.

    `session` may be None for a files-only board (no DB touch). Labels are plain language.
    """

    board: dict[str, list[str]] = {b: [] for b in _BUCKETS}

    setup_present = (runpaths.inputs / SETUP_FILENAME).exists()
    board[_DONE].append("Run folder created")
    if setup_present:
        board[_DONE].append("Setup/Kickoff workbook generated")
    else:
        board[_NEXT].append("Generate the Setup/Kickoff workbook")

    if cycle_id is None or session is None:
        # No cycle yet: the next move is to fill & upload the setup doc.
        if setup_present:
            board[_WAITING].append("Fill in the Setup/Kickoff workbook and upload it")
        return board

    counts = _cycle_counts(session, cycle_id)
    board[_DONE].append(
        f"Cycle created ({counts['lots']} lots, {counts['dcs']} DCs, "
        f"{counts['suppliers']} suppliers, {counts['timeframes']} timeframes)"
    )

    total_rounds = counts["rounds"]
    rounds_with_bids = counts["rounds_with_bids"]
    analysis_versions = counts["analysis_versions"]
    award_frozen = counts["award_frozen"]
    open_adjustments = counts["open_adjustments"]

    if rounds_with_bids > 0:
        board[_DONE].append(f"Bids loaded for {rounds_with_bids} of {total_rounds} round(s)")
    if analysis_versions > 0:
        board[_DONE].append(f"{analysis_versions} alignment analysis version(s) sealed")

    # What's in flight / what's next, in the buyer's terms.
    if rounds_with_bids == 0:
        board[_NEXT].append("Send out the Round 1 bid template and load the returned bids")
    elif analysis_versions == 0:
        board[_DOING].append("Run the alignment analysis on the loaded round")
    elif not award_frozen:
        board[_DOING].append("Review the alignment scenarios")
        board[_NEXT].append("Select a scenario and freeze the award")
    else:
        board[_DONE].append("Award frozen")
        if open_adjustments > 0:
            board[_DOING].append(f"{open_adjustments} post-award adjustment version(s) recorded")
        board[_NEXT].append("Record any further negotiated reprices as new versions")

    # Waiting-on-you: the gated, sponsor-action step.
    if rounds_with_bids < total_rounds and rounds_with_bids > 0:
        board[_WAITING].append("Upload the next round's bids when they come in")
    elif analysis_versions > 0 and not award_frozen:
        board[_WAITING].append("Pick the scenario you want to award")

    return board


def _cycle_counts(session: Session, cycle_id: str) -> dict[str, int]:
    """Read the governed counts the kanban reasons over (all read-only)."""

    def scalar(sql: str) -> int:
        value = session.execute(text(sql), {"cyc": cycle_id}).scalar()
        return int(value) if value is not None else 0

    return {
        "dcs": scalar(
            "SELECT count(DISTINCT dc_id) FROM cyc.cycle_projected_volume WHERE cycle_id = :cyc"
        ),
        "lots": scalar("SELECT count(*) FROM cyc.cycle_lot WHERE cycle_id = :cyc"),
        "suppliers": scalar(
            "SELECT count(*) FROM cyc.cycle_invited_supplier WHERE cycle_id = :cyc"
        ),
        "timeframes": scalar("SELECT count(*) FROM cyc.cycle_timeframe WHERE cycle_id = :cyc"),
        "rounds": scalar("SELECT count(*) FROM cyc.cycle_round WHERE cycle_id = :cyc"),
        "rounds_with_bids": scalar(
            "SELECT count(DISTINCT round_id) FROM bid.bid_line WHERE cycle_id = :cyc"
        ),
        "analysis_versions": scalar(
            "SELECT count(*) FROM eng.analysis_run WHERE cycle_id = :cyc AND is_sealed = true"
        ),
        "award_frozen": scalar(
            "SELECT count(*) FROM awd.award WHERE cycle_id = :cyc AND status = 'FROZEN'"
        ),
        "open_adjustments": scalar(
            "SELECT count(*) FROM awd.award_adjustment adj "
            "JOIN awd.award a ON a.award_id = adj.award_id "
            "WHERE a.cycle_id = :cyc"
        ),
    }


# ---------------------------------------------------------------------------
# rendering RUN.md
# ---------------------------------------------------------------------------
def render_run_md(runpaths: RunPaths, status: dict[str, list[str]]) -> None:
    """Rewrite RUN.md: keep the existing header bullets, replace the four kanban sections."""

    header = read_status(runpaths)
    lines: list[str] = []
    title = header.get("Run", runpaths.slug)
    lines.append(f"# RUN — {header.get('Commodity', title)}")
    lines.append("")
    # Preserve known header fields in a stable order; cycle may have been written since.
    for key in ("Run", "Commodity", "Cycle", "Created"):
        if key in header:
            lines.append(f"- **{key}:** {header[key]}")
    lines.append("")

    for bucket in _BUCKETS:
        lines.append(f"## {bucket}")
        lines.append("")
        entries = status.get(bucket, [])
        if entries:
            lines.extend(f"- {entry}" for entry in entries)
        else:
            lines.append("- _(nothing here)_")
        lines.append("")

    runpaths.run_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def set_header_field(runpaths: RunPaths, key: str, value: str) -> None:
    """Update a single `- **Key:** value` header bullet in RUN.md (used to record the cycle id)."""

    if not runpaths.run_md.exists():
        return
    path: Path = runpaths.run_md
    out_lines: list[str] = []
    replaced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(f"- **{key}:**"):
            out_lines.append(f"- **{key}:** {value}")
            replaced = True
        else:
            out_lines.append(line)
    if not replaced:
        out_lines.append(f"- **{key}:** {value}")
    path.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
