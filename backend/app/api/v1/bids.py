"""Bids surface (PLAN §5): bid import + list at one grain.

Present-but-empty this phase. Routes land with the bid (`bid`) domain in a later phase.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# TODO(phase-B): POST bid import, GET bids at (cycle, round, grain). No routes yet.
