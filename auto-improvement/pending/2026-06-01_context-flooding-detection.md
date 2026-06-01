# Pending: Context-Flooding (InfoFlood) Detection

## Title
Information-overload jailbreak detection via context-length and entropy heuristics

## Motivation
The InfoFlood attack (arxiv:2506.12274, Jun 2025) achieves near-100% jailbreak success by
flooding the LLM context with large volumes of legitimate-looking reference material that
buries a harmful instruction. Leading guardrail systems prove "highly ineffective" at detecting
this class because each individual sentence in the flood is benign. The attack exploits the
model's tendency to follow the most recent or most prominent instruction in a long context.

## Research finding that led to this idea
`research/2026-06-01T03-13_3-jailbreak-extraction.md` — Finding 6 (InfoFlood).

## Proposed change
Add a context-density heuristic to the scanner: flag inputs that (a) exceed a configurable
length threshold (e.g., 8,000 tokens) AND (b) contain a single short instruction segment
near the end of an otherwise dense information block. This would be a lightweight heuristic
(not regex) that signals high-risk long inputs for additional scrutiny.

## Why it was held back
- Requires a token-counting or character-count heuristic, which may need to integrate with
  the LLM provider's tokenizer for accuracy (adding a dependency).
- False-positive risk: legitimate long-document Q&A tasks (e.g., "summarize this article")
  look structurally similar.
- A character-based threshold (not token-based) may be feasible as a zero-dependency
  heuristic but needs calibration against legitimate long-context workloads.

## Which constraint blocked it
- No suitable zero-dependency implementation within 100 LOC without false-positive tuning
- Risk of blocking legitimate long-document tasks

## Suggested next step for human reviewer
1. Audit typical input lengths in production to calibrate a safe threshold.
2. Implement a simple character-count heuristic as an opt-in `high_length_alert` rule with
   default `enabled: False` so users can enable it for short-context deployments.
3. Add a benchmark test with legitimate long-context inputs (contract review, document summary)
   to validate false-positive rate before enabling by default.
