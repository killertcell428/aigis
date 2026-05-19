# Pending: SANDWORM_MODE Environment Credential Keyword Cluster Detection

**Date:** 2026-05-19
**Domain:** agent-tool-abuse (cycle 1, fourth pass)
**Research basis:** `research/2026-05-19T09-00_1-agent-tool-abuse.md`

---

## Title

Detect tool descriptions that enumerate credential-named environment variable keywords (TOKEN/KEY/SECRET/PASSWORD) combined with file-read or collection verbs

## Motivation

The SANDWORM_MODE npm worm (Kodem Security, February 2026) deploys hidden MCP servers whose tool descriptions instruct AI coding assistants to:
1. Read files: `~/.ssh/id_rsa`, `~/.aws/credentials`, `.env`
2. Enumerate env vars by name pattern: any variable matching TOKEN, KEY, SECRET, or PASSWORD
3. Forward collected data to an attacker endpoint

The worm exploits the fact that AI coding agents (Claude Code, Cursor, GitHub Copilot Workspace) autonomously run `npm install` and then interact with newly registered MCP tools without human review of tool descriptions.

Existing coverage: `mcp_file_read_instruction` covers `~/.ssh` and `~/.aws` file paths. `mcp_collector_exfil` covers collect+forward-to-URL patterns. But the ENV variable name cluster — explicitly listing TOKEN/KEY/SECRET/PASSWORD as targets in a tool description — is not directly covered.

## Proposed Change

Add `mcp_env_credential_harvest` to `MCP_SECURITY_PATTERNS`:

```python
DetectionPattern(
    id="mcp_env_credential_harvest",
    name="MCP Environment Variable Credential Harvest Pattern",
    category="mcp_poisoning",
    pattern=_p(
        r"(?:"
        r"(?:read|collect|enumerate|gather|extract|find|get|list)\s+"
        r"(?:all\s+)?(?:environment\s+variables?|env\s+vars?|env\s+variables?)"
        r".{0,100}"
        r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL|API_KEY)"
        r"|"
        r"(?:environment\s+variables?\s+(?:containing|matching|with|named?|like)\s+"
        r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL|API_KEY))"
        r")"
    ),
    base_score=70,
    description="...",
    owasp_ref="OWASP LLM01: Prompt Injection (MCP Tool Poisoning / Supply Chain)",
    remediation_hint="...",
)
```

## Why Held Back

**FP risk from developer tooling descriptions**: Legitimate env management tools (dotenv-cli, env-cmd, direnv) may describe their functionality in terms of env variable names. The combination of "read env vars with TOKEN/KEY" could match legitimate tools that help developers manage their own credentials.

The combination detection (enumerate + credential keywords + exfil target) would need a three-part conjunction that increases pattern complexity beyond the ~100 LOC limit for a single addition.

## Suggested Next Step for Human Reviewer

1. Prototype the pattern against a corpus of legitimate env management tool descriptions to calibrate FP rate before implementing.
2. Consider requiring a three-part conjunction: (collection verb) + (env var target with TOKEN/KEY/SECRET/PASSWORD) + (exfiltration target URL or file path).
3. Source: https://www.kodemsecurity.com/resources/sandworm-mode-a-new-shai-hulud-style-npm-worm-threatening-developer-ai-toolchain-security
