"""Multi-model Gemini fallback (ADR-018).

The scenario that motivated it: gemini-3.5-flash returned 503 'high demand'
during D4 and blocked a live recommendation. A second free-tier model is a
separate capacity pool, so the fallback tries it before giving up — while a
permanent error (bad key) still fails fast rather than wasting a second call.
"""

import pytest

from agents.registry import FallbackLLM, LLMUnavailableError, is_transient


class FixedLLM:
    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return self.answer


class FailingLLM:
    def __init__(self, exc):
        self.exc = exc
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        raise self.exc


def test_primary_success_never_calls_the_fallback():
    primary = FixedLLM("primary answer")
    secondary = FixedLLM("secondary answer")
    llm = FallbackLLM([primary, secondary], labels=["m1", "m2"])

    assert llm.complete("s", "u") == "primary answer"
    assert primary.calls == 1
    assert secondary.calls == 0  # untouched


def test_transient_primary_failure_falls_through_to_secondary():
    """A 503 on the primary must roll to the next model, not surface an error."""
    primary = FailingLLM(RuntimeError("503 UNAVAILABLE: model is overloaded"))
    secondary = FixedLLM("secondary answer")
    llm = FallbackLLM([primary, secondary], labels=["gemini-3.5-flash", "gemini-flash-latest"])

    assert llm.complete("s", "u") == "secondary answer"
    assert primary.calls == 1 and secondary.calls == 1


def test_non_transient_failure_fails_fast_without_trying_the_next_model():
    """A bad key fails identically on every model; do not waste a second call."""
    primary = FailingLLM(RuntimeError("API_KEY_INVALID"))
    secondary = FixedLLM("secondary answer")
    llm = FallbackLLM([primary, secondary], labels=["m1", "m2"])

    with pytest.raises(LLMUnavailableError):
        llm.complete("s", "u")
    assert primary.calls == 1
    assert secondary.calls == 0  # not tried — permanent error


def test_all_models_transiently_failing_raises_with_every_reason():
    primary = FailingLLM(RuntimeError("503 UNAVAILABLE"))
    secondary = FailingLLM(RuntimeError("429 RESOURCE_EXHAUSTED"))
    llm = FallbackLLM([primary, secondary], labels=["m1", "m2"])

    with pytest.raises(LLMUnavailableError) as exc:
        llm.complete("s", "u")
    message = str(exc.value)
    assert "m1" in message and "m2" in message  # both reasons carried
    assert primary.calls == 1 and secondary.calls == 1


@pytest.mark.parametrize(
    "text,transient",
    [
        ("503 UNAVAILABLE", True),
        ("429 RESOURCE_EXHAUSTED", True),
        ("model is temporarily overloaded", True),
        ("connect timeout", True),
        ("400 API_KEY_INVALID", False),
        ("permission denied", False),
        ("malformed request", False),
    ],
)
def test_transient_classification(text, transient):
    assert is_transient(RuntimeError(text)) is transient


def test_empty_client_list_is_rejected():
    with pytest.raises(ValueError):
        FallbackLLM([])


def test_default_llm_is_gemini_only_without_a_groq_key(monkeypatch):
    from backend.config.settings import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-no-network")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    from agents.registry import default_llm

    labels = default_llm()._labels
    assert all(label.startswith("gemini:") for label in labels)
    assert len(labels) == 2  # primary + one fallback model
    get_settings.cache_clear()


def test_default_llm_appends_groq_when_configured(monkeypatch):
    from backend.config.settings import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-no-network")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-inert-test-key")
    get_settings.cache_clear()
    from agents.registry import default_llm

    labels = default_llm()._labels
    # Groq is the LAST resort — after every Gemini model.
    assert labels[-1].startswith("groq:")
    assert labels[0].startswith("gemini:")
    get_settings.cache_clear()


def test_groq_client_parses_the_openai_shaped_response(monkeypatch):
    """GroqClient calls the OpenAI-compatible endpoint via httpx and reads
    choices[0].message.content. Mock the POST so no network is touched."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk-inert-test-key")
    from backend.config.settings import get_settings

    get_settings.cache_clear()
    from agents.registry import GroqClient

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "groq answer"}}]}

    import httpx

    monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse())
    assert GroqClient().complete("sys", "user") == "groq answer"
    get_settings.cache_clear()


def test_groq_client_requires_a_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from backend.config.settings import get_settings

    get_settings.cache_clear()
    from agents.registry import GroqClient

    with pytest.raises(LLMUnavailableError):
        GroqClient()
    get_settings.cache_clear()
