"""Engine library purity + determinism (PLAN §3, ENG-PLAN §5) — PURE, no DB.

Two invariants, provable without a database:
  1. Determinism — the same frozen inputs always yield the same result (reproducibility is a
     hard requirement for sealed runs, S2). Run twice, assert equality.
  2. Purity — the engine package imports NO db/http/clock modules. We parse the AST of every
     file under `app/engine` and assert none import sqlalchemy/fastapi/requests/etc., and that
     the stub is tagged `engine_version == "stub"` so no stubbed run masquerades as v3.

This test needs only stdlib + the engine package (pydantic), so it passes from day one.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

from app.engine.interface import BidInput, EngineConfig, EngineInputs, ScenarioCode
from app.engine.stub import STUB_VERSION, DeterministicStubEngine

ENGINE_DIR = Path(__file__).resolve().parents[2] / "app" / "engine"

# Modules the pure library must never touch (db / http / nondeterminism).
FORBIDDEN_IMPORT_PREFIXES = (
    "sqlalchemy",
    "fastapi",
    "starlette",
    "requests",
    "httpx",
    "psycopg",
    "random",
    "app.core.db",
    "app.core.security",
)


def _sample_inputs() -> EngineInputs:
    return EngineInputs(
        cycle_id="cyc-1",
        round_code="R1",
        config=EngineConfig(active_tf_codes=("TF1",)),
        bids=(
            BidInput(
                bid_id="b1",
                supplier_id="s1",
                dc_no="DC1",
                lot_id="L1",
                tf_code="TF1",
                landed_cost_per_case=Decimal("10.00"),
            ),
            BidInput(
                bid_id="b2",
                supplier_id="s2",
                dc_no="DC1",
                lot_id="L1",
                tf_code="TF1",
                landed_cost_per_case=Decimal("8.50"),
            ),
            BidInput(
                bid_id="b3",
                supplier_id="s3",
                dc_no="DC1",
                lot_id="L1",
                tf_code="TF1",
                landed_cost_per_case=Decimal("12.00"),
                eligible=False,
                gate_flags=("premium_too_high",),
            ),
        ),
    )


def test_stub_is_deterministic() -> None:
    """Same inputs -> identical results across independent runs and instances."""

    inputs = _sample_inputs()
    first = DeterministicStubEngine().run(inputs)
    second = DeterministicStubEngine().run(inputs)
    assert first == second


def test_stub_result_shape_and_version() -> None:
    """Result is valid-shaped: tagged 'stub', has scores for every bid, a Scenario A, awards."""

    result = DeterministicStubEngine().run(_sample_inputs())

    assert result.engine_version == STUB_VERSION == "stub"
    assert {s.bid_id for s in result.scores} == {"b1", "b2", "b3"}
    assert any(sc.code is ScenarioCode.A for sc in result.scenarios)

    # Single-winner per cell: the cheapest ELIGIBLE bid (b2 @ 8.50) wins DC1/L1/TF1 fully.
    assert len(result.awards) == 1
    award = result.awards[0]
    assert award.supplier_id == "s2"
    assert award.volume_share == Decimal("1.0")
    assert award.scenario_code is ScenarioCode.A


def test_ineligible_bids_excluded_from_allocation() -> None:
    """Ineligible bids never receive an award (b3 is gated out)."""

    result = DeterministicStubEngine().run(_sample_inputs())
    assert all(a.supplier_id != "s3" for a in result.awards)


def test_engine_package_has_no_db_or_http_imports() -> None:
    """Purity (PLAN §3): no file under app/engine imports db/http/nondeterministic modules."""

    offenders: list[str] = []
    for path in ENGINE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for name in names:
                if any(name == p or name.startswith(f"{p}.") for p in FORBIDDEN_IMPORT_PREFIXES):
                    offenders.append(f"{path.name}: {name}")

    assert not offenders, f"Engine purity violation — forbidden imports: {offenders}"
