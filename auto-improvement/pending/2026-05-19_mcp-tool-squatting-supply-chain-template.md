# Pending: MCP Tool Squatting Supply-Chain Compliance Template

**Title:** Compliance template field for MCP server package integrity verification

**Motivation:**
CVE-2025-54994 (`@akoskm/create-mcp-server-stdio`) demonstrated real-world typosquatting in
the MCP ecosystem. Unlike traditional software supply-chain attacks, MCP tool squatting directly
targets AI agent tool selection: a malicious server with a near-identical name to a trusted one
can intercept tool calls without any detectable change in the tool description text.

**Research finding:**
- CVE-2025-54994: npm typosquatting of an MCP server creation utility (UpGuard, 2025)
- arxiv:2506.01333: formal analysis of tool squatting attack class and ETDI mitigation
- PipeLab 2026 incident catalog: multiple instances of same-name MCP server impersonation

**Proposed change:**
Extend an existing compliance template (e.g., `policy_templates/mcp_security.yaml` or
`policy_templates/supply_chain.yaml`) with a new section:

```yaml
mcp_server_integrity:
  description: "Controls for verifying MCP server and tool definition authenticity"
  fields:
    - package_hash_pinning: "MCP server packages pinned to a verified hash or version"
    - signed_tool_allow_list: "Approved tool definitions stored as a signed allow-list"
    - rug_pull_detection: "Tool definition diffs checked on each session start"
    - server_origin_verification: "MCP servers validated against a known-good registry"
```

**Why it was held back:**
Belongs to the supply-chain-llm domain (index 5), not agent-tool-abuse. Adding it here would
spread the supply-chain work across two domains and make the compliance template harder to
maintain consistently.

**Constraint that blocked it:**
No hard constraint — just domain alignment. Reserve for supply-chain-llm cycle (index 5).

**Suggested next step:**
In the next supply-chain-llm cycle, implement this compliance template extension alongside any
other supply-chain hardening for that cycle.
