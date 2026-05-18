# Research: Prompt Injection — 2026-05-18T09-01

**Domain index:** 0 — `prompt-injection`
**Cycle:** Fourth pass at this domain
**Cycle timestamp:** 2026-05-18T09-01

---

## Key Findings

- **Malicious font injection via CSS @font-face remapping (arxiv:2505.16957, May 2026).**
  Researchers from Xi'an Jiaotong-Liverpool University systematically studied how LLM agents
  processing HTML web content can be attacked via manipulated TrueType font files injected using
  standard CSS `@font-face` rules. The attack works by modifying the font's `cmap` table (the
  character code-to-glyph-index mapping), so that glyphs that render as harmless text to human
  users actually encode a different sequence of characters at the LLM token level. Two attack
  scenarios were demonstrated against MCP-enabled agents: (1) "malicious content relay" — the
  agent silently forwards user messages to an attacker-controlled endpoint; (2) "sensitive data
  leakage" — the agent exfiltrates context data via MCP tool calls, bypassing model safety
  mechanisms. The malicious font is loaded via a standard web CDN pattern using
  `@font-face { src: url('https://attacker.com/...'); }` embedded in a scraped or RAG-ingested
  web page. The attack successfully bypassed safety filters in production models.
  Source: https://arxiv.org/abs/2505.16957
  **Aigis takeaway:** The delivery mechanism — `@font-face` CSS with a remote HTTP(S) URL in
  retrieved/external web content — is a concrete, detectable text pattern. Retrieved documents
  processed by an AI agent rarely have a legitimate need to load custom fonts; the presence of
  `@font-face` with an external URL is a reliable signal of a font injection attempt.

- **Prompt injection attacks on agentic coding assistants: 78-study meta-analysis (arxiv:2601.17548, Jan 2026).**
  A systematic analysis of 78 studies (2021–2026) on prompt injection attacks targeting Claude
  Code, GitHub Copilot, Cursor, and skill-based MCP ecosystems. The paper proposes a
  three-dimensional taxonomy across delivery vectors, attack modalities, and propagation behaviors.
  Key finding: attack success rates against state-of-the-art defenses exceed 85% when adaptive
  attacks are used. Specific attack classes identified for coding assistants:
  - Tool-result injection: malicious content embedded in tool return values (file reads, API
    responses) redirects agent actions.
  - Skill file poisoning: installing malicious skill files (equivalent to MCP tools) that
    execute attacker-controlled code when invoked.
  - Protocol exploitation: attacks specific to the MCP protocol structure.
  Source: https://arxiv.org/abs/2601.17548
  **Aigis takeaway:** Tool-result injection patterns (instructions embedded in tool output) are
  covered by existing INDIRECT_INJECTION_PATTERNS. Skill file poisoning is better handled in
  the supply-chain domain (index 5). No new aigis pattern needed from this paper this cycle.

- **Image-based prompt injection: 64% ASR in black-box settings (arxiv:2603.03637, Mar 2026).**
  End-to-end black-box pipeline for embedding adversarial instructions in natural images using
  segmentation-based region selection, adaptive font scaling, and background-aware rendering.
  Tested against GPT-4-turbo on the COCO dataset; achieved up to 64% attack success under stealth
  constraints. The technique is strictly a multimodal (vision) attack: the payload is rendered into
  pixels, not into text or CSS. Rule-based text-pattern filters (like those in aigis) cannot detect
  the visual payload directly; defense requires either image pre-processing or separate multimodal
  classifiers.
  Source: https://arxiv.org/abs/2603.03637
  **Aigis takeaway:** No new text-level aigis pattern is applicable for pixel-embedded visual
  injection. Deferred for research; could be added as a documentation hardening guide in a future
  docs/ cycle.

- **Chatbot plugin RAG poisoning: 13% of e-commerce sites already exposed (arxiv:2511.05797, Nov 2025, IEEE S&P 2026).**
  Study of 17 third-party chatbot plugins deployed on over 10,000 public websites. Key findings:
  - 15/17 plugins scrape third-party content (comments, reviews, product listings) for RAG
    without content isolation, opening a mass indirect prompt injection surface.
  - 8/17 plugins fail to integrity-protect the conversation history transmitted in HTTP requests,
    allowing an adversary to forge system-role messages and boost injection success 3–8x.
  - Manual audit found 13% of randomly sampled e-commerce sites already had chatbot contexts
    containing attacker-inserted third-party content.
  Source: https://arxiv.org/abs/2511.05797
  **Aigis takeaway:** The "conversation history forgery" attack forges
  `{"role": "system", "content": "..."}` JSON into chatbot API calls, but the injection happens
  at the HTTP-request layer rather than in the text content aigis scans. A text-level detection
  rule (`"role": "system"` in retrieved content) would have a high false-positive rate against
  legitimate API documentation and code examples. Deferred; better addressed as a network-layer
  hardening guide.

- **ProxyPrompt: defense against system prompt extraction achieving 94.7% protection (arxiv:2505.11459, May 2026).**
  Defense mechanism for protecting AI system prompts from extraction attacks. Replaces the original
  system prompt with a proxy that preserves task utility while obfuscating the extractable prompt.
  Evaluated against Pleak, Raccoon, and 14 other extraction techniques. Complementary to aigis'
  existing `pi_system_prompt_leak` and `PROMPT_LEAK_PATTERNS` rules.
  Source: https://arxiv.org/abs/2505.11459
  **Aigis takeaway:** Confirms aigis' existing prompt-leakage detection is in the right direction.
  No new pattern needed, but this paper could be referenced in the docs/ hardening guide for
  operators who want server-side extraction defenses.

- **Invisible Unicode injection in retrieved web content: documented real-world exploitation (May 2026).**
  Multiple analyses (Idan Habler / Medium, Hiding in Plain Sight blog, and supporting research)
  document real exploitation of non-rendering Unicode characters — zero-width joiners (U+200D),
  zero-width non-joiners (U+200C), soft hyphens (U+00AD), and the Unicode Tags block (U+E0000–
  U+E007F) — to embed hidden instructions in web content that gets RAG-ingested or browser-
  summarized. The characters are invisible to human viewers but fully tokenized by LLMs. Aigis
  already covers this via `te_zwsp_splitter`, `te_unicode_tag_smuggling`, `enc_tag_block_ascii`,
  and related patterns from domain 7 cycles.
  Source: https://idanhabler.medium.com/hiding-in-plain-sight-weaponizing-invisible-unicode-to-attack-llms-f9033865ec10
  **Aigis takeaway:** Already covered. No new pattern needed this cycle.

---

## Candidate Hardenings

1. **`ii_css_font_injection`** ← **IMPLEMENT THIS CYCLE** — Detect `@font-face` CSS rules with
   remote HTTP(S) font-source URLs in retrieved/external web content. When an AI agent processes
   raw HTML content (via MCP browsing tools, RAG ingestion, or web-page summarization), a malicious
   `@font-face` rule can remap standard ASCII characters to adversarial glyph sequences that the
   LLM processes as injection instructions. The delivery mechanism — `@font-face { src: url(https://
   attacker.com/...) }` — is a detectable, low-false-positive text pattern since retrieved documents
   legitimately processed by AI agents rarely require loading custom remote fonts.
   Source: arxiv:2505.16957, May 2026. Demonstrated ASR against production models; bypassed built-in
   safety filters in both tested scenarios (malicious content relay + sensitive data leakage via MCP).

2. **Image-based pixel injection documentation** — Deferred; text-level detection not feasible.
   Suggest future `docs/hardening-multimodal-injection.md` guide for operators deploying vision-
   enabled AI agents.

3. **Network-layer HTTP request integrity for chatbot plugins** — Deferred; this is a deployment
   hardening concern, not a text-pattern detection problem. Suggest a compliance template addition
   in the compliance-regulation domain cycle.

4. **ProxyPrompt-style system prompt obfuscation guide** — Deferred to docs/ hardening guide;
   no new detection pattern needed since aigis already covers extraction techniques.
