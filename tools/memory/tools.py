"""Memory tools: RecallMemory, StorePreference (fixture-backed in-memory
stores for the sprint; D2 wires preferences/interaction_events tables)."""

from contracts.tools.memory import (
    EpisodicEvent,
    RecallMemoryInput,
    RecallMemoryOutput,
    StorePreferenceInput,
    StorePreferenceOutput,
)

_PREFERENCES: dict[str, dict[str, str]] = {
    "fixture_user": {
        "preferred_airline_program": "skyhigh_airways",
        "home_airport": "DEL",
        "redemption_strategy": "maximize_transfer_ratio",
    }
}

_EPISODIC: dict[str, list[EpisodicEvent]] = {
    "fixture_user": [
        EpisodicEvent(
            event_id="event_1",
            event_type="recommendation_accepted",
            payload={"summary": "transferred voyager_points to skyhigh_airways"},
            created_at="2026-06-20T10:00:00Z",
        ),
        EpisodicEvent(
            event_id="event_2",
            event_type="search",
            payload={"query": "best card for flights"},
            created_at="2026-07-01T18:30:00Z",
        ),
    ]
}


def recall_memory(args: RecallMemoryInput) -> RecallMemoryOutput:
    events = _EPISODIC.get(args.user_id, [])
    return RecallMemoryOutput(
        preferences=_PREFERENCES.get(args.user_id, {}),
        episodic=sorted(events, key=lambda e: e.created_at, reverse=True)[: args.limit],
    )


def store_preference(args: StorePreferenceInput) -> StorePreferenceOutput:
    _PREFERENCES.setdefault(args.user_id, {})[args.key] = args.value
    return StorePreferenceOutput(stored=True, key=args.key, value=args.value)
