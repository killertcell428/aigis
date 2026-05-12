# Research: Incident Postmortems & CVEs — 2026-05-12T07-00

**Domain index:** 9 — `incident-postmortems`
**Cycle:** Second pass (prior pass at 2026-05-09T10-00 covered CVE-2026-26030 MRO escape and ClawHavoc memory-file poisoning)

---

## Key Findings

- **CVE-2026-22218 (CVSS 7.1) & CVE-2026-22219 (CVSS 8.3) — Chainlit AI framework file-read and SSRF (Jan 2026).**
  Kodem / BleepingComputer / The Register reported two critical flaws in Chainlit, a popular
  Python framework for building AI chat applications (patched in v2.9.4, Dec 24 2025):
  - CVE-2026-22218: Improper validation of user-controlled element paths allowed an
    authenticated client to trigger an arbitrary file read by sending a malicious
    "update element" request with a tampered `url` field. The primary attack chain reads
    `/proc/self/environ` to exfiltrate API keys, cloud credentials, and connection strings.
    SQLite database files (SQLAlchemy backend) were also reachable.
  - CVE-2026-22219: The SQLAlchemy backend makes outbound HTTP requests for custom elements;
    supplying a cloud metadata endpoint (`http://169.254.169.254/...`) as the element URL
    causes the Chainlit server to fetch AWS IAM credentials and return them in the element
    payload. The SSRF path did not require any special tool integration — it worked on the
    base UI framework.
  Source: https://www.kodemsecurity.com/resources/cve-2026-22218-cve-2026-22219-arbitrary-file-read-ssrf-in-chainlit
  **Aigis takeaway:** `/proc/self/environ` in an AI prompt or tool response is never
  legitimate; it is the canonical credential-theft target in framework file-read CVEs.
  The existing `se_container_escape` pattern covers `/proc/self/exe|root|ns` but not
  `/proc/self/environ`. A new pattern covering sensitive file paths is warranted.

- **CVE-2026-34070 (CVSS 7.5) — LangChain Core path traversal in legacy load_prompt (Mar 2026).**
  Elvinlatifli / GitLab advisory / The Hacker News described a path traversal vulnerability
  in `langchain_core.prompts.loading.load_prompt()` and `load_prompt_from_config()`. These
  functions accept user-controlled file paths without sanitizing `../` sequences or absolute
  paths. An attacker can craft a malicious configuration JSON or instruct an agent to call
  `load_prompt('../../../etc/shadow')`, reading arbitrary files whose extensions are `.txt`,
  `.json`, or `.yaml`.
  - The attacker supplies a crafted path via prompt injection into an agent that reads external
    documents or configuration files, then calls load_prompt() on the result.
  - Impact: arbitrary file read → API key/credential disclosure from `/proc/self/environ`,
    `/etc/shadow`, or any file with a safe extension.
  - Fixed in `langchain-core >= 1.2.22`; legacy `load_prompt` / `load_prompt_from_config`
    are now formally deprecated in favour of `langchain_core.load` serialization APIs.
  Sources:
  - https://advisories.gitlab.com/pkg/pypi/langchain-core/CVE-2026-34070/
  - https://medium.com/@imr1ck/cve-2026-34070-how-i-discovered-a-high-severity-path-traversal-in-langchain-core-38b0828a34d8
  **Aigis takeaway:** Add a pattern detecting `load_prompt()` or `load_prompt_from_config()`
  calls with traversal sequences or sensitive absolute paths, complementing the existing
  `sc_langchain_deserialization` pattern that covers CVE-2025-68664.

- **CVE-2026-33626 (CVSS 7.5) — LMDeploy vision-language SSRF exploited in 12.5 hours (Apr 2026).**
  Sysdig Threat Research / The Hacker News documented the first CVE in the LMDeploy LLM
  inference engine family. The `load_image()` function in `lmdeploy/vl/utils.py` fetches
  arbitrary URLs without validating private/internal IP ranges. Attackers used it as a
  generic SSRF primitive — requesting `http://169.254.169.254/latest/meta-data/` to obtain
  IAM credentials, then pivoting to scan Redis (6379), MySQL (3306), and administrative
  interfaces. The entire attack unfolded across 10 HTTP requests in 8 minutes; the first
  exploit attempt was logged 12 hours 31 minutes after the GitHub advisory was published.
  - The attack rotated between two vision-language model variants to avoid raising anomaly alerts.
  - Fixed in LMDeploy 0.12.3.
  Sources:
  - https://thehackernews.com/2026/04/lmdeploy-cve-2026-33626-flaw-exploited.html
  - https://vulert.com/blog/lmdeploy-cve-2026-33626-ssrf/
  **Aigis takeaway:** The existing `mcp_ssrf_metadata_endpoint` pattern already catches
  `169.254.169.254` references. No new pattern needed for LMDeploy specifically, but the
  CVE reinforces that AI frameworks' file/image loaders are an underappreciated SSRF surface.

- **36.7% of public MCP servers potentially vulnerable to SSRF (May 2026).**
  PipeLab / Adversa AI research scanning 7,000+ public MCP servers found that 36.7% exposed
  at least one tool (commonly a URL-fetch or image-load tool) that did not block private IP
  ranges. Researchers demonstrated retrieving AWS IAM access keys from an EC2 instance's
  metadata endpoint via a single prompt-injected tool call.
  Source: https://pipelab.org/learn/preventing-ssrf-in-ai-agents/
  **Aigis takeaway:** Validates continued investment in SSRF detection. The `mcp_ssrf_metadata_endpoint`
  pattern is already in place; the `/proc/self/environ` gap (see Chainlit findings) is the
  highest-value addition.

- **MCP server-puppeteer SSRF + indirect prompt injection advisory (May 2026).**
  GitHub issue #3662 on modelcontextprotocol/servers disclosed a combined SSRF + indirect
  prompt injection + sandbox bypass in `@modelcontextprotocol/server-puppeteer`. An agent
  browsing a malicious page could be injected with instructions that trigger internal network
  requests via the puppeteer `goto()` call.
  Source: https://github.com/modelcontextprotocol/servers/issues/3662
  **Aigis takeaway:** Pattern coverage via existing `mcp_ssrf_metadata_endpoint` and
  `indirect_injection_*` patterns. No new pattern needed.

- **OWASP GenAI Q1 2026 round-up: architectural attacks lack CVE coverage.**
  The OWASP GenAI Security Project noted that most AI-layer attacks (memory poisoning,
  cross-agent smuggling, prompt-triggered SSRF) continue to lack CVE identifiers, making
  traditional vulnerability databases insufficient for AI security monitoring.
  Source: https://genai.owasp.org/2026/04/14/owasp-genai-exploit-round-up-report-q1-2026/
  **Aigis takeaway:** Rule-based pattern libraries like aigis's remain more current than CVE
  feeds for AI-native attack techniques.

---

## Candidate Hardenings

1. **`afe_sensitive_file_read`** — Detect references to `/proc/self/environ`, `/proc/<N>/environ`,
   `/proc/self/cmdline`, `/etc/shadow`, `/etc/sudoers`, and SSH private-key paths in AI prompts.
   Derived from Chainlit CVE-2026-22218 (file-read for API key theft) and the impact side of
   LangChain CVE-2026-34070. The existing `se_container_escape` covers `/proc/self/exe|root|ns`
   but misses `environ` — the primary secret-theft target.
   Add to `SANDBOX_ESCAPE_PATTERNS`.

2. **`sc_langchain_load_prompt_path`** — Detect `load_prompt()` / `load_prompt_from_config()`
   calls whose path argument contains `../`, `..\\`, or absolute paths to sensitive directories.
   Derived from CVE-2026-34070 (CVSS 7.5) in LangChain Core. Complements the existing
   `sc_langchain_deserialization` pattern (CVE-2025-68664) already in SUPPLY_CHAIN_PATTERNS.
   Add to `SUPPLY_CHAIN_PATTERNS`.

3. **Hardening guide for AI framework file/image loader SSRF** — A `docs/hardening/`
   guide documenting the class of attacks where AI framework file-load or image-load APIs
   are used as SSRF primitives (LMDeploy, Chainlit, LangChain pattern). → Deferred (outside
   100-LOC non-test limit combined with the two patterns above).
