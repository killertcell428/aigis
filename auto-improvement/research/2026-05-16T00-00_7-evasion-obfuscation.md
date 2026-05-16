# Research: Evasion & Obfuscation — Third Pass (Domain 7)

**Cycle timestamp:** 2026-05-16T00-00
**Domain:** evasion-obfuscation (#7)
**Prior coverage:**
- 2026-05-09T00-15: BIDI override, morse code, leetspeak substitution
- 2026-05-11T12-15: Unicode Tag Block ASCII smuggling (enc_tag_block_ascii, implemented),
  fullwidth Latin obfuscation (enc_fullwidth_keywords, implemented),
  variation selector heuristic (deferred → pending),
  grapheme-cluster tag filter (deferred → pending)

**Focus this pass:** Zero-width character keyword splitting (sparse ZWC interleaving vs. dense blocks), zero-width binary steganography, and acrostic steganographic jailbreaks — all post-May 2025 findings.

---

## Findings

1. **Zero-Width Character Keyword Splitting — distinct gap in existing coverage**
   Source: https://arxiv.org/html/2504.11168v3 (Mindgard, Apr 2026)
   Character injection via zero-width characters is documented as one of twelve evaluated
   character-injection techniques in arxiv:2504.11168. The specific "keyword splitting" form
   inserts exactly one zero-width space (U+200B), zero-width non-joiner (U+200C), zero-width
   joiner (U+200D), or soft hyphen (U+00AD) between each letter of an attack keyword. For
   example, 'i​g​n​o​r​e' (each letter separated by a single U+200B) reads as
   "ignore" but no three consecutive invisible characters appear adjacently — so the existing
   `te_unicode_noise` rule (which requires 3+ consecutive invisible chars) does not trigger.
   arxiv:2504.11168 measured zero-width character injection achieving up to 54% attack success
   rate against production guardrails including Azure Prompt Shield and Vijil Prompt Injection.
   **Aigis takeaway:** Add `enc_zwc_keyword_split` — a pattern matching `[A-Za-z]` followed by
   (invisible char + `[A-Za-z]`) repeated 3+ times — to close this sparse-interleaving gap.
   This requires a minimum of 4 visible letters each separated by one invisible character,
   with virtually no false-positive risk in AI prompt text.

2. **Reverse CAPTCHA — Zero-Width Binary Encoding of Hidden Instructions (arxiv:2603.00164, Feb 2026)**
   Source: https://arxiv.org/abs/2603.00164 ; https://github.com/canonicalmg/reverse-captcha-eval
   Marcus Graves (submitted Feb 26, 2026) introduces the "Reverse CAPTCHA" framework: an
   evaluation showing LLMs reliably follow instructions that are completely invisible to human
   readers. Two encoding schemes are tested: (1) Zero-Width Binary (ZWB) — each ASCII character
   is encoded as 8 binary digits using U+200B for bit-0 and U+200C for bit-1 (96 invisible
   chars for a 12-character instruction); (2) Unicode Tag block — each ASCII char maps to
   U+E0000 + codepoint. Tool-use dramatically amplifies compliance: Cohen's h up to 1.37
   (large effect), meaning models are far more likely to execute an invisible instruction when
   they have tool access. Disclosed after a real-world incident on the Moltbook platform
   (February 16, 2026). The ZWB form (consecutive U+200B/U+200C sequences) is already caught
   by `te_unicode_noise` (3+ consecutive invisible chars); the Tag block form is caught by
   `enc_tag_block_ascii`. The new finding is the tool-use compliance amplification.
   **Aigis takeaway:** No new rule needed for the dense ZWB form (already caught). The
   tool-use finding strengthens the argument for aigis's scanner intercepting MCP tool inputs
   and outputs — the risk is highest in agentic, tool-enabled contexts. Document in remediation.

3. **StegoAttack — Acrostic Steganographic Jailbreaks (arxiv:2505.16765, May 2025)**
   Source: https://arxiv.org/abs/2505.16765
   Researchers at Nankai University's College of Cyber Science propose StegoAttack: an LLM
   generates a benign, coherent paragraph where each sentence's first letter spells out the
   harmful query (acrostic steganography). The cover paragraph passes semantic-stealth checks
   (no surface-level red flags) and linguistic-stealth checks (natural fluency). The receiving
   LLM decodes the acrostic and answers the hidden query. Measured ASR: 95.50% average across
   four safety-aligned LLMs including GPT-4 and Gemini models, outperforming all eight
   evaluated jailbreak baselines. ASR drops by less than 27% under external detectors.
   **Aigis takeaway:** Acrostic steganography is not detectable by regex or rule-based methods.
   It is an LLM-to-LLM channel — detection would require the receiving model to notice the
   acrostic structure and verify the decoded message against policy. Defer to pending.

4. **Invisible Font Injection via Web Pages (arxiv:2505.16957, EMNLP 2025)**
   Source: https://arxiv.org/abs/2505.16957
   Xi'an Jiaotong-Liverpool University researchers demonstrate injecting hidden prompts via
   manipulated CSS/font code-to-glyph mappings in webpages retrieved by tool-enabled LLM
   agents. When the agent fetches the page and processes the text, the font substitution causes
   the rendered characters to differ from the font file's internal mapping, so the agent "reads"
   a hidden instruction that is visually invisible in the rendered page. Two attack scenarios:
   (1) malicious content relay, (2) sensitive data leakage via MCP-enabled tools. Accepted at
   EMNLP 2025. This is a document-layer attack, not a string-level Unicode attack.
   **Aigis takeaway:** Font injection is not catchable at the Unicode / string level; it requires
   analyzing the CSS or font binaries. Useful for a doc-layer hardening guide. Defer to pending.

5. **Promptfoo: Zero-Width Unicode Backdoors in AI-Generated Code (2025)**
   Source: https://www.promptfoo.dev/blog/invisible-unicode-threats/
   Promptfoo documented real-world cases where zero-width characters were injected into
   AI-generated code via poisoned context (e.g., retrieved from a compromised repository or
   web page). The invisible characters appear in code comments, string literals, or identifier
   names and cause silent behavioral differences when executed. The pattern resembles supply
   chain attacks on LLM codegen pipelines: the poisoned context is fetched via a tool call, the
   invisible instructions survive round-tripping through the LLM, and the emitted code contains
   a hidden backdoor. The existing `te_unicode_noise` rule catches dense clusters; the keyword-
   splitting variant would be caught by `enc_zwc_keyword_split`.
   **Aigis takeaway:** Validates that aigis's output scanner (not just input scanner) should
   apply `enc_zwc_keyword_split` — poisoned code output is a real vector.

6. **Character-Level Attacks: Full Classification (arxiv:2508.14070v1, Aug 2025)**
   Source: https://arxiv.org/html/2508.14070v1
   A systematic evaluation of 14 special-character obfuscation classes against four open-source
   aligned LLMs: fullwidth, BIDI, zero-width, homoglyphs, diacritics, zalgo, null bytes, and
   more. Key finding for this cycle: the "zero-width character injection" class (which includes
   keyword splitting) achieved 52–54% average ASR. The "zalgo text" class (excessive combining
   diacritical marks) was evaluated separately and achieved 38% average ASR — lower than
   fullwidth or zero-width, but non-negligible. Zalgo detection was explicitly listed as a
   "future hardening" item by the authors.
   **Aigis takeaway:** Zalgo / excessive combining diacritical marks (U+0300–U+036F) remain an
   open gap. `te_unicode_noise` does not cover them (combining chars are not invisible-zero-width).
   A rule detecting 6+ consecutive combining marks would close this with low FPR. Defer to
   pending for this cycle as a secondary candidate.

7. **Soft Hyphen (U+00AD) as a Steganographic Carrier**
   Source: https://meiert.com/blog/word-division-on-word-break-soft-hyphens-and-zero-width-spaces/ ;
   https://arxiv.org/html/2504.11168v3
   The soft hyphen (U+00AD) is a legitimate typographic character signaling optional line-break
   points within compound words. However, when inserted between every letter of an attack keyword,
   it functions identically to U+200B as a keyword splitter. U+00AD is included in `te_unicode_noise`
   but only when three or more appear consecutively — `b­y­p­a­s­s` (one U+00AD between each letter
   of "bypass") would not trigger the existing rule. The `enc_zwc_keyword_split` rule proposed in
   finding 1 explicitly includes U+00AD in its character class.
   **Aigis takeaway:** Covered by `enc_zwc_keyword_split` (implemented this cycle).

8. **Unit 42 (Palo Alto) — First Large-Scale Indirect Prompt Injection in the Wild (Mar 2026)**
   Source: https://unit42.paloaltonetworks.com/genai-llm-prompt-fuzzing/
   Unit 42 documented, in March 2026, the first confirmed large-scale indirect prompt injection
   attacks in production commercial platforms. Evasion techniques observed in the wild include
   ad-review evasion (injected into ad copy to manipulate content-moderation LLMs) and system
   prompt leakage via encoding tricks. This confirms that obfuscation-based injection is no
   longer a research scenario — it is happening against live systems. Attackers are using
   combinations of character-level obfuscation and semantic tricks simultaneously.
   **Aigis takeaway:** Urgency for comprehensive encoding bypass coverage. The keyword-splitting
   and zero-width techniques (enc_zwc_keyword_split) are especially relevant for ad-review and
   content-moderation use cases.

---

## Candidate Hardenings

1. **`enc_zwc_keyword_split` detection pattern** (score 50, input/output filter) — Detect
   keywords that are split character-by-character using single invisible Unicode characters
   (zero-width space, ZWNJ, ZWJ, soft hyphen). Pattern: `[A-Za-z](?:[invisible][A-Za-z]){3,}`.
   Fills the gap not covered by `te_unicode_noise` (which requires 3+ consecutive invisible chars).
   *(Implemented this cycle — see enc_zwc_keyword_split in ENCODING_BYPASS_PATTERNS.)*

2. **Zalgo / combining diacritical overdrive detection** (score 30–40) — Detect 6+ consecutive
   combining diacritical marks (U+0300–U+036F). Covers the 38% ASR "zalgo text" class from
   arxiv:2508.14070. Low FPR: most real-world text has 0–2 combining marks per sentence.
   *(Defer to pending: secondary priority, lower ASR, still worth adding in next cycle.)*

3. **Invisible font injection warning in agent hardening guide** — Document the font-injection
   attack vector (arxiv:2505.16957) in `docs/` as a guide for developers building agents that
   fetch and process external web content or PDFs. Recommend validating that retrieved content
   is plaintext-only before passing to the LLM, or using headless rendering in a sandbox.
   *(Defer to pending: documentation-only, low urgency compared to code changes.)*

4. **Acrostic steganography pending** — StegoAttack (arxiv:2505.16765) achieves 95.5% ASR but
   is not detectable by rule-based methods. Deferred to pending for future consideration of
   LLM-assisted detection strategies.
