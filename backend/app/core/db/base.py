"""SQLAlchemy declarative base + schema-qualified naming convention.

The eight logical layers are real PostgreSQL schemas (PLAN §1.7). Every mapped class lives
in exactly one schema; `SchemaBase(<schema>)` produces a per-layer base so domain packages
declare `class Foo(RefBase): ...` and inherit `__table_args__ = {"schema": "ref"}`.

A deterministic naming convention is set on the shared `MetaData` so constraint/index names
are stable across migrations and round-trip cleanly (kills SQLite-ism / autogenerate drift).
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# The eight logical layers = the eight PostgreSQL schemas (PLAN §2).
SCHEMAS: tuple[str, ...] = ("ref", "norm", "cyc", "bid", "eng", "awd", "perf", "audit")

# Stable, schema-aware constraint naming so Alembic autogenerate is reproducible.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Root declarative base. All mapped classes share one `MetaData`."""

    metadata = metadata


def SchemaBase(schema: str) -> type[Base]:  # noqa: N802 (factory returns a class)
    """Return an abstract declarative base bound to `schema`.

    Domain packages subclass the returned base so all their tables land in the right
    PostgreSQL schema without repeating `__table_args__` on every model.
    """

    if schema not in SCHEMAS:
        raise ValueError(f"unknown layer schema: {schema!r} (expected one of {SCHEMAS})")

    class _LayerBase(Base):
        __abstract__ = True
        __table_args__ = {"schema": schema}

    _LayerBase.__name__ = f"{schema.capitalize()}Base"
    _LayerBase.__qualname__ = _LayerBase.__name__
    return _LayerBase
