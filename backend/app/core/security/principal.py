"""The verified principal (security/PLAN §2).

AuthN is delegated to an external IdP (DEP-4). An edge adapter validates the token
(signature/issuer/audience/expiry) and extracts the principal; the backend trusts it and
never reimplements authN. The principal carries the subject, the tenant, and the roles
assigned *within that tenant* — domain services receive an already-authorized principal and
never re-derive authz.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from functools import cached_property

from app.core.security.rbac import Permission, Role, permissions_for_roles


@dataclass(frozen=True, slots=True)
class Principal:
    """An authenticated, tenant-scoped caller. Immutable for the request lifetime."""

    subject: str
    tenant_id: uuid.UUID
    roles: frozenset[Role]
    email: str | None = None
    source: str = "api"  # api | worker | import — recorded on audit events.

    # Internal: tenant_code is convenience metadata for logs/correlation, not authz.
    tenant_code: str | None = field(default=None)

    @cached_property
    def permissions(self) -> frozenset[Permission]:
        """The flattened permission set granted by this principal's roles."""

        return permissions_for_roles(self.roles)

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    @property
    def actor(self) -> str:
        """Stable actor string for audit rows: subject + sorted role codes."""

        role_codes = ",".join(sorted(r.value for r in self.roles))
        return f"{self.subject}[{role_codes}]"
