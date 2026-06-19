"""The per-RFP run-vault manager (PILOT_SYSTEM_DESIGN §2).

The Run Vault (`RFP_PILOT_VAULT`, sponsor-owned) is the single git repository the routine runs in;
every RFP is a structurally-IDENTICAL sub-folder ("run") under `runs/<slug>/`. This module owns the
scaffold: it stamps out the identical layout for every run, names files by their normalized
workflow stage (zero-padded so they sort by workflow), and commits each change to the vault's git
history. Our code is handed a `vault_root: Path` (a param — tests pass a temp dir); it never assumes
a fixed location on disk.

The scaffold (identical every run):

    runs/<slug>/
      inputs/      # fill-out docs the pilot generates + the formally-uploaded filled files
      outputs/     # generated, VERSIONED workbooks (alignment, booking guide, post-award)
      memory/      # extra docs the sponsor provides + the pilot's own ad-hoc outputs
      NOTES.md     # running notes/memory — "remember X" lands here; links each memory file by name
      RUN.md       # the kanban/status manifest (Done · Doing · Next · Waiting on you)
      cycle_id.txt # the link to the governed Postgres cycle

DB = governed data; the vault = the documents + their git history. This module touches only the
filesystem + git, never Postgres.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Subdirectory names — the identical-every-run scaffold (§2).
SUBDIR_INPUTS = "inputs"
SUBDIR_OUTPUTS = "outputs"
SUBDIR_MEMORY = "memory"
_SUBDIRS = (SUBDIR_INPUTS, SUBDIR_OUTPUTS, SUBDIR_MEMORY)

_RUNS_DIR = "runs"
_NOTES_NAME = "NOTES.md"
_RUN_NAME = "RUN.md"
_CYCLE_ID_NAME = "cycle_id.txt"


@dataclass(frozen=True)
class RunPaths:
    """Every meaningful path inside one run folder — the handle the service threads through.

    `root` is `<vault_root>/runs/<slug>`; the three subdirs and the three manifest files hang off
    it. `slug` is the run's stable identifier (`<commodity-slug>-<YYYYMMDD>-<short-id>`).
    """

    root: Path
    inputs: Path
    outputs: Path
    memory: Path
    notes_md: Path
    run_md: Path
    cycle_id_file: Path
    slug: str


# ---------------------------------------------------------------------------
# slug + path construction
# ---------------------------------------------------------------------------
def _slugify(text: str) -> str:
    """A filesystem-safe, lowercase, hyphenated slug fragment from a free-text label."""

    cleaned = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return cleaned.strip("-") or "rfp"


def _build_run_paths(vault_root: Path, slug: str) -> RunPaths:
    root = vault_root / _RUNS_DIR / slug
    return RunPaths(
        root=root,
        inputs=root / SUBDIR_INPUTS,
        outputs=root / SUBDIR_OUTPUTS,
        memory=root / SUBDIR_MEMORY,
        notes_md=root / _NOTES_NAME,
        run_md=root / _RUN_NAME,
        cycle_id_file=root / _CYCLE_ID_NAME,
        slug=slug,
    )


def run_paths(vault_root: Path, slug: str) -> RunPaths:
    """The `RunPaths` for an existing run slug (does not create anything)."""

    return _build_run_paths(Path(vault_root), slug)


# ---------------------------------------------------------------------------
# normalized workflow-stage file naming (§2)
# ---------------------------------------------------------------------------
def stage_filename(
    stage: int, label: str, *, version: int | None = None, ext: str = "xlsx"
) -> str:
    """Normalized, zero-padded, workflow-stage filename so files sort by the step that made them.

    >>> stage_filename(1, "setup_kickoff")
    '01_setup_kickoff.xlsx'
    >>> stage_filename(4, "round1_alignment", version=1)
    '04_round1_alignment_v1.xlsx'
    """

    body = f"{stage:02d}_{_slugify_label(label)}"
    if version is not None:
        body = f"{body}_v{version}"
    ext = ext.lstrip(".")
    return f"{body}.{ext}"


def _slugify_label(label: str) -> str:
    """Keep underscores in stage labels (they're already snake_case); only sanitize the rest."""

    cleaned = re.sub(r"[^a-z0-9_]+", "_", label.strip().lower())
    return cleaned.strip("_") or "file"


# ---------------------------------------------------------------------------
# seed content for the two manifests
# ---------------------------------------------------------------------------
def _seed_run_md(slug: str, *, commodity: str, label: str) -> str:
    """The kanban skeleton RUN.md every run starts with (Done / Doing / Next / Waiting)."""

    today = datetime.now(UTC).date().isoformat()
    return (
        f"# RUN — {label}\n\n"
        f"- **Run:** `{slug}`\n"
        f"- **Commodity:** {commodity}\n"
        f"- **Cycle:** not created yet\n"
        f"- **Created:** {today}\n\n"
        "## Done\n\n"
        "- Run folder created\n\n"
        "## Doing\n\n"
        "- _(nothing in flight)_\n\n"
        "## Next\n\n"
        "- Fill & upload the Setup/Kickoff workbook in `inputs/`\n\n"
        "## Waiting on you\n\n"
        "- _(nothing yet)_\n"
    )


def _seed_notes_md(slug: str, *, label: str) -> str:
    """The header NOTES.md every run starts with; dated 'remember X' entries append below."""

    today = datetime.now(UTC).date().isoformat()
    return (
        f"# NOTES — {label}\n\n"
        f"_Run `{slug}` · running notes & memory. "
        "Dated entries are appended below; memory files live in `memory/`._\n\n"
        f"- {today}: run created.\n"
    )


# ---------------------------------------------------------------------------
# run creation + listing
# ---------------------------------------------------------------------------
def create_run(vault_root: Path, *, commodity: str, label: str) -> RunPaths:
    """Stamp out the IDENTICAL run scaffold for a new RFP and commit it to the vault.

    slug = `<commodity-slug>-<YYYYMMDD>-<short-id>`. Creates `runs/<slug>/{inputs,outputs,memory}/`
    plus seeded NOTES.md, RUN.md, and an (empty) cycle_id.txt — the same structure every run. If the
    vault is (or should be) a git repo, the new run is committed.
    """

    vault_root = Path(vault_root)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6]
    slug = f"{_slugify(commodity)}-{stamp}-{short}"

    paths = _build_run_paths(vault_root, slug)
    for subdir in (paths.inputs, paths.outputs, paths.memory):
        subdir.mkdir(parents=True, exist_ok=False)
    paths.run_md.write_text(
        _seed_run_md(slug, commodity=commodity, label=label), encoding="utf-8"
    )
    paths.notes_md.write_text(_seed_notes_md(slug, label=label), encoding="utf-8")
    # cycle_id.txt is created empty (the link is written on setup ingest); keeps the scaffold
    # structurally identical from the first commit.
    paths.cycle_id_file.write_text("", encoding="utf-8")
    # Keep empty subdirs under git so the scaffold is identical (git ignores empty dirs).
    for subdir in (paths.inputs, paths.outputs, paths.memory):
        (subdir / ".gitkeep").write_text("", encoding="utf-8")

    git_init_and_commit(vault_root, f"run {slug} created")
    return paths


def list_runs(vault_root: Path) -> list[RunPaths]:
    """All runs in the vault, ordered by slug (so they sort by commodity then date)."""

    runs_root = Path(vault_root) / _RUNS_DIR
    if not runs_root.is_dir():
        return []
    slugs = sorted(p.name for p in runs_root.iterdir() if p.is_dir())
    return [_build_run_paths(Path(vault_root), slug) for slug in slugs]


# ---------------------------------------------------------------------------
# write + git helpers
# ---------------------------------------------------------------------------
def write_to_run(runpaths: RunPaths, subdir: str, filename: str, data: bytes) -> Path:
    """Write `data` to `runs/<slug>/<subdir>/<filename>` and return the path (no commit here)."""

    if subdir not in _SUBDIRS:
        raise ValueError(
            f"unknown run subdir {subdir!r}; expected one of {', '.join(_SUBDIRS)}"
        )
    target_dir = runpaths.root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    path.write_bytes(data)
    return path


def is_git_repo(vault_root: Path) -> bool:
    """True if `vault_root` is the top of a git working tree."""

    return (Path(vault_root) / ".git").exists()


def git_init_and_commit(vault_root: Path, message: str) -> None:
    """Init the vault as a git repo if needed, stage everything, and commit `message`.

    A no-op for the commit step if git reports nothing to commit (e.g. a re-run with no changes).
    Git failures are swallowed deliberately: the vault's version history is a convenience layer, and
    a missing/unconfigured git must never break the file scaffold the pilot depends on.
    """

    vault_root = Path(vault_root)
    if not is_git_repo(vault_root):
        if not _git(vault_root, "init"):
            return
        # Identity for commits in a fresh sponsor vault (tests run in a bare environment).
        _git(vault_root, "config", "user.email", "pilot@kr-rfp.local")
        _git(vault_root, "config", "user.name", "KR RFP Pilot")
    _commit(vault_root, message)


def git_commit_run(vault_root: Path, slug: str, message: str) -> None:
    """Stage + commit the vault for a change inside run `<slug>` (init first if needed)."""

    git_init_and_commit(Path(vault_root), f"[{slug}] {message}")


def _commit(vault_root: Path, message: str) -> None:
    _git(vault_root, "add", "-A")
    # `git commit` exits non-zero when there's nothing staged; that's fine, swallow it.
    _git(vault_root, "commit", "-m", message)


def _git(vault_root: Path, *args: str) -> bool:
    """Run a git command in `vault_root`; return True on success, False on any failure.

    Never raises: git is a best-effort convenience here (see `git_init_and_commit`).
    """

    try:
        result = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "-C", str(vault_root), *args],  # noqa: S607 — git on PATH by design
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return False
    return result.returncode == 0


# ---------------------------------------------------------------------------
# close-run: archive (zip the full normalized history) then purge (remove + commit)
# ---------------------------------------------------------------------------
# The full normalized history a close-out archives (PILOT_SYSTEM_DESIGN step 10): the inputs/
# outputs/ memory/ subfolders PLUS the NOTES.md + RUN.md manifests and the cycle_id.txt link.
_ARCHIVE_SUBDIRS = (SUBDIR_INPUTS, SUBDIR_OUTPUTS, SUBDIR_MEMORY)
_ARCHIVE_FILES = (_NOTES_NAME, _RUN_NAME, _CYCLE_ID_NAME)


def archive_run(runpaths: RunPaths) -> Path:
    """Zip the FULL normalized history of a run into a folder-set zip under the vault; return it.

    Archives the complete run picture (step 10): every file under inputs/ + outputs/ + memory/ plus
    NOTES.md, RUN.md and cycle_id.txt — each stored under the run slug inside the zip so the archive
    is a faithful, self-describing folder set. The zip is written under `<vault>/archives/` (NOT
    inside the run folder, so a subsequent purge of the run folder leaves the archive intact). This
    is the present step of the present→confirm→purge close-out; `purge_run` does the removal after
    the buyer confirms.
    """

    archives_dir = runpaths.root.parent.parent / "archives"
    archives_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    zip_path = archives_dir / f"{runpaths.slug}-{stamp}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for subdir in _ARCHIVE_SUBDIRS:
            base = runpaths.root / subdir
            if not base.is_dir():
                continue
            for item in sorted(base.rglob("*")):
                if item.is_file() and item.name != ".gitkeep":
                    arcname = Path(runpaths.slug) / item.relative_to(runpaths.root)
                    zf.write(item, arcname.as_posix())
        for filename in _ARCHIVE_FILES:
            path = runpaths.root / filename
            if path.is_file():
                arcname = Path(runpaths.slug) / filename
                zf.write(path, arcname.as_posix())
    return zip_path


def purge_run(vault_root: Path, slug: str) -> None:
    """Remove the run folder from the vault and commit the removal (close-out, after confirm).

    The governed Postgres records for the cycle REMAIN (only the vault's document folder is purged);
    the archive zip made by `archive_run` already preserves the full history. Commits the removal so
    the vault's git history records the close-out. Idempotent: a missing run folder is a no-op.
    """

    vault_root = Path(vault_root)
    run_root = vault_root / _RUNS_DIR / slug
    if run_root.is_dir():
        shutil.rmtree(run_root)
    git_init_and_commit(vault_root, f"[{slug}] run closed — folder purged (records retained)")
