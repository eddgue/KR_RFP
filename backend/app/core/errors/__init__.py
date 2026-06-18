"""Uniform error taxonomy + FastAPI exception handlers (PLAN §5, ADR-0007)."""

from app.core.errors.taxonomy import AppError, ErrorCode, ProblemDetail

__all__ = ["AppError", "ErrorCode", "ProblemDetail"]
