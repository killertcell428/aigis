# Pending: Stateful Multi-Turn Injection Scoring

**Cycle:** 0 (prompt-injection second pass), 2026-05-09T18-17
**Research source:** AgentSentry (arxiv:2602.22724, Feb 2026)

## Motivation

AgentSentry models multi-turn indirect prompt injection as a "temporal causal takeover"
process: across multiple turns, attacker-controlled content accumulates in the agent state
and progressively displaces the user goal's causal influence. No single turn is clearly
malicious, but cumulatively the injection succeeds. AgentSentry's inference-time defence
reduces ASR by ~80 percentage points on multi-turn IPI benchmarks.

## Proposed Change

Add a turn-window scorer to `aigis/filters/` that tracks the last N turns of an
OpenAI-style messages array and computes a cumulative injection risk signal:
- Each user/assistant/tool turn is scanned for indirect injection patterns
- A sliding score accumulates across turns (decaying with age)
- If the rolling sum exceeds a threshold, emit a `multi_turn_ipi_escalation` finding

## Why Held Back

**Constraint: breaking abstraction / context state.** aigis's `Guard.check_messages()`
currently scans the whole messages array for patterns but does not maintain state across
*separate calls*. A multi-turn scorer either requires (a) maintaining external state
(per-session storage, introducing a required dependency or side-effect), or (b) accepting
the full conversation history on each call and scanning the window — which changes the
API contract.

Neither change is "the smallest possible diff". Option (b) could be done within the
stateless model but would substantially alter the messages-array scanning semantics
and risk regressions in multi-agent scanning.

## Suggested Next Step

Design a `Guard.check_conversation(messages, session_id=None)` method that accepts a
full conversation array and returns per-turn findings + a cross-turn escalation score.
Can reuse existing `INDIRECT_INJECTION_PATTERNS` scanning; the new addition is the
accumulation window. Keep `check_messages()` unchanged for backwards compat.
