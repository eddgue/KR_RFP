"""Shared PilotService wiring for the console's run-scoped surfaces (runs + bids).

Both the runs router (file/setup/template) and the bids router (import/list) drive the SAME
`app.pilot.service.PilotService` — no domain logic is reimplemented in the API layer. The service
is built against the configured `vault_root` with `isolate_db=False` so it shares the request's
governed session (no per-run database is provisioned), exactly the way the MCP server wraps it.
These helpers are factored here so neither router duplicates the wiring; the test suite redirects
the vault by monkeypatching `_vault_root` on THIS module.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config.settings import get_settings
from app.core.errors.taxonomy import AppError, ErrorCode
from app.pilot.service import PilotService
from app.pilot.vault import RunPaths


@lru_cache
def _vault_root() -> Path:
    """The configured vault root, created on first use (so a fresh box just works)."""

    root = Path(get_settings().vault_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def service() -> PilotService:
    """A PilotService on the configured vault; `isolate_db=False` shares the request session."""

    # isolate_db=False: the console shares the request's governed session, no per-run DB.
    return PilotService(_vault_root(), isolate_db=False)


def resolve_paths(slug: str) -> RunPaths:
    """The `RunPaths` for an existing run, or 404 if the slug isn't a real run."""

    paths = service().run_paths(slug)
    if not paths.root.is_dir():
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"No run named {slug!r}.",
            status_code=404,
        )
    return paths
