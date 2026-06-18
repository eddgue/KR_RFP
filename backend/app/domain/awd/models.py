"""Mapped classes for the `awd` schema — STUB (no models yet).

Target tables (PLAN §2): selected awards, freeze/layer, sign-off, outputs — `award`
(multi-row/cell, `frozen_at`), `award_layer` (the only post-freeze write path), `signoff`,
`generated_document`. Mostly net-new (lift v1.4 generators to render from records).
Tenant-scoped (`client_id`). Selection promotes a scenario to an award; the engine never
asserts an award (decision-support; author != approver).

The immutability guard in core/audit attaches to `Award` (frozen rows are write-once) once it
is modelled here.

Models land in a later phase. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

AwdBase = SchemaBase("awd")
