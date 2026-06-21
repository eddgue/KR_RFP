"""Kroger fiscal calendar package — the authoritative 13-period reference for the flat-13 model.

See `app.fiscal.calendar` for the period <-> date lookups, the timeframe presets (the per-cycle
period->timeframe grouping), and the intake fan-out (`expand_to_periods`). The period spans come
from the sponsor's conversion table (`data/kroger_fiscal_periods.csv`); nothing here is derived by a
date rule, so a future calendar quirk is a data update, not a code change (INTAKE_TEMPLATE_DESIGN
§1a).
"""

from __future__ import annotations
