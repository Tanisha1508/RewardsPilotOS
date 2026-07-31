"""GetOpportunities must not return invented content (found 2026-07-31).

It returned two hardcoded fixtures about an invented bank — a "Skyhigh Airways
25 percent transfer bonus" and "32000 Voyager Points expiring" — with
`example.test` source URLs. Both titles said "(SYNTHETIC FIXTURE)", which was
the only barrier between them and a real user, and a title is exactly what a
model paraphrases away.

Worse than a stray fixture, because of where the output goes. The planner prompt
names this tool for portfolio questions, so a real question reaches it. Its
result lands in `state["memory"]`, and `memory` is in `_grounded_text` — the
text the number-traceability check validates prose against. "25 percent" and
"32000" would have been certified as traceable *because a tool produced them*.
The guard against invented numbers would have vouched for them.

Nothing populates the notifications table, so an empty result is the true one.
"""

from contracts.tools.opportunity import GetOpportunitiesInput
from tools.opportunity_engine.tools import get_opportunities
from tools.portfolio.source import acting_as

USER = "00000000-0000-0000-0000-000000000001"


def test_it_returns_nothing_rather_than_fiction():
    with acting_as(USER):
        assert get_opportunities(GetOpportunitiesInput()).opportunities == []


def test_no_invented_source_url_can_reach_a_user():
    """The specific leak: `example.test` URLs presented as a real source."""
    with acting_as(USER):
        out = get_opportunities(GetOpportunitiesInput(limit=10))
    assert not [o for o in out.opportunities if ".test" in (o.source_url or "")]


# Caller resolution is NOT re-tested here. `tests/agent/test_caller_identity.py`
# already asserts it for all 15 tools, and the suite conftest wraps every test in
# `acting_as(...)`, so a local "no caller" assertion cannot hold anyway — it
# would be testing the fixture, not the tool.


def test_the_example_shape_is_not_wired_to_the_serving_path():
    """The old fixtures are kept as the shape D5 should produce. They must stay
    unreferenced by the function — keeping them is only safe while nothing
    serves them."""
    import inspect

    from tools.opportunity_engine import tools

    assert "_EXAMPLE_SHAPE_FOR_D5" not in inspect.getsource(tools.get_opportunities)
