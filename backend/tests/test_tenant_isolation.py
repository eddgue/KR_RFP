"""Tenant isolation (security/PLAN §1, S7) — integration.

A tenant-scoped repository never returns another tenant's rows. We seed two tenants, write a
commodity under each, and assert each tenant's scoped repository sees only its own. This is the
application-layer half of defence-in-depth; the RLS backstop (Platform & Data M10) is tested
separately once the policy set lands.
"""

from __future__ import annotations

import pytest

from app.domain.ref.models import Commodity
from app.domain.ref.repository import CommodityRepository

pytestmark = pytest.mark.integration


def test_scoped_read_returns_only_own_tenant(db_session, seed_tenants) -> None:
    """A token for tenant A cannot read tenant B's commodity via the scoped repository."""

    tenant_a = seed_tenants["a"]
    tenant_b = seed_tenants["b"]

    db_session.add_all(
        [
            Commodity(client_id=tenant_a, commodity_code="APPLE", commodity_name="Apples (A)"),
            Commodity(client_id=tenant_b, commodity_code="APPLE", commodity_name="Apples (B)"),
            Commodity(client_id=tenant_b, commodity_code="ONION", commodity_name="Onions (B)"),
        ]
    )
    db_session.flush()

    repo_a = CommodityRepository(db_session, tenant_a)
    repo_b = CommodityRepository(db_session, tenant_b)

    a_codes = {c.commodity_code for c in repo_a.list()}
    b_codes = {c.commodity_code for c in repo_b.list()}

    assert a_codes == {"APPLE"}
    assert b_codes == {"APPLE", "ONION"}

    # Cross-tenant lookup by a valid code returns nothing for the wrong tenant.
    assert repo_a.get_by_code("ONION") is None
    # And the APPLE A sees is A's row, not B's.
    a_apple = repo_a.get_by_code("APPLE")
    assert a_apple is not None and a_apple.client_id == tenant_a
