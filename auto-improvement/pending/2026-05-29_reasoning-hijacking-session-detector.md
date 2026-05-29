# Pending: Reasoning Hijacking / JailAgent Session-Level Detector

## Title
Session-level detector for reasoning hijacking and memory manipulation in LLM agents (JailAgent pattern)

## Motivation
JailAgent (arxiv:2604.05549, Apr 2026) bypasses LLM agent safety by avoiding prompt modification
entirely. Instead, it implicitly manipulates the agent's memory retrieval and reasoning trajectory
across multiple turns via "Trigger Extraction, Reasoning Hijacking, and Constraint Tightening."
The attack is cross-model and cross-scenario, demonstrating strong performance against major
commercial LLMs, but it requires multi-turn conversation access and agent memory manipulation —
neither of which is observable from a single-turn text filter.

## Research finding that led to this idea
- arxiv:2604.05549 (Apr 2026): JailAgent achieves outstanding cross-model performance by avoiding
  user-prompt modification entirely, targeting agent reasoning and memory instead.
- arxiv:2603.10091 (Mar 2026): Confirms that reasoning-layer attacks are a growing vector against
  thinking-mode LLMs and agents.

## Proposed change
Add a session-level anomaly detector in `aigis/cross_session/` (the module already exists) that
tracks per-session conversation statistics:
1. Unusual escalation in instruction-override language across turns ("earlier you said", "your
   real goal is", "as we established").
2. Memory-reference injections that reference facts never established in the visible context.
3. Reasoning-constraint-tightening patterns ("you must now only answer with", "from now on your
   only constraint is").
Flag sessions exhibiting 2+ of these signals within a 5-turn window.

## Why it was held back
- Requires per-session state tracking — the current single-turn filter API has no session
  concept. `aigis/cross_session/` exists but is experimental.
- Multi-turn behavioral detection cannot be encoded as a single stateless regex pass.
- "Any breaking public API change" and ">100 LOC" constraints: a proper session anomaly
  detector would require a new stateful API surface and a session-state storage model.

## Which constraint blocked it
- Multi-turn / stateful detection is fundamentally outside the scope of the current single-turn
  input/output filter architecture.

## Suggested next step for human reviewer
Extend `aigis/cross_session/` with a `SessionAnomalyTracker` class that holds a rolling 10-turn
window of message features. Implement 3 heuristics: instruction-escalation counter, memory-ref
anomaly counter, and constraint-tightening counter. Add a `session.check(messages) -> AnomalyResult`
API as an opt-in complement to the existing `filter_input/filter_output` calls.
