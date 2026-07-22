"""Opportunity Engine tool: GetOpportunities (fixture notifications for the
sprint; D5 wires monitor.py change records into the notifications table)."""

from tools.portfolio.source import current_user
from contracts.tools.opportunity import (
    GetOpportunitiesInput,
    GetOpportunitiesOutput,
    Opportunity,
)

_FIXTURE_OPPORTUNITIES = [
    Opportunity(
        notif_id="notif_1",
        type="promotion",
        title="Skyhigh transfer bonus July 2026 (SYNTHETIC FIXTURE)",
        body=(
            "Voyager Points transfers to Skyhigh Airways earn a 25 percent bonus "
            "until July 31 2026, capped at 50000 transferred points."
        ),
        source_change_id="change_demo_promo_1",
        source_url="https://example.test/demo-bank/voyager/promotions",
        created_at="2026-07-10T08:00:00Z",
    ),
    Opportunity(
        notif_id="notif_2",
        type="expiry",
        title="Voyager Points expiring window (SYNTHETIC FIXTURE)",
        body="32000 Voyager Points expire on 2028-06-30 per the fixture balance.",
        source_change_id=None,
        source_url="https://example.test/demo-bank/policies",
        created_at="2026-07-12T08:00:00Z",
    ),
]


def get_opportunities(args: GetOpportunitiesInput) -> GetOpportunitiesOutput:
    # Identity comes from the ambient context, never from model output
    # (KNOWN_LIMITATIONS 24, Class C). The fixture set is not yet
    # user-scoped, so the resolved id is unused here — but the call still
    # runs, so a missing caller fails loudly now rather than at D5 when
    # real per-user notifications land.
    current_user()
    return GetOpportunitiesOutput(opportunities=_FIXTURE_OPPORTUNITIES[: args.limit])
