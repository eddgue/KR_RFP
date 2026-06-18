"""Mapped classes for the `cyc` schema — STUB (no models yet).

Target tables (PLAN §2): the kickoff keystone (the in-gate) — `cycle`, `cycle_timeframe`,
`cycle_round`, `cycle_dc`, `cycle_lot`, `cycle_objective`, `cycle_pricing` + `cycle_safety`,
`cycle_pba_term`, `cycle_commercial_term`, `cycle_rfi_question`, `cycle_timeline_event`,
`cycle_narrative`, `cycle_invited_supplier`, `cycle_ingate_approval` (G12). KEEP:
scope-consistency trigger; invited-supplier denominator. Tenant-scoped (`client_id`).

Models land in a later phase. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

CycBase = SchemaBase("cyc")
