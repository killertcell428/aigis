# Pending: Foot-In-The-Door Multi-Turn Jailbreak Detection

## Title
Cross-turn escalation detection for FITD (Foot-In-The-Door) jailbreak pattern

## Motivation
arxiv:2502.19820 (Feb 2025, FITD) achieves 94% average ASR across seven LLMs including GPT-4o
and Claude by exploiting the psychological foot-in-the-door principle: minor initial commitments
lower resistance to more significant transgressions. The attacker sends a benign first request
to establish compliance, then uses "bridge prompts" to escalate gradually toward a harmful goal.

## Research finding
Source: https://arxiv.org/abs/2502.19820

Each turn looks benign in isolation. The harm emerges from the escalation trajectory. No single
message contains the full attack; the attack is the sequence.

## Proposed change
Add a cross-turn risk accumulator in `aigis/cross_session/` that:
1. Tracks cumulative risk score across a conversation window (e.g., last 5 turns).
2. Raises an alert when the sequence shows a monotonically increasing risk trajectory
   (each turn's score is ≥ the previous) even if no individual turn crosses the threshold.
3. Optionally flag the "bridge prompt" turn that shows the steepest risk escalation.

## Why held back
**Constraint: single-turn regex filter cannot detect this attack.** The FITD attack's defining
feature is the escalation pattern, not any single message. Detecting it requires:
- State across conversation turns (session-level tracking)
- Time-series analysis of risk scores

This is an architectural addition, not a regex rule. It would touch > 100 LOC across non-test
files (violation of the ≤100 LOC constraint for a single cycle).

## Which constraint blocked it
- Single-turn regex cannot detect cross-turn escalation.
- Change would exceed 100 LOC constraint.

## Suggested next step for human reviewer
The `aigis/cross_session/` module exists. A small SessionRiskAccumulator class that tracks
per-session running risk scores and emits a warning when 3 consecutive turns each exceed a
low threshold (e.g., 15 points) could be added in a dedicated cycle. This is an architecture-
appropriate addition and fits the project philosophy.
