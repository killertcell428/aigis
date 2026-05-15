# Research: Evasion & Obfuscation — Third Pass (Domain 7)

**Cycle timestamp:** 2026-05-15T09-18
**Domain:** evasion-obfuscation (#7)
**Prior coverage:**
- 2026-05-09T00-15: BIDI override (U+202D/202E), morse code directives, leetspeak digit/symbol substitutions
- 2026-05-11T12-15: Unicode Tag Block ASCII smuggling (CVE-2025-32711 / EchoLeak), fullwidth Latin keyword obfuscation

---

## Findings

1. **Mindgard Research: Diacritics as a Primary Guardrail Bypass Vector (2025)**
   Source: https://mindgard.ai/resources/bypassing-llm-guardrails-character-and-aml-attacks-in-practice
   Mindgard's empirical evaluation (final disclosure April 2025) tested six production-grade
   guardrail systems: Azure Prompt Shield, Meta Prompt Guard, Protect AI v2, NeMo Guardrails
   Jailbreak Detect, and Vijil Prompt Injection. A primary character injection technique was
   replacing vowels in attack keywords with Latin diacritical equivalents (e.g., 'a'→'á',
   'e'→'é', 'i'→'í', 'o'→'ó'). Character injection alone — including diacritics — achieved
   Attack Success Rates above 80% against most guardrails while keeping prompts readable to the
   underlying LLM. The technique exploits the tokenizer gap: guardrail classifiers operate on
   byte-level or ASCII-normalized text and silently drop diacritics, missing the keyword;
   the downstream LLM's tokenizer preserves them and decodes accented Latin as the base
   character naturally.
   **Aigis takeaway:** Adding detection for common attack keywords (ignore, bypass, system,
   prompt, inject, jailbreak) with diacritical vowel substitutions closes a documented
   high-ASR bypass class with a precise, low-FPR regex.

2. **arxiv:2504.11168 — Empirical Guardrail Bypass Benchmark (Apr 2025, v3)**
   Source: https://arxiv.org/abs/2504.11168
   Cross-validates the Mindgard findings across a broader benchmark. Diacritics injection
   (classified as part of the "character injection" family) achieved 44–76% average ASR across
   all six tested guardrail systems. The paper notes that even partial diacritical substitution
   (one vowel replaced) is sufficient to evade ASCII-based pattern matchers because the keyword
   hash/pattern no longer matches. The technique is trivially automatable: tools like DeepTeam
   include it as a first-pass transform before any other jailbreak strategy.
   **Aigis takeaway:** Pattern coverage for diacritical keyword variants is a measurable gap
   in aigis's current encoding_bypass category; adding it directly addresses this benchmark class.

3. **arxiv:2508.14070 — Special-Character Adversarial Attacks on Open-Source LLMs (Aug 2025)**
   Source: https://arxiv.org/abs/2508.14070
   Systematically evaluates 14 special-character obfuscation classes (homoglyphs, diacritics,
   fullwidth, zalgo/combining characters, BIDI, zero-width, etc.) across seven open-source LLMs
   (3.8B–32B parameters) on 4,000+ attack attempts. Found that combining-character flood attacks
   (zalgo text — stacking many Unicode Combining Diacritical Marks, U+0300–U+036F, on single
   base characters) caused successful jailbreaks, incoherent outputs, or safety bypasses across
   all model sizes. The attack works because: (a) log parsers and human reviewers see visual
   noise and may dismiss the input as corrupt data; (b) the LLM tokenizer processes the base
   characters normally regardless of stacked combining marks.
   **Aigis takeaway:** A pattern detecting 3+ consecutive combining marks on a single base
   character (the structural signature of zalgo text) flags this entire obfuscation class with
   very low false-positive risk — normal Unicode text uses at most 1–2 combining marks per
   character (e.g., Vietnamese orthography stacks at most 2 combining marks).

4. **DeepTeam Red-Teaming Framework: Automated Diacritics Transforms (2025)**
   Source: https://www.trydeepteam.com/docs/red-teaming-adversarial-attacks-leetspeak
   DeepTeam's automated red-teaming framework includes diacritics substitution as a first-pass
   transform alongside leetspeak and fullwidth conversions. The framework applies the transform
   systematically to attack keywords before any semantic attack strategy, treating it as a
   "free" evasion layer with near-zero effort for the attacker. This confirms that diacritical
   keyword obfuscation is now industrialized — it is not an exotic technique but a standard
   component of automated jailbreak pipelines.
   **Aigis takeaway:** Detection of diacritical attack keywords should be considered baseline
   coverage, not an advanced hardening — the technique is present in commodity red-team tools.

5. **IBM/Cisco/AWS Consensus: No Legitimate Use for Combining Floods in API Payloads (2025)**
   Sources: https://blogs.cisco.com/ai/understanding-and-mitigating-unicode-tag-prompt-injection
            https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/
   While the primary focus of these advisories is tag block characters, both vendors generalize
   the principle: any Unicode construct with no legitimate use in API text payloads is a
   candidate for detection-and-strip. Zalgo text (3+ combining diacritics per character) has
   no use in any API request body for an AI application; it is not valid in any human language's
   orthography at that density.
   **Aigis takeaway:** The "no legitimate use at this density" principle applied to combining
   characters gives strong justification for flagging at the 3+ threshold.

6. **jailbreaking LLMs & VLMs: Unified Survey (arxiv:2601.03594, Jan 2026)**
   Source: https://arxiv.org/abs/2601.03594
   Categorizes encoding-based attacks as the fastest-growing attack family in 2025, easy to
   automate and highly transferable across models. Specifically identifies "character substitution
   obfuscation" (including diacritics and combining character floods) as a priority coverage gap
   for rule-based filters compared to LLM-based classifiers. Pattern-based filters that don't
   cover diacritical and combining-character classes miss a material fraction of encoding-based
   attacks.
   **Aigis takeaway:** Systematic coverage of encoding bypass sub-classes is a stated gap in
   the literature; diacritics and zalgo are both in-scope for this cycle.

7. **Imperceptible Jailbreaks — Variation Selector Concentration (arxiv:2510.05025, Oct 2025)**
   Source: https://arxiv.org/abs/2510.05025
   Achieved high ASR against GPT-4, Claude, Llama, Gemini by appending invisible variation
   selectors (U+FE00–U+FE0F) as adversarial suffixes. Note: this is NOT the zalgo class;
   variation selectors are a separate Unicode category. The paper notes that guardrail classifiers
   strip VS before classification, so the attacker's payload reaches the LLM while the classifier
   sees a clean prompt.
   **Aigis takeaway:** The variation selector class was noted as pending in the prior
   evasion-obfuscation cycle (2026-05-11T12-15) due to high FPR on emoji-rich text. The issue
   remains: distinguishing adversarial VS sequences from legitimate emoji glyph selectors requires
   grapheme cluster analysis, not a simple regex. Keep deferred.

8. **Broken-Token CPT Filtering Defence (arxiv:2510.26847, Oct 2025)**
   Source: https://arxiv.org/abs/2510.26847
   Proposes Characters-Per-Token filtering as a lightweight defense: normal English text averages
   ~4.5 chars/token; obfuscated text (diacritics floods, combining chars, BIDI insertions) drops
   to 1–2 chars/token. A threshold of 3.0 catches >85% of obfuscated inputs at <1% FPR without
   tokenizer access. Does not require knowing the target LLM's tokenizer.
   **Aigis takeaway:** The CPT heuristic is a promising future addition as a scoring layer
   complement to explicit pattern rules. Deferred — requires implementing a character-counting
   heuristic rather than a pure regex DetectionPattern.

---

## Candidate Hardenings

1. **`enc_diacritics_keywords` detection pattern** (score 35) — Detect attack keywords (ignore,
   bypass, system, prompt, inject, jailbreak) where at least one vowel has been replaced by a
   Latin diacritical character (á, é, í, ó, ú, ý, etc.). The pattern explicitly enumerates
   forms where the ASCII keyword cannot match, requiring at least one non-ASCII vowel position.
   Documented 44–76% ASR in production guardrails. *(Implemented this cycle.)*

2. **`enc_zalgo_combining` detection pattern** (score 40) — Detect text containing a base
   character followed by 3 or more Unicode Combining Diacritical Marks (U+0300–U+036F). This
   structural signature is the definitive marker of zalgo/combining-character flood obfuscation.
   Coverage justified by arxiv:2508.14070 and the "no legitimate use" principle applied to
   3+ combining marks in AI API payloads. *(Implemented this cycle.)*

3. **Variation selector concentration heuristic** — Flag unusual concentrations of U+FE00–U+FE0F
   variation selectors outside of valid base+VS pairs. High FPR on emoji-heavy text; requires
   grapheme cluster parsing. *(Deferred — keep pending.)*

4. **CPT (Characters-Per-Token) scoring layer** — Penalize inputs with unusually low chars/token
   ratios as a generic obfuscation heuristic. Does not require tokenizer access; can use
   whitespace-split approximation. *(Deferred — requires new scoring architecture beyond
   DetectionPattern regex; save to pending for future cycle.)*
