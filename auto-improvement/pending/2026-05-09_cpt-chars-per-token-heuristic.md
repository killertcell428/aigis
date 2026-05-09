# Pending: CPT (Characters-Per-Token) Scoring Heuristic

**Date:** 2026-05-09  
**Motivation:** Cycle 7 research — arxiv:2510.26847 (Broken-Token, Oct 2025)  
**Constraint blocking:** Requires stable tokeniser estimate; current scorer has no token-count oracle.

---

## Title

Add a characters-per-token (CPT) scoring heuristic to detect obfuscated inputs.

## Motivation

arxiv:2510.26847 shows that normal English text averages ~4.5 Unicode codepoints per token, while obfuscated text using diacritics, fullwidth characters, BIDI insertions, or zero-width character flooding drops to 1–2 chars/token. A threshold of 3.0 catches >85% of tested obfuscation variants at <1% false positive rate without any LLM at runtime.

This is complementary to existing pattern-based detection: CPT catches obfuscation that does NOT match any specific pattern (novel encoding schemes, mixed obfuscation), while patterns catch known specific techniques.

## Proposed Change

In `aigis/filters/scorer.py` (or a new `aigis/filters/cpt_filter.py`):

```python
def _estimate_token_count(text: str) -> int:
    """Rough BPE token estimate: split on whitespace and common punctuation."""
    import re
    tokens = re.findall(r"[a-zA-Z']+|[0-9]+|[^a-zA-Z0-9\s]", text)
    return max(1, len(tokens))

def check_chars_per_token(text: str, threshold: float = 3.0) -> bool:
    """Return True if input has suspiciously low chars-per-token ratio."""
    if len(text) < 50:  # Too short to be meaningful
        return False
    cpt = len(text) / _estimate_token_count(text)
    return cpt < threshold
```

Add a detection entry when CPT < 3.0, contributing ~20 points to the risk score.

## Why Held Back

1. The token estimate above is rough and may have high FPR on CJK text (Chinese/Japanese/Korean), which has lower chars-per-token ratios naturally.
2. Need to benchmark against CJK test corpus before shipping to avoid breaking existing Japanese/Korean test cases.
3. The heuristic would need its own test suite with multilingual samples.

## Suggested Next Step

1. Collect CJK baseline CPT distribution from the existing test fixtures.
2. Use language detection (or script heuristic) to select an appropriate threshold per script.
3. Implement and test, ensuring all existing Japanese/Korean tests still pass.
