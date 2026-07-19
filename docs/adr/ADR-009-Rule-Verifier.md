# ADR-009: Manual Approval for Rule Verification

## Status

Accepted (Fast-follow)

## Context

Reward programs change frequently through issuer websites and updated terms and conditions.

The Knowledge Pipeline detects document changes, but detecting that a document changed is different from determining whether business rules changed.

Automatic extraction from issuer documents is unreliable because:

- document formats differ across issuers
- information is often embedded in legal prose
- tables and PDFs vary significantly
- important changes may appear only in amended clauses

Applying extracted values directly to production rule files introduces an unacceptable risk of incorrect recommendations.

## Decision

The MVP uses a manual verification workflow. The system:

1. Detects changed issuer documents.
2. Extracts candidate values.
3. Compares against existing rule files.
4. Generates a verification record.
5. Requires explicit human approval.
6. Updates rule files only after approval.
7. Re-runs rule and graph evaluations.

The system never modifies production rule files automatically.

The Rule Verifier is a subsystem of the Knowledge Platform, not the Rule Engine.

```
Knowledge Platform
    │
    ├── Crawler
    ├── Parser
    ├── Extractor
    ├── Rule Verifier
    └── Retrieval
                │
                ▼
        rules/seed/
                │
                ▼
        Rule Engine
```

The Rule Engine consumes verified rules. It is never responsible for deciding whether a rule has changed.

## Consequences

Advantages

- Prevents accidental rule corruption.
- Preserves trust.
- Supports full source traceability.
- Aligns with the no-fabrication principle.

Trade-offs

- Manual verification effort.
- Slower propagation of issuer changes.

This trade-off is acceptable for the MVP.

## Future Work

Introduce a Rule Verifier service that automates:

- field extraction
- structured diff generation
- confidence scoring
- verification queue generation

Manual approval remains mandatory regardless of extraction automation.
