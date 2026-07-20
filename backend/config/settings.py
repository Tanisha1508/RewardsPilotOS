"""Application settings (BUILD_SPEC §12).

Every value is read from the environment. Nothing here carries a default that
could silently connect a test run to a real database or accept an unsigned
token: `database_url` and `supabase_jwt_secret` default to None and the code
that needs them raises rather than guessing.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_jwt_secret: str | None = None

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    redis_url: str | None = None
    chroma_persist_dir: str = "data/embeddings"

    backend_url: str | None = None
    frontend_url: str | None = None
    env: str = "development"

    # Tests never fall back to `database_url`. Pointing a suite that creates and
    # drops tables at whatever database happens to be configured is how a dev
    # database gets wiped; opting in through a separate variable makes that
    # impossible by accident (additive to BUILD_SPEC §12 — see ADR-013).
    test_database_url: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url] if self.frontend_url else []


@lru_cache
def get_settings() -> Settings:
    return Settings()
