"""Opportunity Engine tool: GetOpportunities.

**Returns nothing, deliberately, until real opportunities are tracked
(2026-07-31).** Nothing populates the `notifications` table — the wiring sweep
confirmed it has no reader and no writer — so there is nothing true to return.

It used to return two hardcoded fixtures about an invented bank: a "Skyhigh
Airways 25 percent transfer bonus" and "32000 Voyager Points expiring", with
`example.test` source URLs. Both titles carried "(SYNTHETIC FIXTURE)", which was
the only thing standing between them and a real user, and titles are exactly
what a model paraphrases away.

Why that was worse than it looks. The planner prompt names this tool for
portfolio questions, so a real question could reach it. Its output lands in
`state["memory"]`, and `memory` is in **both** the digest sent to the model and
`_grounded_text` — the text the number-traceability check validates against. So
"25 percent" and "32000" would have been certified as traceable *because a tool
produced them*. The guard that exists to stop invented numbers would have
blessed these.

Returning an empty list is the honest answer and matches how `CheckCap` was
fixed: it reports "unknown" rather than reading an empty table as zero. An empty
result here says "nothing is being tracked", which is true. Fixtures that say
something false are worse than nothing, because nothing cannot be misquoted.

The fixtures are kept below, unreferenced by the serving path, as the shape D5
should produce when `monitor.py` change records reach the notifications table.
"""

from tools.portfolio.source import current_user
from contracts.tools.opportunity import (
    GetOpportunitiesInput,
    GetOpportunitiesOutput,
    Opportunity,
)

# NOT served. Retained as the expected shape for D5 — see the module docstring.
_EXAMPLE_SHAPE_FOR_D5 = [
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
    # Empty until something real populates it. See the module docstring: the
    # previous fixtures were invented, and `memory` feeds the traceability
    # check, so they would have been certified as sourced numbers.
    return GetOpportunitiesOutput(opportunities=[])
