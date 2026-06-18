"""Pydantic request/response models for the `ref` layer.

Tenant is ambient (from context), so it never appears on a request body (PLAN §5). The
create schemas carry no `client_id`; the service stamps it from the tenant context.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.domain.ref.models import ClientStatus


class CommodityCreate(BaseModel):
    """Create a commodity. No `client_id` — it is stamped from the tenant context."""

    code: str = Field(max_length=32)
    name: str = Field(max_length=200)


class CommodityRead(BaseModel):
    """A commodity as returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    code: str
    name: str


class ClientRead(BaseModel):
    """A tenant as returned to clients (admin surfaces)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    status: ClientStatus
