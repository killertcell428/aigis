# Pending: MCPoison snapshot-swap timing detection

**Title:** Stateful post-approval snapshot change alerting (MCPoison / CVE-2025-54136)

**Motivation:** CVE-2025-54136 (MCPoison, Check Point Research) shows that an attacker
who controls a shared MCP config repository can silently swap a previously-approved benign
MCP server entry for a malicious one after the victim has already approved it. The existing
`mcp_rug_pull_indicator` rule catches language *about* version changes in tool text, but
does not catch an actual configuration swap that happens between approval and the next
agent session startup.

**Proposed change:** Extend `MCPToolSnapshot` + `save_snapshots`/`load_snapshots` to
record an "approval timestamp" field when a user explicitly approves a tool. If a
subsequent snapshot differs AND the diff occurs within a configurable window (default:
7 days), surface a `rug_pull_alert` with `swapped_after_approval=True`. Would also require
a small CLI flag (`aig mcp --approve <server>`) to write the approval timestamp.

**Why held back:** Requires a stateful persistence model (approval ledger file) plus a
new CLI subcommand interaction. The approval-recording path involves user-facing workflow
changes that should be reviewed by the human maintainer before shipping. This is also
closer to a breaking workflow change (new CLI arg) than a pure additive rule. Changes
would span `mcp_scanner.py`, `cli.py`, and the snapshot JSON schema — likely >100 LOC.

**Suggested next step:** Design the approval-ledger schema and CLI UX first (PR/design doc),
then implement in a single focused cycle once design is agreed.
