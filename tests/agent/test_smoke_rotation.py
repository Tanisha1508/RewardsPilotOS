"""The smoke suite's query rotation (KNOWN_LIMITATIONS 26).

The Gemini free tier allows 20 requests/day/model and a full N=3 run costs 24+,
so the four queries run as two fixed pairs on alternating days. These tests
guard the property that makes that acceptable: **every query is covered every
other day**. A rotation that quietly dropped one would look identical in the
output while starving a query indefinitely.

Pure scheduling logic — no LLM is called, so these belong in the fast suite
even though the suite they describe does not.
"""

from datetime import date

import pytest

from evaluation.smoke.run import GROUPS, QUERIES, select_queries, todays_group


def test_every_query_belongs_to_exactly_one_group():
    assert all(query["group"] in GROUPS for query in QUERIES)


def test_the_groups_partition_the_queries():
    """No query in both groups, none in neither — the property that makes
    'covered every other day' true rather than approximately true."""
    grouped = [q["id"] for group in GROUPS for q in select_queries(group)]
    assert sorted(grouped) == sorted(q["id"] for q in QUERIES)
    assert len(grouped) == len(set(grouped))


def test_both_groups_are_non_empty_and_balanced():
    """Balance is what keeps each day inside quota; an empty group would mean a
    wasted day of coverage."""
    sizes = [len(select_queries(group)) for group in GROUPS]
    assert all(size > 0 for size in sizes)
    assert max(sizes) - min(sizes) <= 1


@pytest.mark.parametrize("day,expected", [(1, "a"), (2, "b"), (22, "b"), (23, "a"), (31, "a")])
def test_group_follows_day_of_month_parity(day, expected):
    """Stateless and reproducible: same day, same pair, on any machine."""
    assert todays_group(date(2026, 7, day)) == expected


def test_a_full_run_is_available_on_request():
    """`all` exists for a deliberate full-coverage run, accepting the Groq
    fall-through that implies once Gemini's daily budget is spent."""
    assert len(select_queries("all")) == len(QUERIES)


def test_an_unknown_group_fails_loudly():
    """A typo must not silently run zero queries and report success."""
    with pytest.raises(SystemExit):
        select_queries("c")


def test_the_rotation_covers_every_query_within_two_days():
    """The claim item 26 rests on, asserted directly rather than assumed."""
    covered = {q["id"] for day in (1, 2) for q in select_queries(todays_group(date(2026, 7, day)))}
    assert covered == {q["id"] for q in QUERIES}
