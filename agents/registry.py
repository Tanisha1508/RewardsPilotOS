"""Agent registry: the LLM-backed agents in the system and the shared LLM
client they use. The only place LLM calls are constructed (no LLM calls
outside agents/, BUILD_SPEC §3)."""

import os
import time
from typing import Protocol


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class LLMUnavailableError(Exception):
    """The LLM could not produce a response (after the single retry)."""


class GeminiClient:
    """Gemini via GEMINI_API_KEY (google-genai SDK). Model swappable through
    the single GEMINI_MODEL env var (BUILD_SPEC §1)."""

    def __init__(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise LLMUnavailableError("GEMINI_API_KEY is not set")
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

    def complete(self, system: str, user: str) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self._model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        return response.text or ""


def complete_with_retry(llm: LLM, system: str, user: str, backoff_s: float = 1.0) -> str:
    """1 retry per LLM node with backoff (BUILD_SPEC §8)."""
    try:
        return llm.complete(system, user)
    except Exception:
        time.sleep(backoff_s)
        try:
            return llm.complete(system, user)
        except Exception as exc:
            raise LLMUnavailableError(f"LLM failed after retry: {exc}") from exc


AGENTS = {
    "planner": "agents.planner — intent classification and tool planning",
    "recommender": "agents.recommendation — structured recommendation writing",
}
