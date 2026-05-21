# Pending: Multi-Turn Escalation Correlator Rule

## Title
Cross-turn Crescendo/AutoAdv escalation detection for the session correlator

## Motivation
The Crescendo attack (USENIX Security 2025, arxiv:2404.01833) starts with benign prompts and
gradually escalates over multiple turns to elicit harmful outputs. The automated variant
(Crescendomation) achieves 29–61% higher success rates than single-turn attacks on GPT-4 and
49–71% on Gemini-Pro. AutoAdv (arxiv:2511.02376) achieves 95% ASR on Llama-3.1-8B within six
turns using adaptive pattern learning. Both attacks are completely invisible to single-turn
input filters.

## Research finding that led to this idea
Research file: `research/2026-05-21T06-14_3-jailbreak-extraction.md`
Findings: "Crescendo Multi-Turn Escalation" and "AutoAdv"

## Proposed change
Extend `aigis/cross_session/correlator.py` (or the session-level behavioral monitor) with a
Crescendo-detection heuristic:

1. Track topic-drift score across turns within a session: measure how much each prompt
   "drifts" toward more sensitive topics using a keyword-density distance metric.
2. Flag when drift is monotonically increasing over ≥3 consecutive turns AND the final turn
   hits a high-risk keyword cluster.
3. Expose a `crescendo_risk_score` field on the session-level `ScanResult`.

## Why it was held back
Requires changes to the session correlator (multi-file) and a new data structure for per-turn
topic-drift tracking. Total diff would exceed 100 LOC. Also requires the session correlator to
be stateful across turns, which changes the existing API surface.

## Constraint blocking it
- Exceeds 100 LOC across non-test files.
- Potentially breaking change to `CrossSessionCorrelator` public API.
- Needs design review before implementation.

## Suggested next step for human reviewer
Design a small, additive interface: a `CrossSessionCorrelator.record_turn()` method that
accepts a text and updates internal state, with `crescendo_score()` returning the current
escalation signal. Keep the drift metric simple (e.g., Jaccard distance of last-N-turn keyword
sets against a sensitive-topic vocabulary). Once the interface is stable, implementation should
fit in one cycle (< 100 LOC).
