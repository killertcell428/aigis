# Research: data-exfiltration — 2026-05-20T06-03

## Domain: data-exfiltration (index 2, fourth pass)
## Cycle timestamp: 2026-05-20T06-03

Previous cycles covered:
- Cycle 1 (2026-05-07): Markdown image URL exfil, OAST relay domains.
- Cycle 2 (2026-05-10): DNS encode instruct, EchoLeak reference-style markdown bypass, tunnel relay URLs, Unicode Tag Block (pending resolved in next cycle), Mermaid href exfil (pending → resolved later).
- Cycle 3 (2026-05-14): Unicode Tag Block smuggling implemented, CSS font injection, sharded exfiltration (arxiv:2602.22450), CSS hidden text (pending).

This pass focuses on:
1. SSRF via RFC 1918 private IPs in MCP OAuth/CIMD fields (extending existing IMDS coverage)
2. Log-To-Leak attacks: prompt injection forcing agents to call logging MCP tools
3. Credential leakage via debug print statements in agent skills (arxiv:2604.03070)
4. Cloud log injection via LLM debugging agents (LogJack, arxiv:2604.15368)

---

## Findings

- **CIMD SSRF via RFC 1918 Private IP — MCP November 2025 spec attack surface**:
  The MCP November 2025 specification (2025-11-25) introduced Client ID Metadata Documents (CIMD):
  clients identify themselves by registering a URL that the Authorization Server must fetch to
  retrieve client metadata. Post-release security analysis found that CIMD URLs are a new SSRF
  vector — a malicious client registers a CIMD URL pointing at an internal endpoint
  (10.x.x.x, 192.168.x.x, 172.16-31.x.x, or 127.0.0.1), causing the AS to make requests to
  internal infrastructure. The existing `mcp_ssrf_metadata_endpoint` rule covers cloud IMDS
  (169.254.169.254) but NOT the RFC 1918 private IP ranges that are equally reachable in most
  enterprise and cloud environments.
  - Source: https://modelcontextprotocol.io/specification/2025-11-25/changelog
  - Source: https://aaronparecki.com/2025/11/25/1/mcp-authorization-spec-update
  - **aigis takeaway**: Implement `mcp_ssrf_private_ip` (input, score 70) scoped to OAuth
    field names (authorization_endpoint, client_metadata_url, jwks_uri, redirect_uri, etc.)
    to close the RFC 1918 gap left by `mcp_ssrf_metadata_endpoint`. **→ IMPLEMENTED this cycle.**

- **CVE-2026-39974 — n8n-MCP SSRF via multi-tenant HTTP headers (CVSS 9.8)**:
  BlueRock Security found that the n8n-MCP server (MCP providing AI assistants with access to
  n8n node documentation) allowed an authenticated attacker to pass arbitrary URLs through
  multi-tenant HTTP headers, causing the server to issue HTTP requests to those URLs and return
  the response bodies. This creates a powerful exfiltration channel: the attacker queries
  169.254.169.254/latest/meta-data/ to extract cloud IAM credentials, or private-range endpoints
  to access internal APIs. BlueRock's broader analysis found 36.7% of 7,000+ MCP servers lacked
  sufficient IP validation. Fixed in n8n-MCP v2.47.4 (SSRF blocklist introduced).
  A companion CVE, CVE-2026-42449, affects the same package with a related CWE-918 issue.
  - Source: https://www.sentinelone.com/vulnerability-database/cve-2026-39974/
  - Source: https://nvd.nist.gov/vuln/detail/CVE-2026-39974
  - Source: https://vulnerablemcp.info/
  - **aigis takeaway**: Reinforces the need for `mcp_ssrf_private_ip` rule. The scoping to
    OAuth field names reduces FP risk for dev-environment tools while covering the attack surface.

- **Log-To-Leak — Forced logging tool invocation for exfiltration (OpenReview, Oct 2025)**:
  A systematic study of prompt-level privacy attacks that covertly force an MCP-enabled agent to
  invoke a malicious logging tool with sensitive content (user queries, tool responses, agent
  replies) as the log argument. The framework decomposes attacks into four components: Trigger
  (initial injection), Tool Binding (naming the specific log tool), Justification (fake compliance
  or audit framing), and Pressure (urgency). Tested across 5 real MCP servers and 4 LLM agents
  (GPT-4o, GPT-5, Claude-Sonnet-4, GPT-OSS-120b) with consistently high ASR. This is distinct
  from `mcp_collector_exfil` (which catches explicit "collect+send-to-URL"), using an existing
  seemingly-legitimate tool instead of an overt exfil endpoint.
  - Source: https://openreview.net/forum?id=UVgbFuXPaO
  - **aigis takeaway**: The pattern would target "invoke/call [log/debug/audit] tool with
    [user query / conversation / session content]". Held back this cycle due to FP risk from
    legitimate observability tool documentation. Saved to pending/.

- **Credential Leakage in LLM Agent Skills — Large-Scale Study (arxiv:2604.03070, Apr 2026)**:
  First large-scale empirical study of credential leakage in 17,022 skills from the SkillsMP
  marketplace. Found 520 affected skills with 1,708 security issues. Key findings:
  (1) 76.3% of leakage only surfaces via cross-modal analysis (natural-language description + code);
  (2) Debug logging (print/console.log to stdout) causes 73.5% of leaks, exposing credentials
  to the LLM's context window; (3) 89.6% of leaked credentials are exploitable without privileges.
  Primary attack vector is developer negligence: `print(api_key)`, `console.log(token)`.
  - Source: https://arxiv.org/abs/2604.03070
  - **aigis takeaway**: An output filter catching debug print statements with credential-like
    variable names could detect skills that leak credentials into LLM context. Held back this
    cycle due to high FP risk (legitimate logging) and cross-modal detection complexity.
    Saved to pending/.

- **LogJack — Cloud Log Injection Against LLM Debugging Agents (arxiv:2604.15368, Apr 2026)**:
  LLM debugging agents that ingest cloud logs (AWS CloudWatch, GCP Cloud Logging, Azure Monitor)
  and auto-remediate issues are vulnerable to indirect prompt injection via crafted log entries.
  Benchmark of 42 payloads across 5 log categories, 8 models: verbatim command execution rates
  0% (Claude Sonnet 4.6) to 86.2% (Llama 3.3 70B). Remote code execution via `curl | bash`
  succeeded on 6/8 models. Existing cloud guardrails largely failed: Azure Prompt Shield detected
  only 1/32 obvious payloads; GCP Model Armor detected none. The existing `mcp_log_format_injection`
  rule covers the `[LEVEL]`-prefix camouflage form. LogJack additionally shows attacks via
  JSON structured logs (`{"level": "ERROR", "message": "...injection..."}`) not covered by
  the existing rule — this is a candidate for a follow-on extension.
  - Source: https://arxiv.org/abs/2604.15368
  - **aigis takeaway**: Possible extension of `mcp_log_format_injection` to cover JSON
    structured log format (`"level":` / `"severity":` field). Saved to pending/ for next cycle.

- **arxiv:2506.01055 — Personal Data Leakage via Simple Injection During Agent Tasks (Jun 2025)**:
  Study using a fictitious banking agent shows 20% average ASR for data-flow-based injection
  attacks; 15-50 percentage point utility drop under attack. Most LLMs avoid leaking passwords
  due to safety alignment but remain vulnerable to other PII leakage. Demonstrates that even
  "simple" injections can exfiltrate observed personal data during task execution, not only
  system prompts.
  - Source: https://arxiv.org/abs/2506.01055
  - **aigis takeaway**: Validates existing PII detection patterns; no new rule needed.

- **Credential Leakage via Agent Skill Print Statements — stdout-to-LLM Exfil vector**:
  Skills that call `print(api_key)` or `console.log(secret)` during execution expose those
  values in the LLM's tool-output context window. An indirect prompt injection can then
  instruct the agent to summarize or forward that output. The arxiv:2604.03070 study found
  the majority of skill marketplace leaks happen this way — not via injection, but via
  developer inadvertence combined with stdout being fed into the LLM context.
  - Source: https://arxiv.org/abs/2604.03070
  - **aigis takeaway**: Possible output filter `out_debug_credential_print` that flags tool
    output containing `print(` or `console.log(` with adjacent credential keywords.
    Held back due to FP complexity. Saved to pending/.

---

## Candidate hardenings

1. **`mcp_ssrf_private_ip`** (score 70, MCP_SECURITY_PATTERNS) — Detect RFC 1918 private IP
   addresses in OAuth/CIMD endpoint fields (authorization_endpoint, client_metadata_url,
   jwks_uri, redirect_uri, token_endpoint). Closes the gap left by `mcp_ssrf_metadata_endpoint`
   which only covers cloud IMDS addresses. Scoped to OAuth field names to minimize FP from
   legitimate internal dev-environment URLs. **Selected for this cycle.**

2. **`mcp_log_to_leak`** (score 65, MCP_SECURITY_PATTERNS) — Detect injected prompts that bind
   a logging/audit/debug tool by name and instruct the agent to invoke it with sensitive content
   (user query, conversation, session). Based on Log-To-Leak (OpenReview, Oct 2025).
   **Held back: FP risk from legitimate observability documentation. Saved to pending/.**

3. **JSON structured log injection extension** — Extend `mcp_log_format_injection` to cover
   `"level":`/`"severity":` JSON field patterns (LogJack, arxiv:2604.15368).
   **Held back: overlap with existing rule needs careful scope analysis. Saved to pending/.**

4. **`out_debug_credential_print`** — Output filter detecting debug print/log statements
   adjacent to credential-named variables in tool output.
   **Held back: High FP risk, cross-modal complexity. Saved to pending/.**
