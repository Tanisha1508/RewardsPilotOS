// Cards the Rule Engine can actually compute for.
//
// Mirrors `rules/parser/catalog.py` and the `reward_currency` each rule file
// declares, hand-written per the project's no-codegen convention for
// cross-boundary names.
// `tests/rules/test_frontend_card_catalog_matches.py` reads this file and
// asserts every entry still resolves to a card_key AND names a `currency` graph
// node — so a rename fails a test instead of silently producing cards the engine
// cannot reason about.
//
// Shared by the setup flow and Portfolio's quick-add. Two copies would let the
// two disagree, and the failure would be invisible: a card added during
// onboarding that quietly computes nothing.
//
// The point is not convenience. Both `reward_currency` (which must match a
// transfer-graph currency node) and `(issuer, card_name)` (which must match the
// catalogue) were free text, and one typo produced a card that tracked fine and
// silently computed nothing. It also caused a real bug: the seed script used
// `amex_membership_rewards`, a *card* node, so Amex transfers returned no paths
// (KNOWN_LIMITATIONS 31).
export const KNOWN_CARDS = [
  {
    label: "HDFC Infinia",
    issuer: "hdfc",
    card_name: "HDFC Infinia",
    network: "visa",
    reward_currency: "hdfc_reward_points",
    blurb: "Reward Points · SmartBuy bonuses",
  },
  {
    label: "Axis Bank Atlas",
    issuer: "axis",
    card_name: "Axis Bank Atlas",
    network: "visa",
    reward_currency: "edge_miles",
    blurb: "EDGE Miles · 5× on travel",
  },
  {
    label: "Amex Platinum Travel",
    issuer: "amex",
    card_name: "Amex Platinum Travel",
    network: "amex",
    reward_currency: "membership_rewards",
    blurb: "Membership Rewards",
  },
] as const;
