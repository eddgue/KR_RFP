"""FastAPI application factory (PLAN §5, §6).

Builds the app: mounts the /api/v1 router, registers the uniform exception handlers, wires the
immutability guard listeners, and installs a tenant-context middleware STUB.

Tenant-context middleware (security/PLAN §1, §2): in production an auth-edge adapter validates
the IdP token (sig/iss/aud/exp) and establishes the verified principal from its claims — NEVER
from the request body. Until that adapter lands (DEP-4), this stub establishes a development
principal in non-production environments only, and leaves production requests unauthenticated
(the security dependencies then deny protected routes). The principal/tenant are stashed on
`request.state` for the security dependencies to read.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.api.router import api_router
from app.core.audit.guards import register_immutability_guards
from app.core.config.settings import Environment, Settings, get_settings
from app.core.errors.handlers import register_exception_handlers
from app.core.security.principal import Principal
from app.core.security.rbac import Role

# A stable dev tenant id so local requests resolve to a consistent tenant (matches the
# migration's seeded ref.client when DATABASE_URL points at a freshly migrated DB).
_DEV_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _dev_principal(settings: Settings) -> Principal:
    """A development principal for non-production environments only.

    Holds analyst+cat_man+approver roles so local work can exercise guarded routes. This is a
    scaffold convenience, never a production code path.
    """

    return Principal(
        subject="dev@local",
        tenant_id=_DEV_TENANT_ID,
        roles=frozenset({Role.ANALYST, Role.CAT_MAN, Role.APPROVER}),
        email="dev@local",
        tenant_code=settings.default_tenant_code,
    )


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""

    settings = get_settings()

    app = FastAPI(
        title="Kroger Produce RFP / Sourcing — System of Record",
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    register_exception_handlers(app)
    register_immutability_guards()

    @app.middleware("http")
    async def tenant_context_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Establish request correlation + the verified principal/tenant (STUB).

        Production: replace the dev-principal block with the IdP token-verification adapter
        (DEP-4). Tenant is ALWAYS derived from the verified principal, never from input.
        """

        request.state.request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.principal = None

        if settings.env is not Environment.PRODUCTION:
            request.state.principal = _dev_principal(settings)
        # else: no principal -> security dependencies deny protected routes until DEP-4 lands.

        return await call_next(request)

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
