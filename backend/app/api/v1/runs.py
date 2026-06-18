"""Runs surface (PLAN §5, ENG-PLAN §4): POST run -> run_id; GET scores/scenarios.

Present-but-empty this phase. Routes land with the engine runner (`eng`) in a later phase;
the engine only proposes (decision-support) — reads compare and surface, never assert.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# TODO(phase-D): POST /cycles/{id}/rounds/{r}/run -> {run_id}; GET /runs/{id}/scores,
# /runs/{id}/scenarios, /runs/{id}/scenarios/{code}/awards. No routes yet.
