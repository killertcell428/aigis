# Research: Incident Postmortems & CVEs — 2026-05-18T00-07

**Domain index:** 9 — `incident-postmortems`
**Cycle:** Third pass (prior passes covered Chainlit CVE-2026-22218, LangChain CVE-2026-34070,
LMDeploy CVE-2026-33626, SSRF patterns. This pass targets late-April–May 2026 incidents.)

---

## Key Findings

- **CVE-2026-33017 (CVSS 9.3) — Langflow unauthenticated RCE exploited within 20 hours.**
  Langflow's POST `/api/v1/build_public_tmp/{flow_id}/flow` endpoint accepted attacker-supplied
  flow definitions containing arbitrary Python code in node configuration fields, with no
  authentication required and no sandbox. An attacker sends one HTTP request embedding Python
  code (`exec()`, `subprocess.run()`, `os.system()`) in a `CustomComponent` node's `code`
  field and gets immediate shell access under the server's process identity. Within 20 hours of
  the GitHub advisory being published, Sysdig Threat Research observed active exploitation;
  CISA added CVE-2026-33017 to its KEV catalog. JFrog Security Research separately found that
  the "fixed" 1.8.1 version was still exploitable through a variant path.
  Sources:
  - https://thehackernews.com/2026/03/critical-langflow-flaw-cve-2026-33017.html
  - https://www.sysdig.com/blog/cve-2026-33017-how-attackers-compromised-langflow-ai-pipelines-in-20-hours
  - https://research.jfrog.com/post/langflow-latest-version-was-not-fixed/
  **Aigis takeaway:** An AI agent directed to generate or modify Langflow flow definitions could
  be manipulated (via prompt injection) to embed Python code execution payloads. Detection of
  Python exec/eval/subprocess primitives in flow configuration JSON (`"code"` field context) is
  directly actionable.

- **CVE-2026-21858 (CVSS 10.0) + CVE-2026-27493 — n8n expression injection, 24,700 instances
  exposed, CISA KEV.**
  n8n's workflow engine evaluates `{{ }}` template expressions as JavaScript in several node
  types (including Form nodes, Code nodes, and Set nodes). CVE-2026-21858 allowed unauthenticated
  RCE via the n8n web-form handler in versions ≤1.65.0; CVE-2026-27493 is a second-order
  expression injection in Form nodes that chains expression evaluation with a sandbox escape to
  reach host-level code execution. CISA reported 24,700 exposed instances at the time of
  advisory publication, flagged in its Known Exploited Vulnerabilities (KEV) catalog.
  Attackers exploited n8n expression context to call `require('child_process').execSync('id')`,
  `process.env.SECRET`, or `process.mainModule.require('child_process')` — none of which appear
  in any legitimate n8n workflow expression. Fixed in n8n ≥1.121.0.
  Sources:
  - https://thehackernews.com/2026/01/critical-n8n-vulnerability-cvss-100.html
  - https://horizon3.ai/attack-research/attack-blogs/the-ni8mare-test-n8n-rce-under-the-microscope-cve-2026-21858/
  - https://thehackernews.com/2026/03/cisa-flags-actively-exploited-n8n-rce.html
  **Aigis takeaway:** The `{{ require('child_process') }}` and `{{ process.env.* }}` patterns are
  reliable attack signals with near-zero false positive rate in any AI payload. An AI agent
  generating n8n workflow YAML/JSON could be manipulated to inject these expressions. New rule
  `afe_n8n_expression_injection` warranted.

- **CVE-2026-42208 (CVSS 9.3) — LiteLLM SQL injection in AI proxy Authorization header, added
  to CISA KEV within 3 weeks of disclosure.**
  LiteLLM (the open-source LLM gateway with ~3.4M daily downloads) had a pre-authentication
  SQL injection in the proxy's API key verification path: the caller-supplied key from the
  `Authorization: Bearer <key>` header was interpolated directly into a SQL query without
  parameterization. Exploitation required one HTTP request to any LLM API route proxied through
  LiteLLM. Attackers read `litellm_credentials.credential_values` and `litellm_config` tables
  — both containing upstream LLM provider API keys. The first in-the-wild exploitation was
  recorded 26 hours after the GitHub advisory was indexed (April 26, 2026), and CISA added it
  to KEV on May 8, requiring federal agency patches by May 11.
  Sources:
  - https://thehackernews.com/2026/04/litellm-cve-2026-42208-sql-injection.html
  - https://bishopfox.com/blog/cve-2026-42208-pre-authentication-sql-injection-in-litellm-proxy
  - https://www.sysdig.com/blog/cve-2026-42208-targeted-sql-injection-against-litellms-authentication-path-discovered-36-hours-following-vulnerability-disclosure
  **Aigis takeaway:** Existing `sqli_*` patterns cover the generic SQL injection class. The
  LiteLLM case reinforces that AI gateways are high-value targets; no new pattern needed
  but the existing SQL injection patterns are justified for API gateway contexts.

- **Microsoft Security Blog — "Prompts Become Shells": Semantic Kernel RCE chain (May 2026).**
  Microsoft's May 7 post documented the broader pattern of prompt injection → framework RCE:
  CVE-2026-26030 (Semantic Kernel Python SDK, CVSS 9.9) and CVE-2026-25592 (.NET SDK) were
  exploitation examples. The root cause was LLM-controlled values reaching `eval()` in the
  InMemoryVectorStore filter path. Microsoft noted that enabling Code Interpreter, Python REPL,
  or `allow_dangerous_code=True` in LangChain expands the prompt-injection-to-RCE attack
  surface by giving the agent a direct code execution primitive. In Q1 2026, 93% of surveyed
  AI agent deployments used unscoped API keys, and the "unsafe default" of `allow_dangerous_code`
  in the CSV Agent node pre-1.8.0 exposed arbitrary Python execution via a one-line prompt
  injection. CVE-2026-26030 (afe_python_mro_escape) was addressed in a prior cycle.
  Source: https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
  **Aigis takeaway:** `allow_dangerous_code=True` in LangChain CSV Agent, Pandas DataFrame
  Agent, and similar agent types enables arbitrary Python REPL execution. Any AI agent output
  suggesting this configuration is a risk signal worth flagging. New rule
  `sc_langchain_dangerous_code` warranted.

- **OX Security — MCP STDIO design vulnerability enables RCE across 7,000+ servers (April 2026).**
  OX Security disclosed that the MCP STDIO transport model (all languages: Python, TypeScript,
  Java, Rust) accepts arbitrary OS command strings in the `command` field of MCP server
  configurations; Anthropic confirmed this is by design. OX demonstrated RCE on LiteLLM,
  LangChain, IBM LangFlow, and six production platforms by supplying crafted STDIO launch
  commands. The existing `sc_ide_hook_tamper` pattern covers the STDIO hook write path via
  `.claude/settings.json`. No new rule is needed for the STDIO command vector itself (it
  overlaps with existing `cmdi_shell` and `sc_ide_hook_tamper` patterns), but the finding
  validates continued investment in MCP security coverage.
  Source: https://thehackernews.com/2026/04/anthropic-mcp-design-vulnerability.html
  **Aigis takeaway:** Existing patterns `sc_ide_hook_tamper`, `cmdi_shell`, and `se_reverse_shell`
  cover the primary STDIO attack path. No new rule needed this cycle for MCP STDIO.

- **Langflow `allow_dangerous_code=True` unsafe default hardcoded in CSV Agent pre-1.8.0.**
  Independent of CVE-2026-33017, Microsoft's agentic security post and JFrog analysis both
  documented that Langflow ≤1.7.x hardcoded `allow_dangerous_code=True` in the CSV Agent and
  Pandas DataFrame Agent nodes. This parameter disables LangChain's internal safety guard and
  passes user-controlled input directly to a Python REPL. Any prompt injection into the agent's
  data pipeline could reach `exec()` without any additional exploit step. The same parameter
  name (`allow_dangerous_code`) is used across LangChain, Langflow, and downstream frameworks.
  Source: https://www.microsoft.com/en-us/security/blog/2026/05/14/configuration-becomes-vulnerability-exploitable-misconfigurations-ai-apps/
  **Aigis takeaway:** Detecting `allow_dangerous_code=True` in AI-generated configuration or
  prompts is directly actionable and complements the `afe_python_mro_escape` and
  `sc_langchain_deserialization` patterns already in place.

- **Adversa AI — Top Agentic AI Security Resources May 2026: framework RCE becoming commodity.**
  Adversa AI's May 2026 roundup noted that agentic framework RCE vulnerabilities (CrewAI, n8n,
  Langflow, Semantic Kernel, and LiteLLM) have consolidated into a class of attack where
  prompt injection escalates to host-level code execution in under 20 hours post-disclosure.
  The attack pattern is now templated in commodity red-teaming tools like DeepTeam.
  Source: https://adversa.ai/blog/top-agentic-ai-security-resources-may-2026/
  **Aigis takeaway:** Rule-based detection of the shared primitives (`{{ require(...) }}`,
  `allow_dangerous_code`, `build_public_tmp`, STDIO command injection) is more durable than
  framework-specific signatures, because the same payload classes reappear across frameworks.

- **CISA KEV cadence for AI framework CVEs accelerating (Q1–Q2 2026).**
  CISA added four AI framework CVEs to KEV between January and May 2026:
  CVE-2026-21858 (n8n, CVSS 10.0), CVE-2026-33017 (Langflow, CVSS 9.3),
  CVE-2026-33626 (LMDeploy, CVSS 7.5), and CVE-2026-42208 (LiteLLM, CVSS 9.3).
  All four were actively exploited within 36 hours of disclosure, two within 20 hours.
  Source: https://www.dataminr.com/resources/intel-brief/n8n-remote-code-execution-vulnerability/
  **Aigis takeaway:** The accelerating exploitation cadence justifies proactive rule additions
  ahead of the next KEV addition cycle. Both `afe_n8n_expression_injection` and
  `sc_langchain_dangerous_code` address CVEs already in KEV.

---

## Candidate Hardenings

1. **`afe_n8n_expression_injection`** (score 75, sandbox_escape) — Detect n8n `{{ }}` expression
   syntax containing dangerous JavaScript operations: `require('child_process')`, `process.env.*`,
   `process.mainModule`, `execSync(`, `spawnSync(`, `new Function(`. Derived from
   CVE-2026-21858 (CVSS 10.0, CISA KEV) and CVE-2026-27493 (expression injection via n8n Form
   nodes). These operations are never legitimate in n8n workflow expressions; legitimate n8n
   expressions use `$json.*`, `$("Node").item.*`, and built-in n8n functions, not Node.js system
   APIs. Add to `SANDBOX_ESCAPE_PATTERNS`.

2. **`sc_langchain_dangerous_code`** (score 60, supply_chain) — Detect explicit use of
   `allow_dangerous_code=True` (Python) or `"allow_dangerous_code": true` (JSON) in AI-generated
   configurations or agent instructions. This parameter disables LangChain's internal safety guard
   for CSV Agent, Pandas DataFrame Agent, and similar REPL-backed agent types, enabling arbitrary
   Python execution via prompt injection. Derived from: Microsoft Security Blog (May 2026),
   Langflow ≤1.7.x hardcoded default in CSV Agent node. Complements existing
   `afe_python_mro_escape` and `sc_langchain_deserialization` patterns. Add to `SUPPLY_CHAIN_PATTERNS`.

3. **Hardening guide: AI Workflow Automation RCE (n8n, Langflow, LiteLLM)** — A `docs/hardening/`
   guide documenting the class of agentic framework vulnerabilities where prompt injection escalates
   to host-level RCE through code-execution defaults. → Deferred (prioritizing the two new rules
   to stay within 100 LOC non-test limit).
