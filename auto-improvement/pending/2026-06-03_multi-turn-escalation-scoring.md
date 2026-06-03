# Pending: Multi-turn escalation scoring in scan_conversation

**Title:** Weight later messages higher when earlier messages were flagged at low risk

**Motivation:**
Agent Session Smuggling (Unit 42, April 2025) exploits stateful A2A sessions to inject
instructions gradually — building trust over several turns before issuing an unauthorised
action. The current `scan_conversation` method scans each message independently; a multi-turn
escalation that spreads across 3–5 benign-looking messages can achieve a low per-message risk
score while succeeding in aggregate.

**Research finding that led here:**
Cycle 6 research (2026-06-03T09-09_6-multi-agent.md):
- Unit 42 Agent Session Smuggling PoC demonstrated gradual trust-building over multiple turns
  before triggering an unauthorised stock trade
- TAMAS benchmark (arxiv:2511.05269) measured colluding-agent attacks succeeding 60–82%
  of the time via multi-turn coordination

**Proposed change:**
In `AgentMessageScanner.scan_conversation()`, after the per-message scan loop, run an
escalation pass:
- If a later message's risk score exceeds a per-message threshold (e.g. 20) AND any prior
  message from the same `from_agent` also exceeded that threshold, apply a configurable
  multiplier (default 1.5×, capped at 100) to the later message's final score.
- Optionally expose a `conversation_risk` aggregate field on the result list.

**Why it was held back:**
- Altering `scan_conversation` scoring output is a public-API change: callers who use the
  returned `MessageScanResult.risk_score` as a threshold will see higher scores for the same
  content.
- The change would require updating the docstring, adding a new option, and potentially
  bumping a minor version — larger than a single-cycle patch.
- Needs careful calibration to avoid false positives in multi-step orchestration pipelines
  where repeated moderate-risk scores are normal (e.g. a search agent that always returns
  URLs alongside results).

**Which constraint blocked it:**
Hard constraint: "Any breaking public API change in aigis/" and total diff > 100 LOC.

**Suggested next step:**
Design the scoring change under an opt-in flag
(`scan_conversation(messages, multi_turn_escalation=False)`) so default behaviour is
unchanged, implement with tests, and land in a dedicated minor release.
