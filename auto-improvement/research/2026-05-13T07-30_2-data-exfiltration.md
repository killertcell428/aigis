# Research: data-exfiltration — 2026-05-13T07-30

## Domain: data-exfiltration (index 2, third pass)
## Focus: Novel output-channel exfiltration — diagram DSLs, web-search covert channels, URL-index analysis

Prior cycles covered:
- Cycle 1 (2026-05-07): markdown image URL exfil, OAST relay domains.
- Cycle 2 (2026-05-10): DNS encode instruct, reference-style Markdown exfil (EchoLeak), tunnel relay URLs, Unicode Tag Block (pending).

This pass targets newer documented vectors: diagram DSL hyperlink abuse, web-search-tool covert channels, backdoored tool-use exfiltration, and OpenAI's URL-index mitigation analysis.

---

## Findings

- **Mermaid Diagram `href=` Exfiltration — M365 Copilot (Adam Logue, Aug/Sep 2025)**: Indirect
  prompt injection via a maliciously crafted Excel spreadsheet directed M365 Copilot to
  hex-encode tenant email content and embed it as the `href` of a Mermaid flowchart node
  styled as a "Verify Identity" button. Clicking the rendered button silently sent the
  encoded data to an attacker-controlled server. Microsoft patched in September 2025 by
  disabling interactive hyperlinks in Mermaid rendered output. The technique is generalisable
  to PlantUML and D2 diagram DSLs.
  - Source: https://www.adamlogue.com/microsoft-365-copilot-arbitrary-data-exfiltration-via-mermaid-diagrams-fixed/
  - Source: https://www.theregister.com/2025/10/24/m365_copilot_mermaid_indirect_prompt_injection/
  - Source: https://cybersecuritynews.com/copilot-prompt-injection-vulnerability-2/
  - **aigis takeaway**: Output filter should flag any Mermaid/PlantUML/D2 code fence that
    contains `href=` or `url=` pointing to an external host.
    (**IMPLEMENTED this cycle: `out_diagram_href_exfil`**)

- **Web-Search Tool as Covert Exfiltration Channel (Rall et al., arxiv:2510.09093, Oct 2025)**:
  Researchers demonstrated that an AI agent equipped with a web-search tool and access to a
  corporate RAG knowledge base can be hijacked by a malicious webpage. The hidden instruction
  directs the agent to base64-encode the retrieved secret and issue it as a web-search query,
  leaking the data to an attacker who controls the search-logged domain. Unlike URL-based
  exfiltration (which requires rendering a link), this channel abuses the agent's legitimate
  search capability as the covert transport. Tested across multiple LLMs; success rates varied
  by model size and system-prompt hardening.
  - Source: https://arxiv.org/abs/2510.09093
  - **aigis takeaway**: Input filter should detect instructions that pair encoding directives
    with web-search tool invocations.
    (**IMPLEMENTED this cycle: `exfil_search_query_encode`**)

- **Backdoored Tool-Use Exfiltration — Back-Reveal (arxiv:2604.05432, Apr 2026)**: Researchers
  introduced "Back-Reveal", a backdoor embedded into a fine-tuned LLM agent. When triggered
  by a semantic cue, the backdoored agent invokes memory-access or retrieval tool calls to
  collect user session context, then exfiltrates it via disguised retrieval tool calls that
  send the data to an attacker-controlled endpoint. This represents a supply-chain risk:
  the exfiltration logic is baked into the model weights, not into a prompt.
  - Source: https://arxiv.org/abs/2604.05432
  - **aigis takeaway**: Hard to detect with static regex (the trigger is a semantic pattern
    in model weights). Runtime monitoring of outbound tool calls to unexpected external
    endpoints is the correct mitigation. Send to pending for future behavioral-rule work.

- **OpenAI URL-Index Exfil Mitigation Paper (Jan 2026)**: OpenAI published a paper describing
  their defenses against URL-based data exfiltration. Core technique: compare any agent-generated
  URL against an independent web index; URLs that do not appear in the index (i.e., dynamically
  generated with encoded data) trigger a user-visible warning ("Check this link is safe") or
  are blocked. This mitigation targets the *channel* not the injection vector, so it is
  complementary to prompt-injection detection.
  - Source: https://cdn.openai.com/pdf/dd8e7875-e606-42b4-80a1-f824e4e11cf4/prevent-url-data-exfil.pdf
  - Source: https://openai.com/index/ai-agent-link-safety/
  - **aigis takeaway**: The URL-index approach is infrastructure-level and not directly
    implementable in a rule-based firewall. Document in a hardening guide for future cycles.

- **Link Trap Prompt Injection (Trend Micro / Keysight, Jun 2025)**: A variation where
  injected instructions cause the LLM to construct a URL that encodes conversation context
  in query parameters and present it as a user-action link (e.g., "Click here to confirm").
  Differs from markdown image exfil (which auto-fetches) in that it requires a user click
  — making it slightly harder to exploit but harder to detect because the link looks benign.
  - Source: https://www.keysight.com/blogs/en/tech/nwvs/2025/06/12/link-trap-prompt-injection-attack
  - **aigis takeaway**: The existing `out_markdown_img_exfil` and `out_reference_style_markdown_exfil`
    patterns cover auto-fetch variants. The click-required variant is partially caught by
    these patterns if the URL carries encoded query params. No new pattern needed this cycle.

- **Indirect Memory Poisoning → Exfiltration (Palo Alto Unit 42, Oct 2025)**: An agent
  processing a malicious booking website silently exfiltrated the user's booking details by
  encoding them in a C2 URL's query parameters and requesting that URL via the `scrape_url`
  tool. The exfiltration URL was disguised as a "verification" step.
  - Source: https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/
  - **aigis takeaway**: The `exfil_send_to_external` input pattern partially covers this.
    Tool-call auditing (behavioral) would provide better coverage. No new pattern this cycle.

- **Credential Leakage in LLM Agent Skills (arxiv:2604.03070, Apr 2026)**: Large-scale empirical
  study of 200+ real-world LLM agent "skills" (plugins/tools) found that many hardcode credentials
  (API keys, OAuth tokens) in tool descriptions or function source, making them visible to the
  LLM context and susceptible to indirect prompt injection for exfiltration.
  - Source: https://arxiv.org/abs/2604.03070
  - **aigis takeaway**: aigis's existing `mcp_hardcoded_credential` and `pii_api_key_input`
    patterns already cover some of this. A focused MCP-scanner hardening for tool-description
    credential scanning is a candidate for a future supply-chain or agent-tool-abuse cycle.

---

## Candidate Hardenings

1. **`out_diagram_href_exfil`** (output, score 65) — Mermaid/PlantUML/D2 code fence with
   `href=` or `url=` to an external host. Covers Adam Logue's M365 Copilot attack (Aug 2025).
   **→ IMPLEMENTED**

2. **`exfil_search_query_encode`** (input, score 65) — Instructions pairing a web-search tool
   call with an encoding operation (base64/hex) applied to secrets/context. Covers
   arxiv:2510.09093 (Rall et al., Oct 2025). **→ IMPLEMENTED**

3. *(pending)* Back-Reveal backdoored tool use — semantic/behavioral detection, not regex;
   requires outbound tool-call monitoring. Too large and behavioral for this cycle.

4. *(pending)* URL-index allowlist for agent-generated links — infrastructure-level mitigation;
   document in a hardening guide in a future compliance/docs cycle.

5. *(pending)* Credential leakage in MCP skill descriptions — extend `mcp_scanner.py` to
   scan tool-description strings for API key patterns; good candidate for a future
   agent-tool-abuse cycle.
