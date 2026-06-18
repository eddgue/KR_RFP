"""Reference-layer services (add + flush, never commit — PLAN §7).

The service stamps `client_id` from the tenant context (never from the request body), emits a
domain event for the audit writer, and stages the row. The unit of work owns the commit, so
the change and its audit event land in the same transaction (security/PLAN §3).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.audit.events import DomainEvent, EventType
from app.core.audit.writer import AuditWriter
from app.core.errors.taxonomy import AppError, ErrorCode
from app.core.security.principal import Principal
from app.core.security.tenant import TenantContext
from app.domain.ref.models import Commodity
from app.domain.ref.repository import CommodityRepository
from app.domain.ref.schemas import CommodityCreate


class CommodityService:
    """Create/read commodities, tenant-scoped, with audit on mutation."""

    def __init__(self, session: Session, tenant: TenantContext, principal: Principal) -> None:
        self._session = session
        self._tenant = tenant
        self._principal = principal
        self._repo = CommodityRepository(session, tenant.tenant_id)
        self._audit = AuditWriter(session)

    def create(self, data: CommodityCreate) -> Commodity:
        """Stage a new commodity for the active tenant and emit a CREATED event.

        Stamps `client_id` from context, refuses a duplicate code, adds + flushes (no commit).
        """

        if self._repo.get_by_code(data.commodity_code) is not None:
            raise AppError(
                code=ErrorCode.CONFLICT,
                message="A commodity with this code already exists for the tenant.",
                status_code=409,
            )

        commodity = Commodity(
            client_id=self._tenant.tenant_id,
            commodity_code=data.commodity_code,
            commodity_name=data.commodity_name,
            abbreviation=data.abbreviation,
        )
        self._repo.add(commodity)  # add + flush -> commodity.id populated

        self._audit.append(
            DomainEvent(
                event_type=EventType.CREATED,
                client_id=self._tenant.tenant_id,
                entity_type="ref.commodity",
                entity_id=commodity.id,
                actor=self._principal.actor,
                source=self._principal.source,
                before=None,
                after={"code": commodity.commodity_code, "name": commodity.commodity_name},
            )
        )
        return commodity
