"""A model that is out of requests for the day must not be re-probed on every
call (measured 2026-07-30).

Gemini's free tier is 20 requests per day *per model*. The pinned primary was
exhausted, so every LLM call spent a ~0.6 s round trip on a guaranteed 429
before falling through — paid twice per chat, because the workflow makes two
LLM calls.

The distinction being tested is between the two kinds of 429: a per-minute rate
limit clears in seconds and is worth retrying, a per-day quota does not clear
today and is not.
"""

import pytest

from agents.registry import (
    FallbackLLM,
    LLMUnavailableError,
    is_daily_quota_exhausted,
    is_transient,
)

DAILY_429 = (
    "429 RESOURCE_EXHAUSTED. Quota exceeded for metric: "
    "generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, "
    "model: gemini-3.5-flash. quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier"
)
PER_MINUTE_429 = "429 RESOURCE_EXHAUSTED. Quota exceeded: requests per minute, please retry in 6s"


class Counting:
    """Records how many times it was actually called."""

    def __init__(self, error: str | None = None, reply: str = "ok"):
        self.error, self.reply, self.calls = error, reply, 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        return self.reply


def test_a_daily_quota_error_is_told_apart_from_a_rate_limit():
    assert is_daily_quota_exhausted(RuntimeError(DAILY_429))
    assert not is_daily_quota_exhausted(RuntimeError(PER_MINUTE_429))
    # Both are still transient — the point is to fall through either way.
    assert is_transient(RuntimeError(DAILY_429))
    assert is_transient(RuntimeError(PER_MINUTE_429))


def test_an_exhausted_model_is_not_called_again():
    """The behaviour that saves the round trip."""
    dead, alive = Counting(error=DAILY_429), Counting(reply="answer")
    llm = FallbackLLM([dead, alive], labels=["primary", "fallback"])

    for _ in range(5):
        assert llm.complete("s", "u") == "answer"

    assert dead.calls == 1, "the exhausted model was re-probed"
    assert alive.calls == 5


def test_a_per_minute_limit_is_still_retried_every_time():
    """The other half. Benching a model over a limit that clears in seconds
    would take it out of service for fifteen minutes for no reason."""
    limited, alive = Counting(error=PER_MINUTE_429), Counting(reply="answer")
    llm = FallbackLLM([limited, alive], labels=["primary", "fallback"])

    for _ in range(3):
        llm.complete("s", "u")

    assert limited.calls == 3


def test_the_cooldown_expires_so_the_model_comes_back():
    """Self-correcting: the quota rolls over and nothing has to notice."""
    flaky, alive = Counting(error=DAILY_429), Counting(reply="answer")
    llm = FallbackLLM([flaky, alive], labels=["primary", "fallback"])
    llm.complete("s", "u")
    assert flaky.calls == 1

    llm.QUOTA_COOLDOWN_S = 0  # cooldown served
    llm._benched["primary"] = 0
    llm.complete("s", "u")

    assert flaky.calls == 2, "the model was never given another chance"


def test_everything_benched_says_so_rather_than_all_models_failed():
    """An honest message: nothing was attempted, so nothing failed."""
    dead = Counting(error=DAILY_429)
    llm = FallbackLLM([dead], labels=["only"])
    with pytest.raises(LLMUnavailableError):
        llm.complete("s", "u")

    with pytest.raises(LLMUnavailableError, match="quota cooldown"):
        llm.complete("s", "u")
    assert dead.calls == 1


def test_a_permanent_error_still_breaks_the_chain_immediately():
    """Unchanged behaviour: a bad key fails identically on every model."""
    bad, alive = Counting(error="401 API key not valid"), Counting(reply="answer")
    llm = FallbackLLM([bad, alive], labels=["primary", "fallback"])

    with pytest.raises(LLMUnavailableError):
        llm.complete("s", "u")
    assert alive.calls == 0
