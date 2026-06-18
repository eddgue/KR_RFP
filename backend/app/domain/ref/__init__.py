"""Reference layer (`ref` schema): tenancy + reference dimensions + alias machinery.

Wired end-to-end as the reference implementation pattern (models -> schemas -> repository ->
service). Target tables (PLAN §2): client, commodity, subcommodity, dc, supplier(+alias),
item(+alias), loading_location, fiscal_calendar, zip_centroid, master_data_quarantine. This
phase ships `client` (the tenant) and `commodity` (tenant-scoped reference) as the pattern.
"""

from app.domain.ref.models import Client, Commodity

__all__ = ["Client", "Commodity"]
