"""Mapped classes for the `audit` schema — STUB (read models, no models yet).

Target tables (PLAN §2, security/PLAN §3): live append-only event log — `event_log`
(hash-chained: `before/after_state_hash`, `prev_event_hash`, `event_hash`, per-tenant `seq`)
and `decision_note`. Tenant-scoped (`client_id`).

WRITES are produced solely by `app/core/audit/writer.py` (the single hash-chained writer);
DB-layer write-only enforcement (UPDATE/DELETE triggers + INSERT/SELECT-only grants) is owned
by Platform & Data's M1. This package will hold the READ models only (e.g. for "open last
cycle" and `verify_chain`).

The migration `0001_baseline` creates a minimal `audit.event_log` table so the writer's INSERT
target exists; full read models land in a later phase. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

AuditBase = SchemaBase("audit")
