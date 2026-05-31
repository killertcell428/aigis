# Pending: Crescendo Multi-Turn Jailbreak Detection (v2)

## Title
Cross-session escalation detection for Crescendo-style gradual jailbreaks

## Motivation
Crescendo (arxiv:2404.01833, USENIX Security 2025) achieves 98% ASR on GPT-4 and 100% on
Gemini-Pro by starting on benign, adjacent topics and escalating gradually across 5–10 turns,
referencing the model's own prior replies to normalize increasingly harmful territory. The
automated version (Crescendomation) wraps this into an API loop. Each individual turn is
entirely benign; the harmful output only emerges after sustained escalation. This is the
fourth time Crescendo appears in jailbreak research cycles (first: 2026-05-08; updated here).

## Research finding
- Crescendo Multi-Turn Jailbreak (Russinovich et al., arxiv:2404.01833)
  https://arxiv.org/abs/2404.01833
- USENIX Security 2025: https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich
- Attack success rates: 98% GPT-4, 100% Gemini-Pro, outperforms SOTA by 29–61%

## Proposed change
Extend `aigis/cross_session/correlator.py` with a topic-drift escalation scorer:
1. Track conversation turn topics (BM25 or keyword-distance from prior turns).
2. Detect a monotonic drift toward a predefined "high-risk topic cluster" over 5+ turns.
3. If drift score exceeds threshold, flag session as `crescendo_risk` and surface in audit log.

## Why held back
Requires multi-turn session context — single-pass rule-based detection cannot see it.
The existing `aigis/cross_session/correlator.py` module provides the infrastructure
but adding topic-drift scoring would require either:
(a) keyword-set-based topic distance (zero dependencies) — feasible but low precision, or
(b) embedding-based semantic drift — violates the zero-runtime-dependency constraint.

## Constraint that blocked it
Architectural: single-turn rule-based regex cannot detect multi-turn escalation.
Dependency: embedding-based topic drift requires a runtime library (sentence-transformers, etc.).

## Suggested next step
Pick up in a memory-context or multi-agent cycle. Implement as a keyword-set topic-drift
heuristic using the cross-session correlator without embedding dependencies. A per-turn
"danger proximity" score summed over a window is sufficient for a meaningful baseline.
