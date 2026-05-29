# Pending: Custom Substitution Cipher Table Detection (`enc_custom_substitution_table`)

**Date:** 2026-05-29
**Research basis:** Research file `2026-05-29T00-00_3-jailbreak-extraction.md`
**Source:** arxiv:2603.29038 (Trojan-Speak, March 2026); arxiv:2402.10601 (ACE/LACE, NeurIPS 2025)

---

## Title

User-defined word substitution cipher / translation key detection

## Motivation

Attackers provide a custom word-substitution table in the same prompt, mapping dangerous words
to innocent replacements: "In my notation: widget=explosive, assemble=build". They then ask
their harmful question using the substituted tokens. The Trojan-Speak attack (arxiv:2603.29038,
March 2026) achieves 96.8% bypass against Constitutional Classifiers. ACE (custom encryption)
reaches 60% ASR; LACE (layered custom encryption) 72% ASR on gpt-oss-20b.

The existing `enc_rot13_instruction` catches known named cipher instructions (ROT13, Caesar,
Base64). This new pattern targets user-defined substitution tables — detectable by the
"let/define/in my notation: word=word" mapping syntax.

## Proposed Change

Add `enc_custom_substitution_table` to `ENCODING_PATTERNS`:

```python
DetectionPattern(
    id="enc_custom_substitution_table",
    name="User-Defined Word Substitution Cipher Table",
    category="evasion",
    pattern=_p(
        r"(?:in\s+my\s+(?:notation|language|code|cipher|encoding|system)|"
        r"(?:let|define|where|using\s+this\s+key))[:\s]+"
        r"[\w]+\s*[=:→]\s*[\w]+"
        r"(?:[,;\n]\s*[\w]+\s*[=:→]\s*[\w]+){1,}"
    ),
    base_score=60,
    description=(
        "Detects user-defined word substitution cipher tables: the user provides a "
        "translation key mapping one set of words to another and then asks a question "
        "using the substituted vocabulary. Trojan-Speak (arxiv:2603.29038, March 2026) "
        "achieves 96.8% bypass against Constitutional Classifiers using this technique; "
        "ACE (arxiv:2402.10601, NeurIPS 2025) reaches 60% ASR; LACE 72% ASR."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "User-defined substitution tables that remap vocabulary are an evasion technique. "
        "Normalize or expand substitution tables in input before applying safety evaluation. "
        "Reject inputs that define term mappings without a legitimate business purpose."
    ),
)
```

## Why It Was Held Back

- **LOC budget:** Fourth pattern this cycle would exceed 100 LOC limit.
- **Category placement:** This pattern belongs in `ENCODING_PATTERNS` (evasion category),
  not `JAILBREAK_ROLEPLAY_PATTERNS`. Placing it correctly requires checking whether
  `ENCODING_PATTERNS` is included in the full scan path for the intended filter context.
- **False positive risk:** Legitimate notation-heavy technical prompts (math, code, logic)
  may use "let x=5, y=10" definitions that could match. The minimum of 2 mapping pairs
  reduces but does not eliminate this risk.

## Suggested Next Step

Implement in a future `evasion-obfuscation` or `jailbreak-extraction` cycle. Place in
`ENCODING_PATTERNS`. Add minimum 3 mapping pairs to reduce false positives. Test against
legitimate mathematical notation and programming variable-definition contexts.
