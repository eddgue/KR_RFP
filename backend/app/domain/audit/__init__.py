"""Audit layer (`audit` schema) — present-but-empty stub read models (PLAN §2).

Writes go through `app/core/audit/` (the single hash-chained writer), never through services
directly. This package will hold the read models for `event_log` + `decision_note`.
"""
