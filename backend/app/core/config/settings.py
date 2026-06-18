"""Single typed configuration surface (PLAN §7).

All runtime configuration is sourced from the environment via pydantic-settings; there are
no literals or secrets in code. One field (`engine_impl`) selects the engine implementation
(stub vs real, per the D2 spike).
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def is_production(self) -> bool:
        return self.env is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""

    return Settings()
