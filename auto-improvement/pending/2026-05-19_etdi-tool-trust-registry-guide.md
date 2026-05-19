# Pending: ETDI Tool Trust Registry Documentation

**Title:** Hardening guide for MCP tool identity verification (ETDI approach)

**Motivation:**
Tool squatting and rug pull attacks can occur without any detectable text signal in the tool
description itself — the manipulation happens at the server-origin or tool-version level.
The Enhanced Tool Definition Interface (ETDI) paper (arxiv:2506.01333) proposes signing tool
definitions with OAuth-backed credentials so that MCP clients can verify definition integrity.
As of May 2026, this spec extension has not been adopted officially, but the approach is
well-documented and actionable for operators who maintain their own MCP server allow-lists.

**Research finding:**
arxiv:2506.01333 (ETDI, Jun 2025): OAuth-enhanced tool definitions with cryptographic signatures
prevent both tool squatting (same-name impersonation by a different server) and rug pulls (silent
redefinition after initial approval). The paper formally defines both attack classes and proposes
a backward-compatible extension to the MCP tool registration flow.

**Proposed change:**
Add `docs/hardening-mcp-tool-trust.md` with:
- Plain-language explanation of rug pull and tool squatting attacks
- ETDI approach (signed tool allow-lists)
- Practical operator guidance: maintain a pinned, hash-verified list of trusted MCP servers and
  tool definition versions; re-verify on each session start
- Example: how to combine aigis MCP scanning + a local signed allow-list for defense-in-depth

**Why it was held back:**
Documentation-only change. Suited for a dedicated documentation cycle or when the ETDI spec
receives wider adoption to warrant official guidance.

**Constraint that blocked it:**
No implementation constraint — pure documentation. Held because the cycle already delivered a
detection-pattern hardening, and the documentation adds value but has lower urgency.

**Suggested next step:**
When domain 8 (compliance-regulation) or domain 5 (supply-chain-llm) runs next, consider
adding this guide alongside any compliance template updates. The guide pairs well with a
supply-chain template field for MCP server integrity verification.
