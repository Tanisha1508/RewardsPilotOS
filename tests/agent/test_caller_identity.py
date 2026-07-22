"""Caller identity is never an LLM-suppliable argument (KNOWN_LIMITATIONS 24,
Class C).

`user_id` used to be a required field on seven tool input contracts, so the
identity those tools read was whatever the model put in the plan — even though
the authenticated value was already in context, and
`tools/graph_engine/tools.py` had always resolved it correctly from
`current_user()`.

The field is *removed*, not ignored-if-present, and these tests hold that line
from both directions: the schema no longer accepts it, and the tools resolve
the ambient user instead. Same "cannot be re-armed" pattern as
`tests/rules/test_month_defaulting.py` — an argument that still exists is an
argument something can still rely on.
"""

import pytest

from contracts.tools.memory import RecallMemoryInput, StorePreferenceInput
from contracts.tools.opportunity import GetOpportunitiesInput
from contracts.tools.portfolio import UserScopedInput
from tools.portfolio.source import UnknownUserError, _current_user, acting_as
from tools.registry import REGISTRY, execute, validate_args

# The seven tools that used to take a user_id.
AFFECTED = (
    "GetPortfolio",
    "GetCards",
    "GetRewardBalances",
    "GetTravelGoals",
    "RecallMemory",
    "StorePreference",
    "GetOpportunities",
)

INPUT_MODELS = (
    UserScopedInput,
    RecallMemoryInput,
    StorePreferenceInput,
    GetOpportunitiesInput,
)

# Minimal valid args now that user_id is gone.
MINIMAL = {
    "GetPortfolio": {},
    "GetCards": {},
    "GetRewardBalances": {},
    "GetTravelGoals": {},
    "RecallMemory": {"intent": "spend", "query": "cards"},
    "StorePreference": {"key": "home_airport", "value": "DEL"},
    "GetOpportunities": {},
}


@pytest.mark.parametrize("model", INPUT_MODELS)
def test_user_id_is_gone_from_the_input_contract(model):
    """Not merely unused — absent. This is the assertion that stops it being
    quietly reintroduced as an optional field later."""
    assert "user_id" not in model.model_fields


@pytest.mark.parametrize("tool", AFFECTED)
def test_the_registry_schema_advertises_no_user_id(tool):
    """The Planner prompt's tool catalogue is generated from these schemas, so
    this is also what stops the model being *told* to supply one."""
    properties = REGISTRY[tool].input_model.model_json_schema().get("properties", {})
    assert "user_id" not in properties


@pytest.mark.parametrize("tool", AFFECTED)
def test_a_plan_supplying_user_id_does_not_get_it_honoured(tool):
    """A model that emits `user_id` anyway must not be able to steer the read.

    Pydantic ignores unknown fields rather than rejecting them, so validation
    still passes — the point is that the value cannot reach the source. The
    schema test above is what keeps it out of the prompt in the first place;
    this is the belt to that braces.
    """
    args = {**MINIMAL[tool], "user_id": "somebody-else"}
    validated = validate_args(tool, args)
    assert not hasattr(validated, "user_id")


@pytest.mark.parametrize("tool", AFFECTED)
def test_tools_run_on_the_ambient_user(tool):
    """The session-wide `acting_as` from tests/conftest.py is the caller, and
    every affected tool resolves it without being told."""
    result = execute(tool, MINIMAL[tool])
    assert result.status == "success", result.error


def test_the_ambient_user_is_what_reaches_the_source():
    """The identity the source is queried with must be the *context's*, and it
    must follow the context when it changes.

    Asserted with a spy rather than by comparing returned data: the in-memory
    fake serves one seeded portfolio and ignores the user it is handed, so a
    data-level assertion here would pass no matter which id was used and prove
    nothing. The genuine cross-user isolation proof is
    `tests/integration/test_tool_sources.py::test_uuid_users_are_isolated_from_each_other`,
    which runs against real Postgres.
    """
    from contracts.tools.portfolio import GetCardsOutput
    from tools.portfolio.source import get_source, set_source

    seen: list[str] = []

    class SpySource:
        def cards(self, user_id: str) -> GetCardsOutput:
            seen.append(user_id)
            return GetCardsOutput(cards=[])

    original = get_source()
    set_source(SpySource())
    try:
        with acting_as("user-a"):
            execute("GetCards", {})
        with acting_as("user-b"):
            execute("GetCards", {})
    finally:
        set_source(original)

    assert seen == ["user-a", "user-b"]


@pytest.mark.parametrize("tool", AFFECTED)
def test_no_caller_context_fails_loudly(tool):
    """With no ambient user there is nobody to read as. A tool that returned
    empty here would be indistinguishable from a real user holding nothing —
    the unknown/not-applicable collapse the project forbids."""
    token = _current_user.set(None)
    try:
        with pytest.raises(UnknownUserError):
            REGISTRY[tool].handler(REGISTRY[tool].input_model(**MINIMAL[tool]))
    finally:
        _current_user.reset(token)
