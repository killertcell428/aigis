# Pending: RTS Attack — Nested Scenario + Toxic Knowledge Injection

**Date:** 2026-05-26
**Cycle:** 4 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-26T06-17_3-jailbreak-extraction.md`

---

## Motivation

arxiv:2510.01223 (October 2025) documents the RTS (Semantically Relevant Nested Scenarios with
Targeted Toxic Knowledge) attack, achieving 96.15% ASR on GPT-4o and 96.69% average across 6
SOTA models. The attack embeds a fragment of the harmful answer as "background context" in a
plausible scenario, then asks the model to reason within the scenario — causing it to naturally
extend the pre-loaded toxic content. No overt harmful request phrase is present.

Partially-detectable signal:
```
(in (this|the|a) (scenario|situation|context|story)).{0,200}(now (explain|elaborate|continue|complete|describe))
```

## Why Held Back

**False positive risk:** "In this scenario, now explain how the character would respond" and
similar constructions are very common in legitimate reasoning, simulation, game design, and
roleplay-writing tasks. The partial pattern covers only a narrow slice of real RTS attacks.

## Which Constraint

The full RTS attack compresses semantic relevance across the entire prompt — not detectable
from a structural pattern alone. Would require semantic similarity scoring, which is outside
the zero-runtime-dependency constraint.

## Suggested Next Step

Document in the hardening guide as a known high-ASR attack class; recommend that operators
enable output scanning as a secondary defense layer. If a semantic similarity module is ever
added as an optional component, RTS would be a primary use case.
