# Pending: Echo Chamber Multi-Turn Jailbreak Detection

**Date:** 2026-05-21
**Research finding:** auto-improvement/research/2026-05-21T09-07_3-jailbreak-extraction.md (finding 4)
**Constraint blocking:** Requires multi-turn conversation state tracking; outside current single-scan architecture.

---

## Title

Detect Echo Chamber-style conversational context poisoning across multiple turns.

## Motivation

arxiv:2601.05742 ("The Echo Chamber Multi-Turn LLM Jailbreak", NeuralTrust, Jan 2026) documented a
jailbreak that embeds "steering seeds" — harmless-looking contextual hints — into early conversational
turns to build a poisoned context that progressively nudges the model toward harmful outputs.
Unlike Crescendo (which escalates topic directly), Echo Chamber works by conditioning semantic
associations: early turns establish innocent-looking associations that are later exploited to obtain
harmful outputs. NeuralTrust demonstrated this against OpenAI and Google models in standard black-box
settings and recommends "toxicity accumulation scoring" that tracks escalation across turns.

## Proposed Change

Implement a stateful `ConversationRiskTracker` class that:
1. Accepts a list of `(role, text)` turn pairs
2. Computes per-turn risk scores using the existing `scan()` function
3. Detects monotonic drift toward higher-risk topics using topic vector similarity
4. Emits a `conversation_escalation` signal when cumulative drift exceeds threshold

This extends the architecture sketch from `auto-improvement/pending/2026-05-08_crescendo-multiturn-detection.md`.

## Why Deferred

- Requires stateful multi-turn context tracking not present in the current single-scan API
- A robust implementation would exceed the 100 LOC non-test limit in a single cycle
- The prior Crescendo pending proposal (`2026-05-08_crescendo-multiturn-detection.md`) already
  outlines the API design; this is an incremental step on top of that

## Constraint Blocking

- >100 LOC for a meaningful implementation
- Potential API surface change (new `filter_conversation()` function needed)

## Suggested Next Step

Implement `aigis.conversation.ConversationRiskTracker` as an opt-in class that wraps the existing
`scan()` function, adds a sliding window, and emits `conversation_risk` events. Keep default
`filter_input()` behavior unchanged. Target a dedicated multi-agent or jailbreak domain cycle.
