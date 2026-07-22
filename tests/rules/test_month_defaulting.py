"""An absent month resolves to the current month (KNOWN_LIMITATIONS 24).

The bug: `month` was required on all three rule tools with a
`^\\d{4}-\\d{2}$` pattern and no default. Most real queries carry no period
("which card for a ₹50,000 flight?"), so the Planner had no basis to fill it,
correctly declined, and `validate_plan` rejected the whole invocation — the
comparison never ran and the answer shipped with zero computed numbers. Found
by the first live smoke run: 0/3 on the portal-hotel query, 2/3 on the flight
query.

Same class as the D4 `cards=[]` bug, one argument further along — which is why
these tests assert the *shape* of the contract (absent is accepted, malformed
still is not, the engine keeps no default) rather than any particular figure.
"""

import inspect

import pytest
from pydantic import ValidationError

from contracts.tools.rule_engine import CalculateEarnInput, CheckCapInput, CompareCardsInput
from rules.engine.engine import RuleEngine
from rules.evaluator.validity import current_month
from tools.registry import execute, validate_args

INPUTS = (CalculateEarnInput, CheckCapInput, CompareCardsInput)

# Minimal valid args per tool, month deliberately omitted.
MONTHLESS = {
    "CalculateEarn": {"card_key": "hdfc_infinia", "amount": 50000, "category": "flights"},
    "CheckCap": {"card_key": "hdfc_infinia", "cap_scope": "smartbuy"},
    "CompareCards": {"cards": ["hdfc_infinia"], "amount": 50000, "category": "flights"},
}


@pytest.mark.parametrize("tool,args", MONTHLESS.items())
def test_plan_validation_accepts_an_invocation_with_no_month(tool, args):
    """The exact failure: a monthless invocation used to be rejected here, so
    the tool never ran. This is the assertion that closes item 24."""
    validate_args(tool, args)  # must not raise


@pytest.mark.parametrize("model", INPUTS)
def test_absent_month_is_none_on_the_dto(model):
    field = model.model_fields["month"]
    assert field.default is None
    assert not field.is_required()


@pytest.mark.parametrize("model", INPUTS)
@pytest.mark.parametrize("bad", ["2026-7", "26-07", "July 2026", "2026/07", ""])
def test_a_malformed_month_is_still_rejected(model, bad):
    """Absent and malformed are different states. Making the field optional
    must not smuggle a bad value through — the pattern still applies whenever a
    month is actually supplied."""
    args = {**MONTHLESS[model.__name__.replace("Input", "")], "month": bad}
    with pytest.raises(ValidationError):
        model(**args)


@pytest.mark.parametrize("tool,args", MONTHLESS.items())
def test_the_resolved_month_is_the_current_month(tool, args):
    """Absent must mean *now*, not the epoch. Asserted through the tool layer,
    where the resolution actually happens."""
    result = execute(tool, args)
    assert result.status == "success", result.error
    payload = result.result
    months = (
        [entry["month"] for entry in payload["results"]]
        if tool == "CompareCards"
        else [payload["month"]]
    )
    assert months and all(month == current_month() for month in months)


@pytest.mark.parametrize("tool,args", MONTHLESS.items())
def test_a_monthless_comparison_still_computes(tool, args):
    """The user-visible symptom of item 24 was an answer with no numbers in it.
    A verified P1 card must compute without being told a month."""
    payload = execute(tool, args).result
    if tool == "CompareCards":
        assert any(entry["status"] == "computed" for entry in payload["results"])
    elif tool == "CalculateEarn":
        assert payload["status"] == "computed"


def test_engine_compare_cards_has_no_month_default():
    """Locks the trap closed. `month` defaulted to "1970-01", which predates
    every `valid_from` in every rule file — so since ADR-012 any caller that
    omitted it got base earn everywhere, silently and plausibly. The fix must
    not re-arm it, and neither may a future one."""
    month = inspect.signature(RuleEngine.compare_cards).parameters["month"]
    assert month.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        RuleEngine().compare_cards(["hdfc_infinia"], 50000, "flights", None)


def test_no_engine_entry_point_defaults_the_month():
    """The same check across the whole engine surface, so the trap cannot
    reappear on a sibling method instead."""
    for name in ("calculate_earn", "check_cap", "compare_cards"):
        month = inspect.signature(getattr(RuleEngine, name)).parameters["month"]
        assert month.default is inspect.Parameter.empty, f"{name} defaults month"
