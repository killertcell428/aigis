# Pending: Back-Reveal Backdoored Tool Use Exfiltration Detection

## Title
Runtime tool-call monitoring for backdoored LLM agent exfiltration (Back-Reveal)

## Motivation
Arxiv:2604.05432 (Apr 2026) introduced "Back-Reveal", a backdoor embedded into a fine-tuned
LLM agent's weights. When a semantic trigger phrase is encountered, the backdoored agent
autonomously invokes memory-access and retrieval tool calls to collect user session context,
then routes the collected data to an attacker-controlled endpoint via disguised tool calls
(e.g., a "retrieval" call whose URL encodes the exfiltrated data in query parameters).

Unlike prompt-injection exfiltration (which embeds instructions in user inputs or retrieved
content), Back-Reveal hides the exfiltration logic in model weights. Static regex rules
cannot detect it because there is no visible instruction in the prompt.

## Research Finding
`auto-improvement/research/2026-05-13T07-30_2-data-exfiltration.md`

Source: https://arxiv.org/abs/2604.05432

## Proposed Change
Extend `aigis/audit/` or a new `aigis/monitor/tool_call_audit.py` module to:
1. Record all outbound tool-call URLs during an agent session.
2. Flag sequences where a retrieval/memory tool call is immediately followed by a
   network tool call (fetch_url, http_request, etc.) whose URL contains long encoded
   query parameters (≥ 32 base64 chars in a query param).
3. Alert if the destination domain changes mid-session (first retrieval from A, then
   network call to B).

## Why Held Back
- Behavioral, not static: requires runtime tool-call sequence analysis, not regex.
- Requires a stateful session model (tool-call log per session) that does not yet
  exist in aigis.
- Likely > 100 LOC across new and existing files.
- Touching `monitor/` and `audit/` involves public API surface that warrants human review.

## Suggested Next Step
Design a `ToolCallSequenceAuditor` class with a minimal API (record_call, check_sequence)
and define the alert conditions precisely before implementing. Consider whether this belongs
in the existing `aigis/monitor/` directory or as a new `aigis/audit/tool_seq.py` module.
