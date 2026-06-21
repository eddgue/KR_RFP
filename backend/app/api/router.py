"""Mounts the versioned sub-routers (PLAN §5).

`health` is live this phase; the lifecycle routers (`cycles`, `bids`, `runs`, `awards`,
`documents`, `ingest`) are present-but-empty — they define an `APIRouter` with a TODO and no
real routes yet, so the layer map is visible from day one.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, awards, bids, cycles, documents, health, ingest, runs

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cycles.router, prefix="/cycles", tags=["cycles"])
api_router.include_router(bids.router, prefix="/bids", tags=["bids"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(awards.router, prefix="/awards", tags=["awards"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
