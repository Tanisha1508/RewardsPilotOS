"""Knowledge-focused agent behavior: metadata filter inference for hybrid
retrieval (BUILD_SPEC §6 step 3 — issuer/program/doc_type inferred from the
query by the Planner)."""

_ISSUER_HINTS = {
    "hdfc": "hdfc",
    "infinia": "hdfc",
    "axis": "axis",
    "atlas": "axis",
    "amex": "amex",
    "american express": "amex",
    "demo bank": "demo_bank",
    "voyager": "demo_bank",
    "sample bank": "sample_bank",
    "trailblazer": "sample_bank",
}

_DOC_TYPE_HINTS = {
    "transfer": "transfer_rules",
    "partner": "transfer_rules",
    "promotion": "promotions",
    "offer": "promotions",
    "bonus": "promotions",
    "lounge": "benefit_guides",
    "benefit": "benefit_guides",
    "expiry": "issuer_policies",
    "expire": "issuer_policies",
    "policy": "issuer_policies",
}


def infer_filters(query: str) -> dict[str, str]:
    lowered = query.lower()
    filters: dict[str, str] = {}
    for hint, issuer in _ISSUER_HINTS.items():
        if hint in lowered:
            filters["issuer"] = issuer
            break
    for hint, doc_type in _DOC_TYPE_HINTS.items():
        if hint in lowered:
            filters["doc_type"] = doc_type
            break
    return filters
