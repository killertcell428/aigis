# Pending: MCP Tool-Description Credential Scanning

## Title
Extend mcp_scanner.py to flag hardcoded credentials in tool descriptions

## Motivation
Arxiv:2604.03070 (Apr 2026) documented a large-scale study of 200+ real-world LLM agent
"skills" (MCP tools / plugins). A significant fraction hardcoded credentials — API keys,
OAuth tokens, database passwords — directly in tool description strings. Because tool
descriptions are part of the LLM context, any indirect prompt injection that causes the
agent to repeat or log its tool descriptions can leak these credentials to an attacker.

aigis already scans input for `pii_api_key_input` and has `mcp_hardcoded_credential` in
`mcp_scanner.py`, but the mcp_scanner coverage for tool-description strings may be narrower
than the new API-key patterns in the input filter.

## Research Finding
`auto-improvement/research/2026-05-13T07-30_2-data-exfiltration.md`

Source: https://arxiv.org/abs/2604.03070

## Proposed Change
Audit `aigis/mcp_scanner.py` to ensure all key patterns from `pii_api_key_input`
(GitHub tokens, Anthropic keys, Google service account JSON, etc.) are also covered
when scanning MCP tool description strings. Add test cases in `tests/test_mcp_scanner.py`
that use sample tool descriptions containing hardcoded credentials.

## Why Held Back
- Requires auditing mcp_scanner.py coverage in detail — a task best scoped to an
  agent-tool-abuse cycle where MCP scanner internals are already in context.
- Risk of touching > 100 LOC if multiple patterns need extension.

## Suggested Next Step
In the next agent-tool-abuse cycle: diff the patterns in `mcp_scanner.py` against the
current `DATA_EXFIL_PATTERNS` and `PII_PATTERNS` in `filters/patterns.py`, and add
any missing coverage with targeted tests.
