# Research: Evasion & Obfuscation — Third Pass (Domain 7)

**Cycle timestamp:** 2026-05-16T00-00
**Domain:** evasion-obfuscation (#7)
**Prior coverage:**
- 2026-05-09T00-15: BIDI override, morse code, leetspeak digit substitutions
- 2026-05-11T12-15: Unicode Tag Block ASCII smuggling (CVE-2025-32711/EchoLeak), fullwidth Latin characters

---

## Findings

1. **Mathematical Alphanumeric Symbols — 58.7% ASR Against Production Guardrails**
   Source: https://arxiv.org/abs/2405.14490 ; https://arxiv.org/abs/2605.03441
   The Unicode Mathematical Alphanumeric Symbols block (U+1D400–U+1D7FF) contains styled variants
   of every Latin/Greek letter — bold (𝗶𝗴𝗻𝗼𝗿𝗲), italic (𝑖𝑔𝑛𝑜𝑟𝑒), bold italic (𝒾𝑔𝓃𝑜𝓇𝑒), script
   (𝓲𝓰𝓷𝓸𝓻𝓮), fraktur (𝖎𝖌𝖓𝖔𝖗𝖊), monospace (𝚒𝚐𝚗𝚘𝚛𝚎), double-struck, and more.
   Attackers substitute attack keywords with these styled variants; the base LLM reads them as
   plain ASCII (the codepoints appear in LLM pre-training corpora), but ASCII-based safety classifiers
   miss them. arxiv:2405.14490 (2024, widely cited in 2025) measured 58.7% average cross-script
   homoglyph success rate against GPT-4, Claude 3 Opus, and Gemini 1.5 Pro, including content
   policy breaches and prompt leakage. arxiv:2605.03441 ("Exposing LLM Safety Gaps Through
   Mathematical Encoding", May 2026) confirmed 46–56% ASR against 8 target models including
   GPT-5-Mini. Unicode NFKC normalization resolves most of these codepoints to their ASCII
   equivalents, but few production guardrails apply it before classification.
   **Aigis takeaway:** A rule flagging 4+ consecutive Mathematical Alphanumeric Symbols covers
   this entire obfuscation class with very low FPR in API prompt contexts (mathematicians use
   individual styled chars; long keyword-length runs are essentially never legitimate).

2. **Combining Diacritics / Zalgo Text — 44–76% ASR (arxiv:2504.11168, Apr 2025)**
   Source: https://arxiv.org/abs/2504.11168 ; https://arxiv.org/abs/2508.14070
   Unicode Combining Diacritical Marks (U+0300–U+036F) stack visually on base characters.
   "Zalgo text" stacks dozens on each letter (e.g., ḭ̸̧͊g̷͙̈n̸̪̓o̵̙͝r̷̝͘ê), producing output that
   is visually unreadable to humans but semantically intact for LLMs. arxiv:2504.11168 tested
   diacritics as one of six character injection subtypes against Azure Prompt Shield, Meta Prompt
   Guard, and four other production guardrails, reporting 44–76% ASR across datasets. The ACL
   LLMSEC-2025 workshop paper (Mindgard, https://aclanthology.org/2025.llmsec-1.8.pdf) reported
   some defenses reaching 100% evasion success against diacritic-injected prompts. Three or more
   consecutive combining marks never occur in any natural language's well-formed Unicode text.
   **Aigis takeaway:** A rule triggering on 3+ consecutive combining diacritics (U+0300–U+036F)
   closes this class with very low FPR; legitimate language text never stacks 3+ diacritics in
   a row, even in Vietnamese, Tibetan, or heavily accented European text.

3. **Zero-Width Character Injection — 44–76% ASR; Confirmed in Production Agent Incidents**
   Source: https://arxiv.org/abs/2504.11168 ; https://arxiv.org/abs/2603.00164 ;
           https://embracethered.com/blog/posts/2025/amp-code-fixed-invisible-prompt-injection/
   Zero-Width Space (U+200B), Zero-Width Non-Joiner (U+200C), Zero-Width Joiner (U+200D),
   BOM (U+FEFF), and Word Joiner (U+2060) inserted between letters of blocked keywords shatter
   token boundaries, so regex classifiers see no recognizable keyword (e.g., "ign​ore" passes
   a naive "ignore" blocklist). arxiv:2603.00164 ("Reverse CAPTCHA", Feb 2026) tested
   zero-width binary encoding (ZWS/ZWNJ pairs as 0/1) against GPT and Claude families; with
   tool use enabled, model compliance with hidden zero-width-encoded instructions spiked
   dramatically (Cohen's h up to 1.37). Confirmed in production: a February 2025 supply-chain
   attack embedded malicious instructions in IDE rules files using invisible Unicode chars;
   Amp Code (Sourcegraph's AI coding agent) had a zero-width injection bug patched in 2025.
   The existing `te_unicode_noise` pattern flags 3+ consecutive zero-width chars; this
   technique inserts them one at a time between individual letters, which `te_unicode_noise`
   does not catch.
   **Aigis takeaway:** Candidate for future cycle — requires proximity detection (ZW chars
   next to attack keywords) or density-based scoring; a threshold rule without keyword
   context has high FPR in CJK/Arabic text that legitimately uses ZWJ for ligature control.
   Deferring to pending.

4. **Soft Hyphen (U+00AD) Injection — CRITICAL Severity Flag in Agent Files (Apr 2026)**
   Source: https://github.com/msitarzewski/agency-agents/issues/478 ;
           https://www.keysight.com/blogs/en/tech/nwvs/2025/05/16/invisible-prompt-injection-attack
   The SOFT HYPHEN (U+00AD / SHY) renders as invisible in all common editors, browsers, and
   Markdown renderers, but exists in the raw byte stream. Inserting it between characters of
   blocked keywords (i­g­n­o­r­e) breaks string matching while the LLM tokenizer may reconstruct
   the surrounding text. GitHub issue agency-agents #478 (April 2026) flagged U+00AD embedded
   inside agent definition file headings as CRITICAL severity. Paubox (Nov 2025) documented the
   same technique in phishing email filter bypass. NFKC normalization does NOT remove U+00AD.
   **Aigis takeaway:** Candidate for future cycle — density-based rule (>1 U+00AD per 20 chars)
   is needed rather than binary presence, since U+00AD appears legitimately in typeset text.
   Deferring to pending.

5. **HTML Entity Encoding Bypass — 36% ASR vs. BrowseSafe; 58–74% in Fuzzing**
   Source: https://www.lasso.security/blog/red-teaming-browsesafe-perplexity-prompt-injections-risks ;
           https://arxiv.org/abs/2510.13543
   HTML entities (`&#105;&#103;&#110;&#111;&#114;&#101;` = "ignore") are decoded by downstream
   renderers but passed through safety classifiers that operate on raw strings. Lasso Security
   red-teamed Perplexity's BrowseSafe guardrail in January 2026, achieving 36% bypass using
   entity-encoded instructions hidden in HTML. In-Browser LLM Fuzzing (arxiv:2510.13543) showed
   that by the 10th fuzzing iteration, agentic browser defenses fail in 58–74% of cases using
   entity mutation strategies. Unit 42 confirmed entity encoding in real-world indirect prompt
   injection attacks on browsing agents.
   **Aigis takeaway:** Relevant for web-agent pipelines; existing `enc_markdown_hidden` covers
   CSS/Markdown concealment but not raw HTML entity encoding. Candidate for future cycle
   targeting the MCP/browser-tool pipeline context.

6. **Variation Selector Imperceptible Jailbreaks — 72–100% ASR (arxiv:2510.05025, Oct 2025)**
   Source: https://arxiv.org/abs/2510.05025
   Unicode variation selectors (U+FE00–U+FE0F, VS1–VS16) are invisible suffix characters normally
   used for emoji/CJK glyph selection. Adversarially optimized sequences of 800–1,200 variation
   selectors appended to attack prompts achieved 72–100% ASR on Llama-3.1, Mistral, Gemma, and
   Falcon. The variation selectors form an invisible adversarial suffix that the LLM tokenizer
   processes but humans cannot see. The existing pending proposal (2026-05-11) defers this due
   to FPR concerns with legitimate emoji text.
   **Aigis takeaway:** Still deferred — the adversarial suffix uses hundreds of VS chars;
   detecting 5+ consecutive VS-1 through VS-16 (U+FE00–U+FE0F) outside emoji/CJK context
   would be effective but requires Unicode grapheme cluster context to distinguish legitimate use.
   Ongoing pending.

7. **arxiv:2508.14070 — Special-Character Attacks: Systematic Measurement (Aug 2025)**
   Source: https://arxiv.org/abs/2508.14070
   Systematic evaluation of 14 special-character obfuscation classes including combining diacritics,
   fullwidth, BIDI, zero-width, zalgo, and mathematical Unicode against 7 open-source models
   (3.8B–32B params). Key finding: architectural choices, not model size, determine robustness.
   Models with explicit Unicode normalization preprocessing are significantly more robust.
   Also confirms that combining diacritics and mathematical Unicode are distinct, measurable
   obfuscation families alongside fullwidth (which aigis already covers).
   **Aigis takeaway:** Validates implementing mathematical Unicode and zalgo as separate,
   independent detection patterns rather than relying on fullwidth coverage alone.

---

## Candidate Hardenings

1. **`enc_math_unicode_keywords` detection pattern** (score 45) — Detect 4+ consecutive
   Mathematical Alphanumeric Symbol characters (U+1D400–U+1D7FF). Covers bold, italic, script,
   fraktur, monospace, double-struck variants of attack keywords. ASR source: arxiv:2405.14490
   (58.7%), arxiv:2605.03441 (46–56%). Very low FPR in API prompt contexts. *(Implement this
   cycle.)*

2. **`enc_zalgo_text` detection pattern** (score 35) — Detect 3+ consecutive Unicode combining
   diacritical marks (U+0300–U+036F). Covers zalgo text and mild diacritic substitution attacks.
   ASR source: arxiv:2504.11168 (44–76%). Very low FPR — legitimate text never has 3+ consecutive
   combining marks. *(Implement this cycle.)*

3. **Zero-width keyword splitter rule** — Single ZW chars interleaved between keyword letters.
   Requires keyword-proximity detection or density scoring to avoid FPR on CJK/Arabic.
   Defer to pending.

4. **Soft hyphen (U+00AD) density rule** — Density-based (>1 per 20 chars) rather than binary.
   NFKC does not strip U+00AD so needs explicit detection. Defer to pending.

5. **HTML entity decode pass for web-agent pipelines** — Apply html.unescape() before keyword
   matching in MCP tool output / browser-agent context. Deferred: broader architectural change
   in scanner pipeline; save to pending.

6. **Variation selector suffix detection** — Flag 5+ consecutive U+FE00–U+FE0F or U+E0100–
   U+E01EF outside CJK/emoji context. Still deferred due to FPR concerns; keep in pending.
