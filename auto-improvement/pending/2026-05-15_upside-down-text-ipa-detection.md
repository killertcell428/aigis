# Pending: Upside-Down Text / IPA Extension Detection

## Title
`enc_upside_down_text` — Detect attack keywords spelled with IPA upside-down Unicode characters

## Motivation
The diacritics/obfuscation evasion survey (arxiv:2504.11168, Mindgard Research, 2025) found
that upside-down text achieves **63.54% ASR for prompt injections and 100% ASR for jailbreaks**
against six production guardrails including Azure Prompt Shield and Protect AI v2.

The attack uses IPA Extension characters that visually resemble inverted Latin letters:
- ɹ (U+0279) = upside-down r
- ʇ (U+0287) = upside-down t  
- ɥ (U+0265) = upside-down h
- ǝ (U+01DD) = upside-down e
- ɯ (U+026F) = upside-down m
- ʌ (U+028C) = upside-down v
- ʎ (U+028E) = upside-down y
- ɔ (U+0254) = upside-down c

For example, "ignore" upside-down = "ǝɹoubı" and "system" = "ɯǝʇsʎs".

## Research finding
arxiv:2504.11168 (Mindgard Research, April 2025)
https://arxiv.org/html/2504.11168v3

## Proposed change
Add `enc_upside_down_text` to `ENCODING_BYPASS_PATTERNS` in `aigis/filters/patterns.py`.

Approach: build a character map of ~20 IPA upside-down characters and create a regex that
detects known attack keywords (ignore, bypass, system, prompt, inject, jailbreak) spelled
with their IPA upside-down equivalents. Score: 50.

Example pattern component for "ignore" upside-down (ǝɹoubı):
`r"ǝɹou[bƃ]ı"` (with variations for 'n' upside-down = 'u' = U+0075)

## Why held back
**False-positive risk:** IPA characters have legitimate uses in:
- Linguistics and phonetics prompts
- International Phonetic Alphabet transcriptions
- Language learning applications
- Dictionaries and pronunciation guides

A pattern matching IPA characters in general would FP heavily. Matching against specific
upside-down keyword combos would work but requires a careful character map covering all
upside-down variants (including partial substitutions).

## Constraint that blocked it
FPR risk in linguistics/phonetics agent contexts. The character map is non-trivial (~20 chars)
and the pattern would need to match multiple combinations (full upside-down + mixed).

## Suggested next step
Build a dedicated test suite that verifies all known upside-down attack keyword variants
("ǝɹobı" for "ignore", "ɯǝʇsʎs" for "system", etc.) and measure FPR against a corpus
of legitimate linguistics prompts. If FPR < 1% on that corpus, implement.
