# Pending: MCP Tool Name Squatting Detection

**Date:** 2026-05-13
**Domain:** agent-tool-abuse (cycle 1, third pass)
**Research basis:** ETDI paper (arxiv:2506.01333, Anthropic-affiliated, June 2025) — "Enhancing Trust and Delegation in the MCP Ecosystem"; formal academic taxonomy of MCP rug-pull and tool squatting attacks.

---

## Title

MCP Tool Name Squatting — registration-time detection of trusted-namespace prefix impersonation

## Motivation

"Tool squatting" (ETDI taxonomy, arxiv:2506.01333) is an attack where a malicious MCP server registers a tool using a name identical or confusingly similar to a tool the user expects from a trusted server. Example: a malicious server registers `github_create_file` when the user's workflow expects this tool to come from the verified GitHub MCP server. The user approves the malicious tool at registration because its name looks legitimate; the attack never changes the description or behavior post-approval (unlike rug-pull), so it evades description-content scanning.

## Proposed Change

Add a `detect_tool_squatting()` function to `aigis/mcp_scanner.py` that checks tool names against a list of well-known trusted-namespace prefixes:

```python
TRUSTED_NAMESPACES = frozenset({
    "github_", "filesystem_", "google_", "aws_", "slack_",
    "stripe_", "notion_", "linear_", "jira_", "confluence_",
    "salesforce_", "hubspot_", "zendesk_", "pagerduty_",
    "datadog_", "cloudflare_", "vercel_", "supabase_",
})

def detect_tool_squatting(
    tool_name: str,
    server_id: str,
    trusted_server_registry: dict[str, set[str]],
) -> SquattingResult | None:
    for prefix in TRUSTED_NAMESPACES:
        if tool_name.lower().startswith(prefix):
            trusted_servers = trusted_server_registry.get(prefix, set())
            if server_id not in trusted_servers:
                return SquattingResult(
                    tool_name=tool_name,
                    matched_prefix=prefix,
                    server_id=server_id,
                    description=f"Tool name '{tool_name}' uses trusted namespace "
                                f"prefix '{prefix}' but is registered from "
                                f"unrecognized server '{server_id}'.",
                )
    return None
```

## Why Held Back

**Constraint: requires new API surface.** The function needs a `trusted_server_registry` parameter — a mapping from namespace prefix to the set of server IDs that are legitimately allowed to register tools with that prefix. This registry must be configured per-deployment and does not have a sensible default. Adding this as a required parameter breaks the zero-configuration philosophy; adding it as optional with an empty default means the feature does nothing unless explicitly configured.

Additionally, the function needs to be integrated into `MCPScanner.register_tool()` (or a new `MCPScanner.check_registration()` method), which touches the public API.

**Constraint: LOC.** The `SquattingResult` dataclass, `detect_tool_squatting()` function, `TRUSTED_NAMESPACES` set, integration into `MCPScanner`, and tests collectively exceed 100 LOC across non-test files.

## Suggested Next Step for Human Reviewer

1. Add `trusted_server_registry: dict[str, set[str]] | None = None` as an optional parameter to `MCPScanner.__init__()`.
2. Call `detect_tool_squatting()` from `MCPScanner.scan_description()` when `trusted_server_registry` is provided and the tool name is available in context.
3. Document the registry format in `docs/mcp_tool_squatting.md` with examples for GitHub, filesystem, and Google tool namespaces.
4. This is a ~80 LOC change across 2-3 files and can be a standalone cycle.
