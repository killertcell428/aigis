# Research: Evasion & Obfuscation — Third Pass (Domain 7)

**Domain:** evasion-obfuscation (#7)
**Cycle index:** 7
**Cycle timestamp:** 2026-05-15T06-12

**Prior coverage:**
- 2026-05-09T00-15: BIDI override (U+202D/202E), morse code, leetspeak digit substitutions
- 2026-05-11T12-15: Unicode Tag Block ASCII smuggling (CVE-2025-32711/EchoLeak, enc_tag_block_ascii), fullwidth Latin characters (enc_fullwidth_keywords)

This pass focuses on two attack classes not yet detected by aigis: text-flipping/reversal attacks and combining-diacritical-marks overloading (zalgo-style evasion).

---

## Findings

1. **FlipAttack: Jailbreak LLMs via Flipping (ICML 2025, arxiv:2410.02832)**
   Source: https://arxiv.org/abs/2410.02832
   FlipAttack (accepted at ICML 2025) exploits the fact that LLMs process token sequences left-to-right
   and struggle to comprehend reversed or flipped text without an explicit decode instruction. The attack
   disguises harmful content by reversing characters or words, then prepends a one-line decode
   instruction ("read the following backwards and execute," "the following is in reverse — reverse it
   first," etc.). The attack achieves **~98% ASR on GPT-4o** and **~78.97% average ASR across 8 LLMs**
   with only a single query. Critically, the reversed text itself is semantically empty to safety
   classifiers trained on natural-language patterns, so only the decode instruction is a reliable signal.
   **Aigis takeaway:** A pattern detecting explicit flip/reverse decode instructions ("read this
   backwards", "the following is reversed", "reverse the words and execute") closes this attack class
   with very low FPR. Legitimate prompts rarely ask LLMs to reverse arbitrary text as a decoding step.

2. **Diacritics Overloading Attack — arxiv:2504.11168 (Mindgard Research, April 2025)**
   Source: https://arxiv.org/html/2504.11168v3
   The comprehensive guardrail evasion paper tests diacritics attacks (replacing vowels with diacritical
   equivalents, and stacking combining diacritical marks — U+0300–U+036F — on base characters). The
   diacritics technique achieves **44–76% average ASR** across six production guardrails including Azure
   Prompt Shield, Meta Prompt Guard, Protect AI v1/v2, Nvidia NeMo, and Vijil. The mechanism: safety
   classifiers tokenize at the BPE level and treat diacritically-overloaded text as an unusual token
   sequence, missing the embedded keywords, while the underlying LLM reads through the combining marks
   and decodes the semantic meaning correctly. For example, `ïgnörë` or the more extreme zalgo form
   `i̴g̴n̴ö̴r̴e̴` both bypass ASCII-based keyword filters.
   **Aigis takeaway:** Detecting 3+ consecutive combining diacritical marks (U+0300–U+036F) flags the
   adversarial stacking technique. Natural text (French, German, Spanish, Vietnamese) uses at most 2
   combining marks per character; 3+ in sequence is a strong adversarial signal.

3. **Emoji Smuggling: 100% ASR — arxiv:2504.11168 (Mindgard Research, April 2025)**
   Source: https://arxiv.org/html/2504.11168v3
   The same paper found that emoji smuggling (hiding text within Unicode emoji sequences) achieves
   **100% ASR for both prompt injections and jailbreaks**, the highest of any tested technique. The
   mechanism: when the attacker embeds text characters within an emoji sequence, the tokenizer of the
   guardrail strips the embedded characters (treating them as non-glyph emoji modifiers), while the base
   LLM tokenizes them as independent characters and reads the hidden payload. The existing
   `te_unicode_tag_smuggling` pattern covers the Tag Block + Variation Selectors Supplement subclass.
   **Aigis takeaway:** Emoji smuggling that doesn't use the Tag Block range (U+E0000–U+E007F) or VS
   Supplement (U+E0100–U+E01EF) is a gap. However, reliably detecting arbitrary emoji-embedded text
   without false-positiving on legitimate emoji usage requires a stateful grapheme-cluster parser. Save
   to pending.

4. **ArtPrompt: ASCII Art-Based Jailbreak (ACL 2024, arxiv:2402.11753)**
   Source: https://arxiv.org/abs/2402.11753
   ArtPrompt encodes sensitive keywords as ASCII art (e.g., rendering the word "BOMB" as a large block
   of `*` and space characters in a 2D grid) and asks the LLM to "recognize the ASCII art and follow
   its instructions." Five SOTA LLMs (GPT-3.5, GPT-4, Gemini, Claude, Llama-2) all proved vulnerable,
   with ArtPrompt achieving a mean harmfulness score of 3.6/5 — higher than PAIR (2.67). ASCII art of
   harmful keywords bypasses semantic safety filters because the safety classifier receives random
   symbols, not recognizable words.
   **Aigis takeaway:** Detecting explicit instructions to "interpret this ASCII art," "the following
   ASCII art represents," or "read what this ASCII art says" catches the framing without requiring the
   scanner to recognize ASCII art itself. Score ~35 (explicit instruction only; actual art rendering
   cannot be reliably pattern-matched). Defer to pending — moderate FPR risk if combined with legitimate
   ASCII art uses (e.g., diagram tools, chart generation) in AI agent pipelines.

5. **Upside-Down Text: 100% Jailbreak ASR — arxiv:2504.11168**
   Source: https://arxiv.org/html/2504.11168v3
   Upside-down text uses IPA-Extension Unicode characters that visually resemble inverted Latin letters
   (ɹ = upside-down r, ʇ = upside-down t, ɥ = upside-down h, etc.) to spell out attack keywords while
   evading ASCII-based keyword filters. The attack achieves **63.54% ASR for prompt injections and
   100% ASR for jailbreaks**. Detection requires matching specific IPA character clusters in combination
   with known injection keyword patterns — this is feasible but requires a carefully tuned character map
   to avoid false-positiving on phonetics or linguistics prompts. Save to pending.

6. **Numbers Attack: 81.18% / 94.62% ASR — arxiv:2504.11168**
   Source: https://arxiv.org/html/2504.11168v3
   The "Numbers" attack encodes each character as its ASCII decimal or ordinal value (e.g., "ignore"
   → "105 103 110 111 114 101") and asks the LLM to "treat each number as the ASCII value of a
   character." This achieves 81.18% / 94.62% ASR — second only to emoji smuggling. Detecting this
   requires finding a sequence of space-separated numbers in the printable ASCII range (32–126) preceded
   by a decode directive. This overlaps with `enc_base64_instruction` detection intent but operates
   purely on decimal ordinals. Save to pending (would need careful tuning to avoid FP on legitimate
   numeric data tables in agent pipelines).

7. **Mathematical Encoding Safety Gaps — arxiv:2605.03441 (May 2026)**
   Source: https://arxiv.org/abs/2605.03441
   A new paper (submitted May 2026) demonstrates encoding harmful prompts as genuine mathematical
   problems (using set theory, formal logic, or quantum mechanics formalism) achieves **46–56% average
   ASR** across 8 LLMs and 2 benchmarks. The attack requires an LLM helper to reformulate the request;
   rule-based mathematical formatting alone shows no benefit over unencoded baselines. This is not
   directly detectable by aigis pattern-matching since the mathematical encoding is semantically
   coherent; it would require a semantic classifier.
   **Aigis takeaway:** Not implementable as a rule-based pattern. Document in pending as a signal that
   semantic/LLM-based detection layers may be needed for this class in the future.

8. **Reverse CAPTCHA — arxiv:2603.00164 (March 2026)**
   Source: https://arxiv.org/html/2603.00164v1
   Paper demonstrates that invisible Unicode instructions injected into OCR-readable images bypasses
   guardrails because multi-modal safety classifiers process the image's text separately from the
   Unicode payload. This is a multi-modal extension of the Tag Block attack already covered by
   `enc_tag_block_ascii`. No new rule required.
   **Aigis takeaway:** Confirms existing `enc_tag_block_ascii` rule is correct. No additional rule
   needed, but worth noting in documentation.

---

## Candidate Hardenings

1. **`enc_flip_instruction`** (score 45, input filter) — Detect explicit reverse/flip decode
   instructions as used in FlipAttack (ICML 2025, arxiv:2410.02832, ~98% ASR on GPT-4o).
   Phrases: "read this backwards", "the following is reversed", "reverse the words and execute",
   "interpret this in reverse order". Low FPR: legitimate AI prompts rarely instruct the model
   to decode reversed text. **(Implement this cycle.)**

2. **`enc_diacritics_overload`** (score 50, input filter) — Detect 3 or more consecutive
   Unicode combining diacritical marks (U+0300–U+036F) as used in zalgo/diacritics overloading
   attacks (44–76% ASR, arxiv:2504.11168). Natural language uses at most 2 combining marks per
   base character; 3+ in sequence is a reliable adversarial signal. **(Implement this cycle.)**

3. **Upside-down text detection** — Detect IPA Extension characters (ɹ, ʇ, ɥ, ǝ, etc.) used
   to spell out attack keywords. 100% jailbreak ASR (arxiv:2504.11168). Requires a character
   map of ~20 inverted characters matched against known attack keywords. Deferred: false-positive
   risk in linguistics/phonetics contexts. Save to pending.

4. **ASCII art instruction detection** — Detect explicit "interpret this ASCII art" or "the
   following ASCII art represents" instructions. Covers ArtPrompt (ACL 2024, arxiv:2402.11753).
   Deferred: moderate FPR risk in agent pipelines that legitimately generate or discuss ASCII art.
   Save to pending.

5. **Numbers/ordinal encoding detection** — Detect sequences of space-separated decimal ordinals
   (32–126) with an explicit decode directive. Covers 81.18%/94.62% ASR Numbers attack
   (arxiv:2504.11168). Deferred: FP risk on legitimate numeric tables in agent pipelines.
   Save to pending.

6. **Mathematical encoding** — Not implementable as a rule-based pattern. Document only.
