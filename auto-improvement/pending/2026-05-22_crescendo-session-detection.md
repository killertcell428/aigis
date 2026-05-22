# Pending: Crescendo / iDecep Multi-Turn Session Heuristics

## Title
Session-level escalation detection for Crescendo and iDecep jailbreaks

## Motivation
Crescendo (Microsoft Research, arxiv:2404.01833, USENIX Security 2025) and iDecep
(arxiv:2604.24082, CMU, Apr 2026) are multi-turn jailbreak attacks that distribute harmful
intent across multiple benign-looking conversational steps. No single turn triggers
single-turn content classifiers. Crescendo achieved 82–94% ASR on major proprietary models;
an automated variant (Crescendomation) outperformed state-of-the-art alternatives by 29–71%.

The attack pattern:
1. Start with benign questions on a neutral topic.
2. Gradually escalate toward the harmful target, using the model's prior responses to justify
   each step.
3. Backtrack and adjust if the model refuses a step, retrying with slight modifications.
4. Eventually elicit the harmful content with no single message appearing overtly malicious.

## Which research finding led to this idea
`auto-improvement/research/2026-05-22T00-11_3-jailbreak-extraction.md` — Crescendo and
iDecep findings.

## Proposed change
Extend `aigis/cross_session/correlator.py` with a Crescendo heuristic:
- Track per-session topic drift: if the conversation topic shifts progressively toward
  high-risk categories (weapons, malware, drugs) across 3+ turns, flag the session.
- Track refusal-then-retry sequences: if the model output contains a refusal followed
  by a closely related user query within the same session, increment a suspicion counter.
- Emit a `session_escalation` event when the suspicion counter crosses a threshold.

## Why it was held back
The cross-session correlator (`aigis/cross_session/correlator.py`) exists but does not yet
have multi-turn topic drift logic. Implementing it requires:
- Access to conversation history (not available in single-turn mode)
- A topic classification step (would be LLM-based — violates zero-runtime-dependency rule,
  or keyword-based — which is inaccurate for gradual escalation)
- Session state management across turns

A keyword-only topic drift detector would have too many false positives in genuine
multi-topic conversations.

## Which constraint blocked it
"Do NOT add features that depend on calling an LLM at runtime" — keyword-only topic drift
is insufficient; LLM-based classification would violate this constraint.
"keep total non-test diff ≤ 100 LOC" — a robust session escalation detector would exceed
this limit.

## Suggested next step for human reviewer
1. Design a lightweight keyword-based topic-drift heuristic for the correlator using
   category word lists (already exist in patterns.py as regex alternations).
2. Prototype a turn-counter + category-score accumulator in `cross_session/correlator.py`.
3. Evaluate false-positive rate on a synthetic multi-turn conversation dataset.
4. Consider an opt-in flag (disabled by default) to avoid breaking existing session use cases.
