"""Clean-room boundary guard (ADR-0001, security/PLAN §5, S14) — PURE, no DB.

`backend/` must NEVER import from `reference/` (the input-only quarantine). This test walks
every Python file under `backend/app` and `backend/alembic`, parses the AST, and fails if any
`import reference` / `from reference...` / `import reference.x` appears. It needs only the
standard library — no database, no app import — so it runs in the lint stage of CI and passes
from day one.
"""

from __future__ import annotations

import ast
from pathlib import Path

# tests/ -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [BACKEND_ROOT / "app", BACKEND_ROOT / "alembic"]
FORBIDDEN_TOP = "reference"


def _python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.exists():
            files.extend(p for p in root.rglob("*.py"))
    return files


def _imports_reference(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == FORBIDDEN_TOP or alias.name.startswith(f"{FORBIDDEN_TOP}."):
                    return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # node.level > 0 is a relative import (e.g. `from . import x`); never `reference`.
            if node.level == 0 and (
                module == FORBIDDEN_TOP or module.startswith(f"{FORBIDDEN_TOP}.")
            ):
                return True
    return False


def test_backend_never_imports_reference() -> None:
    """No file under backend/app or backend/alembic may import the `reference` package."""

    offenders: list[str] = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _imports_reference(tree):
            offenders.append(str(path.relative_to(BACKEND_ROOT)))

    assert not offenders, (
        "Clean-room violation (ADR-0001): backend/ must never import reference/. "
        f"Offending files: {offenders}"
    )


def test_scan_actually_found_files() -> None:
    """Guard the guard: the walk must find files, or the test is silently vacuous."""

    assert _python_files(), "Clean-room scan found no Python files — check SCAN_ROOTS."
