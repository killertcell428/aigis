# Pending: MCP stdio Shell Metacharacter Injection

**Date:** 2026-05-13
**Domain:** agent-tool-abuse (cycle 1, third pass)
**Research basis:** OX Security advisory "The Mother of All AI Supply Chains" (April 2026); CVE-2026-30623 (LiteLLM, stdio MCP transport RCE); CVE-2026-30615 (Windsurf, zero-click); The Hacker News coverage of the Anthropic MCP design vulnerability (April 2026).

---

## Title

MCP stdio Shell Metacharacter Injection — pattern-level detection in tool argument values

## Motivation

The MCP stdio transport spawns MCP server processes via a command string. If tool call arguments contain shell metacharacters (`;`, `&&`, `||`, backtick, `$(...)`, `|`) and the server does not sanitize, arbitrary OS commands execute in the server's process context. CVE-2026-30623 (critical, 150M+ downloads, 200k+ instances) and CVE-2026-30615 (zero-click in Windsurf) were assigned to this class. Anthropic declined to patch the protocol, calling it "expected behavior," which means the defense must be at the client-side scanning layer.

## Proposed Change

Add a `mcp_stdio_cmd_injection` pattern to `MCP_POISONING_PATTERNS` that flags shell metacharacter sequences appearing inside tool argument values, especially when combined with MCP tool invocation context:

```python
DetectionPattern(
    id="mcp_stdio_cmd_injection",
    name="MCP stdio Shell Metacharacter Injection in Tool Arguments",
    category="mcp_poisoning",
    pattern=_p(
        r"(?:\"(?:command|cmd|args?|argv|shell|exec|run)\"\s*:\s*\"[^\"]*"
        r"(?:;|\|\||&&|`|\$\(|>\s*/[a-z])[^\"]*\")"
        r"|(?:shell\s*=\s*True\b.{0,100}(?:;|\|\||&&|`|\$\())"
    ),
    base_score=75,
    ...
)
```

Alternatively, integrate this check into `mcp_scanner.scan_invocation()` as an argument-level inspection pass, which would be more targeted than a flat regex over the entire payload.

## Why Held Back

**Constraint: false-positive risk exceeds acceptable threshold.** Tool responses frequently contain code examples, shell scripts, and command-line documentation that use `&&`, `|`, `;`, and backtick syntax. A pattern broad enough to catch real injection attempts (which embed metacharacters in what appear to be string argument values) would also fire on:
- Shell one-liners in tutorial tool responses
- JSON-encoded command strings in DevOps tools
- Legitimate pipeline commands in filesystem tools

The more targeted approach (scanning the `args` field of a specific JSON invocation structure) requires parsing the invocation JSON rather than pattern-matching the raw string, which is a function-level change to `scan_invocation()` in `mcp_scanner.py`. This is feasible but would add ~40 LOC to the non-test code plus test cases, making it a dedicated cycle task.

## Suggested Next Step for Human Reviewer

1. Implement argument-level parsing in `scan_invocation()`: extract `args` or `arguments` field values from the MCP tool call JSON, then apply a metacharacter check specifically to those values.
2. A targeted scan of `args` values avoids the false-positive problem entirely because legitimate argument values should not contain shell metacharacters when they are non-shell-invocation arguments.
3. Alternatively, add an allow-list of tool names that legitimately accept shell commands (e.g., `bash`, `shell`, `run_command`) and only skip the metacharacter check for those.
