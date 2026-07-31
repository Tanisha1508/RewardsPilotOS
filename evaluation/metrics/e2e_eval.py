"""End-to-end golden set runner (BUILD_SPEC §11).

Each query runs through the full LangGraph workflow. A deterministic eval LLM
plays the Planner (emitting the golden plan, still schema-validated by the
Planner node) and the Recommender (assembling contract-exact output from the
state digest, numbers verbatim). Checks per query:

- recommendation produced (contract-valid)
- citations present
- calculations verbatim from tool results (no invented values)
- numbers in prose traceable to tool outputs / retrieved content (string match)
- confidence reported
- unknowns stated plainly when expected
"""

import json
import re
from pathlib import Path

from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow
from knowledge.pipeline.ingest import ingest_sources
from knowledge.retrieval.hybrid import HybridRetriever
from knowledge.storage.collections import get_client
from tools.knowledge_search.service import set_retriever
from tools.memory.source import InMemoryMemorySource
from tools.memory.source import set_source as set_memory_source
from tools.portfolio.source import InMemoryPortfolioSource, acting_as, load_seed
from tools.portfolio.source import set_source as set_portfolio_source

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "recommendations.json"

_NUMBER_RE = re.compile(r"\d[\d,]{1,}(?:\.\d+)?")  # 2+ digit numbers in prose


class EvalLLM:
    """Deterministic LLM for eval runs: planner returns the golden plan;
    recommender assembles output obeying the hard rules."""

    def __init__(self, intent: str, plan: list[dict]) -> None:
        self._intent = intent
        self._plan = plan

    def complete(self, system: str, user: str) -> str:
        if "Planner prompt" in system:
            return json.dumps({"intent": self._intent, "plan": self._plan})
        state = json.loads(user.split("\n\nYour previous output was rejected")[0])
        calculations = list(state["rule_results"]) + list(state["graph_results"])
        citations = []
        seen = set()
        for chunk in state["knowledge"]:
            key = (chunk["metadata"]["source_url"], chunk["metadata"]["last_changed"])
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                {
                    "source_url": key[0],
                    "last_changed": key[1],
                    "doc_id": chunk["metadata"]["doc_id"],
                }
            )
        # Calibration comes from the deterministic basis in the state digest
        # (agents.recommendation.calibration) — the same ceiling a real LLM is
        # held to, so the eval cannot pass with a confidence the evidence does
        # not support.
        basis = state["confidence_basis"]
        level, reason = basis["ceiling"], basis["reason"]
        unknowns = [
            entry
            for entry in calculations
            if entry.get("status") == "unknown"
            or entry.get("unverified_paths_exist")
            or (entry.get("paths") == [] and entry.get("tool") == "BestTransferPaths")
        ]
        decision = "Deterministic tool results attached; see calculations."
        if unknowns:
            decision += (
                " Some required values are UNKNOWN pending issuer verification; "
                "the system refuses to guess (unknown over incorrect)."
            )
        # Engine-derived sentences the Recommender must reproduce verbatim.
        # Validation rejects output that drops them, so a double that omitted
        # them would fail every query that triggers one — measuring the double,
        # not the system.
        #
        # Taken from `_required_statements`, the same function the validator
        # checks against, rather than a list repeated here. This used to name
        # `expiry_note` and `channel_note` explicitly and fell behind on
        # 2026-07-31 when B2 added `category_note`: e02 ("which card for a
        # 70,000 INR laptop?") started failing, because "electronics" is in no
        # rule file and the new note fired. End-to-end dropped 100% -> 90% and
        # the system was fine — the double had gone stale. Deriving the list
        # means it cannot happen again.
        from agents.recommendation.margin import margin_caveat
        from agents.recommendation.recommender import _required_statements

        notes = _required_statements(margin_caveat(state["rule_results"]), state["rule_results"])
        return json.dumps(
            {
                "decision": decision,
                "reasoning": [
                    "Numbers are copied verbatim from rule_results and graph_results.",
                    "Citations carry source URLs and freshness timestamps from retrieval.",
                    *notes,
                ],
                "calculations": calculations,
                "citations": citations,
                "confidence": {"level": level, "reason": reason},
                "assumptions": ["Fixture data is current as of its recorded timestamps."],
                "alternatives": [],
            }
        )


def _numbers_traceable(recommendation: dict, state: dict) -> bool:
    allowed_text = json.dumps(
        {
            "rule_results": state["rule_results"],
            "graph_results": state["graph_results"],
            "portfolio": state["portfolio"],
            "memory": state["memory"],
            "knowledge": [
                c.model_dump() if hasattr(c, "model_dump") else c for c in state["knowledge"]
            ],
        },
        default=str,
    )
    prose = " ".join(
        [recommendation["decision"]]
        + recommendation["reasoning"]
        + recommendation["assumptions"]
        + recommendation["alternatives"]
    )
    for token in _NUMBER_RE.findall(prose):
        if token.replace(",", "") not in allowed_text and token not in allowed_text:
            return False
    return True


def _install_benchmark_corpus() -> None:
    """Point retrieval at a corpus that includes the fixture issuers.

    The golden set is written against them — "any transfer bonuses right now?"
    and "when do my points expire?" have answers only in the fixture
    `promotions` and `issuer_policies` documents. Those left the serving corpus
    on 2026-07-31 (KNOWN_LIMITATIONS 35) so an invented issuer can never be
    cited to a real user, and these two queries went from answerable to
    uncitable overnight. The pipeline did not change; its corpus did.

    Consistent with how this eval already injects `InMemoryPortfolioSource` and
    `InMemoryMemorySource`: a benchmark supplies its own controlled inputs.
    Isolated in a temp directory so it cannot write invented issuers into the
    index that serves users.
    """
    import tempfile
    from pathlib import Path as _Path

    client = get_client(_Path(tempfile.mkdtemp(prefix="e2e-eval-")))
    ingest_sources(client, include_fixtures=True)
    set_retriever(HybridRetriever(client))


def run() -> dict:
    # The golden set is defined against the demo portfolio, so the eval installs
    # it explicitly. Since D2 the portfolio and memory tools read Postgres by
    # default with no fixture fallback, and an eval that quietly scored against
    # whatever happened to be in a database would not be a golden set at all.
    _install_benchmark_corpus()
    seed = load_seed()
    set_portfolio_source(InMemoryPortfolioSource(seed))
    set_memory_source(InMemoryMemorySource(seed))
    try:
        with acting_as(seed["user_id"]):
            return _run_queries(seed["user_id"])
    finally:
        set_portfolio_source(None)
        set_memory_source(None)


def _run_queries(user_id: str) -> dict:
    dataset = json.loads(DATASET.read_text())
    per_query = []
    for item in dataset["queries"]:
        workflow = build_workflow(EvalLLM(item["intent"], item["plan"]))
        final = workflow.invoke(initial_state(item["query"], user_id))
        recommendation = final["recommendation"]
        checks = {"recommendation_produced": recommendation is not None}
        if recommendation is not None:
            allowed = final["rule_results"] + final["graph_results"]
            checks["citations_present"] = len(recommendation["citations"]) > 0
            checks["calculations_verbatim"] = all(
                entry in allowed for entry in recommendation["calculations"]
            )
            checks["numbers_traceable"] = _numbers_traceable(recommendation, final)
            checks["confidence_reported"] = recommendation["confidence"]["level"] in (
                "high",
                "medium",
                "low",
            ) and bool(recommendation["confidence"]["reason"])
            if item.get("expect_unknown"):
                checks["unknown_stated"] = "unknown" in recommendation["decision"].lower()
        per_query.append({"id": item["id"], "passed": all(checks.values()), "checks": checks})
    passed_count = sum(1 for q in per_query if q["passed"])
    return {
        "name": "end_to_end",
        "queries": len(per_query),
        "passed": passed_count,
        "pass_rate": round(passed_count / len(per_query), 4),
        "per_query": per_query,
    }
