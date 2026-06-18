"""Mapped classes for the `norm` schema — STUB (no models yet).

Target tables (PLAN §2): persistent cross-cycle lot store + attribute taxonomy —
`lot`, `attribute_def`, `lot_attribute`, `item_lot_map` (sticky resolution), `source_artifact`,
`normalization_run`. KEEP: sticky resolution + file lineage (sha256 provenance).

Models land in a later phase; this file fixes the layer's home so the schema map is visible
from day one. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

NormBase = SchemaBase("norm")
