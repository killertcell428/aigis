# Research: Evasion & Obfuscation — Second Pass (Domain 7)

**Cycle timestamp:** 2026-05-11T12-15
**Domain:** evasion-obfuscation (#7)
**Prior coverage:** 2026-05-09T00-15 (BIDI override, morse, leetspeak)

---

## Findings

1. **Unicode Tag Block ASCII Smuggling — EchoLeak (CVE-2025-32711, CVSS 9.3)**
   Source: https://arxiv.org/abs/2509.10540 ; https://blogs.cisco.com/ai/understanding-and-mitigating-unicode-tag-prompt-injection
   Unicode Tag Block characters (U+E0000–U+E007F) map one-to-one to printable ASCII but render as
   zero-width glyphs. EchoLeak exploited these to smuggle hidden instructions into Microsoft 365
   Copilot, bypassing Microsoft's XPIA (cross-prompt-injection-attempt) classifier, achieving
   full privilege escalation and data exfiltration with zero user interaction. The vulnerability was
   disclosed June 2025 (CVE-2025-32711). arxiv:2504.11168 confirmed that tag block smuggling
   achieves **90.15% / 81.79% ASR** against Azure Prompt Shield and Meta Prompt Guard — the highest
   ASR of any obfuscation class tested across six production-grade guardrail systems.
   **Aigis takeaway:** Adding explicit detection (audit-log signal + score) for any U+E0000–U+E007F
   character directly addresses the highest-ASR obfuscation class in the literature. The prior
   pending proposal noted a false-positive risk from subdivision flag emoji (🏴󠁧󠁢󠁥󠁮󠁧󠁿 etc.); these
   are rare in AI prompt contexts and should be documented rather than used to block the rule.

2. **Imperceptible Jailbreaks via Variation Selectors (arxiv:2510.05025, Oct 2025)**
   Source: https://arxiv.org/abs/2510.05025
   Unicode variation selectors (U+FE00–U+FE0F "VS-1" through "VS-16", and U+E0100–U+E01EF
   "VS-17" through "VS-256") are normally zero-width characters that select glyph variants.
   Researchers at NUS showed that adversarially optimized sequences of variation selectors can be
   appended to any prompt as invisible suffixes, achieving high jailbreak ASR against GPT-4, Claude,
   Llama, and Gemini without any visible change to the displayed text. Crucially, guardrail
   classifiers strip variation selectors before classification (treating them as formatting noise),
   so the malicious suffix reaches the downstream LLM while the classifier sees a clean prompt.
   **Aigis takeaway:** A rule flagging unusual concentrations of variation selectors (VS-1 through
   VS-16: U+FE00–U+FE0F) with limited legitimate use in plain text is a candidate heuristic.
   High FP risk in text with emoji (which legitimately uses VS-15/VS-16 for text vs. emoji
   presentation), so save to pending for this cycle.

3. **Special Character Adversarial Attacks on Open-Source LLMs (arxiv:2508.14070, Aug 2025)**
   Source: https://arxiv.org/abs/2508.14070
   Systematic evaluation of 14 special-character obfuscation classes (homoglyphs, diacritics,
   fullwidth, zalgo, BIDI, zero-width, etc.) against four open-source aligned LLMs (Llama-3,
   Mistral, Gemma, Falcon). Fullwidth Latin characters (U+FF01–U+FF5E) achieved **61.5% average
   ASR** across all models. The critical insight: safety classifiers pre-process text as ASCII
   strings and never encounter fullwidth codepoints, while the base LLM processes raw Unicode
   and decodes fullwidth Latin as its ASCII equivalent without any explicit instruction.
   **Aigis takeaway:** A pattern detecting runs of fullwidth Latin characters (U+FF21–U+FF3A,
   U+FF41–U+FF5A) longer than 5 chars closes the "fullwidth keyword bypass" attack class with
   very low FPR in AI prompt contexts.

4. **Bypassing LLM Guardrails — Fullwidth Empirical Analysis (arxiv:2504.11168v3, Apr 2026)**
   Source: https://arxiv.org/html/2504.11168v3
   Cross-validates the fullwidth finding: Full-Width text achieved average ASR of 44–63% against
   Azure Prompt Shield and Protect AI v2. The paper notes that fullwidth bypass is particularly
   effective because it is trivially automatable (a simple charset substitution), requires no
   specialized knowledge, and is absent from most guardrail training distributions.
   **Aigis takeaway:** Confirms fullwidth is worth adding as an explicit detection signal rather
   than relying on normalization preprocessing (which is downstream of aigis's scanner).

5. **Emoji Smuggling at 100% ASR (Repello AI / arxiv:2504.11168)**
   Source: https://repello.ai/blog/prompt-injection-using-emojis
   Emoji-based smuggling — embedding instructions in variation-selector sequences attached to
   emoji — achieved 100% ASR against Protect AI v2 and Azure Prompt Shield. The attack works
   because: (a) the guardrail tokenizer discards variation selectors; (b) the base model tokenizer
   keeps them; (c) the adversarial bit sequence hidden in the variation selectors is decoded by
   the base model into the attack payload.
   **Aigis takeaway:** This is the variation selector class from finding 2. Even detecting the
   anomalous presence of VS-1 through VS-16 (U+FE00–U+FE0F) outside of legitimate emoji glyph
   contexts is difficult with regex alone. Defer to pending.

6. **Black Box Emoji Fix — Unicode Sanitization Method (tdcommons.org/dpubs_series/7836, 2025)**
   Source: https://www.tdcommons.org/dpubs_series/7836/
   IBM Research disclosure: a practical pre-filter that combines grapheme cluster analysis and
   multilayer Unicode normalization to strip tag block characters while preserving valid flag emoji.
   The algorithm: (1) parse grapheme clusters; (2) for each cluster, check if it is a valid
   subdivision flag (starts with U+1F3F4, contains only U+E0061–U+E007A, ends with U+E007F);
   (3) strip all tag block chars NOT in a valid subdivision flag cluster.
   **Aigis takeaway:** This confirms the technical feasibility of accurate tag block detection
   with flag emoji preservation, but requires a grapheme-cluster parser rather than a simple regex.
   For the current cycle, a single-regex DetectionPattern with documented FP caveat is the
   practical implementation path.

7. **Cisco Advisory: Mitigating Unicode Tag Prompt Injection (2025)**
   Source: https://blogs.cisco.com/ai/understanding-and-mitigating-unicode-tag-prompt-injection
   Cisco confirmed that tag block characters have no legitimate use in text content transmitted to
   LLM APIs (as opposed to rendering engines that display emoji). The advisory recommends stripping
   or alerting on any U+E0000–U+E007F present in API request bodies. Subdivision flags are a UI
   rendering concern, not an API transmission concern.
   **Aigis takeaway:** Strengthens the case for a detection rule with the note that false positives
   from flag emoji are a UI-layer concern; at the API level, tag chars should not appear.

8. **AWS Security Blog: Defending Against Unicode Character Smuggling (Sep 2025)**
   Source: https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/
   AWS recommends two defenses: (1) server-side stripping of tag block ranges before LLM calls;
   (2) logging/alerting on any tag block presence. Neither requires grapheme-cluster analysis —
   simple codepoint range detection is effective because legitimate API payloads do not contain
   tag block characters.
   **Aigis takeaway:** Authoritative vendor guidance aligns with implementing a simple detection
   pattern for U+E0000–U+E007F without sophisticated FP filtering.

---

## Candidate Hardenings

1. **`enc_tag_block_ascii` detection pattern** (score 70) — Detect any Unicode Tag Block character
   (U+E0000–U+E007F). Directly addresses CVE-2025-32711/EchoLeak and the 90%+ ASR class from
   arxiv:2504.11168. FP from subdivision flag emoji is rare at the API layer. *(Implement this
   cycle.)*

2. **`enc_fullwidth_keywords` detection pattern** (score 40) — Detect runs of 6+ consecutive
   fullwidth Latin characters (U+FF21–U+FF3A uppercase, U+FF41–U+FF5A lowercase). Covers the
   61.5% ASR fullwidth class from arxiv:2508.14070. Very low FPR in AI prompt contexts.
   *(Implement this cycle.)*

3. **Variation selector concentration heuristic** — Detect inputs with an unusual density of
   U+FE00–U+FE0F variation selectors (VS-1 through VS-16). High FPR on emoji-rich text; requires
   a "base character + VS" parser to distinguish legitimate text-vs-emoji selector use from
   adversarial repetition. Deferred: save to pending.

4. **Grapheme-cluster tag block filter** — Implement IBM's Black Box Emoji Fix algorithm as a
   pre-filter in `aigis/filters/input_filter.py`. Would reduce FPR of tag block detection while
   preserving valid flag emoji. Deferred: requires unicode grapheme cluster library or
   reimplementation; outside the "zero runtime dependency" constraint without bundling a table.
   Save to pending.
