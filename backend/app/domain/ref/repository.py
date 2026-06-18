"""Tenant-scoped repository for the `ref` layer (security/PLAN §1).

Every read for a tenant-scoped entity injects `WHERE client_id = :ctx_tenant`; there is no
un-scoped read path to governed data. The tenant comes from the request context, never from
the caller. This is the application-layer half of defence-in-depth; PostgreSQL RLS is the
DB-layer backstop (Platform & Data M10).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ref.models import Client, Commodity


class CommodityRepository:
    """Tenant-scoped queries over `ref.commodity`."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def list(self) -> Sequence[Commodity]:
        """All commodities for the active tenant — scoped, never cross-tenant."""

        stmt = (
            select(Commodity)
            .where(Commodity.client_id == self._tenant_id)
            .order_by(Commodity.code)
        )
        return self._session.execute(stmt).scalars().all()

    def get_by_code(self, code: str) -> Commodity | None:
        """One commodity by code within the active tenant (scoped)."""

        stmt = select(Commodity).where(
            Commodity.client_id == self._tenant_id,
            Commodity.code == code,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def add(self, commodity: Commodity) -> None:
        """Stage a new commodity. add + flush only — the unit of work commits (PLAN §7)."""

        self._session.add(commodity)
        self._session.flush()


class ClientRepository:
    """Queries over `ref.client` (the tenant registry; not itself tenant-scoped)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, tenant_id: uuid.UUID) -> Client | None:
        return self._session.get(Client, tenant_id)

    def get_by_code(self, code: str) -> Client | None:
        stmt = select(Client).where(Client.code == code)
        return self._session.execute(stmt).scalar_one_or_none()
