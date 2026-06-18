"""The pure decision-support engine library (PLAN §3). NO db/http/clock imports."""

from app.engine.interface import Engine, EngineInputs, EngineResult
from app.engine.stub import DeterministicStubEngine

__all__ = ["Engine", "EngineInputs", "EngineResult", "DeterministicStubEngine"]
