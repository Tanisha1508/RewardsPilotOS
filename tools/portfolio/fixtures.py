"""Fixture portfolio data for the sprint milestone (BUILD_SPEC §14).

The fixture user holds the synthetic Demo Bank Voyager (verified fixture
values available) alongside real cards whose numbers are pending verification
— so end-to-end flows exercise both computed and unknown paths. D2 replaces
this module with Postgres queries behind the same tool contracts."""

from contracts.tools.portfolio import Card, RewardBalance, TravelGoal

FIXTURE_USER_ID = "fixture_user"

CARDS = [
    Card(
        card_id="card_demo_voyager",
        issuer="demo_bank",
        card_name="Demo Bank Voyager (SYNTHETIC FIXTURE)",
        network="visa",
        reward_currency="voyager_points",
        annual_fee=10000.0,
        renewal_date="2027-01-15",
    ),
    Card(
        card_id="card_hdfc_infinia",
        issuer="hdfc",
        card_name="HDFC Infinia",
        network="visa",
        reward_currency="hdfc_reward_points",
        annual_fee=12500.0,  # + GST; verified 2026-07-19 (HDFC official fees page)
        renewal_date="2026-11-01",
    ),
    Card(
        card_id="card_axis_atlas",
        issuer="axis",
        card_name="Axis Bank Atlas",
        network="visa",
        reward_currency="edge_miles",
        annual_fee=5000.0,  # + GST; verified 2026-07-19 (official source)
        renewal_date="2027-03-20",
    ),
]

BALANCES = [
    RewardBalance(
        card_id="card_demo_voyager",
        reward_currency="voyager_points",
        current_balance=32000,
        expiry_date="2028-06-30",
        last_updated="2026-07-15",
    ),
    RewardBalance(
        card_id="card_hdfc_infinia",
        reward_currency="hdfc_reward_points",
        current_balance=48000,
        expiry_date=None,
        last_updated="2026-07-10",
    ),
    RewardBalance(
        card_id="card_axis_atlas",
        reward_currency="edge_miles",
        current_balance=15000,
        expiry_date=None,
        last_updated="2026-07-01",
    ),
]

GOALS = [
    TravelGoal(
        goal_id="goal_skyhigh_trip",
        goal_type="trip",
        description="Award flight on Skyhigh Airways (synthetic fixture goal)",
        target_date="2027-03-01",
        target_program="skyhigh_airways",
        required_points=10000,
    )
]
