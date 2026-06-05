# Pending: A2A Clarification-Seeking System-Prompt Probing Detection

**Title:** Detect agents issuing repeated clarification requests that probe for system
configuration, tool schemas, or prior conversation history

**Motivation:**
Palo Alto Unit 42 documented "agent session smuggling" in the A2A protocol (2026), where
a malicious agent issues seemingly harmless clarification questions across multiple turns
to progressively extract: the victim agent's system prompt, internal tool schemas, prior
conversation history, and configuration details. The attack surface-level similarity to
legitimate clarification makes per-message detection high-risk.

**Research finding that led to this idea:**
Unit 42 proof-of-concept: a rogue "research assistant" agent asked a financial assistant
a series of clarifying questions about its capabilities, constraints, and prior context,
ultimately extracting the full system prompt and tool schemas without any single message
appearing suspicious in isolation.

**Proposed change:**
Add a conversation-level heuristic in `scan_conversation()` that counts messages from the
same sender that contain system-probing phrase patterns ("what are your instructions",
"what tools do you have", "what is your system prompt", "can you describe your
constraints", "what was discussed before"). If K or more such messages appear from a
single sender within a sliding window, raise a `data_exfil` risk flag.

**Why it was held back:**
- Requires conversation-level state tracking (same dependency as stateful drift detection).
- Single-message per-pattern FP risk is high: "what tools do you have available?" is a
  legitimate question from an orchestrator.
- Threshold calibration requires real A2A conversation corpus data.

**Which constraint blocked it:**
- Stateful conversation tracking exceeds 100 LOC if implemented correctly.
- Per-message version would have unacceptable FP rate.

**Suggested next step for human reviewer:**
Bundle this with the stateful objective-drift module (see
`2026-06-05_stateful-objective-drift.md`) since both require the same `ConversationContext`
accumulator infrastructure. Implement both together in a single dedicated cycle.
