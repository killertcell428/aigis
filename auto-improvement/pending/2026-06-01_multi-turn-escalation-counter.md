# Pending: Multi-Turn Session Escalation Counter

## Title
Session-level escalation counter for Crescendo and MultiBreak-style repeated jailbreak attempts

## Motivation
Crescendo (Russinovich et al., USENIX Security 2025, arxiv:2404.01833) demonstrates that
multi-turn attacks achieve 56–82% ASR against GPT-4 and Gemini Flash by starting with benign
questions and escalating gradually. MultiBreak (arxiv:2605.12869, May 2026) quantifies safety
degradation: models that refuse turn 1 have up to 44.8% higher compliance probability by turn
4–6 when the attacker rephrases and persists. GPT-4.1-mini reached 80.4% ASR at 6 turns.

## Research finding that led here
- Crescendo: https://arxiv.org/abs/2404.01833
- MultiBreak benchmark: https://arxiv.org/html/2605.01687
- Safety degradation: https://arxiv.org/html/2605.12869v1

## Proposed change
Add an optional session-level escalation counter to the `Guard` class:
- Track count of blocked inputs within a session identifier (caller-supplied session token)
- After N consecutive blocked inputs (default: 3), reduce the block threshold by a configurable
  amount (e.g., -10 per block, capped at -30) so rephrased harmful requests are caught at
  lower base_score
- Expose as `Guard(session_escalation=True, escalation_window=3, escalation_decay_minutes=30)`
- Default: disabled (backward compatible)

## Why it was held back
Requires session-state infrastructure (dict or external store) in the `Guard` class, which
currently has zero instance state. The session store design is non-trivial for thread safety
and TTL management. Adding this without tests for concurrent sessions and memory bounds would
be risky.

## Constraint that blocked it
"Any single change touching > 100 LOC across non-test files" — the session-state infrastructure
would exceed 100 LOC in Guard + types + tests.

## Suggested next step for the human reviewer
Design the session-state store as a separate class (e.g., `SessionTracker`) in a new file,
then wire it into `Guard` as an optional dependency. This splits the 100-LOC budget across
two cycles. The first cycle implements `SessionTracker` with tests; the second wires it into
`Guard`.
