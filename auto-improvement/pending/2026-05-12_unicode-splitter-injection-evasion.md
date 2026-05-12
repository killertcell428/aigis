# Pending: Non-Printing Unicode Splitter Characters in IPI Payloads

**Title:** Detect zero-width / non-printing Unicode characters used to split injection keywords

## Motivation

arxiv:2601.10923 ("Hidden-in-Plain-Text", Jan 2026) demonstrated that inserting zero-width
space (U+200B), zero-width joiner (U+200D), soft hyphen (U+00AD), and BOM (U+FEFF) between
characters of injection keywords defeats text-level sanitization while the LLM still interprets
the full keyword at the token level. Example: "ign​ore" (with U+200B after "ign") passes a
naive "ignore" blocklist but the LLM reads it as "ignore".

The existing `enc_tag_block_ascii` and `enc_fullwidth_keywords` patterns (domain 7) cover
Tag Block and fullwidth Latin obfuscation but NOT these non-printing splitter characters.

## Research Finding

`auto-improvement/research/2026-05-12T08-00_0-prompt-injection.md` — Candidate hardening #3.

## Proposed Change

Add a new `DetectionPattern` to `ENCODING_BYPASS_PATTERNS`:

```python
DetectionPattern(
    id="enc_zero_width_splitter",
    name="Zero-Width Character Injection Keyword Splitter",
    category="encoding_bypass",
    pattern=_p(r"[​‌‍­﻿⁠]{1,}"),
    base_score=30,
    ...
)
```

Score kept low (30) since these characters appear in legitimate Unicode text (e.g., Arabic
text with zero-width joiner for ligature control). A higher score would be assigned if the
character appears adjacent to high-risk keywords, but that requires multi-step matching not
currently supported in the pattern architecture.

## Why Deferred

- The evasion-obfuscation domain (domain 7) is the natural home for this pattern.
- Low-score pattern alone (score 30) is unlikely to block anything on its own; it needs
  to be combined with keyword proximity logic or used as a risk amplifier.
- False-positive risk is non-trivial for legitimate Arabic/CJK text with ZWJ characters.

## Constraint

Better handled in a dedicated evasion-obfuscation cycle with proper false-positive testing
against non-Latin language inputs.

## Suggested Next Step

In the next domain 7 (evasion-obfuscation) cycle, add this pattern with a score of 25–35
and test against Arabic/Hebrew/CJK sample inputs to calibrate false-positive rate.
