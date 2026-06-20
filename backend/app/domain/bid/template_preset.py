"""Bid-template PRESETS — the buyer-side "compose the template from the column superset" core.

EXP-INTAKE-TEMPLATE §1 (first increment). The bid column SET is a superset that is always
available (`template_schema.PRICE_COLUMNS`); a given cycle uses only the columns it needs. A
`BidTemplatePreset` is a named, reusable selection of the supplier-entry columns a template carries
— so a buyer composes a leaner template per cycle (e.g. "All-In only" vs "full cost components")
and the generator emits exactly those columns. The system-owned scope columns (keys D21 + display
names D23) are ALWAYS included; a preset only chooses the supplier-entry columns.

Because the ingester reads by header NAME and tolerates absent optional columns (`.get()`), a
preset-built template round-trips through `ingest_template` for the columns it carries — the preset
IS the saved mapping (no re-inference; canonical headers). Renaming columns + visual grouping + a
persisted custom-preset store + the walk-through wizard are later increments; this one nails
selection + the round-trip.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.bid.template_schema import (
    PRICE_COLUMNS,
    SCOPE_COLUMNS,
    BidColumn,
)

# A bid needs at least one usable PRICE and one VOLUME to be complete + scoreable — so every preset
# must carry one of each (validated below). These also drive the readiness traffic light.
_USABLE_PRICE = (BidColumn.ALL_IN, BidColumn.FOB)
_VOLUME = (BidColumn.WEEKLY_VOL_OFFERED, BidColumn.TOTAL_VOL_OFFERED)


@dataclass(frozen=True)
class BidTemplatePreset:
    """A named selection of supplier-entry columns a cycle's bid template carries (a subset of the
    `PRICE_COLUMNS` superset). Scope columns (keys + names) are always added by the generator."""

    name: str
    description: str
    entry_columns: tuple[BidColumn, ...]

    def __post_init__(self) -> None:
        extra = [c for c in self.entry_columns if c not in PRICE_COLUMNS]
        if extra:
            raise ValueError(
                f"preset {self.name!r}: columns not in the entry superset: "
                + ", ".join(c.value for c in extra)
            )
        if len(set(self.entry_columns)) != len(self.entry_columns):
            raise ValueError(f"preset {self.name!r}: duplicate entry columns")
        if not any(c in self.entry_columns for c in _USABLE_PRICE):
            raise ValueError(
                f"preset {self.name!r}: must include a usable price (All-In or FOB)"
            )
        if not any(c in self.entry_columns for c in _VOLUME):
            raise ValueError(
                f"preset {self.name!r}: must include a volume (Weekly or Total)"
            )

    def bid_headers(self) -> tuple[str, ...]:
        """The full ordered header list for this preset's Bids sheet: scope first, then entries."""

        return tuple(c.value for c in (*SCOPE_COLUMNS, *self.entry_columns))


# --- Built-in presets (the starting menu; a custom-preset store is a later increment) ------------
FULL_PRESET = BidTemplatePreset(
    name="full",
    description="Every entry column — All-In + components + transit + volume + investment.",
    entry_columns=PRICE_COLUMNS,
)
ALL_IN_PRESET = BidTemplatePreset(
    name="all_in_simple",
    description="Simplest: a single All-In $/case + volume (+ transit, comments).",
    entry_columns=(
        BidColumn.ALL_IN,
        BidColumn.TRANSIT_DAYS,
        BidColumn.PRICING_COMMENTS,
        BidColumn.WEEKLY_VOL_OFFERED,
        BidColumn.TOTAL_VOL_OFFERED,
        BidColumn.INVESTED_R1,
    ),
)
COMPONENTS_PRESET = BidTemplatePreset(
    name="components",
    description="Cost stack: FOB + Delivery + VegCool − Lot Discount, + transit + volume.",
    entry_columns=(
        BidColumn.FOB,
        BidColumn.DELIVERY_SURCHARGE,
        BidColumn.VEGCOOL_SURCHARGE,
        BidColumn.LOT_DISCOUNT,
        BidColumn.TRANSIT_DAYS,
        BidColumn.PRICING_COMMENTS,
        BidColumn.WEEKLY_VOL_OFFERED,
        BidColumn.TOTAL_VOL_OFFERED,
        BidColumn.INVESTED_R1,
    ),
)

PRESETS: dict[str, BidTemplatePreset] = {
    p.name: p for p in (FULL_PRESET, ALL_IN_PRESET, COMPONENTS_PRESET)
}


def get_preset(name: str | None) -> BidTemplatePreset:
    """Resolve a preset by name; None or unknown falls back to the full superset preset."""

    if not name:
        return FULL_PRESET
    return PRESETS.get(name.strip().lower(), FULL_PRESET)
