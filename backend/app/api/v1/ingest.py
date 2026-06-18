"""Ingest surface (PLAN §5): itrade/import, kcms/import, normalize/propose+confirm.

Present-but-empty this phase. Routes land with the feed loaders (`perf`, `norm`) in a later
phase; importers validate and quarantine on doubt (flag-first discipline).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# TODO(phase-B): POST /ingest/itrade, /ingest/kcms, /ingest/normalize/propose + /confirm.
# No routes yet.
