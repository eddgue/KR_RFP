"""Importable client-workbook output layer.

Extracted from `demo/run_cycle_demo.py` so any feature (not just the demo) can reuse the
shared presentation formatting (`formatting`), the resolved cycle view (`types.CycleView`),
the synthetic region/transit model (`synthetic`), and the 18-tab scenario-workbook generator
(`scenario_workbook.write_scenario_workbook_xlsx`). The app layer NEVER imports from the demo.
"""

from __future__ import annotations

from app.output.scenario_workbook import write_scenario_workbook_xlsx
from app.output.types import CycleView, Entity, SeededCycle

__all__ = [
    "CycleView",
    "Entity",
    "SeededCycle",
    "write_scenario_workbook_xlsx",
]
