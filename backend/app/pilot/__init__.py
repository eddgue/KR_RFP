"""The pilot core (`app.pilot`) — the per-RFP run-vault manager + setup template/ingest + status.

This package is the PILOT CORE (PILOT_SYSTEM_DESIGN §8 build-order step 3): it stamps out a
git-versioned, structurally-identical run folder per RFP (`vault.py`), generates the blank
Setup/Kickoff workbook the sponsor fills (`setup_template.py`), ingests the filled copy into the
governed Postgres store creating the cycle + scope (`setup_ingest.py`), renders the kanban manifest
(`status.py`), and ties it together behind a small service (`service.py`). The later loop steps
(bid templates, round runs, award freeze, post-award adjustments, flexible ingest, history) are
PART B — left as clearly-marked NotImplementedError stubs on the service.
"""

from __future__ import annotations

from app.pilot.service import PilotService
from app.pilot.vault import RunPaths

__all__ = ["PilotService", "RunPaths"]
