# Pending: Shell Metacharacter Detection in MCP Tool Call Arguments

**Title:** Detect shell metacharacters in MCP tool call argument values

**Motivation:**
The PipeLab "State of MCP Security 2026" report documented the git MCP RCE chain, where unsanitized `--repository` and `--exec` flags passed to GitPython enabled arbitrary file writes and command execution. The attack pattern: a tool call argument contains path traversal sequences (`../`, `..\`), shell metacharacters (`;`, `|`, `&&`, `$()`), or flag injection (`--exec`, `--allow-root`) that get passed unsanitized to a subprocess or filesystem API.

**Research finding:**
PipeLab State of MCP Security 2026 (<https://pipelab.org/blog/state-of-mcp-security-2026/>) documents:
- git MCP RCE via unsanitized `--repository` flag: arbitrary file write achieved
- postmark-mcp backdoor: outgoing emails BCC'd to attacker-controlled address
- Detection signal: arguments containing shell metacharacters or path traversal sequences

**Proposed change:**
Add `scan_tool_call_args(tool_name: str, args: dict[str, str]) -> list[dict]` to `aigis/mcp_scanner.py`. The function inspects each argument value for:
- Path traversal: `\.\.[\\/]` patterns
- Shell metacharacters: `[;&|`$(){}]` in values
- Flag injection: values starting with `--` followed by known dangerous flags (`exec`, `allow-root`, `shell`, `cmd`)

Returns a list of alert dicts similar to the existing `scan_mcp_tool` return format.

**Why it was held back:**
- Scope: belongs in `mcp_scanner.py` (tool call argument validation layer), not `message_scanner.py` (inter-agent message content layer)
- Needs careful false-positive analysis: many legitimate tool arguments contain `--` prefixes, paths with `/`, etc.
- Needs dedicated test design against realistic tool schemas

**Constraint that blocked it:**
Would touch `mcp_scanner.py` which already has ongoing changes this cycle; adding argument validation there + tests would likely exceed 100 LOC if done correctly.

**Suggested next step:**
In a supply-chain or agent-tool-abuse cycle, design `scan_tool_call_args` with a whitelist/allowlist of known-safe argument names per tool type, and write 5–8 tests covering path traversal, flag injection, and safe baseline arguments.
