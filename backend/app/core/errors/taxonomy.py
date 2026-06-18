"""Machine error codes + the problem-shaped error envelope (PLAN §5, ADR-0007).

A single problem-detail envelope with a stable machine code surfaces every failure uniformly,
so the importer's "quarantine with a reason" and the engine's "blocked, never guessed" look
the same to clients. Envelopes carry NO C3 commercial values and NO cross-tenant identifiers
(security/PLAN §5).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    """Stable machine codes. Clients branch on these, never on the message text."""

    # AuthN / AuthZ
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"

    # Tenancy
    TENANT_MISMATCH = "tenant_mismatch"

    # Validation / request shape
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"

    # Governance / immutability
    IMMUTABLE = "immutable"  # mutation of a sealed run / frozen award was refused
    GATE_REQUIRED = "gate_required"  # a governance gate (in-gate / sign-off) is unmet

    # Ingest
    QUARANTINED = "quarantined"  # input rejected to the quarantine queue with a reason

    # Catch-all
    INTERNAL = "internal_error"


class ProblemDetail(BaseModel):
    """RFC-7807-shaped error body returned for every failure."""

    code: ErrorCode = Field(description="Stable machine-readable error code.")
    title: str = Field(description="Short, human-readable summary.")
    detail: str = Field(description="Human-readable explanation (no C3 values, no other-tenant ids).")
    status: int = Field(description="HTTP status code.")
    instance: str | None = Field(default=None, description="Request correlation id, if any.")
    errors: list[dict[str, Any]] | None = Field(
        default=None, description="Field-level validation problems, when applicable."
    )


class AppError(Exception):
    """Application error carrying a machine code and an HTTP status.

    Raised by services, repositories, and guards; mapped to a `ProblemDetail` by the
    exception handlers. The message must never contain commercial values or another tenant's
    identifiers.
    """

    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.errors = errors

    def to_problem(self, instance: str | None = None) -> ProblemDetail:
        return ProblemDetail(
            code=self.code,
            title=self.code.value.replace("_", " ").title(),
            detail=self.message,
            status=self.status_code,
            instance=instance,
            errors=self.errors,
        )
