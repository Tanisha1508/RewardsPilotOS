# Evaluation report

Measured eval results, run on 2026-07-20 against the sprint fixture corpus and seed data (synthetic fixtures clearly labeled; real-issuer numbers ship unverified and are expected to be refused). Product metrics in MASTER_SPEC are targets, not measurements.

| Suite | Size | Metric | Result | Target |
|---|---|---|---|---|
| Retrieval | 20 queries | precision@3 | 0.2833 | reported honestly |
| Retrieval | 20 queries | recall@5 | 1.0000 | reported honestly |
| Retrieval | 20 queries | MRR | 0.5200 | reported honestly |
| Rules | 25 scenarios | exact match | 100.00% (25/25) | 100% |
| Graph | 10 queries | exact match | 100.00% (10/10) | 100% |
| End-to-end | 10 queries | all checks pass | 100.00% (10/10) | 100% |

## End-to-end checks

Per query: recommendation produced (contract-valid), citations present,
calculations verbatim from tool results (no invented values), prose
numbers traceable to tool outputs (string match), confidence reported,
and unknowns stated plainly where expected.

## Failures

None.
