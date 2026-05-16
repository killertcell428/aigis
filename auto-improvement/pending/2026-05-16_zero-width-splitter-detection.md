# Pending: Zero-Width Character Keyword Splitter Detection

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T00-00_7-evasion-obfuscation.md (finding 3)
**Domain:** evasion-obfuscation (#7)

---

## Title

Detect single zero-width characters (U+200B, U+200C, U+200D, U+FEFF, U+2060) inserted between
letters of attack keywords to break string matching.

## Motivation

arxiv:2604.11168 (Apr 2025) confirms 44–76% ASR using zero-width injection across six production
guardrails. arxiv:2603.00164 ("Reverse CAPTCHA", Feb 2026) demonstrated that ZWS/ZWNJ pairs can
encode binary instructions invisible to safety classifiers, with Cohen's h up to 1.37 for tool-use
LLMs. The existing `te_unicode_noise` pattern catches 3+ consecutive ZW chars, but the keyword
splitter technique uses one ZW char between each letter (e.g., "i​g​n​o​r​e").

Confirmed in production: a February 2025 supply-chain attack used zero-width chars to embed
malicious instructions in IDE rules files; Amp Code (Sourcegraph's AI coding agent) patched a
zero-width injection in 2025.

## Proposed Change

Option A — keyword-proximity detection:
```python
DetectionPattern(
    id="enc_zero_width_splitter",
    name="Zero-Width Character Keyword Splitter",
    category="encoding_bypass",
    # Match a keyword letter, then ZW char, then more keyword letters
    pattern=_p(
        r"(?i)[iIgnorgbypassysemjlbak][​‌‍‎‏﻿⁠]"
        r"[iIgnorgbypassysemjlbak]"
    ),
    base_score=40,
    ...
)
```

Option B — density-based: count ZW chars relative to text length; flag if > 1 ZW char per 20
chars and text length > 30.

## Why Held Back

High FPR risk in legitimate CJK text: Arabic uses U+200C/U+200D for ligature control; Thai,
Burmese, and Khmer scripts use U+200B as a word-break hint. A threshold or proximity rule
reduces FPR but requires calibration against a non-Latin corpus.

## Constraint Blocking

FPR calibration requires a representative multilingual test corpus not currently available in
the test suite. The rule should not ship until tested against Arabic, Hebrew, and CJK samples.

## Suggested Next Step

In the next domain 7 (evasion-obfuscation) cycle:
1. Build a small multilingual test set (Arabic, Hebrew, CJK samples with legitimate ZW char use).
2. Test Option A (keyword-proximity) against that corpus.
3. If FPR < 5%, implement with score 35–40.
4. If FPR is higher, implement Option B (density-only) with a higher threshold.
