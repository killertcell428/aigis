# Pending: Incremental Completion Decomposition (ICD) Detection

## Title
Session-level detection for Incremental Completion Decomposition (ICD) jailbreaks

## Motivation
arxiv:2604.25921 ("One Word at a Time: Incremental Completion Decomposition Breaks LLM
Safety", April 2026) introduces ICD: an attacker first elicits a sequence of single-word
continuations related to a malicious goal (e.g., "What is the next word: synthesize...?"),
and then elicits the full harmful response once the model has been anchored. Demonstrated
superior ASR vs. existing methods on AdvBench, JailbreakBench, and StrongREJECT across
multiple model families. The attack is designed to be multi-turn and trajectory-based —
no single turn contains the full harmful request.

## Proposed Change
A session-level heuristic in the cross-session correlator or adversarial loop module:
flag sessions where the input pattern shows repeated single-word-continuation requests
(e.g., "what comes next: X", "continue from: X") in short succession, as this is a
distinctive ICD fingerprint. This would require extending `aigis/cross_session/` with
a new correlator or adding a heuristic to `aigis/adversarial_loop.py`.

## Research Finding
- Source: https://arxiv.org/abs/2604.25921
- Authors: Samee Arif, Naihao Deng, Zhijing Jin, Rada Mihalcea
- Submission: April 2026

## Why Held Back
- ICD is inherently multi-turn; cannot be detected in a single-turn input filter.
- Implementing session-level state would require changes to `aigis/cross_session/` or
  a new session-aware detector — both exceed the "small additive diff" constraint.
- The change would touch >100 LOC across non-test files.

## Constraint That Blocked It
Zero-runtime-dependency / rule-based philosophy: session-level tracking across turns
requires state management infrastructure. Also exceeds 100 LOC non-test diff limit.

## Suggested Next Step
Human reviewer: consider extending the `cross_session` module with a lightweight
turn-sequence heuristic that flags sessions matching the ICD fingerprint (many short
completion-style queries in rapid succession about the same harmful domain). This would
be a meaningful defence against the most effective current trajectory-based jailbreak.
