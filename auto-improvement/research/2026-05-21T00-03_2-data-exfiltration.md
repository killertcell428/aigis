# Research: data-exfiltration (Cycle 2, fourth pass)

**Cycle UTC:** 2026-05-21T00-03
**Domain index:** 2
**Domain key:** data-exfiltration

Previous cycles:
- 2026-05-07: Markdown image exfil, OAST relay domains, DNS tunneling, EchoLeak, reference-style markdown bypass.
- 2026-05-10: OAST domain list expansion, search-query covert channel (arxiv:2510.09093).
- 2026-05-13 (×2): Mermaid diagram href exfil (out_diagram_href_exfil); Unicode tag block detection held in pending, then resolved.
- 2026-05-14: Unicode tag block smuggling (`unicode_tag_block_smuggling`, `out_unicode_tag_block_smuggling`) and sharded exfiltration (`exfil_shard_split_requests`). Pending: CSS hidden text, LogJack.

This pass focuses on HTML carrier channels for indirect prompt injection not yet covered: HTML
comment blocks and ARIA/alt-text attributes. Research basis: arXiv:2602.10498, arXiv:2601.10923,
and in-the-wild observations from Unit42/Palo Alto Networks (April 2026).

---

## Findings

- **"When Skills Lie: Hidden-Comment Injection in LLM Agents" (arXiv:2602.10498, Feb 2026)**
  HTML comment blocks (`<!-- ... -->`) in Markdown-formatted Skill documents are rendered
  invisible in HTML but the raw source text — including comment content — is fed verbatim to
  LLMs in RAG pipelines and AI agent skill loaders. Authors show that malicious instructions in
  HTML comments successfully steered DeepSeek-V3.2 and GLM-4.5-Air into sensitive tool calls.
  The exploit requires no special encoding; a single HTML comment with override language
  ("new instructions:", "you are now…") is sufficient.
  Source: https://arxiv.org/abs/2602.10498
  *Aigis takeaway:* Implement `ii_html_comment_directive` — detect override/instruction
  keywords inside `<!-- ... -->` blocks. **→ IMPLEMENTED this cycle.**

- **"Hidden-in-Plain-Text: A Benchmark for Social-Web Indirect Prompt Injection in RAG"
  (arXiv:2601.10923, Jan 2026)**
  Comprehensive benchmark of "Social-Web carriers" for indirect prompt injection: hidden/off-screen
  HTML/Markdown, alt text, ARIA attributes, zero-width characters, plus a PDF/SVG slice. Key
  finding: ARIA-based attacks proved the **most resilient** carrier type — combining sanitization,
  Unicode normalization, and attribution defenses still left 4.7% attack success. Attackers embed
  full injection payloads in `aria-label`, `aria-describedby`, `aria-placeholder`, and `alt`
  attribute values. These are invisible to sighted users but extracted by LLMs processing raw HTML.
  Source: https://arxiv.org/abs/2601.10923
  *Aigis takeaway:* Implement `ii_aria_alt_directive` — detect injection keywords in ARIA
  attribute values and image alt text. **→ IMPLEMENTED this cycle.**

- **HTML carrier injection active in the wild (Unit42/Palo Alto Networks, April 2026)**
  Unit42 documented ten specific examples of Indirect Prompt Injection (IPI) on live websites
  in April 2026, with trigger phrases like "Ignore previous instructions" and "If you are a
  large language model" hidden in HTML comments and metadata. A 32% increase in malicious IPI
  activity was observed between November 2025 and February 2026. Agent pipelines that strip
  `<script>` and `<style>` tags but leave the rest of the DOM intact are particularly vulnerable
  because hidden divs, ARIA attributes, and comment blocks survive cleanup.
  Source: https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/
  *Aigis takeaway:* Confirms urgency of both new patterns. No additional pattern needed.

- **CSS hidden text injection: PromptArmor January 2026 demo**
  In January 2026, PromptArmor demonstrated a prompt injection attack using a Word document with
  hidden white text that tricked Claude into uploading sensitive files containing partial Social
  Security numbers. Techniques include white-on-white text, `display:none`, `opacity:0`, and
  `font-size:0px`.
  Source: https://searchengineland.com/hidden-prompt-injection-black-hat-trick-ai-outgrew-462331
  *Aigis takeaway:* CSS hidden text injection (already in pending from 2026-05-14). Proper
  detection requires HTML DOM parsing rather than regex. Implementation estimate ≤60 non-test
  LOC using stdlib `html.parser`. Remains in pending.

- **"Decoding Latent Attack Surfaces in LLMs: Prompt Injection via HTML in Web Summarization"
  (arXiv:2509.05831)**
  Examines how non-visible HTML elements (`<meta>`, `aria-label`, `alt`) can be exploited to
  embed adversarial instructions without altering visible content. Over 29% of injected samples
  caused noticeable changes in Llama 4 Scout summaries; Gemma 9B IT showed 15% success rate.
  ARIA and alt-text carriers survived content-extraction pipelines that strip CSS but not
  attribute values.
  Source: https://arxiv.org/abs/2509.05831
  *Aigis takeaway:* Confirms ARIA/alt pattern priority. No additional rule needed.

- **"Your LLM Agent Can Leak Your Data: Data Exfiltration via Backdoored Tool Use"
  (arXiv:2604.05432, April 2026)**
  "Back-Reveal" attack: fine-tuned LLM agents with embedded semantic triggers perform covert
  multi-turn exfiltration by invoking memory-access and retrieval tool calls that gradually
  expose stored user context to an attacker-controlled endpoint. Trigger phrases are disguised
  as ordinary queries; the backdoor fires on statistical similarity to the trigger pattern.
  Source: https://arxiv.org/abs/2604.05432
  *Aigis takeaway:* This is a supply-chain (backdoored fine-tune) threat rather than a text
  pattern. Detection via input/output scanning is limited. Deferred to `supply-chain-llm` domain
  for a future cycle.

- **Microsoft Defender: 50+ CSS manipulation prompts across 31 companies (Feb 2026)**
  Microsoft's Defender team identified manipulation prompts from 31 companies across 14 industries
  embedded in web content via CSS hiding techniques — used for AI SEO manipulation and context
  hijacking. Reinforces that CSS hidden text injection is an active, widespread threat.
  Source: https://brainbyteslab.org/articles/llm-seo-manipulating-ai-summarization/
  *Aigis takeaway:* Further motivation for CSS hidden text filter (still in pending).

---

## Candidate hardenings

1. **`ii_html_comment_directive`** (score 70, input filter) — Detect override/instruction-injection
   keywords in HTML comment blocks. Based on arXiv:2602.10498, Feb 2026. ✅ **Implemented.**

2. **`ii_aria_alt_directive`** (score 65, input filter) — Detect injection keywords in ARIA
   attributes (`aria-label`, `aria-describedby`, `aria-placeholder`, `aria-roledescription`)
   and `alt` text. Based on arXiv:2601.10923, Jan 2026. ARIA attacks most resilient carrier;
   4.7% ASR survived all combined defenses. ✅ **Implemented.**

3. **CSS hidden text filter** — Implement a DOM-based filter using stdlib `html.parser` to extract
   text from CSS-hidden elements (`display:none`, `visibility:hidden`, `opacity:0`, `font-size:0`,
   `color:white`). PromptArmor January 2026 demo confirmed real-world exploit. More complex than
   regex (needs DOM traversal) but no new dependency. → **Remains in pending.**

4. **Back-Reveal backdoored tool detection** — Detect statistical patterns of covert multi-turn
   memory reads followed by suspicious retrieval calls. Requires behavioral analysis across
   multiple turns. → **Send to supply-chain-llm domain.**
