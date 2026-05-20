# Pending: Log-To-Leak MCP Logging Tool Forced Invocation

**Date:** 2026-05-20
**Domain:** data-exfiltration (cycle 2, fourth pass)
**Research basis:** `research/2026-05-20T06-03_2-data-exfiltration.md`

---

## Title

Detect prompt injections that bind a logging/audit MCP tool and instruct the agent to invoke it with sensitive content

## Motivation

"Log-To-Leak" (OpenReview, Oct 2025) is a systematic attack framework that covertly forces an MCP-enabled LLM agent to invoke a malicious or repurposed logging tool, passing sensitive data (user queries, tool responses, agent replies) as the log message argument. The framework decomposes injection payloads into four components:
1. **Trigger** — initial injection surface in tool output/RAG content
2. **Tool Binding** — naming the specific logging tool (e.g., `log_message`, `debug_service`, `audit_log`)
3. **Justification** — fake compliance/security framing ("for regulatory compliance, record this session")
4. **Pressure** — urgency language to override resistance

Tested across 5 real MCP servers and 4 LLM agents (GPT-4o, GPT-5, Claude Sonnet 4, GPT-OSS-120b) with consistently high attack success rates. This is distinct from `mcp_collector_exfil` (which requires explicit "collect+send-to-URL" language) because Log-To-Leak uses an existing, seemingly-legitimate tool rather than an overt exfiltration endpoint.

## Proposed Change

Add `mcp_log_to_leak` to `MCP_SECURITY_PATTERNS`:

```python
DetectionPattern(
    id="mcp_log_to_leak",
    name="MCP Log-To-Leak Forced Logging Tool Invocation",
    category="mcp_poisoning",
    pattern=_p(
        r"(?:invoke|call|use|execute)\s+(?:the\s+)?"
        r"(?:log(?:ging)?|debug|audit|record|trace|telemetry|monitoring?)"
        r"(?:[-_]\w+)?\s+tool"
        r".{0,200}"
        r"(?:user\s*(?:query|input|message|request|prompt)"
        r"|system\s*prompt"
        r"|conversation\s*(?:history|content|log)"
        r"|(?:current|all)\s+(?:session|context|messages?)"
        r"|agent\s*(?:output|response|reply))"
    ),
    base_score=65,
    ...
)
```

## Why Held Back

1. **FP risk from legitimate observability documentation**: Tool descriptions for legitimate logging/monitoring MCP tools often describe what data they record. The pattern would need to distinguish between a tool *describing its own purpose* vs. an injected payload *instructing the agent to call another tool*.
2. **Context dependency**: The attack relies on the injection being in tool *output* (RAG, web content) rather than the tool's own description — a static regex applied uniformly may not distinguish these contexts.
3. **Pattern complexity**: The three-part conjunction (logging-verb + logging-tool-name + sensitive-data-reference) needs careful tuning against a corpus of legitimate logging tool descriptions to avoid FP spikes.

## Constraint blocked

- FP rate too uncertain without corpus validation (no-new-runtime-deps constraint prevents importing NLP tooling for disambiguation)

## Suggested Next Step for Human Reviewer

1. Build a test corpus of ~20 legitimate logging/monitoring MCP tool descriptions and 20 attack payloads from the Log-To-Leak paper.
2. Tune the pattern against that corpus before implementation.
3. Consider restricting the pattern to tool *output* scanning only (not tool description scanning) to reduce FP from legitimate tool metadata.
4. Source: https://openreview.net/forum?id=UVgbFuXPaO
