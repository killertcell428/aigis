# Research: agent-tool-abuse (Cycle 1)

**Cycle UTC:** 2026-05-07T14-50  
**Domain index:** 1  
**Domain key:** agent-tool-abuse  

---

## Findings

- **CVE-2025-54136 "MCPoison" (Cursor IDE, CVSS 7.2)** — Check Point Research disclosed that an attacker who controls a shared GitHub repo can swap a previously-approved benign MCP config for a malicious one to achieve persistent RCE every time the victim opens Cursor. No re-prompt, no warning. Addressed in Cursor 1.3 (July 2025). *Aigis implication:* the "rug pull" already covered by `mcp_rug_pull_indicator`; however, the swap timing and silent persistence aspect motivates strengthening snapshot-diff detection.  
  Source: https://securityboulevard.com/2025/08/cve-2025-54135-cve-2025-54136-frequently-asked-questions-about-vulnerabilities-in-cursor-ide-curxecute-and-mcpoison/

- **Log-To-Leak (OpenReview 2025/2026)** — A new injection framework that covertly forces agents to invoke a malicious *logging* tool to exfiltrate user queries, tool responses, and agent replies — without disrupting the primary task. Four structural components: Trigger, Tool Binding, Justification, Pressure. Evaluated on GPT-4o, GPT-5, Claude-Sonnet-4 across 5 real MCP servers. High fidelity exfil with low task-quality degradation. *Aigis implication:* no existing rule covers the "log exfil" pattern; a new rule targeting the combination of collection + external URL forwarding would catch it.  
  Source: https://openreview.net/forum?id=UVgbFuXPaO

- **LogJack (arxiv:2604.15368, Apr 2025)** — Indirect prompt injection via cloud log content. Benchmark of 42 payloads across 5 log categories; tested 8 models. RCE via `curl | bash` succeeds on 6/8 models. Key finding: log formatting (`[ERROR]`, `WARN:`, timestamp prefix) provides contextual camouflage that defeats Azure Prompt Shield (detected 1/32) and GCP Model Armor (detected 0/32). *Aigis implication:* a rule that detects log-format wrappers around injection keywords would close this gap.  
  Source: https://arxiv.org/abs/2604.15368

- **ToolCommander (NAACL 2025, arxiv:2412.10198)** — Two-stage attack: (1) inject a Manipulator Tool that collects user queries; (2) dynamically update the tool to forward stolen data to an attacker endpoint. ASR 91.67% for privacy theft, 100% for DoS in some configurations. *Aigis implication:* a pattern combining "collect user queries/inputs" + "send/forward to https://" would catch stage-1+2 tool descriptions.  
  Source: https://arxiv.org/abs/2412.10198

- **SSRF via prompt injection (arxiv:2506.23260)** — Survey documents how tool-calling agents can be coerced into fetching internal cloud metadata endpoints (AWS IMDS `169.254.169.254`, GCP metadata, Azure IMDS) by embedding the URL in a tool response or description. Cloud IAM credentials are exfiltrated without any file-read operation. *Aigis implication:* the cloud metadata IP is a deterministic signal — never legitimate in tool text.  
  Source: https://arxiv.org/html/2506.23260v1

- **ToolHijacker (arxiv:2504.19793, NDSS 2026)** — Automated framework crafting malicious tool descriptions that achieve 96.7% tool-selection hijack rate using Retrieval-optimized (R) + Selection-optimized (S) sequences. Already addressed in aigis with the `detect_selection_bias` function (H1–H5 heuristics) added in the mcp_scanner module from prior cycle work.  
  Source: https://arxiv.org/html/2504.19793v2

- **MCPTox benchmark (arxiv:2508.14925)** — Evaluates tool poisoning on 20 real MCP servers; o1-mini achieves 72.8% ASR. Most attacks embed instructions in `<IMPORTANT>` tags or append them after seemingly benign content. *Aigis implication:* `mcp_important_tag` already covers the tag pattern; MCPTox confirms high real-world impact. Post-approval persistence attacks are the gap.  
  Source: https://arxiv.org/html/2508.14925v1

- **postmark-mcp malicious server (incident, 2025)** — First publicly documented malicious MCP server; was pulling ~1,500 downloads/week with ~300 org integrations before discovery (Koi Security). Contained hidden instructions in tool descriptions. *Aigis implication:* real-world confirmation that MCP tool description scanning is production-necessary, not just theoretical.  
  Source: https://pipelab.org/blog/state-of-mcp-security-2026/

---

## Candidate Hardenings

1. **`mcp_log_format_injection`** — New rule detecting log-level prefixes (`[ERROR]`, `[WARNING]`, etc.) combined with injection keywords in the same string. Targets LogJack contextual-camouflage attack. Small regex, zero dependencies. ✅ **Implemented this cycle.**

2. **`mcp_ssrf_metadata_endpoint`** — New rule detecting cloud IMDS IPs (`169.254.169.254`, `169.254.170.2`, `metadata.google.internal`) in tool text. These are never legitimate in a tool description or response. ✅ **Implemented this cycle.**

3. **`mcp_collector_exfil`** — New rule detecting ToolCommander-style "collect user queries + forward to https://" patterns. Two-stage exfil detection from tool descriptions. ✅ **Implemented this cycle.**

4. **Snapshot-diff timing attack detection** — Detect MCPoison "swap after approval" by recording approval timestamps and alerting on changes within a short window post-approval. Requires a stateful persistence layer not currently in aigis; send to pending/.

5. **Log-To-Leak tool-binding detection** — More precise Trigger+Justification+Pressure template matching from the Log-To-Leak framework. More complex multi-part regex; defer to pending/ to avoid >100 LOC.
