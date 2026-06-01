# Pending: Distributed Prompt-Splitting Detection

## Title
Multi-turn distributed prompt-splitting jailbreak detection

## Motivation
The "Prompt, Divide, and Conquer" attack (arxiv:2503.21598, Mar 2025) decomposes a harmful
request into individually benign prompt segments distributed across multiple API calls or
LLM instances. Each segment looks harmless in isolation; only the aggregated output reveals
the harmful intent. The technique achieved 73.2% success rate for malicious code generation
across 500 harmful prompts spanning 10 cybersecurity domains.

## Research finding that led to this idea
`research/2026-06-01T03-13_3-jailbreak-extraction.md` — Finding 3 (Prompt, Divide, and Conquer).

## Proposed change
Add a cross-turn session-level correlator that tracks partial outputs across a session and
flags when the cumulative output structure matches known harmful-content templates. This would
require extending the `cross_session/` module with a lightweight state machine that detects
"result aggregation" patterns (e.g., multiple outputs with numbered continuation markers being
assembled into a single document).

## Why it was held back
Single-turn regex detection is insufficient: each individual prompt segment is benign. Detection
requires multi-turn state tracking, which aigis does not currently implement for this attack
class. Implementing this without a robust session-state layer risks both false positives
(legitimate multi-step tasks) and architectural over-scope.

## Which constraint blocked it
- Would touch > 100 LOC across non-test files (cross_session correlator)
- Requires semantic understanding of partial outputs, not just regex

## Suggested next step for human reviewer
1. Review the `cross_session/` module for existing session-state infrastructure.
2. Design a lightweight "output aggregation detector" that flags N successive outputs from the
   same session that together appear to form a harmful document.
3. Consider integration with the `audit/` log to allow post-hoc correlation without adding
   real-time session state overhead.
