"""`rfp_pilot_server` — the stdio MCP server that drives the produce-RFP pilot.

A thin `FastMCP` server (PILOT_SYSTEM_DESIGN §7) wrapping `app.pilot.PilotService`. Every tool:

  * reads the run's vault folder from `PILOT_VAULT_ROOT` (the cloned RFP_PILOT_VAULT),
  * opens a `run_unit_of_work(run_slug)` ONLY where the governed Postgres store is touched — a
    session bound to THIS run's OWN isolated database (D30), so no run can see another's data and a
    run never touches demo data (the unit of work owns the commit; the service add+flushes),
  * calls `PilotService` (ALL logic lives there — handlers stay thin), and
  * returns a PLAIN-LANGUAGE summary in the buyer's vocabulary: lots, DCs, rounds, awards — NAMES,
    never raw keys (D23).

Environment:
  * `DATABASE_URL`     — the governed store (read by `app.core.config.settings`).
  * `PILOT_VAULT_ROOT` — the path to the cloned RFP_PILOT_VAULT the routine runs in.

Run as a stdio server:  `python -m rfp_mcp.rfp_pilot_server`  (see mcp/.mcp.json + mcp/README.md).
The package is `rfp_mcp` (not `mcp`) so it never shadows the installed MCP SDK's `mcp` import.
"""

from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

from app.cycle.loader import load_cycle
from app.output.types import CycleView
from app.pilot.run_db import run_unit_of_work
from app.pilot.service import PilotService
from app.pilot.vault import RunPaths

# The MCP app — `mcp dev` / Claude Code register this object's stdio transport.
app = FastMCP("rfp-pilot")

_VAULT_ENV = "PILOT_VAULT_ROOT"


# --------------------------------------------------------------------------- #
# wiring — the vault root + the service factory (handlers stay thin)
# --------------------------------------------------------------------------- #
def _vault_root() -> Path:
    """The cloned RFP_PILOT_VAULT root from `PILOT_VAULT_ROOT` (raises a clear error if unset)."""

    raw = os.environ.get(_VAULT_ENV)
    if not raw:
        raise RuntimeError(
            f"{_VAULT_ENV} is not set — point it at the cloned RFP_PILOT_VAULT folder "
            "(see mcp/README.md)."
        )
    return Path(raw).expanduser()


def _service() -> PilotService:
    return PilotService(_vault_root())


def _paths(slug: str) -> RunPaths:
    """Resolve a run slug to its vault `RunPaths` (no DB touch)."""

    return _service().run_paths(slug)


# --------------------------------------------------------------------------- #
# plain-language rendering helpers (names not keys, D23)
# --------------------------------------------------------------------------- #
def _render_board(board: dict[str, list[str]]) -> str:
    """Render the kanban dict as a compact Done · Doing · Next · Waiting board."""

    lines: list[str] = []
    for bucket in ("Done", "Doing", "Next", "Waiting on you"):
        entries = board.get(bucket, [])
        lines.append(f"{bucket}:")
        if entries:
            lines.extend(f"  - {entry}" for entry in entries)
        else:
            lines.append("  - (nothing here)")
    return "\n".join(lines)


def _name_to_id(cycle: CycleView) -> dict[str, dict[str, str]]:
    """Build name -> id lookups per dimension so the sponsor's NAMES resolve to engine keys."""

    return {
        "dc": {dc.name: dc.id for dc in cycle.dcs},
        "lot": {lot.name: lot.id for lot in cycle.lots},
        "tf": {tf.name: tf.id for tf in cycle.tfs},
        "supplier": {sup.name: sup.id for sup in cycle.suppliers},
    }


def _resolve_analysis_run(history: dict[str, Any], ref: str) -> str:
    """Resolve an analysis-run REF (a version ordinal like "1", or a raw id) to its run id."""

    runs = history["analysis_runs"]
    ref = ref.strip()
    if ref.lstrip("v").isdigit():
        wanted = int(ref.lstrip("v"))
        for run in runs:
            if run["version"] == wanted:
                return str(run["analysis_run_id"])
    for run in runs:
        if str(run["analysis_run_id"]) == ref:
            return ref
    raise ValueError(
        f"no analysis version matches '{ref}'. Available: "
        + ", ".join(f"v{r['version']}" for r in runs)
    )


def _resolve_award(history: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve an award REF (its award code, or a raw id) to its history record."""

    ref = ref.strip()
    awards: list[dict[str, Any]] = list(history["awards"])
    for award in awards:
        if award["award_code"] == ref or str(award["award_id"]) == ref:
            return award
    raise ValueError(
        f"no award matches '{ref}'. Available: "
        + ", ".join(str(a["award_code"]) for a in awards)
    )


def _parse_changes(changes_json: str, cycle: CycleView) -> list[tuple[str, str, str, str, Decimal]]:
    """Parse a `changes_json` list of NAME-based reprices into the engine's keyed cell tuples.

    Each change is an object: {"dc", "lot", "supplier", "new_price", "timeframe"? }. The sponsor
    speaks names; we resolve them to keys here. `timeframe` defaults to the cycle's single TF when
    omitted. Raises a clear, name-based error on any unresolved name (never guesses silently).
    """

    lookup = _name_to_id(cycle)
    default_tf = cycle.tfs[0] if cycle.tfs else None
    raw = json.loads(changes_json)
    if not isinstance(raw, list):
        raise ValueError("changes_json must be a JSON list of {dc, lot, supplier, new_price} rows")

    out: list[tuple[str, str, str, str, Decimal]] = []
    for row in raw:
        dc_id = _lookup_name(lookup["dc"], row.get("dc"), "DC")
        lot_id = _lookup_name(lookup["lot"], row.get("lot"), "lot")
        sup_id = _lookup_name(lookup["supplier"], row.get("supplier"), "supplier")
        tf_name = row.get("timeframe") or (default_tf.name if default_tf else None)
        tf_id = _lookup_name(lookup["tf"], tf_name, "timeframe")
        out.append((dc_id, lot_id, tf_id, sup_id, Decimal(str(row["new_price"]))))
    return out


def _lookup_name(index: dict[str, str], name: object, label: str) -> str:
    if not name:
        raise ValueError(f"a {label} name is required in each change row")
    resolved = index.get(str(name))
    if resolved is None:
        raise ValueError(
            f"{label} '{name}' isn't in this cycle's scope. Known {label}s: "
            + ", ".join(sorted(index)) + "."
        )
    return resolved


# --------------------------------------------------------------------------- #
# tools — start / list / status
# --------------------------------------------------------------------------- #
@app.tool()
def run_start(commodity: str, label: str, rehearsal: bool = False) -> str:
    """Start a new RFP run: stamp the vault folder + generate the Setup/Kickoff workbook.

    Returns the run slug (use it for every later call) + the file the sponsor fills next. Set
    `rehearsal=true` for a practice run on synthetic data — every artifact it generates is stamped
    SYNTHETIC so it can never be mistaken for a live cycle.
    """

    paths = _service().start_run(commodity=commodity, label=label, rehearsal=rehearsal)
    setup = paths.inputs / "01_setup_kickoff.xlsx"
    mode = (
        "  Mode: REHEARSAL — synthetic data (artifacts stamped SYNTHETIC).\n"
        if rehearsal
        else ""
    )
    return (
        f"Started the {commodity} run.\n"
        f"  Run: {paths.slug}\n"
        f"{mode}"
        f"  Next: fill in the Setup/Kickoff workbook I generated at "
        f"`inputs/{setup.name}`, then upload it back into this run's inputs/ and tell me to "
        f"ingest the setup."
    )


@app.tool()
def run_list() -> str:
    """List every RFP run in the vault (so the sponsor can switch between parallel RFPs)."""

    runs = _service().list_runs()
    if not runs:
        return "No runs yet. Say 'start a new RFP for <commodity>' to begin."
    lines = [f"  - {p.slug}" for p in runs]
    return "Runs in the vault:\n" + "\n".join(lines)


@app.tool()
def run_status(run_slug: str) -> str:
    """The kanban for a run — Done · Doing · Next · Waiting on you — in plain language."""

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        board = _service().status(session, paths)
    return f"Where {run_slug} stands:\n" + _render_board(board)


# --------------------------------------------------------------------------- #
# tools — setup
# --------------------------------------------------------------------------- #
@app.tool()
def setup_template(run_slug: str) -> str:
    """Re-generate the Setup/Kickoff workbook into the run's inputs/ (it was made at run_start)."""

    paths = _paths(run_slug)
    from app.pilot.setup_template import build_setup_workbook
    from app.pilot.vault import SUBDIR_INPUTS, stage_filename, write_to_run

    name = stage_filename(1, "setup_kickoff")
    write_to_run(paths, SUBDIR_INPUTS, name, build_setup_workbook())
    return (
        f"Setup/Kickoff workbook is at `inputs/{name}` for {run_slug}. "
        "Fill it in, upload it back into inputs/, then tell me to ingest the setup."
    )


@app.tool()
def setup_ingest(run_slug: str, uploaded_filename: str) -> str:
    """Ingest the filled Setup/Kickoff workbook (already uploaded into inputs/) -> the cycle."""

    paths = _paths(run_slug)
    uploaded = paths.inputs / uploaded_filename
    with run_unit_of_work(run_slug) as session:
        svc = _service()
        svc.ingest_setup(session, paths, uploaded)
        cycle = load_cycle(session, paths.cycle_id_file.read_text(encoding="utf-8").strip())
    return (
        f"Setup ingested for {run_slug}. The {cycle.cycle_name} cycle is live with "
        f"{len(cycle.dcs)} DCs, {len(cycle.lots)} lots, {len(cycle.suppliers)} suppliers, "
        f"{len(cycle.rounds)} round(s). Next: ask me for the Round 1 bid template."
    )


# --------------------------------------------------------------------------- #
# tools — bids
# --------------------------------------------------------------------------- #
@app.tool()
def bid_template(run_slug: str, round_no: int) -> str:
    """Generate the owned bid template for a round into inputs/ (suppliers fill it, by line)."""

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        path = _service().generate_bid_template(session, paths, round_no)
    return (
        f"Round {round_no} bid template is ready at `inputs/{path.name}` for {run_slug}. "
        f"Send it to the suppliers (or fill it yourself), then upload the returned file into "
        f"inputs/ and tell me to load the Round {round_no} bids."
    )


@app.tool()
def ingest_bids(run_slug: str, round_no: int, uploaded_filename: str) -> str:
    """Load a returned bid file (already in inputs/) the strict, key-validated way -> bid lines."""

    paths = _paths(run_slug)
    uploaded = paths.inputs / uploaded_filename
    with run_unit_of_work(run_slug) as session:
        count = _service().ingest_bids(session, paths, round_no, uploaded)
    return (
        f"Loaded {count} priced bid line(s) for Round {round_no} of {run_slug}. "
        f"Next: tell me to run the Round {round_no} alignment."
    )


@app.tool()
def ingest_any(run_slug: str, round_no: int, uploaded_filename: str, confirm: bool) -> str:
    """Flexible "take my file as-is" ingest: confirm=false proposes a mapping; true loads it.

    Drop a supplier's own spreadsheet. With confirm=false I read it, infer which columns are
    DC / supplier / lot / price / volume, and show you the mapping in plain language — nothing is
    loaded. Once you confirm, call again with confirm=true and I write a clean, keyed file into
    inputs/ and load it the strict way.
    """

    paths = _paths(run_slug)
    uploaded = paths.inputs / uploaded_filename
    with run_unit_of_work(run_slug) as session:
        result = _service().ingest_any(session, paths, round_no, uploaded, confirm=confirm)

    if confirm:
        return (
            f"Loaded {result} priced bid line(s) for Round {round_no} of {run_slug} from "
            f"`{uploaded_filename}` (normalized into a clean keyed file in inputs/). "
            f"Next: run the Round {round_no} alignment."
        )

    # confirm=false: result is a MappingProposal — describe the inferred mapping for a quick OK.
    lines = [
        f"Here's how I read `{uploaded_filename}` (header row {result.header_row}):"  # type: ignore[union-attr]
    ]
    for field, m in result.mappings.items():  # type: ignore[union-attr]
        lines.append(f"  - {field}: column '{m.source_header}' ({m.confidence} confidence)")
    confident = "Looks clear" if result.is_confident else "Some columns are uncertain"  # type: ignore[union-attr]
    lines.append(f"{confident}. If that's right, confirm and I'll load it.")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# tools — run the round
# --------------------------------------------------------------------------- #
@app.tool()
def run_round(run_slug: str, round_no: int) -> str:
    """Run the alignment analysis on a round -> a versioned alignment workbook in outputs/.

    Returns the exact file I generated + its analysis version.
    """

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        out_path = _service().run_round(session, paths, round_no)
    version = out_path.stem.rsplit("_v", 1)[-1]
    return (
        f"Round {round_no} alignment is done for {run_slug}. "
        f"I sealed Analysis v{version} and wrote the workbook to `outputs/{out_path.name}`. "
        f"Review the scenarios, then tell me which one to award."
    )


# --------------------------------------------------------------------------- #
# tools — award + post-award
# --------------------------------------------------------------------------- #
@app.tool()
def select_award(
    run_slug: str, analysis_run_ref: str, scenario_code: str, award_code: str
) -> str:
    """Freeze a chosen scenario into an award + generate the booking guides.

    `analysis_run_ref` is the alignment version (e.g. "1" or "v1") or its raw id; `scenario_code`
    is the scenario you picked (B is the risk-adjusted recommendation); `award_code` is your label
    for the award.
    """

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        history = _service().history(session, paths)
        analysis_run_id = _resolve_analysis_run(history, analysis_run_ref)
        _service().freeze_award(
            session,
            paths,
            analysis_run_id=analysis_run_id,
            scenario_code=scenario_code,
            award_code=award_code,
        )
    return (
        f"Froze award {award_code} (Scenario {scenario_code}) for {run_slug}. "
        f"The booking guides are in outputs/ (`08_award_booking_guide.xlsx` for the internal "
        f"book, `08_award_supplier_guides.xlsx` per supplier). "
        f"Record any negotiated reprices as new versions when they come in."
    )


@app.tool()
def record_adjustment(
    run_slug: str,
    award_ref: str,
    adjustment_type: str,
    effective_date: str,
    reason: str,
    changes_json: str,
) -> str:
    """Record a post-award reprice as the next VERSION + generate the post-award workbook.

    `award_ref` is the award code (or its id); `effective_date` is YYYY-MM-DD; `changes_json` is a
    JSON list of NAME-based cells, e.g. `[{"dc": "Dallas DC", "lot": "Lot 2 - Roma",
    "supplier": "Sunbelt Produce", "new_price": 10.75}]` (timeframe is optional when the cycle has
    a single one). Returns the post_award_vN file I generated.
    """

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        history = _service().history(session, paths)
        award = _resolve_award(history, award_ref)
        cycle = load_cycle(session, str(history["cycle_id"]))
        line_changes = _parse_changes(changes_json, cycle)
        out_path = _service().record_adjustment(
            session,
            paths,
            award_id=str(award["award_id"]),
            adjustment_type=adjustment_type,
            effective_date=date.fromisoformat(effective_date),
            reason=reason,
            line_changes=line_changes,
        )
    version = out_path.stem.rsplit("_v", 1)[-1]
    return (
        f"Recorded post-award version {version} on award {award['award_code']} for {run_slug} "
        f"({len(line_changes)} cell(s) repriced, effective {effective_date}). "
        f"The versioned workbook is at `outputs/{out_path.name}`."
    )


# --------------------------------------------------------------------------- #
# tools — history + notes
# --------------------------------------------------------------------------- #
@app.tool()
def history(run_slug: str) -> str:
    """The run's full version history: sealed alignment versions + the award's versions."""

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        hist = _service().history(session, paths)

    runs = cast(list[dict[str, Any]], hist["analysis_runs"])
    awards = cast(list[dict[str, Any]], hist["awards"])
    output_files = cast(list[str], hist["output_files"])

    lines = [f"History for {run_slug}:"]
    if runs:
        lines.append("  Alignment versions:")
        for run in runs:
            lines.append(
                f"    - v{run['version']} (Round {run['round_number']}, sealed "
                f"{run['sealed_at']})"
            )
    else:
        lines.append("  No alignment analyses yet.")
    for award in awards:
        lines.append(f"  Award {award['award_code']} (Scenario {award['scenario_code']}):")
        for v in award["versions"]:
            lines.append(
                f"    - v{v['version_no']} {v['adjustment_type']} "
                f"(effective {v['effective_date']}, {v['n_lines']} cell(s))"
            )
    if output_files:
        lines.append("  Files in outputs/: " + ", ".join(output_files))
    return "\n".join(lines)


@app.tool()
def feedback(run_slug: str) -> str:
    """Distil THIS run's sealed records into a dev-facing FEEDBACK.md (the platform feedback loop).

    Writes/refreshes `<run>/FEEDBACK.md` — data-quality + competition gaps, concentration/cap-breach
    risk, template fit (where flexible ingest had to adapt), process friction (re-runs,
    renegotiations), and the sponsor's notes — for the platform team to review and adapt the engine,
    templates, and analysis. Data stays in the private vault; only structure + signals feed dev.
    """

    paths = _paths(run_slug)
    with run_unit_of_work(run_slug) as session:
        path = _service().feedback_file(session, paths)
    return (
        f"Wrote the development-feedback file for {run_slug} to {path}. It distils this run's "
        "data-quality, competition, concentration, template-fit, and process signals for the "
        "platform team — review it to adapt the engine, templates, and analysis."
    )


@app.tool()
def remember(run_slug: str, note: str, related_file: str = "") -> str:
    """Append a dated note to the run's NOTES.md (optionally linking a memory/ file by name)."""

    paths = _paths(run_slug)
    _service().remember(paths, note, related_file=related_file or None)
    return f"Noted in {run_slug}'s NOTES.md: {note}"


@app.tool()
def add_memory(run_slug: str, filename: str, note: str) -> str:
    """Record a memory file the sponsor already placed in the run, linking it from NOTES.md.

    The file is expected to already sit in the run's memory/ folder (the formal upload flow); this
    links it with a dated note so it's traceable.
    """

    paths = _paths(run_slug)
    target = paths.memory / filename
    if not target.is_file():
        return (
            f"I don't see `memory/{filename}` in {run_slug} yet. Upload it into the run's "
            "memory/ folder first, then ask me to record it."
        )
    _service().add_memory(paths, filename, target.read_bytes(), note)
    return f"Linked `memory/{filename}` in {run_slug}'s NOTES.md: {note}"


# --------------------------------------------------------------------------- #
# tools — close-out (archive -> confirm -> purge)
# --------------------------------------------------------------------------- #
@app.tool()
def close_run(run_slug: str) -> str:
    """Archive the full run history to a zip and return its path (the skill confirms, then purges).

    This is the PRESENT step: I zip inputs/ + outputs/ + memory/ + NOTES.md + run_data.json. Show
    the sponsor the zip and CONFIRM before calling purge_run. The governed Postgres records remain.
    """

    paths = _paths(run_slug)
    zip_path = _service().close_run(paths)
    return (
        f"Archived {run_slug} to `{zip_path}` (inputs, outputs, notes, memory, and the "
        f"governed run_data.json all rode along). Confirm with the sponsor, then call purge_run "
        f"to remove the vault folder. The Postgres records stay put."
    )


@app.tool()
def purge_run(run_slug: str) -> str:
    """Remove a run's vault folder AFTER the sponsor confirms the archive (records remain)."""

    _service().purge_run(run_slug)
    return (
        f"Removed the vault folder for {run_slug}. The archive zip is kept under the vault's "
        f"archives/ and the governed Postgres records remain — nothing about the run is lost."
    )


def main() -> None:
    """Run the stdio MCP server (the entry point `python -m mcp.rfp_pilot_server` invokes)."""

    app.run()


if __name__ == "__main__":
    main()
