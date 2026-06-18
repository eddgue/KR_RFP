"""Shared route dependencies (PLAN §5): db session, principal, tenant.

Re-exports the canonical dependencies so routers import them from one place. The principal and
tenant are ambient (from the auth context), never from request bodies (PLAN §5).
"""

from __future__ import annotations

from app.core.db.session import get_db
from app.core.security.deps import get_principal, get_tenant, require_permission

__all__ = ["get_db", "get_principal", "get_tenant", "require_permission"]
