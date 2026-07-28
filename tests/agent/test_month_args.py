"""An invented `month` must not reach the engine (found live 2026-07-28).

The Planner emitted `month: 2025-05` on a query asked 2026-07-28, because the
prompt told it to "default to the current month" and it has no idea what that
is. The month is schema-valid, so `validate_plan` passed it straight through.

That is not cosmetic: since ADR-012 `month` selects which accelerated programs
are in force. `test_the_dormant_bug_this_prevents` pins the concrete damage.
"""

from agents.planner.month_args import query_names_a_period, strip_unrequested_month
from rules.engine.engine import RuleEngine


def _compare(month: str | None):
    return {
        "tool": "CompareCards",
        "args": {
            "cards": ["axis_atlas"],
            "amount": 50000,
            "category": "flights",
            **({"month": month} if month else {}),
        },
    }


def test_the_live_regression_an_invented_month_is_dropped():
    errors: list[str] = []
    plan = strip_unrequested_month(
        [_compare("2025-05")],
        "Which of my cards is best for a Rs 50,000 flight booking?",
        errors,
    )

    assert "month" not in plan[0]["args"]
    # Everything else survives untouched.
    assert plan[0]["args"]["amount"] == 50000
    assert plan[0]["args"]["cards"] == ["axis_atlas"]
    # And the correction is recorded rather than silent.
    assert any("dropped invented month" in error and "2025-05" in error for error in errors)


def test_a_month_the_user_named_is_preserved():
    """Parsing a period out of the query is legitimate work, not guessing."""
    for query in (
        "How much would I earn on a 50,000 flight in August?",
        "What did I earn last month?",
        "Compare my cards for 2026-08",
        "Am I near my cap this month?",
    ):
        errors: list[str] = []
        plan = strip_unrequested_month([_compare("2026-08")], query, errors)
        assert plan[0]["args"].get("month") == "2026-08", query
        assert errors == [], query


def test_a_plan_without_a_month_is_untouched():
    errors: list[str] = []
    plan = strip_unrequested_month([_compare(None)], "Best card for flights?", errors)

    assert plan[0]["args"] == {"cards": ["axis_atlas"], "amount": 50000, "category": "flights"}
    assert errors == []


def test_period_detection():
    assert query_names_a_period("what about August 2026")
    assert query_names_a_period("my spend this month")
    assert query_names_a_period("earnings in 2026-08")
    assert not query_names_a_period("Which card is best for a Rs 50,000 flight booking?")
    assert not query_names_a_period("best card for groceries")


def test_the_dormant_bug_this_prevents():
    """The reason this matters, stated in numbers.

    Amex's Reward Multiplier is valid to 2026-07-31. A query asked in 2026-08
    must fall back to base earn and say so. With the invented 2025-05 it does
    not — it reports the accelerated figure with no note and no confidence
    penalty, which is the ADR-012 failure reached by a different route.
    """
    engine = RuleEngine()

    correct = engine.calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2026-08"
    )
    invented = engine.calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2025-05"
    )

    assert correct.points == 1000.0
    assert correct.applied == "base"
    assert correct.expiry_note is not None

    assert invented.points == 3000.0  # 3x overstatement
    assert invented.applied == "accelerated"
    assert invented.expiry_note is None  # ...and silent about it

    # Which is why the month must never be invented in the first place.
    errors: list[str] = []
    plan = strip_unrequested_month(
        [
            {
                "tool": "CalculateEarn",
                "args": {
                    "card_key": "amex_plat_travel",
                    "amount": 50000,
                    "category": "hotels",
                    "channel": "reward_multiplier",
                    "month": "2025-05",
                },
            }
        ],
        "How much do I earn on a 50,000 rupee hotel booking?",
        errors,
    )
    assert "month" not in plan[0]["args"]
