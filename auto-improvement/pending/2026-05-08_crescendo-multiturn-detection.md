# Pending: Crescendo / Multi-Turn Gradual Escalation Detection

**Date:** 2026-05-08
**Research basis:** Research file `2026-05-08T05-49_3-jailbreak-extraction.md`

---

## Title

Stateful multi-turn jailbreak detection (Crescendo / gradual escalation pattern)

## Motivation

The Crescendo attack (Microsoft Research / USENIX Security 2025, arXiv 2404.01833) gradually escalates
dialogue over multiple turns — each individual turn appears benign, but the conversation trajectory
reveals malicious intent. A 2025 follow-up study found multi-turn jailbreaks exceed 70% success rates
against models optimized only for single-turn protection. Single-turn rule-based filters cannot detect
this pattern because each message in isolation is clean.

## Proposed Change

Add an optional stateful conversation scorer that:
1. Maintains a rolling window of the last N turns' risk scores.
2. Flags conversations where the topic vector drifts monotonically toward a high-risk category
   (e.g., "general history" → "weapons history" → "weapon synthesis").
3. Emits a `crescendo_escalation` risk signal when the slope of risk score over turns exceeds a threshold.

This could be implemented as a new module `aigis/filters/conversation_state.py` with a class
`ConversationRiskTracker` that holds per-session state and is updated on each `filter_input` call.

## Why It Was Held Back

- **>100 LOC constraint:** A robust implementation would require at minimum 150–200 LOC across the
  new module, a session state interface, and tests — exceeding the 100-LOC non-test limit for a
  single cycle.
- **Potential API surface change:** Exposing per-session state tracking may require changes to the
  public `filter_input` / `scan` API signatures, which is a breaking public API change.

## Suggested Next Step

Implement in a dedicated cycle:
1. Define `ConversationRiskTracker` as an opt-in class (default = current single-turn behavior).
2. Add `filter_conversation(turns: list[str]) -> ConversationScanResult` as a new function that does
   NOT change existing `filter_input` / `scan` signatures.
3. Keep the stateful tracker behind a feature flag / explicit instantiation so zero-state usage
   remains the default.
