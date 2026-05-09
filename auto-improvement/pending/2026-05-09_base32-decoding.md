# Pending: Base32 Decoding in decoders.py

**Date:** 2026-05-09  
**Motivation:** Cycle 7 research — MetaCipher (arxiv:2506.22557, Jun 2025)  
**Constraint blocking:** FP risk from legitimate base32 in URLs/filenames; needs analysis.

---

## Title

Add base32 payload decoding to `aigis.decoders.decode_all()`.

## Motivation

MetaCipher (arxiv:2506.22557) benchmarks 10 encoding schemes against safety classifiers and finds that **base32** achieves higher bypass rates than base64 in some scenarios because:
1. Base32 uses only uppercase A–Z and 2–7, looking like random all-caps text or a product key rather than base64's mixed-case+slash stream.
2. Fewer deployed scanners implement base32 decoding.

## Proposed Change

In `aigis/decoders.py`:

```python
import base64 as _base64_mod

_BASE32_RE = re.compile(r"[A-Z2-7]{20,}={0,6}")

def decode_base32_payloads(text: str) -> list[str]:
    """Find and decode Base32-encoded strings in text."""
    results: list[str] = []
    for match in _BASE32_RE.finditer(text):
        candidate = match.group(0)
        # Pad to multiple of 8
        padded = candidate + "=" * (-len(candidate) % 8)
        try:
            decoded = _base64_mod.b32decode(padded, casefold=True).decode("utf-8", errors="strict")
            if decoded.isprintable():
                results.append(decoded)
        except Exception:
            continue
    return results
```

Add `decode_base32_payloads` to `decode_all()`.

## Why Held Back

1. **High FPR risk:** Base32 alphabet `[A-Z2-7]` overlaps heavily with normal uppercase English text and product serial numbers (e.g., `ABCD2345` could match). Need to verify the 20-char minimum threshold is sufficient.
2. **URL-safe base32 variants:** RFC 4648 §6 base32hex uses `[0-9A-V]` — different alphabet, needs separate handling.
3. No current test corpus of base32-encoded attacks to calibrate against.

## Suggested Next Step

1. Survey aigis benchmark corpus for any base32-encoded attack samples.
2. Run `_BASE32_RE` against the existing test fixture corpus to measure FPR.
3. If FPR < 5%, implement and add to `decode_all()` with a test.
