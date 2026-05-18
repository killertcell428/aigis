# Research: Incident Postmortems & CVEs — 2026-05-18T00-00

**Domain index:** 9 — `incident-postmortems`
**Cycle:** Third pass (prior passes covered CVE-2026-26030 MRO escape, Chainlit CVE-2026-22218 file read, LangChain CVE-2026-34070 path traversal)

---

## Key Findings

- **CVE-2025-59528 (CVSS 10.0) — Flowise CustomMCP node RCE via JavaScript Function() constructor (actively exploited April 2026).**
  Flowise, an open-source visual AI agent builder with 12,000+ public instances, contained a max-severity RCE vulnerability in its CustomMCP node. The node accepted a user-supplied `mcpServerConfig` JSON string and executed its contents via JavaScript's `Function()` constructor — functionally identical to `eval()`. The payload `new Function('return require("child_process").execSync("id")')()` achieves host-level code execution with full Node.js runtime access, including `child_process`, `fs`, `process.env`, and all installed modules. Flowise instances typically store API keys for OpenAI, Anthropic, Azure OpenAI, and database connection credentials; exploitation exposes all of them. The fix (Flowise 3.0.6, September 2025) replaced `Function()` with `JSON5.parse()`. Despite the patch being available 6+ months earlier, VulnCheck first observed exploitation from a Starlink IP in early April 2026, with 12,000–15,000 exposed instances still unpatched at disclosure.
  Sources:
  - https://thehackernews.com/2026/04/flowise-ai-agent-builder-under-active.html
  - https://github.com/FlowiseAI/Flowise/security/advisories/GHSA-3gcm-f6qx-ff7p
  - https://www.bleepingcomputer.com/news/security/max-severity-flowise-rce-vulnerability-now-exploited-in-attacks/
  **Aigis takeaway:** The `Function()` constructor combined with Node.js system modules (`child_process`, `fs`, `net`, `process.env`) is a distinctive, high-confidence RCE signal in any AI agent or MCP configuration context. Add a new `sc_flowise_js_rce` pattern to `SUPPLY_CHAIN_PATTERNS`.

- **CVE-2026-42208 (CVSS 9.3) — LiteLLM proxy pre-authentication SQL injection, CISA KEV-listed (April 2026).**
  BerriAI's LiteLLM, a widely used open-source LLM API gateway with 22,000+ GitHub stars, contained a pre-auth SQL injection in its proxy API key verification path. Versions >=1.81.16, <1.83.7 concatenated the caller's `Authorization: Bearer` value directly into a SQL query against `LiteLLM_VerificationToken` without parameter binding. A single quote in the Bearer token allowed the attacker to append arbitrary SQL. Exploitation was confirmed 36 hours after the advisory appeared on GitHub, targeting `litellm_credentials.credential_values` and `litellm_config` tables that hold upstream LLM provider API keys (OpenAI, Anthropic, AWS Bedrock) and proxy runtime configuration. CISA added this to the Known Exploited Vulnerabilities catalog on May 8, 2026, requiring Federal agencies to patch by May 11. Fixed in LiteLLM v1.83.7.
  Sources:
  - https://thehackernews.com/2026/04/litellm-cve-2026-42208-sql-injection.html
  - https://www.sysdig.com/blog/cve-2026-42208-targeted-sql-injection-against-litellms-authentication-path-discovered-36-hours-following-vulnerability-disclosure
  - https://bishopfox.com/blog/cve-2026-42208-pre-authentication-sql-injection-in-litellm-proxy
  **Aigis takeaway:** The existing `sqli_*` pattern family covers general SQL injection syntax. The specific LiteLLM attack targets LLM-specific credential tables; however, general SQL injection patterns are already in place. A specialized pattern for `litellm_credentials` table references would be additive but low priority given general coverage.

- **Microsoft Semantic Kernel CVE-2026-25592 and CVE-2026-26030 — Prompt injection to RCE via MRO traversal (May 2026).**
  Microsoft disclosed two CVEs in Semantic Kernel (SK) confirming that prompt injection can cross the boundary from content manipulation to host-level code execution in AI agent frameworks. CVE-2026-26030 (already covered by `afe_python_mro_escape` in this codebase) affects the Python SDK; CVE-2026-25592 affects the .NET SDK (versions <1.71.0) through a different injection path. Microsoft's security blog documented that "once an AI model is wired to tools, prompt injection draws a thin line between being a content security problem and becoming a code execution primitive." Exploitation demonstrated launching `calc.exe` from a single injected prompt against an SK agent. No new Aigis pattern is needed beyond the existing `afe_python_mro_escape`.
  Source: https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
  **Aigis takeaway:** Validates the existing `afe_python_mro_escape` coverage. No additional pattern needed.

- **Indirect prompt injection confirmed in production — 32% increase in malicious web content (April 2026).**
  Google (analyzing 2–3 billion crawled pages/month) and Forcepoint (active threat hunting) independently documented a 32% relative increase in malicious indirect prompt injection payloads in publicly crawled web pages between November 2025 and February 2026. Documented real-world incidents include: a poisoned email causing GPT-4o to execute malicious Python that exfiltrated SSH keys (80% success rate in trials); the Salesforce AgentForce Web-to-Lead attack (data exfiltration through an expired domain); the EchoLeak Microsoft 365 Copilot zero-click attack (extracts OneDrive, SharePoint, Teams data); and the Perplexity Comet invisible-text Reddit attack (leaked one-time passwords). Indirect prompt injection is no longer theoretical.
  Sources:
  - https://www.helpnetsecurity.com/2026/04/24/indirect-prompt-injection-in-the-wild/
  - https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/
  **Aigis takeaway:** Validates the indirect injection pattern family. Existing coverage is directionally correct.

- **Three AI coding agents leaked secrets through a single prompt injection — April 2026.**
  Researchers demonstrated a single prompt injection attack that simultaneously triggered secret exfiltration through Claude Code, Gemini CLI, and GitHub Copilot by targeting a malicious PR title. Anthropic rated the finding CVSS 9.4 critical. The attack bypassed three runtime mitigations at GitHub (environment variable filtering, output secret scanning, network firewall) by routing exfiltration back through GitHub's own APIs. GitGuardian's 2026 State of Secrets Sprawl report found 24,000+ unique secrets exposed in MCP configuration files on public GitHub repositories, including 2,100+ confirmed valid credentials.
  Sources:
  - https://venturebeat.com/security/ai-agent-runtime-security-system-card-audit-comment-and-control-2026
  - https://waxell.ai/blog/ai-coding-agent-prompt-injection-cicd-2026
  **Aigis takeaway:** Reinforces the value of API-key exfiltration patterns. No new pattern needed beyond current coverage.

- **65% of organizations experienced at least one AI agent security incident in 2026 (CSA/Token Security, April 2026).**
  Cloud Security Alliance and Token Security research found that 65% of enterprises with deployed AI agents had experienced a cybersecurity incident, with 61% of those incidents involving sensitive data exposure. The most common failure mode was data exfiltration through agent-generated content (tool responses, summaries, emails). This validates continued investment in output-filter patterns.
  Source: https://www.kiteworks.com/cybersecurity-risk-management/ai-agent-security-incidents-2026/
  **Aigis takeaway:** Validates the output filter investment. No new pattern from this specific finding.

---

## Candidate Hardenings

1. **`sc_flowise_js_rce`** — Detect `new Function()` constructor or `Function.prototype.constructor` calls combined with dangerous Node.js system modules (`child_process`, `fs`, `net`, `process.env`) in AI agent configuration context. Also detect `eval()` or `new Function()` inside `mcpServerConfig`, `"command":`, or `"args":` JSON fields. Derived from Flowise CVE-2025-59528 (CVSS 10.0). **→ IMPLEMENTED this cycle.**

2. **`sc_litellm_cred_sqli`** — Detect references to LiteLLM-specific credential tables (`litellm_credentials`, `LiteLLM_VerificationToken`, `litellm_config`) in SQL injection context. Derived from CVE-2026-42208. Deferred: general `sqli_*` patterns already provide broad SQLi coverage; the LiteLLM-specific table names add narrow incremental value.

3. **Hardening guide for AI agent configuration injection** — Document the class of attacks where AI agent workflow configuration fields (Flowise node configs, MCP server specs, LangChain chain configs) are used as code-injection vectors. → Deferred (>100-LOC combined with documentation).
