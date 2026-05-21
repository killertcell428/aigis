# Research: Evasion & Obfuscation — Third Pass (Domain 7)

> **Note:** This research was conducted during the same cycle session as domain 3
> (jailbreak-extraction). The candidate implementations (`enc_zero_width_splitter`,
> `enc_zw_steganography`) were found to already be present in origin/master as
> `enc_zwc_splitter` and `enc_zwc_binary_payload`. No implementation needed;
> keeping this file as research record.

**Cycle timestamp:** 2026-05-21T09-07
**Domain:** evasion-obfuscation (#7)
**Prior coverage:**
- 2026-05-09T00-15 — BIDI override, Morse code, leetspeak
- 2026-05-11T12-15 — Tag block ASCII smuggling (CVE-2025-32711), fullwidth Latin obfuscation

---

## Findings

1. **Reverse CAPTCHA: Zero-Width Binary Steganography (arxiv:2603.00164, Feb 2026)**
   Source: https://arxiv.org/abs/2603.00164
   Marcus Graves (Feb 26, 2026) evaluated five frontier LLMs from two providers across two
   zero-width encoding schemes and four "hint" levels. The attack embeds full instructions as a
   bit sequence using zero-width Unicode characters — typically U+200B for bit-0 and U+200C for
   bit-1, or U+200C for bit-0 and U+2063 for bit-1 — producing a dense run of invisible
   characters that renders as blank space to human reviewers but is processed as a valid
   instruction by the LLM. Key findings: (a) explicit decoding instructions increase compliance
   by up to 95 percentage points within a single model/encoding pair; (b) tool use dramatically
   amplifies attack success (Cohen's h up to 1.37, a large effect); (c) provider-specific
   encoding preferences were observed — OpenAI models decoded zero-width binary; Anthropic
   models preferred Unicode Tag encoding. A real-world incident on the Moltbook platform
   (Feb 16, 2026) confirmed active exploitation using the U+200C/U+2063 variant.
   **Aigis takeaway:** A pattern detecting 4+ consecutive characters from the zero-width set
   (U+200B, U+200C, U+200D, U+2060, U+2063) flags steganographic bit-encoding with very low
   FPR — legitimate text never contains dense runs of these characters.

2. **Hidden-in-Plain-Text: Zero-Width Keyword Splitters (arxiv:2601.10923, Jan 2026)**
   Source: https://arxiv.org/abs/2601.10923
   Social-web indirect prompt injection benchmark for RAG systems. One documented attack carrier:
   inserting zero-width characters (U+200B, U+200C, U+00AD, U+FEFF) between the letters of
   injection keywords to defeat text-level sanitization filters. "ign​ore" (with U+200B after
   "ign") passes a naive "ignore" blocklist because the string comparison fails, while the LLM's
   tokenizer reassembles the keyword at the token level and follows the instruction. The paper
   also evaluates off-screen CSS, hidden HTML spans, and ARIA attributes as indirect carriers.
   **Aigis takeaway:** A pattern matching ASCII-letter + ZW-char + ASCII-letter specifically
   catches the keyword-splitter technique with low FPR. Resolves pending proposal
   `auto-improvement/pending/2026-05-12_unicode-splitter-injection-evasion.md`.

3. **Broken-Token: Characters-Per-Token Detection (arxiv:2510.26847, Oct 2025)**
   Source: https://arxiv.org/abs/2510.26847
   Proposes CPT-Filtering: obfuscated inputs (diacritics, fullwidth, zero-width flooding,
   BIDI insertions) produce significantly lower characters-per-token ratios than normal text,
   because BPE tokenizers represent out-of-distribution characters with many short tokens.
   Normal English text averages ~4.5 chars/token; obfuscated inputs drop to 1–2 chars/token.
   Validated on >100,000 prompts; a CPT threshold of 3.0 detects >85% of obfuscation variants
   at <1% FPR.
   **Aigis takeaway:** Complementary to pattern-based detection. Already in pending as
   `auto-improvement/pending/2026-05-09_cpt-chars-per-token-heuristic.md`; held back by
   CJK false-positive risk. No new action this cycle.

4. **RoguePrompt: Dual-Layer Cipher Attack (arxiv:2511.18790, Nov 2025)**
   Source: https://arxiv.org/abs/2511.18790
   Automated jailbreak pipeline partitioning a forbidden prompt and applying two nested
   encodings (ROT-13 + Vigenère cipher) plus natural-language decoding instructions. Achieved
   93.93% filter bypass, 79.02% payload reconstruction, and 70.18% full execution success
   across multiple frontier LLMs. The Vigenère stage is the key novelty — standard safety
   training does not include Vigenère-encoded harmful content.
   **Aigis takeaway:** ROT-13 alone is already covered by `enc_rot13_instruction`. The
   Vigenère addition would be useful but is harder to detect via regex without a high FPR
   (Vigenère key-header syntax is inconsistently formatted). Save to pending.

5. **Script Mixing / Homoglyph Attacks Against LLaMA (July 2025)**
   Source: https://github.com/meta-llama/llama/issues/1382 ; https://inspiroz.com/what-is-a-homoglyph-attack/
   Documented attack combining Cyrillic lookalike characters (Cyrillic а U+0430 ≈ Latin a U+0061,
   Cyrillic о U+043E ≈ Latin o U+006F, etc.) with zero-width spaces to bypass LLaMA content
   filters. The existing `enc_mixed_script` pattern (score 30) covers adjacent Cyrillic/Latin
   pairs but does not cover the combined case where a single Latin word is mostly ASCII with
   only 1–2 Cyrillic homoglyphs substituted.
   **Aigis takeaway:** The `enc_mixed_script` pattern is currently the right tool; strengthening
   it to detect single-character Cyrillic substitution inside otherwise-Latin words is the next
   hardening step. Defer to a future cycle.

6. **Zero-Width Steganography — Promptfoo & Real-World Incidents (Feb 2026)**
   Source: https://www.promptfoo.dev/blog/invisible-unicode-threats/
   A supply-chain attack targeting GitHub Copilot and Cursor AI agents (Pillar Security, Feb 2025)
   used invisible Unicode characters in `.cursorrules` / `.clinerules` files to issue hidden
   instructions. The poisoned rules files told the AI to inject backdoors, disable security
   checks, or exfiltrate credentials in every code generation. Tool use was identified as the
   primary amplifier — the AI blindly follows rules files before executing any tool calls.
   **Aigis takeaway:** The `enc_zw_steganography` pattern directly addresses this attack vector:
   the dense zero-width encoding in the rules file would trigger on any scan of the file content.

7. **"Scary Agent Skills": Hidden Unicode in MCP Skill Files (embracethered.com, 2026)**
   Source: https://embracethered.com/blog/posts/2026/scary-agent-skills/
   Documented MCP skills and Claude/Cursor rules files distributed with invisible Unicode-encoded
   instructions that instruct the AI agent to leak files, send data to external URLs, or add
   backdoors. The invisible content is embedded using the same zero-width bit-encoding schemes
   as arxiv:2603.00164. Specific targets include `.claude/CLAUDE.md`, MCP server tool
   descriptions, and skill manifest files retrieved at agent startup.
   **Aigis takeaway:** For agentic pipelines, aigis should scan fetched skill descriptions and
   retrieved config files (tool outputs), not just user prompts. The `enc_zw_steganography`
   pattern applies to this vector.

8. **Unicode Exploits in Application Security (prompt.security, 2025–2026)**
   Source: https://prompt.security/blog/unicode-exploits-are-compromising-application-security
   Survey of Unicode abuse vectors in production AI applications: zero-width joiners (U+200D),
   direction overrides (BIDI), soft hyphens (U+00AD), BOM (U+FEFF), and tag block characters.
   Recommends server-side stripping before any LLM call, with aigis-style pre-screening as
   the primary defense layer.
   **Aigis takeaway:** Confirms the value of the new keyword-splitter pattern covering
   U+200B, U+200C, U+00AD, U+FEFF, U+2060.

---

## Candidate Hardenings

1. **`enc_zero_width_splitter` detection pattern** (score 30) — Detect zero-width or invisible
   Unicode characters (U+200B, U+200C, U+00AD, U+FEFF, U+2060) sandwiched between two ASCII
   letters. Directly addresses keyword-splitter attacks from arxiv:2601.10923 and the broader
   class of text-sanitization bypasses via invisible character insertion. FPR very low when
   limited to the "letter + ZW + letter" context. **Resolves pending proposal
   `2026-05-12_unicode-splitter-injection-evasion.md`.** *(Implement this cycle.)*

2. **`enc_zw_steganography` detection pattern** (score 65) — Detect 4+ consecutive zero-width
   characters (U+200B, U+200C, U+200D, U+2060, U+2063). Directly addresses zero-width binary
   steganography from arxiv:2603.00164 (Reverse CAPTCHA, Feb 2026) and the Moltbook/Pillar
   Security real-world incidents. FPR is negligible — legitimate text never contains dense
   consecutive runs of these characters. *(Implement this cycle.)*

3. **Vigenère cipher instruction detector** (`enc_vigenere_instruction`, score 40) — Detect
   explicit "Vigenère key" or "decode with Vigenère" instructions. Addresses the RoguePrompt
   dual-layer bypass (arxiv:2511.18790, 93.93% filter bypass). Harder to regex without FPR;
   defer to pending.

4. **`enc_mixed_script` improvement** — Strengthen the existing mixed-script detector to catch
   single Cyrillic homoglyph substitutions in otherwise-Latin words. Requires testing against
   multilingual corpora. Defer to pending.
