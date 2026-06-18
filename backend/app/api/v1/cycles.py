"""Cycles surface (PLAN §5): /cycles, timeframes, rounds, full cycle view ("open last cycle").

Present-but-empty this phase. Routes land with the cycle (`cyc`) domain in a later phase;
every route will be permission-guarded and tenant-scoped at the repository boundary.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# TODO(phase-C): GET /cycles, POST /cycles (DRAFT), GET /cycles/{id} (full view),
# /cycles/{id}/rounds, the Stage-0 in-gate approval (G12). No routes yet.
