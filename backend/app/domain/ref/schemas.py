"""Pydantic request/response models for the `ref` layer.

Tenant is ambient (from context), so it never appears on a request body (PLAN §5). The
create schemas carry no `client_id`; the service stamps it from the tenant context. Field
names mirror the `ref` mapped classes (db/baseline/schema.sql).
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CommodityCreate(BaseModel):
    """Create a commodity. No `client_id` — it is stamped from the tenant context."""

    commodity_code: str = Field(max_length=40)
    commodity_name: str = Field(max_length=120)
    abbreviation: str | None = Field(default=None, max_length=20)


class CommodityRead(BaseModel):
    """A commodity as returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID | None
    commodity_code: str
    commodity_name: str
    active_flag: bool


class ClientRead(BaseModel):
    """A tenant as returned to clients (admin surfaces)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_code: str
    client_name: str
    is_active: bool
