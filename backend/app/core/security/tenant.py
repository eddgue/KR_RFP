"""Request-scoped tenant context (security/PLAN §1).

The active tenant is derived from the verified principal's claim — **never** from a request
body, query param, or client-controlled header (the #1 cross-tenant leak vector). Repositories
filter every read by the active tenant and stamp every write with it. The DB-layer backstop
(RLS keyed to a `SET LOCAL app.current_tenant` GUC) is owned by Platform & Data's M10; this
module is the application-layer source of truth for that value.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.security.principal import Principal


@dataclass(frozen=True, slots=True)
class TenantContext:
    """The active tenant for a request. Built from the principal, not from input."""

    tenant_id: uuid.UUID
    tenant_code: str | None = None

    @classmethod
    def from_principal(cls, principal: Principal) -> TenantContext:
        """Derive the tenant context from the verified principal — the only safe source."""

        return cls(tenant_id=principal.tenant_id, tenant_code=principal.tenant_code)

    # The GUC the unit of work sets per transaction so PostgreSQL RLS sees the same tenant.
    GUC_KEY: str = "app.current_tenant"

    @property
    def guc_value(self) -> str:
        return str(self.tenant_id)
