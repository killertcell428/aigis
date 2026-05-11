# Pending: Grapheme-Cluster Tag Block Filter (IBM Black Box Emoji Fix)

**Date:** 2026-05-11
**Research finding:** auto-improvement/research/2026-05-11T12-15_7-evasion-obfuscation.md (finding 6)
**Constraint blocking:** Requires Unicode grapheme cluster parser; no-runtime-dependency constraint.

---

## Title

Implement a pre-filter that strips Unicode Tag Block characters while preserving valid subdivision flag emoji sequences.

## Motivation

The `enc_tag_block_ascii` pattern (added this cycle) correctly detects Unicode Tag Block characters (U+E0000–U+E007F) used in the EchoLeak-class attack. However, subdivision flag emoji such as 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (England) legitimately use tag block characters in their encoding:
- U+1F3F4 (BLACK FLAG) + U+E0067 U+E0062 U+E0065 U+E006E U+E0067 (tag letters g,b,e,n,g) + U+E007F (CANCEL TAG)

A rule-based pre-filter that strips malicious tag chars while preserving valid flag sequences would reduce false positives for applications that pass flag emoji through the API.

IBM Research documented this algorithm as "Black Box Emoji Fix" (tdcommons.org/dpubs_series/7836, 2025):
1. Parse the input into Unicode grapheme clusters.
2. For each cluster, check if it is a valid subdivision flag (U+1F3F4 + lowercase tag letters + U+E007F).
3. Strip all tag block characters NOT in a valid subdivision flag cluster.

## Proposed Change

Add a function to `aigis/decoders.py`:

```python
def strip_tag_block(text: str, preserve_flags: bool = True) -> str:
    """Strip Unicode Tag Block chars (U+E0000-U+E007F).
    
    If preserve_flags=True, valid subdivision flag emoji sequences
    (U+1F3F4 + tag letters + U+E007F) are kept intact.
    """
    import re
    if not preserve_flags:
        return re.sub(r"[\U000E0000-\U000E007F]", "", text)
    # Remove tag chars not part of a valid flag sequence
    FLAG_RE = re.compile(
        r"\U0001F3F4[\U000E0061-\U000E007A]+\U000E007F"  # valid flag
        r"|[\U000E0000-\U000E007F]"  # any other tag char (strip)
    )
    return FLAG_RE.sub(
        lambda m: m.group(0) if m.group(0).startswith("\U0001F3F4") else "",
        text
    )
```

Call this in `filter_input` / `filter_output` as a pre-processing step before pattern matching.

## Why Held Back

1. **Dependency concern:** Python's built-in `re` module handles the grapheme cluster logic imperfectly for complex emoji sequences; the correct implementation requires either `regex` (third-party) or a manual grapheme cluster table. Both add dependencies.
2. **Correctness risk:** An incorrect flag-preservation implementation could allow attackers to bypass detection by wrapping tag block payloads inside a partial flag-like sequence. Getting this right requires careful testing.
3. **Scope:** This is a normalization/preprocessing improvement, not a new detection rule. The current `enc_tag_block_ascii` pattern provides the detection signal; stripping is an optional enhancement.

## Constraint Blocking

Violates the zero-runtime-dependency constraint if it requires the `regex` package. A pure-Python implementation with the `re` module may be feasible (as shown above) but requires thorough testing against edge cases in the Unicode subdivision flag standard (BCP 47 extension T).

## Suggested Next Step

1. Verify that the `FLAG_RE.sub(lambda ...)` approach correctly handles all subdivision flags in Python 3.11+ (test against England 🏴󠁧󠁢󠁥󠁮󠁧󠁿, Scotland 🏴󠁧󠁢󠁳󠁣󠁴󠁿, Wales 🏴󠁧󠁢󠁷󠁬󠁳󠁿, Texas 🏴󠁵󠁳󠁴󠁸󠁿).
2. Add as an opt-in normalize step: `aigis.decoders.strip_tag_block(text, preserve_flags=True)`.
3. Document in the remediation hint for `enc_tag_block_ascii` that this function is available.
