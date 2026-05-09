# Research: Incident Postmortems & CVEs — 2026-05-09T10-00

**Domain index:** 9 — `incident-postmortems`
**Cycle:** First pass (no prior research file for index 9)

---

## Key Findings

- **CVE-2026-26030 (CVSS 9.9) — Microsoft Semantic Kernel Python SDK eval() RCE.**
  InMemoryVectorStore built Python lambda filter expressions via `eval()` with user-controlled
  field values interpolated directly into the expression. An attacker could smuggle an MRO-traversal
  payload (e.g., `().__class__.__mro__[-1].__subclasses__()[100]('os').system('id')`) through the
  LLM's natural-language guardrails into the eval() sink to achieve full remote code execution.
  Fixed in semantic-kernel 1.39.4 (safe-parser replaces eval). CVSS 9.9.
  Sources:
  - https://nvd.nist.gov/vuln/detail/cve-2026-26030
  - https://advisories.gitlab.com/pkg/pypi/semantic-kernel/CVE-2026-26030/
  - https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
  **Aigis takeaway:** Add a pattern detecting Python MRO/subclass traversal strings in AI prompts;
  `__subclasses__()` and `__mro__[N]` are never legitimate in AI agent inputs.

- **CVE-2026-25592 (CVSS 7.3) — Microsoft Semantic Kernel .NET SDK path traversal.**
  `SessionsPythonPlugin.DownloadFileAsync` / `UploadFileAsync` accepted user-controlled file paths
  without directory scope validation; `../` sequences could write arbitrary files on the host.
  Fixed in Microsoft.SemanticKernel.Core 1.70.0 / 1.71.0.
  Sources:
  - https://nvd.nist.gov/vuln/detail/CVE-2026-25592
  - https://www.sentinelone.com/vulnerability-database/cve-2026-25592/
  **Aigis takeaway:** Existing `cmdi_path_traversal` pattern already catches `../` sequences.
  No new pattern needed for this CVE specifically.

- **ClawHavoc supply-chain campaign (Feb 2026) — 341–900 malicious OpenClaw skills.**
  Koi Security researcher Oren Yomtov audited all 2,857 skills on OpenClaw's ClawHub registry
  and identified 341 malicious entries (12% of the registry, rising to ~900 by independent scans),
  primarily delivering Atomic macOS Stealer (AMOS). The campaign specifically targeted OpenClaw's
  persistent memory files: **SOUL.md** and **MEMORY.md**. Modifying these files installs backdoors
  that survive context resets because OpenClaw re-reads them at session start.
  Over 135,000 exposed OpenClaw instances found; 12,800+ directly exploitable.
  Sources:
  - https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/
  - https://www.esecurityplanet.com/threats/hundreds-of-malicious-skills-found-in-openclaws-clawhub/
  - https://www.clawbot.blog/blog/the-clawhavoc-campaign-how-malicious-ai-agent-skills-exposed-the-verification-ga/
  **Aigis takeaway:** Add a pattern detecting instructions to write/modify agent persistent memory
  files by name (SOUL.md, MEMORY.md, .agent_memory).

- **CVE-2026-32173 (CVSS 8.6) — Azure SRE Agent unauthenticated WebSocket live command stream.**
  An unauthenticated WebSocket endpoint on the Azure SRE Agent exposed live command streams to any
  Entra ID account holder. Attackers could observe — and potentially inject into — agent command
  execution in real time.
  Source: Adversa AI / Stellar Cyber roundups (May 2026)
  **Aigis takeaway:** Coverage via existing `out_known_exfil_relay` and WebSocket patterns
  in `mcp_poisoning`. No new pattern required.

- **OWASP GenAI Exploit Round-up Q1 2026 — CVE gap in AI-specific incidents.**
  The OWASP GenAI Security Project found that most AI-related security events in Q1 2026 are
  NOT mapped to CVE identifiers; only classical software vulnerabilities embedded in AI platforms
  (like eval() sinks) consistently receive CVE tracking. "Architectural" attacks (memory poisoning,
  supply-chain skill tampering, multi-agent collusion) have no CVE equivalent.
  Source: https://genai.owasp.org/2026/04/14/owasp-genai-exploit-round-up-report-q1-2026/
  **Aigis takeaway:** aigis's rule-based, incident-informed patterns are more relevant than CVE
  tracking alone for AI-native attacks.

- **Indirect prompt injection increase (2025–2026).**
  Google Security and Help Net Security documented a 32% relative increase in malicious indirect
  prompt injection in the wild between November 2025 and February 2026. A single prompt injection
  attempt against a GUI-based agent succeeds 17.8% of the time without safeguards; at the 200th
  attempt, the breach rate hits 78.6% (Anthropic Claude Opus 4.6 system card).
  Source: https://www.helpnetsecurity.com/2026/04/24/indirect-prompt-injection-in-the-wild/
  **Aigis takeaway:** Validates continued investment in indirect_injection and mcp_poisoning
  pattern categories. No new pattern needed this cycle.

- **Microsoft "prompts become shells" blog (2026-05-07).**
  Microsoft Security documented the category of vulnerabilities where prompt injection reaches
  an underlying code-execution sink (eval, exec, subprocess) in AI agent frameworks, noting that
  Semantic Kernel CVE-2026-25592 and CVE-2026-26030 are the first publicly tracked CVEs in this
  class. They predict more will follow as AI frameworks expand their tool surfaces.
  Source: https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/
  **Aigis takeaway:** The `afe_python_mro_escape` pattern directly addresses this
  "prompt-to-shell via eval" class.

---

## Candidate Hardenings

1. **`afe_python_mro_escape`** — Python MRO/subclass traversal sandbox escape strings in prompts.
   Derived from CVE-2026-26030. Add to `SANDBOX_ESCAPE_PATTERNS`. ✅ Implemented.

2. **`afe_agent_memory_file_write`** — Instructions targeting AI agent persistent memory files
   (SOUL.md, MEMORY.md, .agent_memory) for modification. Derived from ClawHavoc campaign.
   Add to `MEMORY_POISONING_PATTERNS`. ✅ Implemented.

3. **Skill/plugin integrity verification guidance doc** — A `docs/hardening/skill-marketplace-hygiene.md`
   guide covering ClawHavoc-style supply-chain threats. → Deferred to pending (documentation
   is outside the 100-LOC diff limit once combined with pattern changes).

4. **OpenClaw/ClawHub-specific supply chain pattern** — Detect references to ClawHub skill
   installs or OpenClaw skill registry URLs. → Deferred: too framework-specific and likely
   to have high false-positive rate without testing against real OpenClaw logs.
