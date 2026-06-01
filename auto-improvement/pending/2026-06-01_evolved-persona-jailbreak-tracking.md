# Pending: Evolved Persona Jailbreak Multi-Turn Tracking

## Title
Detection of evolved persona jailbreaks via persona-consistency tracking across turns

## Motivation
Enhancing Jailbreak Attacks via Persona Prompts (arxiv:2507.22171, March 2026) shows that
evolved, semantically detailed personas reduce refusal rates by 50–70% across multiple LLMs and
boost ASR by 10–20% when combined with existing techniques. Unlike crude DAN-style "act as an
evil AI" attacks (covered by `jb_evil_roleplay`), evolved personas create coherent, detailed
characters whose stated history, role, and worldview organically justify unsafe outputs without
triggering explicit jailbreak keywords.

Example: a persona framed as "Dr. Elena Vasquez, a retired toxicologist who now runs an
underground chemistry forum" establishes detailed justification for harmful synthesis requests
across multiple turns.

## Proposed change
Track persona establishment across session turns. Flag when:
1. A detailed persona is established in turn N with specific profession + knowledge domain
2. Followed in turn N+1 by a request that would be harmful if answered literally

## Why it was held back
Multi-turn detection requires cross-turn state, which is not available to single-turn aigis
input filters. The cross-session correlator infrastructure (`aigis/cross_session/`) exists but
is designed for session-level correlation, not within-session turn-level persona tracking.

## Which constraint blocked it
Multi-turn / stateful detection not supported by the current single-turn filter architecture.
Extending it would require > 100 LOC changes across the correlator, session store, and filter
pipeline.

## Research finding
arxiv:2507.22171 (Persona Prompts, March 2026): https://arxiv.org/abs/2507.22171

## Suggested next step
Design a lightweight within-session persona tracker in `aigis/cross_session/` that records
persona-establishment signals from prior turns and exposes them as enrichment context to the
input filter on each new turn. This is a structured extension of the existing `CrossSessionCorrelator`.
