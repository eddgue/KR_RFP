#!/usr/bin/env python3
"""Seed the deployed (or local-compose) KR_RFP database so the console renders something real.

What this writes (all COMMITTED — see the note on the dry-run script below):

  (a) an `admin` web-console user      — password from $SEED_ADMIN_PASSWORD, so you can log in;
  (b) the TOMATO synthetic full cycle  — the `app.pilot.synthetic` builders (shared with the e2e
                                         test), driven through PilotService end to end and FROZEN;
  (c) the POTATO real-data cycle       — `backend/scripts/potato_legacy_dryrun.py`'s legacy
                                         converters, driven the same way and FROZEN.

Both cycles end FROZEN/finalized so the Awards screens render. The runs are created on the WEB
CONSOLE path (`db_runs=True, persist_outputs=False`) — exactly how the live console makes runs — so
they land as `pilot.run` rows with a linked governed cycle and a frozen `awd.award`. That is what
the runs list and the Awards screens resolve from (the stateless console reads identity + awards
from the DB, never from disk; ADR-0018). No files are written server-side.

Run it locally (against the compose stack) or in the cloud (against Cloud SQL) the same way — it
reads DATABASE_URL from the environment via the app settings, like every other entrypoint:

    DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/kr_rfp \\
        SEED_ADMIN_PASSWORD=... python deploy/gcp/seed.py

It needs a database migrated to head (`alembic upgrade head`). It is IDEMPOTENT for the admin user
(upsert) and ADDITIVE for the cycles (each call appends a fresh TOMATO + POTATO run — runs are
cheap and there is no natural unique key to upsert on; pass --skip-tomato / --skip-potato or
--admin-only to control what runs).

Why this lives at deploy/gcp/ but imports backend test/scripts modules: it runs INSIDE the backend
image (the Dockerfile copies tests/ and scripts/ in), where `app`, `tests`, and `scripts` are all
importable. The docker-compose `seed` service mounts this file in and invokes it with that image.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import traceback
from pathlib import Path

# --------------------------------------------------------------------------- #
# import path: make the backend package tree importable whether we are invoked
# from the repo root (local) or from /app inside the backend image (cloud).
# --------------------------------------------------------------------------- #
_THIS = Path(__file__).resolve()
# repo-root/deploy/gcp/seed.py -> repo root is two parents up.
_REPO_ROOT = _THIS.parents[2]
_BACKEND = _REPO_ROOT / "backend"
for _candidate in (_BACKEND, _REPO_ROOT):
    if _candidate.is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
# Inside the backend image the cwd is /app and `app`/`tests`/`scripts` are already importable;
# the loop above is the local (repo-root invocation) fallback.


def _log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# (a) admin console user
# --------------------------------------------------------------------------- #
def seed_admin(username: str = "admin") -> str:
    """Upsert the console admin user with the password from $SEED_ADMIN_PASSWORD.

    Reuses `app.auth.create_user.upsert_user` (argon2 hash, active, no 2FA yet) so the seed and the
    operational `python -m app.auth.create_user` path agree byte for byte. Idempotent: re-running
    just resets the password.
    """

    from app.auth.create_user import upsert_user

    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not password:
        raise SystemExit(
            "SEED_ADMIN_PASSWORD is not set — refusing to seed an admin with a blank/default "
            "password. Set it (e.g. export SEED_ADMIN_PASSWORD=...), then re-run."
        )
    user_id = upsert_user(username, password)
    _log(f"  [admin] upserted console user {username!r} (id={user_id})")
    return user_id


# --------------------------------------------------------------------------- #
# shared console-path driver: start_run -> ingest setup -> bids -> analyze -> freeze
# --------------------------------------------------------------------------- #
def _latest_analysis_run_id(session, cycle_id: str) -> str:  # type: ignore[no-untyped-def]
    from sqlalchemy import text

    return str(
        session.execute(
            text(
                "SELECT analysis_run_id FROM eng.analysis_run WHERE cycle_id = :cyc "
                "ORDER BY run_started_at DESC LIMIT 1"
            ),
            {"cyc": cycle_id},
        ).scalar_one()
    )


def _drive_console_cycle(
    *,
    commodity: str,
    label: str,
    setup_bytes: bytes,
    fill_template: callable,  # (template_bytes, cycle_view) -> filled_bytes
    award_code: str,
) -> str:
    """Drive ONE full cycle through PilotService on the WEB-CONSOLE path and FREEZE it.

    Console path: `db_runs=True` (writes a `pilot.run` row so the run lists + the cycle links),
    `persist_outputs=False` (governed DB writes only; deliverables render on request — no files).
    Everything rides a single `unit_of_work`, which COMMITS on success — that is the difference from
    the dry-run script (which rolls back). Returns the new cycle_id.
    """

    from app.core.db.session import unit_of_work
    from app.cycle.loader import load_cycle
    from app.cycle.scope import build_scope_from_cycle
    from app.domain.bid.template_generator import generate_template_bytes
    from app.pilot.service import PilotService

    # The vault root is unused on the console path (no folder is scaffolded), but PilotService still
    # needs one for its RunPaths shape — point it at a throwaway temp dir.
    tmp_root = Path(tempfile.mkdtemp(prefix="kr_seed_"))
    service = PilotService(tmp_root, isolate_db=False, db_runs=True, persist_outputs=False)

    with unit_of_work() as session:
        # 1) start the run (mints a slug, writes the pilot.run row; no folder, no isolated DB).
        paths = service.start_run(commodity=commodity, label=label, session=session)
        _log(f"  [{label}] run started: slug={paths.slug}")

        # 2) ingest the setup workbook from BYTES (no-disk) -> governed cycle, linked on the run.
        cycle_id = service.ingest_setup_bytes(session, paths, setup_bytes)
        cycle = load_cycle(session, cycle_id)
        _log(
            f"  [{label}] setup ingested: cycle_id={cycle_id} "
            f"({len(cycle.dcs)} DCs, {len(cycle.lots)} lots, {len(cycle.suppliers)} suppliers, "
            f"{len(cycle.tfs)} TFs, {len(cycle.rounds)} round(s))"
        )

        # 3) generate the Round 1 owned bid template IN MEMORY, fill it, ingest from BYTES.
        scope = build_scope_from_cycle(cycle, 1)
        template_bytes = generate_template_bytes(scope)
        filled = fill_template(template_bytes, cycle)
        result = service.ingest_bids_bytes(session, paths, 1, filled)
        _log(
            f"  [{label}] round 1 bids ingested: {result.ingested} priced line(s), "
            f"{result.quarantined_bids} quarantined"
        )

        # 4) run the engine on round 1 -> sealed eng.analysis_run + scores + scenarios.
        service.run_round(session, paths, 1)
        analysis_run_id = _latest_analysis_run_id(session, cycle_id)
        _log(f"  [{label}] analysis sealed: analysis_run_id={analysis_run_id}")

        # 5) freeze Scenario B (the risk-adjusted recommendation) -> awd.award (the Awards screen).
        award_id = service.freeze_award(
            session,
            paths,
            analysis_run_id=analysis_run_id,
            scenario_code="B",
            award_code=award_code,
        )
        _log(f"  [{label}] award FROZEN: award_id={award_id} (code={award_code})")

        # unit_of_work COMMITS here on a clean exit — the run, cycle, analysis, and award persist.
    _log(f"  [{label}] committed.")
    return cycle_id


# --------------------------------------------------------------------------- #
# (b) TOMATO synthetic full cycle — reuse the e2e test builders
# --------------------------------------------------------------------------- #
def seed_tomato() -> str:
    """Seed the synthetic TOMATO cycle, FROZEN, using the committed e2e-cycle builders.

    `build_filled_setup` / `fill_bid_template` (in `app.pilot.synthetic`) are the exact synthetic
    builders the `test_full_cycle_loop_e2e` test drives (2 DCs, 2 lots, 2 suppliers, 1 TF, 2
    rounds) — the test imports them from the same module, so the seed and the test stay in
    lock-step. (They live in the app package, not the test module, so the seed never imports pytest
    at runtime.)
    """

    from app.pilot.synthetic import build_filled_setup, fill_bid_template

    _log("[TOMATO] seeding synthetic full cycle ...")
    return _drive_console_cycle(
        commodity="Field Tomatoes",
        label="TOMATO synthetic (seed)",
        setup_bytes=build_filled_setup(),
        fill_template=lambda template_bytes, _cycle: fill_bid_template(template_bytes),
        award_code="AWD-TOMATO-SEED",
    )


# --------------------------------------------------------------------------- #
# (c) POTATO real-data cycle — reuse the legacy dry-run converters, but COMMIT
# --------------------------------------------------------------------------- #
def seed_potato() -> str:
    """Seed the real-data POTATO cycle, FROZEN, using the legacy dry-run's converters.

    Reuses `scripts.potato_legacy_dryrun`'s `parse_legacy` / `build_setup_bytes` /
    `fill_bid_template` (the legacy-workbook -> OUR-inputs conversion) but drives them through the
    COMMITTING console path here (the dry-run script itself rolls back). Needs the legacy sample
    workbook at `reference/samples/potato_2026_rfp_input.xlsx` (in the repo / copied in the image).
    """

    from scripts.potato_legacy_dryrun import (
        LEGACY_INPUT,
        build_setup_bytes,
        fill_bid_template,
        parse_legacy,
    )

    from app.cycle.scope import build_scope_from_cycle  # noqa: F401 (imported for clarity/parity)

    if not Path(LEGACY_INPUT).is_file():
        _log(
            f"  [POTATO] SKIPPED — legacy input not found at {LEGACY_INPUT}. "
            "(Reference samples are not present in this image/checkout.)"
        )
        return ""

    _log("[POTATO] seeding real-data cycle from the legacy workbook ...")
    data = parse_legacy(Path(LEGACY_INPUT))
    setup_bytes = build_setup_bytes(data)

    def _fill(template_bytes: bytes, cycle) -> bytes:  # type: ignore[no-untyped-def]
        # The legacy bids key on the TF *label* (TF1/TF2); the generated template carries the TF
        # *code* (TF01/TF02). Resolve via the loaded cycle's code->name map (as the script does).
        tf_code_to_label = {tf.code: tf.name for tf in cycle.tfs}
        filled_bytes, stats = fill_bid_template(template_bytes, data, tf_code_to_label)
        _log(
            f"  [POTATO] template fill: scope_rows={stats.scope_rows} filled={stats.filled} "
            f"unmatched={stats.unmatched_keys}"
        )
        return filled_bytes

    return _drive_console_cycle(
        commodity=data.config.commodity,
        label="POTATO legacy (seed)",
        setup_bytes=setup_bytes,
        fill_template=_fill,
        award_code="AWD-POTATO-SEED",
    )


# --------------------------------------------------------------------------- #
# verification: count what we created so the runbook can assert it
# --------------------------------------------------------------------------- #
def _report_counts() -> None:
    """Print the headline counts the runbook checks: console users, runs, cycles, frozen awards."""

    from sqlalchemy import text

    from app.core.db.session import unit_of_work

    with unit_of_work() as session:
        users = session.execute(text("SELECT count(*) FROM auth.app_user")).scalar_one()
        runs = session.execute(text("SELECT count(*) FROM pilot.run")).scalar_one()
        cycles = session.execute(text("SELECT count(*) FROM cyc.cycle")).scalar_one()
        awards = session.execute(text("SELECT count(*) FROM awd.award")).scalar_one()
    _log(
        "\n=== seed summary ===\n"
        f"  auth.app_user rows : {users}\n"
        f"  pilot.run rows     : {runs}\n"
        f"  cyc.cycle rows     : {cycles}\n"
        f"  awd.award rows     : {awards}"
    )


# --------------------------------------------------------------------------- #
# entrypoint
# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Seed the KR_RFP database (admin + two cycles).")
    parser.add_argument("--admin-only", action="store_true", help="seed only the admin user")
    parser.add_argument("--skip-tomato", action="store_true", help="skip the TOMATO synthetic run")
    parser.add_argument("--skip-potato", action="store_true", help="skip the POTATO real-data run")
    parser.add_argument(
        "--admin-username", default="admin", help="console admin username (default: admin)"
    )
    args = parser.parse_args(argv)

    from app.core.config.settings import get_settings

    db_url = get_settings().database_url
    # Redact credentials in the echo.
    safe = db_url
    if "@" in safe and "//" in safe:
        scheme, rest = safe.split("//", 1)
        if "@" in rest:
            safe = f"{scheme}//***@{rest.split('@', 1)[1]}"
    _log(f"KR_RFP seed — DATABASE_URL={safe}")

    try:
        seed_admin(args.admin_username)
        if not args.admin_only:
            if not args.skip_tomato:
                seed_tomato()
            if not args.skip_potato:
                seed_potato()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 — surface the full traceback, fail loudly
        _log("SEED FAILED:")
        traceback.print_exc()
        return 1

    _report_counts()
    _log("\nseed: done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
