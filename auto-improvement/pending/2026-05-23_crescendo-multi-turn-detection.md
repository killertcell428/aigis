# Pending: Crescendo Multi-Turn Jailbreak Detection

## Title
Crescendo multi-turn escalation detection in the session correlator

## Motivation
Crescendo (Russinovich et al., USENIX Security 2025, arxiv:2404.01833) achieves 98% ASR on
GPT-4 and 100% on Gemini-Pro by gradually escalating conversation topics across multiple turns.
Each individual turn is largely benign — harmful-classification rates drop from 60-80%
(single-turn) to 10-20% (final Crescendo turn) when evaluated in isolation. Automated
(Crescendomation) outperforms other SOTA jailbreaks by 29-61% on GPT-4.

## Research finding that led to this idea
`auto-improvement/research/2026-05-23T00-22_3-jailbreak-extraction.md` — finding 2 (Crescendo).

## Proposed change
Add a cross-turn escalation heuristic to `aigis/cross_session/correlator.py`:
1. Track topic drift across turns using a simple n-gram or TF-IDF similarity metric.
2. Detect rapid category drift: if turn N is in category X and turn N+k jumps to a high-risk
   category while each intermediate step had low per-turn risk scores, raise a session-level alert.
3. Alternative: detect when a session accumulates a rising total risk score across turns even
   though each individual turn is below the blocking threshold.

## Why it was held back
Multi-turn behavioral detection requires access to session state across message boundaries.
The current `CrossSessionCorrelator` tracks threat accumulation but does not model topic drift.
Implementing topic drift detection reliably without high false-positive rates requires either:
- An n-gram / embedding model (new optional runtime dependency)
- A heuristic based on risk-category transitions (feasible but needs careful tuning)

This exceeds the "small safe change" constraint for this cycle.

## Which constraint blocked it
> 5. Any single change touching > 100 LOC across non-test files

The cross-session correlator change would require >100 LOC across `correlator.py` and new tests.

## Suggested next step for the human reviewer
1. Review `aigis/cross_session/correlator.py` to understand current session accumulation logic.
2. Design a category-transition matrix: define which category sequences (e.g., "benign → technical
   curiosity → harmful instructions") are suspicious.
3. Implement a lightweight heuristic (e.g., if a session has 3+ turns with risk_score 0-20 each
   followed by a turn with risk_score 50+, flag the session) before adding embedding-based drift.
4. Consider a sliding window approach: sum risk scores over the last N turns and alert if the
   window sum crosses a configurable threshold.
