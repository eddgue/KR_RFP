"""Mapped classes for the `bid` schema — STUB (no models yet).

Target tables (PLAN §2): intake, eligibility, capacity, landed cost — `bid_submission`,
`bid` (line), `bid_price`, `bid_index_component`, `grow_origin`, `ship_from_zip`,
`supplier_capability`, `capacity_statement` + `capacity_constraint`, `eligibility_result` +
`gate_result` + `exception`, `landed_cost_result`. KEEP: 5-mode landed cost; 7-gate
eligibility; capacity scopes; demand != capacity CHECK. Tenant-scoped (`client_id`).

Models land in a later phase. No mapped classes are defined yet.
"""

from __future__ import annotations

from app.core.db.base import SchemaBase

BidBase = SchemaBase("bid")
