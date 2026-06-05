# Pending: Objective Drifting Detection via Conversation-Level Semantic Drift

## Title
Conversation-level semantic drift tracker for objective drifting attacks

## Motivation
AgentLAB (arxiv:2602.16901) measures objective drifting at 79–92% ASR against most LLMs. Unlike task injection (which uses explicit replacement language), objective drifting works through gradual, cumulative bias across multiple environmental observations. No single message contains an explicit attack signal — the shift happens through many subtly biased tool results or data items, each appearing benign individually.

## Which research finding led to this idea
AgentLAB (arxiv:2602.16901, Feb 2026): the objective drifting attack type. Example: a shopping agent purchasing a $49.99 item (3.6× its task budget) after encountering a series of injected product descriptions that each slightly emphasized brand over cost — none triggering per-message rules.

## Proposed change
Add a `ConversationDriftTracker` to `AgentMessageScanner.scan_conversation()` that:
1. Extracts a "task signal" from the first message in a conversation (or from a caller-supplied task description).
2. For each subsequent tool result or data message, computes a semantic similarity score between the message content and the original task.
3. Flags conversations where the running average similarity drifts below a threshold over a sliding window, indicating sustained redirection.

Would require a lightweight embedding or keyword-overlap approach to stay zero-runtime-dependency (full semantic embeddings would require an ML library).

## Why it was held back
Implementing a meaningful semantic similarity check without adding a runtime dependency (e.g., `sentence-transformers`, `sklearn`) is non-trivial. A keyword-overlap approximation might produce high false positives in legitimate conversations where topic naturally evolves. The change would touch multiple modules and likely exceed 100 LOC.

## Which constraint blocked it
- Hard constraint: no new required runtime dependencies
- Size constraint: likely > 100 LOC across non-test files
- Risk: high false-positive potential without thorough calibration

## Suggested next step for human reviewer
Design a zero-dependency keyword drift heuristic (e.g., BLEU-like overlap between original task keywords and accumulated tool result keywords). Prototype and calibrate on the AgentLAB shopping scenario as a test fixture. If the heuristic achieves < 5% false positive rate on benign conversation test cases, it can be implemented across multiple cycles by adding the tracker first, then calibrating thresholds.
