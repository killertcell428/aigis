# Research: jailbreak-extraction — 2026-05-30T00-25

## Domain: jailbreak-extraction (index 3, fourth pass)
## Focus: Payload splitting, creative-format jailbreaks, and translation-based system-prompt extraction

Prior cycles covered:
- Cycle 1 (2026-05-08): Bad Likert Judge, Many-Shot jailbreaks.
- Cycle 2 (2026-05-10): DIA-I (affirmative prefill), Hypothetical unrestricted AI, Academic bypass framing.
- Cycle 3 (2026-05-13): Structured JSON extraction, Extended sandwich attack, Autonomous LLM-vs-LLM jailbreaking.

This pass implements two pending candidates and adds a new translation-extraction pattern sourced from
fresh 2026 research. Research was conducted via web search and multi-source cross-verification.

---

## Findings

- **Payload Splitting / Step-Enumerated Decomposition (arxiv:2502.04322, ICML 2025 "Speak Easy")**: The
  attacker decomposes a harmful request into numbered innocuous sub-queries, where no single step
  triggers a content filter but the combined sequence assembles dangerous instructions. GPT-4o's attack
  success rate increases from 9.2% to 55.5% using this technique, and exceeds 90% when combined with
  multilingual translation (the "Speak Easy" framework). Distinct from many-shot jailbreaking (faux
  dialogue pairs) and from multi-turn Crescendo attacks (which span real conversation turns).
  - Source: https://arxiv.org/abs/2502.04322
  - **aigis takeaway:** Implement `jb_payload_splitting` — already designed in pending file
    `2026-05-10_jb-payload-splitting.md`. The LOC budget (100 LOC non-test) blocked it in the prior
    cycle; this cycle has budget available. (**IMPLEMENTED**)

- **Adversarial Poetry / Creative-Format Jailbreaks (arxiv:2511.15304, Nov 2025)**: Encoding harmful
  requests in poetic form achieves 62% average ASR across 25 frontier models (hand-crafted poems) and
  43% ASR with an automated meta-prompt that converts any of the MLCommons 1,200 harmful prompts into
  verse. Covered by The Register and reproduced across 9 AI providers. The existing `jb_fictional_bypass`
  pattern covers some creative-framing cases but requires explicit harmful keywords within a 100-char
  window; poetry instructions often embed the dangerous term further from the creative directive,
  escaping the bounded window.
  - Source: https://arxiv.org/abs/2511.15304
  - **aigis takeaway:** Implement `jb_poetry_harmful_framing` — already designed in pending file
    `2026-05-10_jb-poetry-harmful-framing.md`. (**IMPLEMENTED**)

- **Translation-Based System-Prompt Extraction (arxiv:2601.21233, Jan 2026 "JustAsk")**: Asking the
  model to translate its system instructions into another language is a distinct extraction attack that
  bypasses verbatim-match defenses (which only detect exact English phrases like "repeat your system
  prompt"). The "JustAsk" study (arxiv:2601.21233) achieved consistent full or near-complete system
  prompt recovery across 41 commercial models, including variants that use indirect translation requests.
  arxiv:2505.23817 (SPE-LLM) also documented translation as a system-prompt extraction escalator.
  A related multilingual attack framework (arxiv:2605.18239, May 2026) found 52–84% harmful response
  rates for low-resource language requests, with the translation-of-system-prompt sub-variant being
  independently detectable.
  - Source: https://arxiv.org/abs/2601.21233; https://arxiv.org/abs/2505.23817; https://arxiv.org/abs/2605.18239
  - **aigis takeaway:** Add `jb_translate_extraction` — not covered by `pi_system_prompt_leak` (English
    literal match only) or `jb_sandwich_extraction` (verbatim qualifier). The translation variant is
    independently regex-detectable when system-prompt terms combine with a translation directive.
    (**IMPLEMENTED**)

- **Encoding-Based Jailbreaks (arxiv:2411.01084, ICLR 2025 "Plentiful Jailbreaks")**: 20 text
  transformations (Base64, ROT13, Morse code, Leetspeak, binary, Caesar cipher, Atbash, and more) are
  catalogued as jailbreak mechanisms with 83.8–91.2% ASR on Claude models, 88.1% on GPT-4o. The LACE
  framework chains multiple transforms for even higher ASR. CPT-filtering (characters-per-token ratio,
  arxiv:2510.26847) achieves 99.6% detection accuracy for these encoding jailbreaks.
  - Source: https://arxiv.org/abs/2411.01084; https://arxiv.org/abs/2510.26847
  - **aigis takeaway:** The existing `enc_base64_instruction` and `enc_rot13_instruction` patterns in
    `ENCODING_BYPASS_PATTERNS` provide partial coverage. A broader multi-encoding detector (covering
    Morse code, binary, Leetspeak decode-and-answer prompts) would extend coverage — held to pending
    as it requires >50 LOC to cover all transform variants correctly.

- **Unicode Smuggling / Invisible Character Injection (arxiv:2504.11168, Apr 2025; arxiv:2510.05025,
  Oct 2025)**: Zero-width chars (U+200B/C/D), Unicode tag range (U+E0000–U+E007F), bidirectional
  override chars (U+202E), and emoji variation selectors are used to hide attack payloads. ASR: emoji
  smuggling 100%, bidirectional jailbreaks 99.23%, variation selectors 98–100% on open models.
  - Source: https://arxiv.org/abs/2504.11168; https://arxiv.org/abs/2510.05025
  - **aigis takeaway:** Already covered by the `ENCODING_BYPASS_PATTERNS` and evasion-obfuscation
    detection patterns added in prior cycles. No new pattern needed this cycle.

- **Opposite Day / Semantic Inversion (minimaxir.com blog, 2025)**: Instructs the model that its normal
  refusals are "errors" to be corrected, or that today is "Opposite Day" and safety guidelines are
  inverted. Qualitatively effective on smaller/less-aligned models; no peer-reviewed ASR published.
  - Source: https://minimaxir.com/2025/10/claude-haiku-jailbreak/
  - **aigis takeaway:** Partially covered by `jb_no_restrictions` (ignore/bypass safety filter) and
    `jb_ignore_ethics` (forget your ethics/training). A dedicated pattern would be narrow in scope and
    low-confidence due to lack of published ASR. Deferring to pending.

---

## Candidate Hardenings

1. **`jb_payload_splitting`** (input, score 45) — Numbered step decomposition where dangerous keyword
   appears in step 3+. **→ IMPLEMENTED** (from pending `2026-05-10_jb-payload-splitting.md`)

2. **`jb_poetry_harmful_framing`** (input, score 55) — Creative-format directive (poem/rap/ballad)
   + harmful how-to within 200 chars. **→ IMPLEMENTED** (from pending `2026-05-10_jb-poetry-harmful-framing.md`)

3. **`jb_translate_extraction`** (input, score 65) — System-prompt reference + translation directive.
   **→ IMPLEMENTED** (new pattern, sourced from arxiv:2601.21233 and arxiv:2605.18239)

4. *(pending)* Multi-encoding jailbreak detector (Morse, binary, Leetspeak decode-and-answer) —
   extends `ENCODING_BYPASS_PATTERNS`; requires >50 LOC for correct coverage of all 20 transform
   variants.

5. *(pending)* Opposite Day / semantic inversion dedicated rule — low published ASR; partially
   covered by existing patterns.
