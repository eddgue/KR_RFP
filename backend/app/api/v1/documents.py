"""Documents surface (PLAN §5): generate booking guide / deck / letters.

Present-but-empty this phase. Routes land with document generation (`awd.generated_document`)
in a later phase; documents render from records and stamp + filter by tenant.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# TODO(phase-E): POST /documents (generate draft from records, DOCUMENT_DRAFT). No routes yet.
