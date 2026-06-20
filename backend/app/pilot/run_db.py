"""Per-run database isolation (D30): every run gets its OWN Postgres database.

A run starts BLANK (a freshly created + migrated database), carries no demo data, and is invisible
to every other run — the compliance substrate the skill harness reads. The run's database name is
derived deterministically from its slug; provisioning creates + migrates it to head; the run
operates only within it via `run_unit_of_work`; close/purge drops it.

Why a separate DATABASE (not a shared one with a tenant column): the engine + intake carry globally
unique reference codes (`ref.dc` DC01.., suppliers, items). A shared store collides across runs and
lets one run see another's rows. A database per run gives hard isolation with the SAME schema names,
so nothing in the app has to change — only WHERE the session points (D30). Version isolation (D32)
follows: each run's store is pinned to the migration head it was provisioned at.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.settings import get_settings

_NAME_RE = re.compile(r"[^a-z0-9]+")
_DB_PREFIX = "kr_rfp_run_"
_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
# alembic.ini declares `script_location = alembic` (relative), which Alembic resolves against the
# process CWD — so provisioning would only work when CWD is backend/. The MCP server runs from
# elsewhere, so pin the scripts dir to an absolute path next to alembic.ini (CWD-independent).
_ALEMBIC_SCRIPTS = _ALEMBIC_INI.parent / "alembic"

# One engine per run database URL (connection pools are reused across a run's calls).
_engines: dict[str, Engine] = {}


def run_db_name(slug: str) -> str:
    """Deterministic, identifier-safe Postgres database name for a run slug."""

    base = _NAME_RE.sub("_", slug.lower()).strip("_")
    return (_DB_PREFIX + base)[:63]  # Postgres identifier limit is 63 bytes


def run_db_url(slug: str) -> str:
    """The connection URL for a run's database (same server/credentials as the app DB)."""

    # render_as_string(hide_password=False): str(URL) masks the password as '***', which would
    # break the connection — keep the real credential in the URL we hand to create_engine.
    url = make_url(get_settings().database_url).set(database=run_db_name(slug))
    return url.render_as_string(hide_password=False)


def _admin_engine() -> Engine:
    """An AUTOCOMMIT engine on the maintenance database for CREATE/DROP DATABASE (no txn block)."""

    admin_url = make_url(get_settings().database_url).set(database="postgres")
    return create_engine(admin_url, isolation_level="AUTOCOMMIT", future=True)


def _migrate_to_head(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_ALEMBIC_SCRIPTS))  # CWD-independent (D30)
    cfg.set_main_option("sqlalchemy.url", url)  # env.py respects a pre-set URL (D30)
    command.upgrade(cfg, "head")


def provision_run_database(slug: str) -> str:
    """Create the run's database (if absent) and migrate it to head; return its URL.

    The database is BLANK by construction — it never receives demo/synthetic data and no other run
    can see it. Safe to call once per run at start.
    """

    name = run_db_name(slug)
    admin = _admin_engine()
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        admin.dispose()

    url = run_db_url(slug)
    _migrate_to_head(url)
    return url


def _engine_for(url: str) -> Engine:
    eng = _engines.get(url)
    if eng is None:
        eng = create_engine(url, pool_pre_ping=True, future=True)
        _engines[url] = eng
    return eng


@contextmanager
def run_unit_of_work(slug: str) -> Iterator[Session]:
    """A unit of work bound to THIS run's isolated database — commit on success, roll back on error.

    Mirrors the app's request-scoped unit of work, but the session points at the run's own database,
    so every read/write the Engine agent makes is confined to this run (D30).
    """

    engine = _engine_for(run_db_url(slug))
    factory = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _libpq_url(slug: str) -> str:
    """The run DB URL as a plain libpq URI (no `+psycopg`) for the pg_dump/psql CLIs."""

    return (
        make_url(run_db_url(slug))
        .set(drivername="postgresql")
        .render_as_string(hide_password=False)
    )


def _run_cli(cmd: list[str]) -> None:
    """Run a Postgres CLI (pg_dump/psql); raise with stderr on failure."""

    result = subprocess.run(  # noqa: S603 — fixed argv, no shell
        cmd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed ({result.returncode}): {result.stderr.strip()}")


def dump_run_database(slug: str, out_path: Path) -> Path:
    """Dump the run's database to a plain-SQL file (schema + data) for the vault (git-persisted).

    A full pg_dump restores into an EMPTY database cleanly — tables created, data COPY'd, then FK
    constraints added last — so the FK-heavy schema round-trips without load-order issues. This is
    how a run's governed state survives an ephemeral (web) container: the dump rides the vault git.
    """

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run_cli(
        ["pg_dump", "--no-owner", "--no-privileges", "--file", str(out_path), _libpq_url(slug)]  # noqa: S607
    )
    return out_path


def restore_run_database(slug: str, sql_path: Path) -> None:
    """Rehydrate the run's database from a vault SQL dump into a FRESH empty database.

    The inverse of `dump_run_database`, for session start in a fresh container: drop any stale copy,
    create an EMPTY database (no migrate — the dump carries the schema), then load the dump. After
    this the run resumes exactly where it was sealed.
    """

    name = run_db_name(slug)
    _engines.pop(run_db_url(slug), None)
    admin = _admin_engine()
    try:
        with admin.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :n AND pid <> pg_backend_pid()"
                ),
                {"n": name},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        admin.dispose()
    _run_cli(
        ["psql", "--set", "ON_ERROR_STOP=1", "--quiet", "--file", str(sql_path), _libpq_url(slug)]  # noqa: S607
    )


def drop_run_database(slug: str) -> None:
    """Terminate any lingering connections and DROP the run's database (purge)."""

    name = run_db_name(slug)
    url = run_db_url(slug)
    eng = _engines.pop(url, None)
    if eng is not None:
        eng.dispose()
    admin = _admin_engine()
    try:
        with admin.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :n AND pid <> pg_backend_pid()"
                ),
                {"n": name},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
    finally:
        admin.dispose()
