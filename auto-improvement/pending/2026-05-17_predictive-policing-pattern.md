# Pending: comp_predictive_policing_request pattern

**Date:** 2026-05-17
**Domain:** compliance-regulation (cycle 8)
**Research source:** research/2026-05-17T06-06_8-compliance-regulation.md

## Title

Detection pattern for requests to build AI-based predictive policing systems (EU AI Act Art. 5(1)(d))

## Motivation

EU AI Act Art. 5(1)(d) prohibits AI systems that assess or predict the risk of a person committing a criminal offence based solely on profiling or personality traits (not on objective, verifiable facts directly linked to criminal activity). This is prohibited since 2025-02-02, with fines of €35M or 7% of global turnover.

aigis currently covers Art. 5(1)(c) social scoring and Art. 5(1)(f) emotion recognition but not Art. 5(1)(d) predictive policing. A `comp_predictive_policing_request` pattern would complete coverage of the most enforcement-relevant Art. 5 prohibitions.

## Proposed Change

Add a `DetectionPattern` to `COMPLIANCE_TRANSPARENCY_PATTERNS` in `aigis/filters/patterns.py`:

```python
DetectionPattern(
    id="comp_predictive_policing_request",
    name="AI Predictive Policing / Crime Risk Profiling (Prohibited AI Practice)",
    category="compliance_violation",
    pattern=_p(
        r"(predict\s+(criminal|crime|recidivism|reoffend)\s+(risk|likelihood|probability)"
        r"|criminal\s+risk\s+(scoring|score|model|prediction|assessment)"
        r"|predict\s+who\s+will\s+commit\s+(a\s+)?(crime|offence|offense)"
        r"|assess\s+(criminal|recidivism)\s+(risk|likelihood)\s+from\s+(profile|personality|behavior|behaviour|trait)"
        r"|recidivism\s+(prediction|scoring|risk)\s+(model|system|engine|algorithm)"
        r"|pre.?crime\s+(detection|prediction|scoring|system))"
    ),
    base_score=70,
    ...
)
```

## Why It Was Held Back

The prohibition under Art. 5(1)(d) has a significant carve-out: AI that supports human assessment based on *objective and verifiable facts directly linked to criminal activity* is not prohibited. This means the pattern must be precise enough not to flag legitimate risk assessment tools (e.g. based on confirmed criminal history). The phrasing space for prohibited "profiling/personality-based" crime prediction versus legitimate "evidence-based" risk tools overlaps significantly in natural language, making a low-false-positive regex hard to write without user input on their specific context.

## Constraint Blocking It

- Risk of high false-positive rate: "criminal risk assessment" is used for both prohibited (profiling-only) and permitted (evidence-based) systems.
- The 100 LOC non-test limit is already consumed by the two patterns implemented this cycle.

## Suggested Next Step

In a future compliance-regulation cycle (index 8), research the specific phrasing used in EU AI Act enforcement guidance and NIST guidelines for predictive policing, and draft a pattern that keys on "based solely on profiling" or "personality characteristics" rather than on "criminal risk" generically. User-facing documentation could also note the permitted vs. prohibited boundary.
