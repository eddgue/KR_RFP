"""Awards surface (PLAN §5): select (promote), signoff, approve (freeze).

Present-but-empty this phase. Routes land with the award (`awd`) domain in a later phase.
Promotion, freeze, and send are distinct, permissioned, audited transitions — never implicit
side-effects of a GET or a run (author != approver).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# TODO(phase-E): POST /awards/select (AWARD_SELECT), POST /signoff/approve (SIGNOFF_APPROVE,
# freezes), draft -> SENT (DRAFT_SEND). No routes yet.
