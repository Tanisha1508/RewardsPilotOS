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

// The cards that exist in the engine but cannot yet be added.
//
// Each one has a rule file whose earn rate is `unverified`, which means the
// engine refuses to compute with it and every answer about it comes back
// "unknown" — correct, and useless to the person who holds it. Until 2026-08-03
// they could be added anyway, as free text, and the result was a card that
// tracked perfectly and silently answered nothing.
//
// They are shown rather than hidden, and shown by name. An empty product looks
// small; a product that names seven cards and says which are ready looks like
// what it is, which is a verification queue moving in a known order. The order
// here is the queue's own order (docs/VERIFICATION_QUEUE.md).
//
// This list must stay the exact complement of KNOWN_CARDS —
// `tests/rules/test_frontend_card_catalog_matches.py` asserts every rule file is
// in one list or the other, and that nothing verified is still sitting here. A
// card that graduates moves up, and the test fails until it does.
export const PENDING_CARDS = [
  { label: "HDFC Diners Club Black", card_key: "hdfc_diners_black" },
  { label: "HDFC Regalia", card_key: "hdfc_regalia" },
  { label: "Amex Platinum Reserve", card_key: "amex_plat_reserve" },
  { label: "Amex Membership Rewards Credit Card", card_key: "amex_membership_rewards" },
  { label: "Amex SmartEarn", card_key: "amex_smartearn" },
  { label: "Axis Ace", card_key: "axis_ace" },
  { label: "Axis Magnus", card_key: "axis_magnus" },
] as const;
