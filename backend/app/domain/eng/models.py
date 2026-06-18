"""Mapped classes for the `eng` schema — STUB (no models yet).

Target tables (PLAN §2, ENG-PLAN §3): sealed runs, scores, scenarios, split awards —
`analysis_run` (+ `run_input`, version pins, `is_sealed`), `bid_score` (5-factor),
`scenario` (A-G), `scenario_award` (split, `volume_share`, `cap_breach_flag`),
`round_analysis_snapshot`. KEEP: sealed calc-run spine + hashed manifests + version pins.
Tenant-scoped (`client_id`).

The runner (`runner.py`, later phase) seals the run, freezes inputs, hashes manifests, records
version pins, and calls the engine library; outputs are append-only and immutable (the
immutability guard in core/audit attaches to `AnalysisRun` once it is modelled here).

Migration 0005 (eng.scenario_award split re-grain — G1/D10) is migration-only: it ALTERs the
baseline `eng.scenario_award` (which is itself migration-only, re-expressed in
db/baseline/schema.sql) to add `volume_share` / `is_fallback` / `cap_breach_flag` and relax the
single-winner uniqueness to per-supplier. The full `eng.*` ORM classes land in a later phase; the
split columns are carried by the migration until then.

Models land in a later phase. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

EngBase = SchemaBase("eng")
