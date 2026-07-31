"""Agent registry: the LLM-backed agents in the system and the shared LLM
client they use. The only place LLM calls are constructed (no LLM calls
outside agents/, BUILD_SPEC §3)."""

import time
from typing import Protocol


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class LLMUnavailableError(Exception):
    """The LLM could not produce a response (after the single retry)."""


class GeminiClient:
    """Gemini via GEMINI_API_KEY (google-genai SDK). Model swappable through
    the single GEMINI_MODEL env var (BUILD_SPEC §1, ADR-015).

    Reads config through `Settings`, not `os.environ` directly, so a local
    `.env` is honoured the same way the rest of the app reads it — otherwise the
    key would resolve on Render (process env) but be invisible to a local server
    that only has it in `.env`."""

    def __init__(self, model: str | None = None) -> None:
        from backend.config.settings import get_settings

        settings = get_settings()
        if not settings.gemini_api_key:
            raise LLMUnavailableError("GEMINI_API_KEY is not set")
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        # `model` overrides the configured default so a FallbackLLM can try a
        # second model; unset means the ADR-015 pinned GEMINI_MODEL.
        self.model = model or settings.gemini_model

    def complete(self, system: str, user: str) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        return response.text or ""


# Models the fallback tries after the primary (GEMINI_MODEL). Free tier, both
# proven working (D3 prep). A different model is a separate capacity pool, so a
# transient 503 on one does not necessarily hit the other (ADR-018).
FALLBACK_MODELS = ("gemini-flash-latest",)

# Error signatures that mean "try the next model" rather than "give up". A
# transient availability/rate error on one model may not affect another; a
# permanent error (bad key, malformed request) will hit every model the same
# way, so those fail fast instead of wasting calls.
_TRANSIENT_MARKERS = (
    "503",
    "unavailable",
    "429",
    "resource_exhausted",
    "deadline",
    "timeout",
    "temporarily",
    "overloaded",
    "connect",
)


def is_transient(exc: Exception) -> bool:
    return any(marker in str(exc).lower() for marker in _TRANSIENT_MARKERS)


# A 429 that means "this model is out of requests for the day", as opposed to
# "you are going too fast this minute". Gemini's free tier is 20 requests per
# day *per model*, and it says so explicitly in the quota id (measured
# 2026-07-30: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, limit 20).
#
# The two need separating because the right response is opposite. A per-minute
# limit clears in seconds and is worth retrying. A daily limit does not clear
# today, so every subsequent request to that model is a guaranteed failure that
# still costs a network round trip — measured at ~0.6 s, paid twice per chat
# because the workflow makes two LLM calls.
_DAILY_QUOTA_MARKERS = ("perday", "per day", "requests per day", "free_tier_requests")


def is_daily_quota_exhausted(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text and any(marker in text for marker in _DAILY_QUOTA_MARKERS)


class FallbackLLM:
    """Try each client in order; on a *transient* failure, fall through to the
    next (ADR-018). A non-transient failure (bad key, malformed request) breaks
    immediately — a different model would fail identically. If every client
    fails, raise LLMUnavailableError carrying all the reasons.

    Implements the LLM Protocol, so the workflow is unchanged — it still sees a
    single `complete(system, user)`."""

    #: How long a model is skipped after it reports a daily quota exhaustion.
    #:
    #: Not "until midnight": that needs the reset timezone (Pacific, for Google's
    #: free tier), and being wrong about it either wastes calls all day or
    #: benches a working model for hours. A short window is self-correcting —
    #: the worst case is one wasted probe every 15 minutes instead of one on
    #: every request, which is the ~100x that matters, and the model returns to
    #: service on its own once the quota rolls over.
    QUOTA_COOLDOWN_S = 15 * 60

    def __init__(self, clients: list[LLM], labels: list[str] | None = None) -> None:
        if not clients:
            raise ValueError("FallbackLLM needs at least one client")
        self._clients = clients
        self._labels = labels or [f"llm{i}" for i in range(len(clients))]
        # label -> monotonic deadline before which this client is not tried.
        self._benched: dict[str, float] = {}

    def _available(self, label: str) -> bool:
        until = self._benched.get(label)
        if until is None:
            return True
        if time.monotonic() >= until:
            del self._benched[label]  # cooldown served; probe it again
            return True
        return False

    def complete(self, system: str, user: str) -> str:
        errors: list[str] = []
        skipped: list[str] = []
        for client, label in zip(self._clients, self._labels):
            if not self._available(label):
                skipped.append(label)
                continue
            try:
                return client.complete(system, user)
            except Exception as exc:
                errors.append(f"{label}: {type(exc).__name__}: {exc}")
                if is_daily_quota_exhausted(exc):
                    # Out of requests for the day. Retrying it on the next
                    # call cannot succeed and costs a round trip each time.
                    self._benched[label] = time.monotonic() + self.QUOTA_COOLDOWN_S
                elif not is_transient(exc):
                    break  # permanent — the next model will fail the same way
        if not errors and skipped:
            # Everything was benched, so nothing was even attempted. Say that
            # rather than "all models failed", which would be untrue and would
            # send someone hunting for an error that was never raised.
            raise LLMUnavailableError("every model is in quota cooldown — " + ", ".join(skipped))
        raise LLMUnavailableError("all models failed — " + " | ".join(errors))


class GroqClient:
    """Groq free tier (open models) via the OpenAI-compatible REST API, called
    with httpx — no new SDK dependency (ADR-018).

    The cross-provider fallback tier: reached only when every Gemini model is
    transiently unavailable, so it covers a Gemini-*wide* outage that a
    same-provider fallback cannot. Inert until GROQ_API_KEY is set."""

    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, model: str | None = None) -> None:
        from backend.config.settings import get_settings

        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMUnavailableError("GROQ_API_KEY is not set")
        self._key = settings.groq_api_key
        self.model = model or settings.groq_model

    def complete(self, system: str, user: str) -> str:
        import httpx

        response = httpx.post(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {self._key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"] or ""


def default_llm() -> LLM:
    """The production LLM the application layer runs the workflow with. Kept here
    so LLM construction stays inside agents/ (BUILD_SPEC §3: no LLM calls outside
    agents/) — the application orchestrates, but the client lives here.

    A tiered fallback (ADR-018): pinned GEMINI_MODEL → a second free Gemini model
    (a separate capacity pool, so a transient 503 on one need not hit the other)
    → Groq (a different provider, covering a Gemini-wide outage). The Groq tier is
    appended only when GROQ_API_KEY is configured; otherwise the chain is
    Gemini-only. GEMINI_MODEL still chooses the primary (ADR-015)."""
    from backend.config.settings import get_settings

    settings = get_settings()
    clients: list[LLM] = []
    labels: list[str] = []

    models: list[str] = [settings.gemini_model]
    for model in FALLBACK_MODELS:
        if model not in models:
            models.append(model)
    for model in models:
        clients.append(GeminiClient(model=model))
        labels.append(f"gemini:{model}")

    if settings.groq_api_key:
        clients.append(GroqClient())
        labels.append(f"groq:{settings.groq_model}")

    return FallbackLLM(clients, labels=labels)


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
