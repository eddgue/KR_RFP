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

from app.core.config.settings import get_settings
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


def _apply_cors_for_unexpected(request: Request, response: JSONResponse) -> None:
    """Echo CORS headers onto the 500 envelope so the browser console can read it.

    The catch-all `Exception`/500 handler runs inside Starlette's ServerErrorMiddleware, which sits
    OUTSIDE the CORSMiddleware added in the app factory — so without this, an unexpected 500 reaches
    a cross-origin console with no `Access-Control-Allow-Origin` and surfaces as an opaque
    CORS/network error instead of this problem envelope. Mirror the simple-request CORS contract (a
    500 is never a preflight): reflect an allowed Origin with credentials, and Vary on Origin. The
    other handlers run inside CORSMiddleware, so they need none of this.
    """

    origin = request.headers.get("origin")
    if not origin:
        return
    allowed = {o.strip() for o in get_settings().cors_allow_origins.split(",") if o.strip()}
    if origin not in allowed:
        return
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Vary"] = "Origin"


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    problem = ProblemDetail(
        code=ErrorCode.INTERNAL,
        title="Internal Error",
        detail="An unexpected error occurred.",
        status=500,
        instance=_request_id(request),
    )
    response = _response(problem)
    _apply_cors_for_unexpected(request, response)
    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all handlers onto the app (called by the app factory)."""

    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected)
