# Research: data-exfiltration — 2026-05-20T09-00

## Domain: data-exfiltration (index 2, fifth pass)
## Cycle timestamp: 2026-05-20T09-00
## Focus: CSS hidden text injection, SVG href exfiltration, clipboard read/exfil chains

Prior passes covered (summary):
- Pass 1 (2026-05-07): `out_markdown_img_exfil`, `out_known_exfil_relay`
- Pass 2 (2026-05-10): `exfil_dns_encode_instruct`, `out_reference_style_markdown_exfil`, `out_tunnel_relay_url`
- Pass 3 (2026-05-13): `out_html_img_exfil`, `exfil_search_query_encode`, `out_diagram_href_exfil`
- Pass 4 (2026-05-14): `unicode_tag_block_smuggling`, `exfil_shard_split_requests`, `out_unicode_tag_block_smuggling`

This pass targets three new vectors confirmed in 2025–2026: (1) CSS-hidden injection payloads in
AI-processed HTML, (2) SVG `<image>` / `<a href>` exfiltration, and (3) AI-generated code that reads
the browser clipboard and forwards the contents to an attacker endpoint.

---

## Findings

- **CSS Hidden Text Prompt Injection — confirmed in-the-wild (Unit 42, 2025–2026)**:
  Palo Alto Unit 42 documented real-world indirect prompt injection attacks where attacker-controlled
  webpages hide malicious instructions using CSS: `style="color:white"`, `style="display:none"`,
  `style="font-size:0"`, `style="opacity:0"`, and `style="visibility:hidden"`. When an AI agent
  browses or summarizes these pages, it ingests the hidden text (which LLMs see even when humans
  cannot), and executes the injected instruction — typically "ignore previous instructions" followed
  by an exfiltration directive. The Microsoft Defender team separately identified 50+ distinct
  manipulation prompts (from 31 companies across 14 industries) using CSS hiding techniques in
  AI-summarized webpages. The MDPI Prompt Injection survey (Jan 2026) lists CSS hidden text as one
  of five primary indirect injection delivery vectors.
  - Source: https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/
  - Source: https://searchengineland.com/hidden-prompt-injection-black-hat-trick-ai-outgrew-462331
  - Source: https://www.mdpi.com/2078-2489/17/1/54
  - **aigis takeaway**: Add input filter `ii_css_hidden_text_injection` (score 45) detecting
    HTML elements where the style attribute carries a text-hiding property and the element
    contains at least 40 characters of non-tag text content.
    **→ IMPLEMENTED this cycle.**

- **SVG External Href Exfiltration — natural extension of HTML img and diagram href vectors**:
  SVG files support `<image href="...">` and `<a href="...">` elements that browsers and
  renderers fetch when the SVG is displayed. A prompt-injected LLM can generate SVG output
  containing encoded sensitive data in the query parameter of an `href` URL — functionally
  identical to the Mermaid diagram href attack (Adam Logue, M365 Copilot, Aug 2025) and the
  ForcedLeak HTML `<img>` attack (Noma Security, Sep 2025). The attack generalises because many
  modern chat and document interfaces render SVG inline, including AI-generated visualisations
  and diagrams. The OWASP GenAI Q1 2026 Exploit Round-up (Apr 2026) lists SVG/inline media
  exfiltration as an emerging pattern across several production incidents.
  - Source: https://genai.owasp.org/2026/04/14/owasp-genai-exploit-round-up-report-q1-2026/
  - Source: https://rafter.so/blog/llm-data-exfiltration
  - Source: https://www.adamlogue.com/microsoft-365-copilot-arbitrary-data-exfiltration-via-mermaid-diagrams-fixed/
  - **aigis takeaway**: Add output filter `out_svg_exfil` (score 70) detecting SVG `<image>` or
    `<a>` tags (including `xlink:href` form) pointing to external URLs with encoded query
    parameters — the same structural pattern as `out_html_img_exfil`.
    **→ IMPLEMENTED this cycle.**

- **Clipboard Read + Exfil Chain in AI-Generated Code (2025–2026)**:
  Two distinct attack patterns documented:
  (1) OpenAI ChatGPT Atlas vulnerability (Q4 2025): indirect injection on a webpage caused the
  agent to emit JavaScript that called `navigator.clipboard.readText()` and POST'd the result
  to an attacker C2 endpoint. No user action required — the code ran in the agent's browser
  context. CVE-2026-3938 (Chrome clipboard data leak) confirmed the clipboard API as a live
  exfiltration channel against AI browser agents.
  (2) The "Credential Leakage in LLM Agent Skills" study (arxiv:2604.03070, Apr 2026) analysed
  520 LLM agent skills and found clipboard monitoring via `navigator.clipboard.readText()` and
  `window.clipboardData.getData()` as one of six confirmed adversarial leakage patterns in
  production skills. Attack success rate (when injected): 72% single-turn, 91% multi-turn.
  - Source: https://arxiv.org/abs/2604.03070
  - Source: https://www.androidauthority.com/openai-atlas-clipboard-injection-vulnerability-3609982/
  - Source: https://www.sentinelone.com/vulnerability-database/cve-2026-3938/
  - **aigis takeaway**: Add output filter `out_clipboard_read_exfil` (score 75) detecting
    AI-generated code patterns that pair `navigator.clipboard.readText()` or
    `window.clipboardData.getData()` with an outbound HTTP call (fetch, XMLHttpRequest, axios,
    requests) to a non-localhost URL.
    **→ IMPLEMENTED this cycle.**

- **Back-Reveal: Backdoored Tool-Use Memory Exfiltration** (arxiv:2604.05432, Apr 2026):
  Semantic triggers embedded during fine-tuning cause an LLM agent to silently invoke memory-
  access tool calls (`retrieve_memory`, `search_docs`), then disguise the exfiltrated data as
  normal retrieval output. Attack success 87% single-turn, >97% with majority voting. Not
  addressable by static regex (trigger is a model weight pattern); detection requires model
  provenance verification and behavioral runtime analysis.
  - Source: https://arxiv.org/abs/2604.05432
  - **aigis takeaway**: Out of scope for static regex detection. Send to pending.

- **AI-Generated Code Phone-Home via Tunneling Services** (DEEP#DOOR, Aviatrix, Apr 2026;
  VibeGuard, arxiv:2604.01052):
  Indirect prompt injection via poisoned README or source file instructs an AI coding agent to
  add "telemetry" code that POSTs env vars (API keys, tokens) to an attacker-controlled endpoint
  or public tunneling service (ngrok, bore). The VibeGuard paper documented this pattern in 520
  agent skill submissions. Partial coverage already exists via `exfil_send_to_external` and
  `exfil_keyword`. More targeted coverage (Python `requests.post` + `os.environ` in the same
  code block) is a candidate for a future cycle.
  - Source: https://arxiv.org/abs/2604.01052
  - Source: https://aviatrix.ai/threat-research-center/new-python-backdoor-uses-tunneling-service-to-steal-browser-and-cloud-credentials-2026/
  - **aigis takeaway**: Partially covered. A more specific `out_code_phonehome_envvar` rule is a
    candidate for next data-exfiltration cycle. Send to pending.

---

## Candidate Hardenings

1. **`ii_css_hidden_text_injection`** (input, score 45) — HTML style attribute carrying a
   text-hiding CSS property (`display:none`, `visibility:hidden`, `color:white/transparent`,
   `font-size:0`, `opacity:0`) combined with non-trivial text content (≥40 chars). Covers
   the in-the-wild pattern documented by Unit 42 and Microsoft Defender.
   **→ IMPLEMENTED**

2. **`out_svg_exfil`** (output, score 70) — SVG `<image>` or `<a>` element with an
   `href` or `xlink:href` pointing to an external host carrying an encoded query parameter.
   Same structural attack as ForcedLeak (`out_html_img_exfil`) and Mermaid diagram href
   (`out_diagram_href_exfil`), applied to the SVG media context.
   **→ IMPLEMENTED**

3. **`out_clipboard_read_exfil`** (output, score 75) — `navigator.clipboard.readText()` or
   `window.clipboardData.getData()` paired with an outbound HTTP call in generated code.
   Covers the ChatGPT Atlas clipboard injection CVE and the arxiv:2604.03070 leakage pattern.
   **→ IMPLEMENTED**

4. *(pending)* `out_code_phonehome_envvar` — Python `requests.post`/`os.environ` combination
   in AI-generated code. Partially covered by existing patterns; needs a more targeted rule.

5. *(pending)* Back-Reveal behavioral monitoring — Tool call chain analysis for
   `retrieve_memory` → external URL. Requires runtime behavioral context; out of scope for
   static regex patterns.
