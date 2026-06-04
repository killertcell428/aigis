# Pending: Multi-Turn Objective Drift Scoring

**Title:** Accumulate drift score across conversation turns when agent's stated objective shifts progressively

**Motivation:**
AgentLAB (arxiv:2602.16901) identifies "objective drifting" as distinct from single-turn task injection: the attacker gradually steers the agent's goal across multiple turns without any single message being obviously malicious. Per-message scanning misses this because each individual message may score low risk while the cumulative effect is a complete goal replacement.

**Research finding:**
AgentLAB benchmark (<https://arxiv.org/abs/2602.16901>) found:
- Objective drifting is among the top-2 most prevalent long-horizon attack patterns
- It specifically evades per-message defenses by staying below single-message detection thresholds
- A conversation-level "goal drift" metric is needed: compare the stated objective in the first few messages against the stated objective in recent messages using semantic similarity or keyword-set comparison

**Proposed change:**
Add `scan_conversation_drift(messages: list[AgentMessage]) -> DriftReport` to `AgentMessageScanner`. Approach:
1. Extract "task-framing" sentences (sentences containing task-indicator keywords: task, objective, goal, mission) from each message
2. Build a timeline of stated goals across turns
3. Compute semantic drift: if the keyword sets between early turns and late turns diverge significantly, flag as "objective drift detected"
4. Return `DriftReport(detected: bool, drift_score: float, early_goal_summary: str, late_goal_summary: str, suspicious_turn_indices: list[int])`

**Why it was held back:**
- Stateful: requires maintaining conversation state across turns (the current `scan_conversation` method already does per-message scans but without cumulative state)
- Architectural: `DriftReport` is a new return type; `scan_conversation` signature change would need careful backward compatibility handling
- LOC: the drift scoring logic alone (keyword extraction + set comparison) would be 50–70 LOC; the new data class and tests would push total well above 100 LOC
- Risk: naive keyword-set comparison has high false-positive risk; needs tuning

**Constraint that blocked it:**
100 LOC limit + architectural change to public API signature.

**Suggested next step:**
Design as a separate `ConversationDriftScanner` class (not modifying existing `AgentMessageScanner`), so no public API change occurs. Start with a simple keyword-set Jaccard distance between first-third and last-third of conversation messages. Write 4–5 tests using synthetic multi-turn conversations with and without drift.
