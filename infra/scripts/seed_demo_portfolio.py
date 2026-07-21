"""Seed a demo user's portfolio via the CRUD API (D4, testing/demo only).

Additive — NOT a substitute for empty-portfolio handling, which stands on its
own. This gives a demo account the three verified P1 cards so `/chat` produces
real recommendations against a populated portfolio, matching the fixture_user
pattern used in tests.

It goes through the real HTTP endpoints (auth/sync → portfolio/cards →
portfolio/balances), so it exercises the same path a user would — not a
back-door DB insert. That means it needs a running backend and a demo user's
Supabase access token.

    BACKEND_URL=http://localhost:8000 \\
    DEMO_ACCESS_TOKEN=<supabase access token for the demo account> \\
        .venv/bin/python -m infra.scripts.seed_demo_portfolio

Card figures are the verified P1 values (see rules/seed and knowledge/sources);
balances are illustrative demo amounts and labelled as such. Reward currencies
match the graph node ids so transfer paths resolve.
"""

import json
import os
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# The three verified P1 cards. reward_currency must match a graph node id.
CARDS = [
    {
        "issuer": "hdfc",
        "card_name": "HDFC Infinia",
        "network": "visa",
        "reward_currency": "hdfc_reward_points",
        "annual_fee": 12500.0,  # + GST, verified (HDFC official fees page)
        "renewal_date": "2026-11-01",
        "_demo_balance": 48000,
    },
    {
        "issuer": "axis",
        "card_name": "Axis Bank Atlas",
        "network": "visa",
        "reward_currency": "edge_miles",
        "annual_fee": 5000.0,  # + GST, verified (Axis official)
        "renewal_date": "2027-03-20",
        "_demo_balance": 15000,
    },
    {
        "issuer": "amex",
        "card_name": "Amex Platinum Travel",
        "network": "amex",
        "reward_currency": "amex_membership_rewards",
        "annual_fee": 5000.0,  # + GST, verified (Amex official)
        "renewal_date": "2027-01-10",
        "_demo_balance": 20000,
    },
]


def _call(method: str, path: str, token: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{method} {path} -> HTTP {exc.code}: {exc.read().decode()[:300]}")


def main() -> None:
    token = os.environ.get("DEMO_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "DEMO_ACCESS_TOKEN is not set. Sign in the demo account against "
            "Supabase, then pass its access token (see module docstring)."
        )

    _call("POST", "/api/v1/auth/sync", token, {"name": "Demo User"})
    print("synced demo user")

    for card in CARDS:
        payload = {k: v for k, v in card.items() if not k.startswith("_")}
        created = _call("POST", "/api/v1/portfolio/cards", token, payload)["data"]
        card_id = created["card_id"]
        _call(
            "PUT",
            f"/api/v1/portfolio/balances/{card_id}",
            token,
            {
                "reward_currency": card["reward_currency"],
                "current_balance": card["_demo_balance"],
            },
        )
        print(f"  added {card['card_name']} ({card['reward_currency']}), balance {card['_demo_balance']}")

    cards = _call("GET", "/api/v1/portfolio/cards", token)["data"]
    print(f"done — demo portfolio now has {len(cards)} cards")


if __name__ == "__main__":
    main()
