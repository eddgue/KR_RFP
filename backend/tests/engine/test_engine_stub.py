"""Engine library purity + version-tag guards (PLAN §3, ENG-PLAN §5) — PURE, no DB.

Two invariants, provable without a database:
  1. Purity — every file under `app/engine` imports NO db/http/clock/nondeterminism module, and
     NEVER imports from the `reference/` quarantine (the clean-room boundary, ADR-0001). We parse
     each file's AST and assert it.
  2. Version tagging — the stub tags itself `"stub"` and the real engine tags itself
     `"v3-cleanroom"`, so no stubbed run is ever mistaken for a validated v3 run and vice versa.

This test needs only stdlib + the engine package (pydantic), so it passes standalone.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

from app.engine.interface import BidInput, EngineConfig, EngineInputs, ScenarioCode
from app.engine.stub import STUB_VERSION, DeterministicStubEngine
from app.engine.v3 import V3_VERSION, V3Engine

ENGINE_DIR = Path(__file__).resolve().parents[2] / "app" / "engine"

# Modules the pure library must never touch (db / http / nondeterminism) + the quarantine.
FORBIDDEN_IMPORT_PREFIXES = (
    "sqlalchemy",
    "fastapi",
    "starlette",
    "requests",
    "httpx",
    "psycopg",
    "random",
    "reference",  # clean-room boundary (ADR-0001): engine must never import reference/
    "app.core.db",
    "app.core.security",
)


def _sample_inputs() -> EngineInputs:
    return EngineInputs(
        cycle_id="cyc-1",
        round_code="R1",
        config=EngineConfig(active_tf_codes=("TF1",), final_round_code="R1"),
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


def test_stub_is_deterministic_and_tagged() -> None:
    """The placeholder is deterministic and tagged 'stub' (never mistaken for v3)."""

    inputs = _sample_inputs()
    first = DeterministicStubEngine().run(inputs)
    second = DeterministicStubEngine().run(inputs)
    assert first == second
    assert first.engine_version == STUB_VERSION == "stub"
    assert {s.bid_id for s in first.scores} == {"b1", "b2", "b3"}
    assert any(sc.code is ScenarioCode.A for sc in first.scenarios)


def test_real_engine_tagged_distinctly_from_stub() -> None:
    """The real engine tags itself 'v3-cleanroom' — distinct from the stub tag."""

    result = V3Engine().run(_sample_inputs())
    assert result.engine_version == V3_VERSION == "v3-cleanroom"
    assert result.engine_version != STUB_VERSION


def test_engine_package_is_pure_and_clean_room() -> None:
    """Purity (PLAN §3) + clean-room (ADR-0001): no forbidden or reference imports anywhere."""

    offenders: list[str] = []
    scanned = 0
    for path in ENGINE_DIR.rglob("*.py"):
        scanned += 1
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

    assert scanned > 0, "purity scan found no engine files — check ENGINE_DIR"
    assert not offenders, f"Engine purity/clean-room violation — forbidden imports: {offenders}"
