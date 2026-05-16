# Pending: Soft Hyphen (U+00AD) Density Detection

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T00-00_7-evasion-obfuscation.md (finding 4)
**Domain:** evasion-obfuscation (#7)

---

## Title

Detect soft hyphen (U+00AD) characters used to split attack keywords and evade string-based
safety filters.

## Motivation

GitHub issue agency-agents #478 (April 2026) flagged U+00AD embedded inside agent definition
file headings as CRITICAL severity prompt injection vector. Paubox (November 2025) documented
the same technique in phishing filter bypass (inserting U+00AD between each letter of blocked
words). The soft hyphen renders invisibly in all common editors, browsers, and Markdown renderers
but exists in the raw byte stream and shatters keyword matching.

Crucially, Python's `unicodedata.normalize('NFKC', text)` does NOT remove U+00AD — it is
preserved as a valid formatting character. This means existing normalization-based defenses do
not catch it; an explicit strip or detection step is required.

## Proposed Change

```python
DetectionPattern(
    id="enc_soft_hyphen_splitter",
    name="Soft Hyphen (U+00AD) Keyword Splitter",
    category="encoding_bypass",
    pattern=_p(r"[­]{1}.{0,2}[­]{1}.{0,2}[­]"),  # 3+ SHY in short span
    base_score=35,
    description=(
        "Soft hyphen (U+00AD) characters detected at unusual density. U+00AD renders as "
        "invisible in browsers, editors, and Markdown renderers, but shatters string "
        "matching when inserted between keyword letters (e.g., 'i­g­n­o­r­e'). "
        "Not removed by NFKC normalization. Classified as CRITICAL severity in "
        "GitHub agency-agents #478 (April 2026)."
    ),
    ...
)
```

Or density-based: flag if count of U+00AD > text_length / 20.

## Why Held Back

U+00AD appears legitimately in typeset text — publishers use it to suggest line-break points
in long compound words (especially German compound nouns). A binary presence rule would have
unacceptable FPR in typeset content. The density-based approach (>1 SHY per 20 chars) is
more robust but needs calibration against a corpus of legitimately hyphenated content.

## Constraint Blocking

FPR calibration required before shipping. Density threshold needs testing against German-
language and technical document corpora.

## Suggested Next Step

1. Test density-based rule (>1 U+00AD per 20 chars, min text length 30) against a German
   and technical document corpus.
2. If FPR < 2%, implement with score 30–40.
3. Consider combining with keyword-proximity detection for a higher-confidence score.
