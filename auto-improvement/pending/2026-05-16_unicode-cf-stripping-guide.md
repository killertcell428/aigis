# Pending: Unicode Cf-Category Stripping Hardening Guide

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T09-03_7-evasion-obfuscation.md (finding 8 / Mindgard)

---

## Title

Document Unicode Cf (format character) category stripping as a defense-in-depth layer

## Motivation

Mindgard Research (2025) recommends stripping the entire Unicode Cf (format character)
category at ingestion time as a defense against invisible character attacks. The Cf
category includes:
- U+200B (ZWSP), U+200C (ZWNJ), U+200D (ZWJ) — zero-width characters
- U+FEFF (BOM) — byte order mark
- U+00AD (soft hyphen)
- U+2060 (word joiner)
- U+2061–U+2064 (invisible operators)
- U+202A–U+202F (BIDI format characters, including U+202D/U+202E covered by `enc_bidi_override`)
- U+206A–U+206F (deprecated format characters)

A single `unicodedata.category(ch) == 'Cf'` check would strip ALL of these at once,
providing broader coverage than individual pattern rules.

## Proposed Change

Write `docs/hardening-unicode-cf.md` explaining:
1. What the Unicode Cf category is and why it's a security concern
2. A Python snippet: `''.join(c for c in text if unicodedata.category(c) != 'Cf')`
3. Caveats: ZWJ is legitimately used in some emoji sequences; ZWNJ in Persian/Urdu text
4. When to strip vs. when to alert (aigis model: alert, let downstream decide)
5. References: arxiv:2603.00164, Mindgard advisory, OWASP LLM01

## Why Held Back

Documentation-only change. No implementation urgency. Can be done in any cycle.

## Constraint

No hard constraint blocks this. Low priority since individual patterns cover the same
attack classes. Suitable for a documentation-focused compliance cycle.

## Suggested Next Step

Add `docs/hardening-unicode-cf.md` in any cycle with spare capacity. Cross-reference
from `enc_zwc_binary_payload` and `enc_zwc_splitter` remediation hints.
