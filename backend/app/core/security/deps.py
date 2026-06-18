"""FastAPI security dependencies: get_principal, get_tenant, require_permission.

The principal is established by the tenant-context middleware (app/main.py) from the verified
token and stashed on ``request.state``. These dependencies surface it to routes. Until the IdP
adapter lands (DEP-4), the middleware sets a development principal; production rejects any
request without a verified principal.
"""

from __future__ import annotations

from fastapi import Request

from app.core.errors.taxonomy import AppError, ErrorCode
from app.core.security.principal import Principal
from app.core.security.rbac import Permission, require_permission
from app.core.security.tenant import TenantContext

__all__ = ["get_principal", "get_tenant", "require_permission", "Permission"]


def get_principal(request: Request) -> Principal:
    """Return the verified principal for the request, or deny.

    The principal is never taken from the request body — only from the context the auth edge
    established (security/PLAN §2).
    """

    principal: Principal | None = getattr(request.state, "principal", None)
    if principal is None:
        raise AppError(
            code=ErrorCode.UNAUTHENTICATED,
            message="No verified principal on the request.",
            status_code=401,
        )
    return principal


def get_tenant(request: Request) -> TenantContext:
    """Return the active tenant context, derived from the verified principal only."""

    return TenantContext.from_principal(get_principal(request))
