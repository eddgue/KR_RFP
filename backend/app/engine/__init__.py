"""The pure decision-support engine library (PLAN §3). NO db/http/clock imports.

`V3Engine` is the real, full-fidelity decision-support brain (ADR-0006), a clean-room
re-implementation of v3 steps 1-7 from our own spec (ADR-0001). `DeterministicStubEngine`
remains as the tagged placeholder for contexts that have not yet wired the real feeds.
"""

from app.engine.interface import Engine, EngineInputs, EngineResult
from app.engine.stub import DeterministicStubEngine
from app.engine.v3 import V3Engine

__all__ = ["Engine", "EngineInputs", "EngineResult", "DeterministicStubEngine", "V3Engine"]
