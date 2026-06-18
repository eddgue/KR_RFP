"""FastAPI exception handlers -> the uniform problem envelope (PLAN §5).

Every error path returns a `ProblemDetail` with a stable machine code. Unexpected exceptions
collapse to a generic INTERNAL problem so no stack trace, commercial value, or cross-tenant
identifier leaks to the client.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors.taxonomy import AppError, ErrorCode, ProblemDetail

PROBLEM_MEDIA_TYPE = "application/problem+json"


def _response(problem: ProblemDetail) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(),
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return _response(exc.to_problem(instance=_request_id(request)))


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    problem = ProblemDetail(
        code=ErrorCode.VALIDATION_ERROR,
        title="Validation Error",
        detail="The request failed validation.",
        status=422,
        instance=_request_id(request),
        errors=[{"loc": list(e.get("loc", [])), "msg": e.get("msg")} for e in exc.errors()],
    )
    return _response(problem)


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.INTERNAL
    problem = ProblemDetail(
        code=code,
        title=code.value.replace("_", " ").title(),
        detail=str(exc.detail),
        status=exc.status_code,
        instance=_request_id(request),
    )
    return _response(problem)


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    problem = ProblemDetail(
        code=ErrorCode.INTERNAL,
        title="Internal Error",
        detail="An unexpected error occurred.",
        status=500,
        instance=_request_id(request),
    )
    return _response(problem)


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all handlers onto the app (called by the app factory)."""

    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected)
