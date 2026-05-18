# Research: Incident Postmortems & CVEs — 2026-05-18T03-06

**Domain index:** 9 — `incident-postmortems`
**Cycle:** Third pass (prior passes covered: Chainlit CVE-2026-22218/22219, LangChain CVE-2026-34070,
LMDeploy CVE-2026-33626; Semantic Kernel CVE-2026-26030 MRO escape; Cline CLI supply chain attack)

---

## Key Findings

- **CVE-2026-33017 (CVSS 9.3) — Langflow unauthenticated RCE, exploited in 20 hours (March 2026).**
  Sysdig Threat Research / The Hacker News documented a critical unauthenticated remote code execution
  vulnerability in Langflow, the open-source visual AI pipeline builder. The `POST
  /api/v1/build_public_tmp/{flow_id}/flow` endpoint accepted attacker-supplied flow data containing
  arbitrary Python code in `CustomComponent` node definitions and passed it directly to `exec()` with
  no sandboxing and no authentication required. Exploitation began within 20 hours of the advisory; no
  public PoC existed — attackers derived exploits directly from the advisory description. One confirmed
  incident dumped `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from `/proc/self/environ`. Fixed in
  Langflow 1.9.0 (the endpoint no longer accepts externally supplied `data` parameters).
  Sources:
  - https://www.sysdig.com/blog/cve-2026-33017-how-attackers-compromised-langflow-ai-pipelines-in-20-hours
  - https://thehackernews.com/2026/03/critical-langflow-flaw-cve-2026-33017.html
  - https://github.com/EQSTLab/CVE-2026-33017
  **Aigis takeaway:** Add a pattern detecting references to the `/build_public_tmp/` endpoint path and
  flow payload structures embedding Python code via `CustomComponent` nodes. An AI agent with HTTP
  tool access could be directed via prompt injection to exploit exposed Langflow instances.

- **CVE-2026-44338 (CVSS 7.3) — PraisonAI hardcoded auth bypass, scanned within 4 hours (May 2026).**
  Sysdig / SecurityWeek / The Hacker News reported that the legacy Flask API server in PraisonAI
  (src/praisonai/api_server.py) hard-coded `AUTH_ENABLED = False` and `AUTH_TOKEN = None`, exposing the
  `/agents` endpoint (returns all configured agent metadata) and `/chat` endpoint (executes agent
  workflows) to any unauthenticated network caller. Affected versions: 2.5.6 through 4.6.33. Within 3
  hours 44 minutes of the advisory going public on May 11, 2026 at 13:56 UTC, automated scanners
  (CVE-Detector/1.0) began probing the exact vulnerable endpoint on internet-exposed instances. Attackers
  drained API quotas and accessed sensitive agent workflow outputs. Fixed in PraisonAI 4.6.34.
  Sources:
  - https://www.sysdig.com/blog/cve-2026-44338-praisonai-authentication-bypass-in-under-4-hours-and-the-growing-trend-of-rapid-exploitation
  - https://thehackernews.com/2026/05/praisonai-cve-2026-44338-auth-bypass.html
  - https://www.securityweek.com/hackers-targeted-praisonai-vulnerability-hours-after-disclosure/
  **Aigis takeaway:** Add a pattern detecting hardcoded auth-disabled configuration in AI framework API
  servers (`AUTH_ENABLED = False`, `AUTH_TOKEN = None`, `DISABLE_AUTH = True`, `verify_token = False`).
  An AI agent could be instructed via prompt injection to write or validate such patterns.

- **CVE-2026-25592 (CVSS 10.0) and CVE-2026-26030 (CVSS 9.9) — Microsoft Semantic Kernel prompt
  injection to RCE (May 2026).**
  Microsoft Security Blog documented two vulnerabilities where prompt injection crossed into code
  execution in Semantic Kernel:
  - CVE-2026-25592 (.NET SDK <1.71.0): `DownloadFileAsync`, a file-transfer helper, was accidentally
    tagged `[KernelFunction]` and exposed to the LLM with no path validation. A hostile prompt could
    steer the agent into writing a file to an arbitrary path on the host.
  - CVE-2026-26030 (Python SDK <1.39.4): `InMemoryVectorStore` filter built a LINQ-like expression
    from an f-string using an LLM-controlled field value; the blocklist was bypassed via
    `__class__.__bases__[0].__subclasses__()` traversal. This leads to code execution via eval().
  The existing `afe_python_mro_escape` pattern already covers CVE-2026-26030.
  Sources:
  - https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
  - https://particula.tech/blog/semantic-kernel-cve-2026-25592-prompt-injection-rce
  - https://advisories.gitlab.com/pkg/pypi/semantic-kernel/CVE-2026-26030/
  **Aigis takeaway:** `afe_python_mro_escape` already covers CVE-2026-26030. CVE-2026-25592 (unintended
  KernelFunction exposure with path write) is framework-internal and not pattern-matchable from prompt
  content alone. No new pattern needed for these two.

- **"Clinejection" — AI issue triage bot turned supply chain attack vector (February 2026).**
  Adnan Khan / Snyk documented how the Cline CLI's AI issue-triage bot was misconfigured to run with
  write access to the default branch and automatically process any incoming GitHub issue. A prompt
  injection in a GitHub issue title/body could instruct the AI to run arbitrary shell commands, steal
  the repo's npm publish token, and upload a malicious package version. This led to the Cline 2.3.0
  supply chain attack (cline@2.3.0 installed OpenClaw via postinstall on ~4,000 developer machines).
  The attack chain: untrusted issue text → AI agent with excessive permissions → arbitrary command
  execution → stolen publish token → malicious npm package published.
  Sources:
  - https://snyk.io/blog/cline-supply-chain-attack-prompt-injection-github-actions/
  - https://thehackernews.com/2026/02/cline-cli-230-supply-chain-attack.html
  - https://www.cremit.io/blog/ai-supply-chain-attack-clinejection
  **Aigis takeaway:** The existing `sc_compromised_pkg_version` and indirect injection patterns already
  cover parts of this. No new pattern needed; reinforces that indirect injection detection remains
  high-priority.

- **Trend: "race to exploit" AI framework CVEs now measured in hours, not days (May 2026).**
  Sysdig and SecurityWeek documented a consistent trend across three AI-framework CVEs disclosed in
  Q1–Q2 2026: Langflow CVE-2026-33017 (20 hours), LMDeploy CVE-2026-33626 (12.5 hours), and PraisonAI
  CVE-2026-44338 (3.75 hours). The exploitation window is shrinking, and the first exploiters are
  automated scanners rather than skilled humans. This makes pre-patch detection rules especially
  valuable.
  Source: https://www.sysdig.com/blog/cve-2026-44338-praisonai-authentication-bypass-in-under-4-hours-and-the-growing-trend-of-rapid-exploitation
  **Aigis takeaway:** Rule-based pattern coverage for known-vulnerable framework patterns remains
  valuable even after patches ship, since many production deployments lag in updating.

---

## Candidate Hardenings

1. **`sc_langflow_build_exec`** — Detect references to Langflow's unauthenticated RCE endpoint
   (`/api/v1/build_public_tmp/{flow_id}/flow`) or flow payload structures containing Python code in
   `CustomComponent` nodes. Derived from CVE-2026-33017 (CVSS 9.3). Add to `SUPPLY_CHAIN_PATTERNS`.
   **IMPLEMENTED this cycle.**

2. **`sc_ai_framework_auth_disabled`** — Detect hardcoded auth-disabled configuration patterns in AI
   framework API server code: `AUTH_ENABLED = False`, `AUTH_TOKEN = None`, `DISABLE_AUTH = True`,
   `verify_token = False/None`, `authentication_required = False`. Derived from CVE-2026-44338 (CVSS 7.3).
   Add to `SUPPLY_CHAIN_PATTERNS`.
   **IMPLEMENTED this cycle.**

3. **Hardening guide: AI framework attack surface minimization** — A `docs/hardening/` guide covering
   the "race to exploit" trend in AI frameworks (LMDeploy, Langflow, PraisonAI), recommending network
   isolation for build/preview endpoints, authentication requirements for all agent execution paths,
   and monitoring for CVE-Detector-style automated scanning. **DEFERRED** — combined with the two
   patterns above would exceed 100 LOC, and documentation changes are better scoped to a docs-only cycle.
