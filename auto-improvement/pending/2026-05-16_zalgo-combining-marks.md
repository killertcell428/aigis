# Pending: Zalgo / Combining Diacritical Mark Overdrive Detection

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T00-00_7-evasion-obfuscation.md (finding 6)
**Constraint blocking:** Lower priority than primary implementation; deferred for next evasion cycle.

---

## Title

Detect excessive combining diacritical marks (Zalgo text) used to corrupt keyword readability for human reviewers while remaining parseable by LLMs.

## Motivation

arxiv:2508.14070 ("Special-Character Adversarial Attacks on Open-Source Language Models", Aug 2025) evaluated 14 special-character attack classes against four aligned open-source LLMs. The "zalgo text" class — in which excessive Unicode combining diacritical marks (U+0300–U+036F) are stacked above and below base characters — achieved 38% average attack success rate across Llama-3, Mistral, Gemma, and Falcon. While 38% ASR is lower than fullwidth (61.5%) or zero-width injection (54%), it is non-negligible and the technique is trivially automatable with public Zalgo generator tools.

Zalgo text looks like corrupted, glitching characters (̷l̵i̴k̸e̷ ̴t̶h̷i̷s̵) and is completely unreadable to humans, but the base characters are intact and LLMs process them normally. Attackers use this to obscure attack keywords from visual inspection and from classifiers that normalize text only via NFKC (which does not strip combining marks).

The existing aigis rules do not cover combining diacritical marks:
- `te_unicode_noise` covers zero-width chars (U+200B etc.) and soft hyphen — NOT combining marks
- `enc_bidi_override` covers BIDI control chars — NOT combining marks
- No rule covers U+0300–U+036F

## Proposed Change

Add a detection pattern in `aigis/filters/patterns.py` (ENCODING_BYPASS_PATTERNS):

```python
DetectionPattern(
    id="enc_zalgo_text",
    name="Zalgo / Combining Diacritical Mark Overdrive",
    category="encoding_bypass",
    pattern=_p(r"[̀-ͯ҃-҉᪰-᫿⃐-⃿]{6,}"),
    base_score=35,
    description=(
        "Six or more consecutive combining diacritical marks detected. "
        "Zalgo text stacks Unicode combining characters (U+0300–U+036F and related ranges) "
        "above and below base characters, creating visually corrupted 'glitch' text that is "
        "unreadable to humans but processed normally by LLMs. Attackers use Zalgo encoding "
        "to hide attack keywords from visual inspection and from ASCII keyword filters. "
        "arxiv:2508.14070 measured 38% average attack success rate across four open-source "
        "aligned LLMs using this technique."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection (Encoding Bypass)",
    remediation_hint=(
        "Strip combining diacritical marks before scanning: "
        "unicodedata.normalize('NFD', text) followed by removal of category 'Mn' characters. "
        "In Python: ''.join(c for c in unicodedata.normalize('NFD', text) "
        "if unicodedata.category(c) != 'Mn'). "
        "Six or more consecutive combining marks do not appear in legitimate AI prompt text."
    ),
)
```

## FPR Considerations

- U+0300–U+036F includes combining marks used legitimately in Vietnamese, Greek, and other scripts. However, *consecutive* combining marks (6+ in a row, with no base character between them) are extremely unusual in legitimate text — they require a zero-width base character (like U+25CC) or are the result of aggressive Zalgo generation.
- A threshold of 6+ consecutive combining chars is conservative; most Zalgo generators stack 10–20 per letter.
- Legitimate multilingual text (Vietnamese with tone marks, etc.) uses 1–2 combining chars per base character, not 6+ consecutively.

## Why Held Back

1. The primary implementation slot this cycle was taken by `enc_zwc_keyword_split` (higher ASR, cleaner gap).
2. Secondary priority only — 38% ASR vs. 54% for ZWC splitting.
3. The range U+0300–U+036F is large and requires validating that the 6+ threshold doesn't cause FPR in legitimate multilingual prompts.

## Suggested Next Step

1. Test the regex against a representative corpus of multilingual text (Vietnamese, Greek, Arabic) to measure FPR.
2. Consider including additional combining mark ranges: U+0483–U+0489, U+1AB0–U+1AFF, U+20D0–U+20FF (listed above in the proposed pattern).
3. Implement as the primary hardening in the next evasion-obfuscation cycle (next occurrence of domain #7).
