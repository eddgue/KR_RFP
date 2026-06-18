"""Mapped classes for the `perf` schema — STUB (no models yet).

Target tables (PLAN §2): history feeds + scorecard — `itrade_receipt` (receipt grain),
`kcms_movement`, `supplier_scorecard` (2 snapshots), commercial-pricing tables (re-pointed to
kickoff), VSP tables. KEEP: importer discipline (flag-first, impossible-date reject);
commercial component storage + replayable formula audit. Tenant-scoped (`client_id`).

Models land in a later phase. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

PerfBase = SchemaBase("perf")
