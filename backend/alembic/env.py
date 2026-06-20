"""Alembic environment — wires app metadata + the app's settings DB URL; schema-aware.

The DB URL is NOT in alembic.ini; it is pulled from the single typed config surface
(app.core.config.settings) so there are no secrets in the repo. All eight layer schemas are
included in the version table comparison so autogenerate is schema-aware.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import every domain models module so their tables register on the shared metadata.
# (Most are stubs this phase, but importing them fixes the seam and keeps autogenerate honest.)
import app.domain.audit.models  # noqa: F401
import app.domain.awd.models  # noqa: F401
import app.domain.bid.models  # noqa: F401
import app.domain.cyc.models  # noqa: F401
import app.domain.eng.models  # noqa: F401
import app.domain.norm.models  # noqa: F401
import app.domain.perf.models  # noqa: F401
import app.domain.ref.models  # noqa: F401
from app.core.config.settings import get_settings
from app.core.db.base import SCHEMAS, metadata

config = context.config

# Inject the URL from settings so alembic.ini holds no connection string. A caller may pre-set the
# URL on the Config (e.g. per-run database provisioning, D30) — respect it and don't override.
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def _include_object(obj, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    """Only manage objects in our eight layer schemas (ignore anything else present)."""

    return not (type_ == "table" and getattr(obj, "schema", None) not in SCHEMAS)


def run_migrations_offline() -> None:
    """Emit SQL without a live connection."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=_include_object,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=_include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
