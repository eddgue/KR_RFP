"""Role / permission model and the route-guard factory (security/PLAN §2, ADR-0009).

Permissions are the atomic unit; roles are named bundles. The principal carries roles;
services receive an already-authorized principal and never re-derive authz.

SEPARATION OF DUTIES — author != approver. The roles that *produce* a gate request (Analyst,
Cat Man) deliberately do NOT hold the *approve* permissions (gate approve, freeze, sign-off,
send). Only the Approver role ratifies. This is the separation the governance gates exist to
provide; it is encoded structurally in ROLE_PERMISSIONS below and verified by S8.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from fastapi import Depends

from app.core.errors.taxonomy import AppError, ErrorCode


class Role(StrEnum):
    """The role catalog (security/PLAN §2). Roles are assigned per tenant."""

    ANALYST = "analyst"
    CAT_MAN = "cat_man"
    APPROVER = "approver"
    ADMIN = "admin"
    AUDITOR = "auditor"
    PLATFORM_ADMIN = "platform_admin"  # break-glass cross-tenant; gated + heavily audited.
    SERVICE = "service"  # importers / worker.


class Permission(StrEnum):
    """Atomic permissions mapped to lifecycle transitions (security/PLAN §2 matrix)."""

    # Cycle / kickoff
    CYCLE_EDIT = "cycle:edit"  # create/edit cycle in DRAFT
    INGATE_REQUEST = "ingate:request"  # author the Stage-0 in-gate request
    INGATE_APPROVE = "ingate:approve"  # ratify the Stage-0 in-gate (G12) — Approver only

    # Ingest / run
    FEED_IMPORT = "feed:import"  # import feeds / bids
    RUN_ENGINE = "run:engine"  # execute a sealed analysis run
    SCENARIO_EDIT = "scenario:edit"  # build/edit scenarios

    # Award lifecycle
    AWARD_SELECT = "award:select"  # promote a scenario to award — Cat Man only
    AWARD_FREEZE = "award:freeze"  # freeze award at sign-off — Approver only
    SIGNOFF_APPROVE = "signoff:approve"  # portfolio sign-off — Approver only
    DRAFT_SEND = "draft:send"  # draft -> SENT (G9) — Approver only

    # Documents / read
    DOCUMENT_DRAFT = "document:draft"  # generate draft documents
    AUDIT_READ = "audit:read"  # read audit log / verify chain

    # Administration
    USER_MANAGE = "user:manage"  # manage users <-> roles within the tenant
    CROSS_TENANT = "tenant:cross"  # the gated cross-tenant capability — Platform Admin only


# The named bundles. author != approver is encoded here: producers (Analyst, Cat Man) lack
# every approve/freeze/send permission; only APPROVER holds them.
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ANALYST: frozenset(
        {
            Permission.CYCLE_EDIT,
            Permission.FEED_IMPORT,
            Permission.RUN_ENGINE,
            Permission.SCENARIO_EDIT,
            Permission.DOCUMENT_DRAFT,
            Permission.AUDIT_READ,
        }
    ),
    Role.CAT_MAN: frozenset(
        {
            Permission.CYCLE_EDIT,
            Permission.INGATE_REQUEST,
            Permission.FEED_IMPORT,
            Permission.RUN_ENGINE,
            Permission.SCENARIO_EDIT,
            Permission.AWARD_SELECT,
            Permission.DOCUMENT_DRAFT,
            Permission.AUDIT_READ,
        }
    ),
    Role.APPROVER: frozenset(
        {
            Permission.INGATE_APPROVE,
            Permission.AWARD_FREEZE,
            Permission.SIGNOFF_APPROVE,
            Permission.DRAFT_SEND,
            Permission.AUDIT_READ,
        }
    ),
    Role.ADMIN: frozenset(
        {
            Permission.USER_MANAGE,
            Permission.AUDIT_READ,
        }
    ),
    Role.AUDITOR: frozenset(
        {
            Permission.AUDIT_READ,
        }
    ),
    Role.PLATFORM_ADMIN: frozenset(
        {
            Permission.CROSS_TENANT,
            Permission.AUDIT_READ,
        }
    ),
    Role.SERVICE: frozenset(
        {
            Permission.FEED_IMPORT,
            Permission.RUN_ENGINE,
        }
    ),
}


def permissions_for_roles(roles: Iterable[Role]) -> frozenset[Permission]:
    """Flatten a set of roles into their union of permissions."""

    granted: set[Permission] = set()
    for role in roles:
        granted |= ROLE_PERMISSIONS.get(role, frozenset())
    return frozenset(granted)


def require_permission(permission: Permission):  # type: ignore[no-untyped-def]
    """Build a FastAPI dependency that denies callers lacking `permission`.

    The guard reads the principal from request context (see core/security/deps) and denies
    with the uniform problem envelope and no information leak about other tenants. Imported
    lazily to avoid a circular import between deps and rbac.
    """

    from app.core.security.deps import get_principal
    from app.core.security.principal import Principal

    def _guard(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_permission(permission):
            raise AppError(
                code=ErrorCode.FORBIDDEN,
                message="The caller lacks the required permission for this action.",
                status_code=403,
            )
        return principal

    return _guard
