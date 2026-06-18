"""The FROZEN engine interface (PLAN §3, ADR-0006, ENG-PLAN §1, SPIKE_D2_engine).

This contract is fixed now and does NOT change when the D2 spike resolves. Consumers (the
Engine Runner, the API, the tests) bind to these types and to `Engine.run`, not to any
implementation's math. The real v3 scorer/allocator (Option A) will replace the stub *body*
behind this same interface.

PURITY CONTRACT: this module and its implementations import only stdlib + pydantic. NO
sqlalchemy, no fastapi, no http, no `datetime.now`, no `random` (except via injected config).
The Runner owns the store I/O, the clock, and the transaction; the library is a pure function
of frozen inputs -> result so sealed runs are reproducible (PLAN §3, S2).
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


class EngineConfig(BaseModel):
    """Cycle/run configuration: weights, thresholds, split controls (frozen at run time)."""

    model_config = ConfigDict(frozen=True)

    # Five-factor weights (normalized to sum 1.0 by the implementation if they drift).
    weight_price: Decimal = Decimal("0.35")
    weight_coverage: Decimal = Decimal("0.25")
    weight_historical: Decimal = Decimal("0.20")
    weight_zrisk: Decimal = Decimal("0.10")
    weight_continuity: Decimal = Decimal("0.10")

    # Split-allocation controls (permit-not-force).
    max_sup_dc: int = 2  # max suppliers per DC (max_two_per_dc default)
    conc_thresh: Decimal = Decimal("0.40")  # per-supplier concentration cap -> cap_breach_flag

    active_tf_codes: tuple[str, ...] = ()


class BidInput(BaseModel):
    """One eligible, landed-costed bid line fed to the scorer (frozen)."""

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


class EngineInputs(BaseModel):
    """The frozen input bundle for one run (cycle config + scored/eligible bids)."""

    model_config = ConfigDict(frozen=True)

    cycle_id: str
    round_code: str
    config: EngineConfig
    bids: tuple[BidInput, ...] = ()


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
