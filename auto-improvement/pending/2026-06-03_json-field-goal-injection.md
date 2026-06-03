# Pending: JSON-field goal injection detection

**Title:** Detect goal substitution embedded in structured JSON fields within agent messages

**Motivation:**
When agents exchange structured data (tool results, state objects), an adversary can embed
goal-substitution instructions inside JSON field values such as `"system_directive"`,
`"override_action"`, `"task_override"`, or `"true_goal"`. The receiving agent (or a
downstream JSON-parsing step) may treat these as authoritative instructions, especially if
it has a system prompt that says "process the task field from the tool result".

**Research finding that led here:**
Cycle 6 research (2026-06-03T09-09_6-multi-agent.md):
- Protocol-level LLM agent taxonomy (arxiv:2506.23260) identifies structured-format payload
  injection as a high-severity vector in A2A communication
- OWASP ASI07 (Insecure Inter-Agent Communication) notes that message parsing without schema
  validation enables this class of attack

**Proposed change:**
Add a pattern or JSON-parsing helper to `AgentMessageScanner._check_message_type` that, for
`message_type="tool_result"`, extracts string values from top-level JSON fields and scans
them against `_GOAL_SUBSTITUTION_PATTERNS` and `_HIDDEN_INSTRUCTION_PATTERNS`. Field names
that are themselves suspicious (`system_directive`, `task_override`, `hidden_instruction`)
would also trigger a flag at a lower threshold.

**Why it was held back:**
- Requires a JSON parsing step in the hot path; needs careful exception handling to avoid
  breaking on malformed JSON.
- False-positive risk: legitimate tool results often have fields named "task" or "goal" as
  part of their schema.
- Needs evaluation against real tool-result corpora before setting thresholds.

**Which constraint blocked it:**
Potential false positive rate too high without further evaluation; > 50 LOC to implement
correctly with tests.

**Suggested next step:**
Build a small corpus of real and adversarial tool results, determine appropriate field-name
and value patterns, implement as an opt-in JSON-mode in `scan_message`, and add tests with
both real-world tool schemas and adversarial payloads.
