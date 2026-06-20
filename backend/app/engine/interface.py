"""The FROZEN engine interface (PLAN §3, ADR-0006, ENG-PLAN §1, SPIKE_D2_engine).

This contract is fixed now and does NOT change when the D2 spike resolves. Consumers (the
Engine Runner, the API, the tests) bind to these types and to `Engine.run`, not to any
implementation's math. The real v3 scorer/allocator (Option A) replaces the stub *body*
behind this same interface.

The `run(inputs) -> result` SIGNATURE is stable. The IO dataclasses below were fleshed out (in
a backward-compatible way — every added field carries a default) to carry the *real* run: bid
price components (All-In + fallback parts), volume requirement/offered, the incumbent baseline,
the strategy config (weights/preset/thresholds/constraints/active rounds+TFs/lenses), and the
full output (per-bid scores+gate flags, scenarios A-G, split awards with
volume_share/is_fallback/cap_breach_flag). The frozen `BidInput.eligible`/`gate_flags`/
`landed_cost_per_case` fields are retained so the as-built eligibility/landed layers still feed
the scorer (ADR-0006).

PURITY CONTRACT: this module and its implementations import only stdlib + pydantic. NO
sqlalchemy, no fastapi, no http, no `datetime.now`, no `random` (except via injected config).
The Runner owns the store I/O, the clock, and the transaction; the library is a pure function
of frozen inputs -> result so sealed runs are reproducible (PLAN §3, S2).

CLEAN-ROOM (ADR-0001): the logic behind this interface is re-implemented from our own spec
`project/squads/engine-domain/V3_ENGINE_LOGIC.md`; the quarantined `rfp_analysis_engine_v3.py`
is never read, imported, or copied, and `backend/` never imports from `reference/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ScenarioCode(StrEnum):
    """The lenses A-G (ENG-PLAN §2). A = lowest-cost benchmark; B = risk-adjusted default."""

    A = "A"  # lowest-cost reference (benchmark, never auto-applied)
    B = "B"  # risk-adjusted recommendation (the rec_score default)
    C = "C"  # incumbent defense
    D = "D"  # max-N per DC
    E = "E"  # exclusion
    F = "F"  # custom override
    G = "G"  # preferred supplier


class WeightPreset(StrEnum):
    """Named scoring presets (ADR-0016). CUSTOM = use the explicit weights as given."""

    BALANCED = "balanced"
    PRICE_FOCUS = "price_focus"
    COVERAGE_FOCUS = "coverage_focus"
    RISK_AVERSE = "risk_averse"
    CUSTOM = "custom"


# Canonical scoring weights per named preset (ADR-0016). The five factors are
# price · coverage · historical · zrisk · continuity; each vector sums to 1.0 (the scorer
# renormalizes anyway if a vector drifts >1%). CUSTOM is intentionally ABSENT — it means "use the
# explicit weights as given" (no remap). Continuity stays materially weighted in every preset
# (incumbency carries value in a repeated-game category); PRICE_FOCUS leans hardest on cost,
# RISK_AVERSE hardest on stability (historical + zrisk + continuity). BALANCED is the pilot default.
PRESET_WEIGHTS: dict[WeightPreset, dict[str, Decimal]] = {
    WeightPreset.BALANCED: {
        "weight_price": Decimal("0.31"),
        "weight_coverage": Decimal("0.22"),
        "weight_historical": Decimal("0.18"),
        "weight_zrisk": Decimal("0.09"),
        "weight_continuity": Decimal("0.20"),
    },
    WeightPreset.PRICE_FOCUS: {
        "weight_price": Decimal("0.50"),
        "weight_coverage": Decimal("0.18"),
        "weight_historical": Decimal("0.12"),
        "weight_zrisk": Decimal("0.06"),
        "weight_continuity": Decimal("0.14"),
    },
    WeightPreset.COVERAGE_FOCUS: {
        "weight_price": Decimal("0.24"),
        "weight_coverage": Decimal("0.38"),
        "weight_historical": Decimal("0.12"),
        "weight_zrisk": Decimal("0.08"),
        "weight_continuity": Decimal("0.18"),
    },
    WeightPreset.RISK_AVERSE: {
        "weight_price": Decimal("0.20"),
        "weight_coverage": Decimal("0.20"),
        "weight_historical": Decimal("0.20"),
        "weight_zrisk": Decimal("0.18"),
        "weight_continuity": Decimal("0.22"),
    },
}


class ExclusionRule(BaseModel):
    """Scenario E input: drop a supplier (optionally scoped to a cell). Blank = wildcard."""

    model_config = ConfigDict(frozen=True)

    supplier_id: str
    dc_no: str | None = None
    lot_id: str | None = None
    tf_code: str | None = None


class CustomOverrideRule(BaseModel):
    """Scenario F input: force a named supplier's award at a specific cell."""

    model_config = ConfigDict(frozen=True)

    dc_no: str
    lot_id: str
    tf_code: str
    supplier_id: str


class PreferredRule(BaseModel):
    """Scenario G input: prefer a supplier on a lot (DC/TF optional wildcards)."""

    model_config = ConfigDict(frozen=True)

    lot_id: str
    supplier_id: str
    dc_no: str | None = None
    tf_code: str | None = None


class EngineConfig(BaseModel):
    """Cycle/run configuration: weights, preset, thresholds, split controls, lenses, rounds.

    Strategy-agnostic (ADR-0016): EVERY knob the engine reads lives here. Nothing is hardcoded
    in the implementation. Frozen at run time so a sealed run reproduces under its exact config.
    """

    model_config = ConfigDict(frozen=True)

    # --- Scoring: five-factor weights (normalized to sum 1.0 by the impl if they drift >1%). ---
    preset: WeightPreset = WeightPreset.CUSTOM
    weight_price: Decimal = Decimal("0.35")
    weight_coverage: Decimal = Decimal("0.25")
    weight_historical: Decimal = Decimal("0.20")
    weight_zrisk: Decimal = Decimal("0.10")
    weight_continuity: Decimal = Decimal("0.10")

    # --- Premium bands (price score) + eligibility/RecType thresholds (all config-driven). ---
    premium_band_comparable: Decimal = Decimal("0.03")  # <=3% -> 100; RecType "Comparable"
    premium_band_defensible: Decimal = Decimal("0.07")  # <=7% -> 80;  RecType "Defensible"
    premium_band_max: Decimal = Decimal("0.12")  # <=12% -> 50; >12% -> 20
    global_premium_threshold: Decimal = Decimal("0.12")  # default eligibility ceiling
    coverage_floor: Decimal = Decimal("0.80")  # eligibility coverage floor

    # --- Split-allocation controls (permit-not-force). ---
    max_sup_dc: int = 2  # max suppliers per DC (max_two_per_dc default)
    single_supplier_per_lot: bool = True  # one award per (dc, lot, tf) cell outside D
    conc_thresh: Decimal = Decimal("0.40")  # category concentration flag

    # --- Active timeframes / rounds (final = last active; prior = first if >1, else None). ---
    active_tf_codes: tuple[str, ...] = ()
    final_round_code: str | None = None
    prior_round_code: str | None = None  # None for a single-round (R1-only) cycle -> guarded

    # --- Lenses to run (default: all A-G). ---
    lenses: tuple[ScenarioCode, ...] = (
        ScenarioCode.A,
        ScenarioCode.B,
        ScenarioCode.C,
        ScenarioCode.D,
        ScenarioCode.E,
        ScenarioCode.F,
        ScenarioCode.G,
    )

    # --- Scenario E/F/G rule inputs (config-driven). ---
    exclusions: tuple[ExclusionRule, ...] = ()
    custom_overrides: tuple[CustomOverrideRule, ...] = ()
    preferred_rules: tuple[PreferredRule, ...] = ()

    # --- Per-lot premium overrides (lot_id -> effective threshold); else global. ---
    lot_premium_thresholds: tuple[tuple[str, Decimal], ...] = ()


class BidComponents(BaseModel):
    """The All-In + fallback price parts for ONE bid line (cost construction, §7).

    Price = all_in if present, else FOB + delivery + vegcool - lot_discount - all_lot_discount.
    The discount fields are applied ONLY on the fallback branch (the double-subtract guard):
    when `all_in` is present it is taken verbatim (assumed already net of discounts).
    """

    model_config = ConfigDict(frozen=True)

    all_in: Decimal | None = None
    fob: Decimal | None = None
    delivery_surcharge: Decimal = Decimal("0")
    vegcool_surcharge: Decimal = Decimal("0")
    lot_discount: Decimal = Decimal("0")
    all_lot_discount: Decimal = Decimal("0")


class BidInput(BaseModel):
    """One landed-costed bid line fed to the scorer (frozen).

    `landed_cost_per_case` is the as-built landed-cost layer's output and the *default* Price.
    If `components` is supplied the engine re-derives Price via §7 (All-In primary + fallback)
    and the double-subtract guard; otherwise it uses `landed_cost_per_case` directly.
    """

    model_config = ConfigDict(frozen=True)

    bid_id: str
    supplier_id: str
    dc_no: str
    lot_id: str
    tf_code: str
    landed_cost_per_case: Decimal
    eligible: bool = True
    gate_flags: tuple[str, ...] = ()
    is_incumbent: bool = False

    # --- Real-run extras (all defaulted; the stub path ignores them). ---
    components: BidComponents | None = None
    weekly_vol_offered: Decimal | None = None
    total_vol_offered: Decimal | None = None
    is_as_needed: bool = False  # As-Needed -> coverage score 70, skips the coverage gate


class VolumeRequirement(BaseModel):
    """Demand for one (dc, lot, tf) cell: drives the coverage ratio + Scenario A spend."""

    model_config = ConfigDict(frozen=True)

    dc_no: str
    lot_id: str
    tf_code: str
    weekly_volume: Decimal | None = None
    total_volume: Decimal | None = None
    weeks: int | None = None


class IncumbentBaseline(BaseModel):
    """Incumbent identity + routing (delivered all-in) baseline per (dc, lot).

    `routing_cost_per_case` is the historical delivered all-in baseline (DeltaVsHistPct, §2.3);
    None -> no baseline -> historical score 50.
    """

    model_config = ConfigDict(frozen=True)

    dc_no: str
    lot_id: str
    supplier_id: str
    routing_cost_per_case: Decimal | None = None


class EngineInputs(BaseModel):
    """The frozen input bundle for one run (cycle config + bids + demand + baselines)."""

    model_config = ConfigDict(frozen=True)

    cycle_id: str
    round_code: str
    config: EngineConfig
    bids: tuple[BidInput, ...] = ()
    volumes: tuple[VolumeRequirement, ...] = ()
    incumbents: tuple[IncumbentBaseline, ...] = ()


class BidScore(BaseModel):
    """Per-bid output: the five banded factors -> rec_score, plus eligibility/gate flags."""

    model_config = ConfigDict(frozen=True)

    bid_id: str
    price_score: Decimal
    coverage_score: Decimal
    hist_score: Decimal
    zrisk_score: Decimal
    continuity_score: Decimal
    rec_score: Decimal
    eligible: bool
    gate_flags: tuple[str, ...] = ()


class ScenarioAward(BaseModel):
    """One split award row: a supplier's share of a (scenario, dc, lot, tf) cell."""

    model_config = ConfigDict(frozen=True)

    scenario_code: ScenarioCode
    dc_no: str
    lot_id: str
    tf_code: str
    supplier_id: str
    volume_share: Decimal  # 0..1; sums to 1.0 per cell
    awarded_price: Decimal
    is_recommended: bool = False
    is_fallback: bool = False
    cap_breach_flag: bool = False
    rec_type: str | None = None  # §5 B reason label (Lowest cost / Coverage advantage / …); B-only


class Scenario(BaseModel):
    """A lens header (code + label/description)."""

    model_config = ConfigDict(frozen=True)

    code: ScenarioCode
    label: str
    description: str = ""


class EngineResult(BaseModel):
    """The frozen result bundle: scores, scenarios A-G, and split award rows."""

    model_config = ConfigDict(frozen=True)

    engine_version: str = Field(description="Tags the run; the stub tags itself 'stub'.")
    scores: tuple[BidScore, ...] = ()
    scenarios: tuple[Scenario, ...] = ()
    awards: tuple[ScenarioAward, ...] = ()


class Engine(ABC):
    """The single, frozen entry point. Implementations are pure (PLAN §3)."""

    #: Implementations override this; the Runner records it on `eng.analysis_run`.
    version: str = "abstract"

    @abstractmethod
    def run(self, inputs: EngineInputs) -> EngineResult:
        """Compute scores, scenarios, and split awards from a frozen input bundle.

        Pure: no I/O, no clock, no randomness except via `inputs.config`. The same inputs
        must always yield the same result (reproducibility is a hard requirement for sealed
        runs and the real-data pilot, PLAN §3).
        """

        raise NotImplementedError
