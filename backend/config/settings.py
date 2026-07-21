"""Application settings (BUILD_SPEC §12).

Every value is read from the environment. Nothing here carries a default that
could silently connect a test run to a real database or accept an unsigned
token: `database_url` and `supabase_jwt_secret` default to None and the code
that needs them raises rather than guessing.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_jwt_secret: str | None = None

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"

    # Cross-provider LLM fallback (ADR-018). Free tier, open models. Inert until
    # GROQ_API_KEY is set: with no key the fallback chain is Gemini-only.
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

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

    @field_validator("*", mode="before")
    @classmethod
    def _blank_out_comment_leaks(cls, value):
        """Treat a value that is only a comment as unset.

        `KEY=            # explanation` in a .env file does NOT parse as empty:
        python-dotenv strips an inline comment only when a value precedes it, so
        the comment text becomes the value. That turned "unconfigured" into a
        truthy string, which meant `/health` reported a connection *error*
        instead of `not_configured`, and `get_engine()` tried to connect to
        prose instead of raising a clear error.

        The .env templates now keep comments on their own lines. This catches
        the case anyway, because the failure it produces is confusing enough to
        cost an hour.
        """
        # Only comment-only values. An empty string is left alone: it is already
        # falsy, and coercing it to None would break the non-optional fields
        # that carry defaults (`gemini_model`, `env`, `chroma_persist_dir`).
        if isinstance(value, str) and value.strip().startswith("#"):
            return None
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url] if self.frontend_url else []


@lru_cache
def get_settings() -> Settings:
    return Settings()
