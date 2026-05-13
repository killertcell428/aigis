# Research: data-exfiltration — 2026-05-13T06-13

## Domain: data-exfiltration (index 2, third pass)
## Cycle timestamp: 2026-05-13T06-13
## Focus: Novel exfiltration vectors — HTML img tags, web search query encoding, and covert-channel research

Previous cycles covered:
- First pass (2026-05-07): markdown image exfil (`out_markdown_img_exfil`), OAST relay domains (`out_known_exfil_relay`)
- Second pass (2026-05-10): DNS subdomain encoding (`exfil_dns_encode_instruct`), EchoLeak reference-style markdown (`out_reference_style_markdown_exfil`), tunnel relay services (`out_tunnel_relay_url`)

This pass targets remaining output-channel gaps and a novel input-side attack that abuses AI agent web-search tools.

---

## Findings

- **ForcedLeak: HTML `<img>` tag exfiltration in Salesforce Agentforce** (CVSS 9.4, Noma Security, Sep 2025):
  A prompt injected via Agentforce's Web-to-Lead form (42,000-character Description field) instructed
  the agent to encode CRM email addresses (spaces rendered as `%20`) and embed them as the `src` of an
  HTML `<img>` tag pointing to an expired allowlisted Salesforce-related domain that the attacker had
  purchased for $5. When the page rendered, the browser fetched the URL, silently exfiltrating the stolen
  contacts to the attacker. The existing `out_markdown_img_exfil` pattern only covers Markdown `![alt](url)`
  syntax — ForcedLeak bypassed it by using raw HTML `<img src="...">` instead.
  - Source: https://thehackernews.com/2025/09/salesforce-patches-critical-forcedleak.html
  - Source: https://securityaffairs.com/182676/hacking/forcedleak-flaw-in-salesforce-agentforce-exposes-crm-data-via-prompt-injection.html
  - **aigis takeaway**: Add output filter for HTML `<img>` tags with encoded query params.
    **→ IMPLEMENTED this cycle: `out_html_img_exfil`**

- **Web search query exfiltration via encoded agent context** (arxiv:2510.09093, Oct 2025, revised Apr 2026):
  Attackers plant obfuscated instructions in web pages that AI agents retrieve; those instructions tell
  the agent to encode sensitive context data (conversation history, API keys, user data) and embed it as
  a web search query. The query is logged by the search engine, and an SEO-optimized attacker-controlled
  page ranks first for the encoded string, allowing the attacker to recover the data without any direct
  network connection to the victim. Attack success rate exceeded 80% across five tested agent architectures.
  This is a fundamentally different exfiltration channel from DNS encoding and not previously covered.
  - Source: https://arxiv.org/abs/2510.09093
  - Source: https://arxiv.org/html/2510.09093v2
  - **aigis takeaway**: Add input filter for instructions that pair encoding directives with web-search
    tool calls. **→ IMPLEMENTED this cycle: `exfil_web_search_encode`**

- **Backdoored tool use / Back-Reveal attack** (arxiv:2604.05432, Apr 2026):
  A threat model where adversaries fine-tune LLM agents with semantic triggers that, when activated,
  invoke memory-access tool calls to retrieve stored user context and exfiltrate it via disguised
  retrieval tool responses. Multi-turn interaction amplifies the attack; compromised models reliably
  transmit 32-bit secrets with 87% single-turn accuracy, reaching >97% with majority voting across
  three generations. This attack requires a fine-tuned (backdoored) model and does not match a static
  regex; detection requires model provenance verification.
  - Source: https://arxiv.org/abs/2604.05432
  - **aigis takeaway**: Not addressable by regex in the current aigis architecture; send to pending/.

- **Malicious browser extensions harvesting LLM chat histories** (Microsoft Security Blog, Mar 2026):
  Fake AI-assistant Chromium extensions (~900k installs) logged chat histories and visited URLs as
  Base64-encoded JSON, uploading them periodically to remote C2 endpoints. The exfiltration channel is
  the extension's background script, not the LLM output itself. Out of scope for aigis output-filter
  rules but relevant to supply-chain posture.
  - Source: https://www.microsoft.com/en-us/security/blog/2026/03/05/malicious-ai-assistant-extensions-harvest-llm-chat-histories/
  - **aigis takeaway**: Supply-chain concern, not addressable by current filter patterns.

- **LLM steganographic exfiltration / TrojanStego** (arxiv:2505.20118, May 2025):
  Adversaries fine-tune LLMs to embed sensitive context into natural-looking outputs via linguistic
  steganography — whitespace substitution, token selection patterns, punctuation encoding. The resulting
  outputs are syntactically valid and human-readable; the hidden channel is carried in subtle statistical
  properties of the text. Experimental ASR: 87% single-pass, >97% with majority voting. Not detectable
  by static regex because the steganographic signal is in the probability distribution, not the content.
  - Source: https://arxiv.org/abs/2505.20118
  - Source: https://arxiv.org/abs/2410.03768
  - **aigis takeaway**: Architectural constraint — statistical steganography requires model-level
    detection (canary token injection, output distribution analysis). Feasibility study for docs/; send to pending/.

- **CSS invisible-text injection for prompt hiding** (multiple 2025 reports):
  Attackers embed hidden instructions in web content using CSS invisible-text techniques (white text on
  white background, zero-height elements, `display:none`). When an agent browses and summarizes the page,
  it processes the hidden instruction. The CSS attribute itself is not present in the LLM output being
  filtered — the attack happens at retrieval time. Partially covered by existing indirect injection
  patterns; no new output pattern needed.
  - Source: https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/
  - **aigis takeaway**: Existing `INDIRECT_INJECTION_PATTERNS` partially cover this. No new output rule needed.

- **HashJack — exfil via URL fragment** (reported 2025):
  Instructions hidden in URL fragments (`#...`) can survive link-sharing while evading log-based
  detection because fragment identifiers are never sent to the server. An agent browsing a URL with
  a malicious fragment receives the hidden instruction client-side. Distinct from server-side DNS/URL
  exfil; more relevant to agent browsing context than to aigis output filtering.
  - Source: https://gbhackers.com/agentic-llm-browsers/
  - **aigis takeaway**: Not addressable by current output filter; relevant to agent browsing sandboxing
    guidance — candidate for docs/hardening-guides/. Send to pending/.

---

## Candidate Hardenings

1. **`out_html_img_exfil`** (output, score 70) — HTML `<img>` tag with encoded query params.
   Covers ForcedLeak (CVSS 9.4, Salesforce Agentforce, Sep 2025). **→ IMPLEMENTED**

2. **`exfil_web_search_encode`** (input, score 65) — Instructions pairing encoding directives
   with web-search tool calls. Covers web-search query exfiltration (arxiv:2510.09093, >80% ASR).
   **→ IMPLEMENTED**

3. *(pending)* Backdoored tool use / Back-Reveal (arxiv:2604.05432) — requires model-level
   provenance verification; regex cannot detect fine-tuned steganographic channels.

4. *(pending)* TrojanStego / linguistic steganography — statistical output analysis; not addressable
   by current rule-based architecture. Feasibility study for docs/.

5. *(pending)* HashJack / URL-fragment-based hidden instructions — agent browsing sandboxing guidance
   for docs/hardening-guides/.
