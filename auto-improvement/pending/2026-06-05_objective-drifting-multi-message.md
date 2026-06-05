# Pending: Objective-drifting multi-message semantic analysis

## Title
Multi-message semantic drift detection for inter-agent conversations

## Motivation
AgentLAB (arxiv:2602.16901) documents that objective-drifting attacks work by embedding
individually benign framing injections across multiple messages. No single message triggers
a rule, but the cumulative effect substantially alters the agent's decision. Example:
product descriptions containing "Premium lasts 3× longer" and "Athletes choose premium"
across several tool results cause a shopping agent to consistently choose 3.6× more expensive
products. Per-message pattern matching cannot detect this because no single message contains
an explicit injection signal.

## Research finding that led to this idea
AgentLAB objective-drifting finding in `research/2026-06-05T03-03_6-multi-agent.md`:
> "Individual injections appear benign in isolation, yet their cumulative effect
> substantially alters agent behavior. 38 % ASR across 28 agentic environments."

## Proposed change
Extend `scan_conversation` in `AgentMessageScanner` to detect semantic drift by:
1. Tracking a "running goal summary" initialized from the first message in the conversation.
2. For each subsequent message, heuristically measuring whether the message pushes the
   conversation goal in an unexpected direction (e.g., from cost-minimization to premium
   selection, or from reading emails to accessing external URLs).
3. Emitting a low-confidence `injection_relay` warning when cumulative drift exceeds a
   configurable threshold.

## Why it was held back
"Any directional shift away from the zero-dependency / rule-based philosophy." Semantic
drift detection requires either an LLM call (to evaluate goal alignment) or a semantic
embedding comparison (requires a runtime dependency). Pure regex/rule-based detection
cannot reliably quantify semantic drift across messages without false positives.

## Constraint that blocked it
"Do NOT add features that depend on calling an LLM at runtime" and "Do not introduce
required runtime dependencies." A purely heuristic (keyword-based) approximation would
have unacceptably high false-positive rates.

## Suggested next step for the human reviewer
Consider an opt-in `semantic_drift_detector` hook that the caller can wire to an external
embedding model or lightweight classifier. The hook would receive the current conversation
history and return a drift score; `scan_conversation` would incorporate the score into the
final `MessageScanResult`. This keeps the runtime dependency out of the aigis core while
making the feature available to users who have an embedding endpoint.
