"""SQLAlchemy mapped class for the `pilot` schema — the web-console run identity.

`pilot.run` is the DB-backed identity of a console run (ADR-0018 Slice 2): it replaces the
"run = vault folder" assumption so the stateless web console can resolve/list runs with no
filesystem. The PK is the existing `slug` (`<commodity>-<YYYYMMDD>-<short-id>`); `commodity` +
`label` are the run's metadata (today read from RUN.md/NOTES.md), `rehearsal` is the SYNTHETIC
provenance flag (today the `.rehearsal` sentinel), and `cycle_id` is the link to the governed
cycle (today `cycle_id.txt`), nullable until setup is ingested.

It lives in its own `pilot` schema (created by the pilot migration), separate from the eight domain
layers and from `auth` — a run is console orchestration metadata, not part of the governed data
spine. `cycle_id` is plain text (not an FK): cycle ids are text throughout the pilot path, and the
row must be insertable before any cycle exists. The MCP harness does not use this table (it keeps
its file vault); only the web console reads/writes it.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.core.db.types import created_at_column


class Run(Base):
    """A web-console run (identity + cycle link). Mirrors `pilot.run`."""

    __tablename__ = "run"
    __table_args__ = {"schema": "pilot"}

    slug: Mapped[str] = mapped_column(Text, primary_key=True)
    commodity: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    # The SYNTHETIC-provenance flag (replaces the `.rehearsal` vault sentinel): every artifact a
    # rehearsal run generates is stamped synthetic, never "LIVE CYCLE DATA".
    rehearsal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # The link to the governed cycle (replaces `cycle_id.txt`); null until setup is ingested.
    cycle_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at_column()
