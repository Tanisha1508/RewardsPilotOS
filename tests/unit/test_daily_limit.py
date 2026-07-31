"""One user must not be able to spend everyone's day (A2).

The free Gemini tier is 20 requests per day per model and a question costs two
of them, so roughly ten questions a day exist for all users put together
(measured 2026-07-31). Before this, the first person to ask eleven questions
took the day from everyone else — and the others did not see a rate limit, they
saw a product that had stopped working.

The counting itself needs a database and is covered in tests/integration/. What
is tested here is the decision: when the limit bites, when it does not, and that
it is checked before anything expensive happens.
"""

import uuid

import pytest

from backend.application.chat import DailyLimitReachedError, check_daily_limit
from backend.config.settings import get_settings

USER = uuid.uuid4()


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _with_used(monkeypatch, used: int):
    monkeypatch.setattr("backend.application.chat.answers_used_today", lambda _user: used)


def test_under_the_limit_passes(monkeypatch):
    monkeypatch.setenv("CHAT_DAILY_LIMIT_PER_USER", "5")
    _with_used(monkeypatch, 4)
    check_daily_limit(USER)  # does not raise


def test_at_the_limit_stops(monkeypatch):
    """>= not >: having used 5 of 5 means the next one is refused."""
    monkeypatch.setenv("CHAT_DAILY_LIMIT_PER_USER", "5")
    _with_used(monkeypatch, 5)
    with pytest.raises(DailyLimitReachedError):
        check_daily_limit(USER)


def test_zero_disables_the_limit(monkeypatch):
    """The escape hatch local development and the test suite rely on."""
    monkeypatch.setenv("CHAT_DAILY_LIMIT_PER_USER", "0")
    _with_used(monkeypatch, 9999)
    check_daily_limit(USER)  # does not raise


def test_the_message_says_what_to_do_not_just_no(monkeypatch):
    """A limit a user cannot understand reads as the app being broken. It has to
    say why, when it lifts, and what still works."""
    monkeypatch.setenv("CHAT_DAILY_LIMIT_PER_USER", "5")
    _with_used(monkeypatch, 5)

    with pytest.raises(DailyLimitReachedError) as caught:
        check_daily_limit(USER)

    message = str(caught.value).lower()
    assert "5" in message  # how many they had
    assert "reset" in message  # that it comes back
    assert "shared" in message  # why the limit exists at all
    assert "still work" in message  # the rest of the app is fine


def test_the_error_reports_as_429(monkeypatch):
    """429, not 403: the request was legitimate and will succeed tomorrow."""
    from backend.api.responses import STATUS_BY_EXCEPTION

    mapping = dict(STATUS_BY_EXCEPTION)
    assert mapping[DailyLimitReachedError] == 429


def test_the_limit_is_checked_before_the_llm_is_built(monkeypatch):
    """The point of the limit is to not spend provider quota. Checking after the
    workflow ran would have already paid the cost it exists to prevent."""
    import backend.application.chat as chat

    monkeypatch.setenv("CHAT_DAILY_LIMIT_PER_USER", "5")
    _with_used(monkeypatch, 5)

    def explode():
        raise AssertionError("default_llm() was reached despite the limit")

    monkeypatch.setattr(chat, "default_llm", explode)

    with pytest.raises(DailyLimitReachedError):
        chat.run_chat(USER, "which card for a flight?")
