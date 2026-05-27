# Pending: Multi-Turn Escalation Detection (Crescendo)

**Title:** Session-Level Escalation Scoring for Crescendo-Style Jailbreaks

**Motivation:**
The Crescendo multi-turn jailbreak (arxiv:2404.01833, USENIX Security 2025) achieves high
attack success rates by starting with benign questions and gradually escalating harmfulness
across turns, referencing the model's own prior replies to normalise each next step.
"Crescendomation" automates the technique and achieves near-100% ASR on tested models.
No single turn contains an overt jailbreak phrase; detection requires session-level state.

**Research finding that led to this idea:**
`auto-improvement/research/2026-05-27T09-18_3-jailbreak-extraction.md`
→ "Crescendo Multi-Turn LLM Jailbreak" finding

**Proposed change:**
Extend `aigis/cross_session/` (or `aigis/adversarial_loop.py`) with a session-level
escalation scorer that:
1. Tracks the cumulative risk score across turns in a conversation session
2. Applies a sliding-window harmfulness gradient: flags sessions where scores are rising
   across N consecutive turns even if each turn is individually below threshold
3. Integrates with `aigis.Guard` via an optional `session_context` parameter

**Why it was held back:**
- Touches `cross_session/` module and the `Guard` public API — this is an API change
- Total LOC change would likely exceed 100 LOC across non-test files
- Requires session state persistence design that could introduce required runtime deps
  (e.g. Redis, SQLite) depending on deployment model

**Which constraint blocked it:**
- Potential API change (public Guard interface)
- Likely > 100 LOC across non-test files
- Possible new runtime dependencies

**Suggested next step for the human reviewer:**
Design the session-state API as a purely optional, zero-dependency dict-based accumulator
that callers manage. Keep `Guard` API unchanged; add `SessionTracker` as a separate
composable helper. This would stay within scope for a future cycle's ≤100 LOC constraint.
