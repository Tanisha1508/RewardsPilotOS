// Turning system identifiers into words a cardholder recognises.
//
// The UI was rendering raw values straight from the API: a balance labelled
// `edge_miles`, and a "last updated" reading
// `2026-07-28T19:14:36.719858+00:00`. Both are correct and neither is readable.
//
// Deliberately NOT a general prettifier. Splitting on underscores and
// title-casing would turn `edge_miles` into "Edge Miles", which is wrong — the
// programme is "Axis EDGE Miles". These are proper nouns, so they are looked up,
// never derived.

/** Currency id -> the programme's own name.
 *
 *  Mirrors the `currency` nodes in `database/seed/graph_nodes.json`, per the
 *  project's no-codegen convention for cross-boundary names.
 *  `tests/rules/test_frontend_card_catalog_matches.py` asserts these stay in
 *  step, so a renamed node fails a test rather than silently showing the old
 *  label. Synthetic fixture currencies are intentionally absent: they should
 *  never reach a real user's screen, and if one does, showing the raw id makes
 *  that obvious instead of dressing it up. */
const CURRENCY_LABELS: Record<string, string> = {
  hdfc_reward_points: "HDFC Reward Points",
  edge_miles: "Axis EDGE Miles",
  membership_rewards: "Amex Membership Rewards",
};

/** The programme name, or the raw id when we have no name for it.
 *
 *  Falling back to the id is the honest option: an unrecognised currency is
 *  usually a mis-linked card (see KNOWN_LIMITATIONS 31), and inventing a
 *  friendly label would hide exactly the case worth noticing. */
export function currencyLabel(currency: string): string {
  return CURRENCY_LABELS[currency] ?? currency;
}

/** The same names, applied to a sentence rather than a field.
 *
 *  A recommendation's prose is written around the engine's own vocabulary, so
 *  an answer reads "earning 1,665 hdfc_reward_points" — the identifier leaking
 *  into a sentence a person is meant to read. Seen live on 2026-08-03.
 *
 *  The model is not told to translate it. Naming a currency is a lookup, and
 *  asking a model to perform a lookup it can get subtly wrong ("HDFC Rewards
 *  Points") is how the citation bug happened: derivation is where things drift.
 *  The table beside the prose already resolves ids this way; this gives the
 *  sentence the same treatment.
 *
 *  Unknown ids are deliberately left raw, exactly as `currencyLabel` leaves
 *  them — an id nobody has named is usually a mis-linked card, and it should
 *  look wrong rather than be smoothed over. */
export function nameCurrencies(text: string): string {
  return Object.entries(CURRENCY_LABELS).reduce(
    (out, [id, label]) => out.split(id).join(label),
    text
  );
}

/** A timestamp a person can read, in their own locale.
 *
 *  Balances are user-entered and go stale, so how old the number is forms part
 *  of the answer (KNOWN_LIMITATIONS 1) — which only works if the date is
 *  legible. Absolute rather than "2 days ago": staleness is the point, and a
 *  relative label rounds away the thing being communicated.
 *
 *  Returns the input unchanged if it will not parse, rather than "Invalid Date". */
export function formatDateTime(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.valueOf())) return iso;
  return parsed.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

/** Date only — for renewal dates and other day-granularity fields, where a time
 *  would imply precision the value does not have. */
export function formatDate(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.valueOf())) return iso;
  return parsed.toLocaleDateString(undefined, { dateStyle: "medium" });
}
