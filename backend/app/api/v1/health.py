"""Liveness and readiness endpoints (PLAN §7 observability).

`/health` is liveness — the process is up; no dependencies touched. `/ready` is readiness —
the database is reachable (the store is the product, so readiness gates on it). Both are
unauthenticated so orchestrators can probe them.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter()


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return 200 if the process is alive."""

    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
def ready(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Return 200 if the store is reachable; otherwise the error handlers surface a problem."""

    db.execute(text("SELECT 1"))
    return {"status": "ready"}
