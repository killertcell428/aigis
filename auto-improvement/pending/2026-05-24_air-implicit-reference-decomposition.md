# Pending: AIR Implicit Reference Decomposition — Session-Level Detection

## Title
AIR (Attack via Implicit Reference) — Multi-step decomposition jailbreak, session-level detection

## Motivation
The AIR attack (arxiv:2410.03857, Oct 2024) decomposes a harmful objective into individually
harmless sub-questions linked by implicit referential context ("In the context of compound X
above, explain..."). The model constructs the harmful answer by connecting benign sub-responses.
Measured >90% ASR on GPT-4o, Claude-3.5-Sonnet, and Qwen-2-72B. Inverse scaling — larger
models are more vulnerable. Single-turn regex detection is insufficient because each individual
query looks benign.

## Research finding
- Source: https://arxiv.org/abs/2410.03857 (ICLR 2025 submission)
- Attack via Implicit Reference (AIR)
- ASR: >90% across frontier models; larger models more vulnerable (inverse scaling)

## Proposed change
This requires a session-level scoring approach:
1. Track the last N messages in a session window
2. Score the current message's referential language ("in the context of X above", "given the
   above, detail...") against the accumulated topic vector of prior messages
3. If the cumulative topic drift suggests a harmful objective being assembled in parts, flag

Alternatively, a partial input-side heuristic:
```python
r"(?:in\s+the\s+context\s+of\s+(?:the\s+)?(?:above|previous|compound\s+X)|"
r"given\s+the\s+above[,.]?\s+(?:detail|explain|describe|provide\s+(?:step|procedure))|"
r"based\s+on\s+(?:the\s+)?(?:information|answer|compound)\s+above)"
```
But false-positive rate is high for legitimate referential writing.

## Why it was held back
- Single-turn regex is insufficient for reliable detection
- Session-level detection requires stateful session tracking (not in current aigis architecture)
- Zero-dependency constraint rules out external NLP libraries for semantic similarity

## Which constraint blocked it
> "Do NOT add features that depend on calling an LLM at runtime."
> Session-level stateful tracking is outside current zero-runtime-dependency architecture.

## Suggested next step
Consider as a roadmap item for a future "session-aware scoring" capability. Could be
implemented as an optional stateful middleware layer using only stdlib (simple n-gram
co-occurrence, not embedding-based similarity). Add as a request to the architectural
roadmap document.
