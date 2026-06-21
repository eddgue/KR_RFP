"""`rfp_mcp.rehydrate` — restore every vault run's isolated DB from its committed snapshot.

The web environment is ephemeral: between sessions the container (and its Postgres) is reclaimed,
but the cloned RFP_PILOT_VAULT git repo carries each run's `db/run_db.sql` dump (written after every
governed write by `PilotService.snapshot_run`). This module is the SessionStart counterpart: on a
fresh box it walks the vault and recreates + loads each run's database, so the harness resumes every
run exactly where it was sealed.

Run it once at session start:  `python -m rfp_mcp.rehydrate`  (see the SessionStart hook).
It reads `PILOT_VAULT_ROOT` (the cloned vault) and `DATABASE_URL` (the Postgres server) from the
environment — the same two variables the MCP server uses. It is SAFE to run when there is nothing to
restore (no runs, or runs without a snapshot): it simply reports zero restored and exits 0.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app.pilot.service import PilotService

_VAULT_ENV = "PILOT_VAULT_ROOT"


def _vault_root() -> Path:
    """The cloned RFP_PILOT_VAULT root from `PILOT_VAULT_ROOT` (raises a clear error if unset)."""

    raw = os.environ.get(_VAULT_ENV)
    if not raw:
        raise RuntimeError(
            f"{_VAULT_ENV} is not set — point it at the cloned RFP_PILOT_VAULT folder "
            "(see mcp/README.md)."
        )
    return Path(raw).expanduser()


def main() -> int:
    """Rehydrate all runs from their vault snapshots; print what was restored. Returns exit code."""

    restored = PilotService(_vault_root()).rehydrate_runs()
    if restored:
        print(f"Rehydrated {len(restored)} run(s) from the vault: " + ", ".join(restored))
    else:
        print("No run snapshots in the vault to rehydrate (nothing to do).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
