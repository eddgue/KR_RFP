"""Single typed configuration surface (PLAN §7).

All runtime configuration is sourced from the environment via pydantic-settings; there are
no literals or secrets in code. One field (`engine_impl`) selects the engine implementation
(stub vs real, per the D2 spike).
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# <repo-root>/var/vault — this file is backend/app/core/config/settings.py, so the repo root is
# four parents up from `app/` (config -> core -> app -> backend -> <repo-root>).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_VAULT_ROOT = _REPO_ROOT / "var" / "vault"


class Environment(StrEnum):
    """Deployment environment."""

    LOCAL = "local"
    CI = "ci"
    STAGING = "staging"
    PRODUCTION = "production"


class EngineImpl(StrEnum):
    """Which engine implementation the runner binds (D2 spike: only the stub exists today)."""

    STUB = "stub"


class Settings(BaseSettings):
    """Backend settings. Field names map to env vars case-insensitively."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database — SQLAlchemy + Alembic both read this.
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/kr_rfp"

    # Deployment environment.
    env: Environment = Environment.LOCAL

    # Engine implementation selector.
    engine_impl: EngineImpl = EngineImpl.STUB

    # Default tenant code — local dev/seed ONLY. Runtime tenant context comes from the
    # verified token, never from this value (security/PLAN §1).
    default_tenant_code: str = "KR-DEFAULT"

    # API surface.
    api_v1_prefix: str = "/api/v1"

    # Web-console auth (app/auth) — username/password + TOTP-2FA session.
    # PROD MUST OVERRIDE `auth_secret_key`: this dev default signs the session JWT and is
    # intentionally well-known. Set AUTH_SECRET_KEY to a long random secret in every non-local
    # environment, or sessions are forgeable. The TTL bounds how long a session cookie is valid.
    auth_secret_key: str = "dev-insecure-change-me-in-production"  # noqa: S105 — dev default only
    auth_token_ttl_minutes: int = 720  # 12h dev session; tune per environment.
    # The session cookie is `Secure` by default (HTTPS only). Set AUTH_COOKIE_SECURE=false ONLY for
    # local http://localhost testing — a browser silently drops a Secure cookie over plain http, so
    # login appears to "succeed" but no session sticks. Keep it true in every deployed environment.
    auth_cookie_secure: bool = True
    # The browser console is a separate origin from this API and sends the session cookie
    # cross-origin, so credentialed CORS must allow its EXACT origin(s). Comma-separated; a wildcard
    # "*" is invalid with credentials, so list real origins. Default is the local Next dev server;
    # set CORS_ALLOW_ORIGINS to the deployed console origin(s) in every other environment.
    cors_allow_origins: str = "http://localhost:3000"

    # Pilot run vault root (app/api/v1/runs wraps PilotService against this). Defaults under the
    # repo's `var/vault`; created on first use. Override VAULT_ROOT to point at the sponsor vault.
    vault_root: Path = _DEFAULT_VAULT_ROOT

    @property
    def is_production(self) -> bool:
        return self.env is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""

    return Settings()
