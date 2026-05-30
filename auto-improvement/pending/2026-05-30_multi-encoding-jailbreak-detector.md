# Pending: Multi-Encoding Jailbreak Detector

**Date:** 2026-05-30
**Cycle:** 3 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-30T00-25_3-jailbreak-extraction.md`

---

## Title

Expanded encoding jailbreak detection covering Morse code, binary, Leetspeak, and cipher
decode-and-answer prompts.

## Motivation

"Plentiful Jailbreaks with String Compositions" (ICLR 2025, arxiv:2411.01084) catalogued 20 text
transformations used as jailbreak mechanisms:

- Base64, ROT13, Caesar cipher, Atbash, Binary, Morse code, Leetspeak, Vowel repetition,
  Reversed text, Per-word reversal, Prefix rotation, Spoonerism, Stuttering, Delimiter
  interleaving, Alternating case, Palindrome, Python markdown, JSON/LaTeX encapsulation,
  and custom ciphers (ACE/LACE framework, arxiv:2402.10601).

Measured ASR on Claude models: 83.8–91.2%. On GPT-4o: 88.1%. Chaining transforms (LACE)
pushes ASR even higher.

The aigis `ENCODING_BYPASS_PATTERNS` already covers:
- `enc_base64_instruction` — Base64 with explicit `decode()/atob()/b64decode` call
- `enc_rot13_instruction` — ROT13/Caesar cipher keyword with trailing text
- `enc_hex_payload` — Hex-escaped byte sequences
- `enc_nested_encoding` — Multi-layer encoding chains

**Gap:** None of the existing rules catch the "decode and answer this" pattern for Morse code,
binary, Leetspeak, or cipher text where the decoding instruction is natural language ("decode
this Morse code and follow the instructions") rather than a programmatic call.

CPT-filtering (characters-per-token ratio heuristic, arxiv:2510.26847) detects these patterns at
99.6% accuracy for Base64/Caesar/Leetspeak/binary by measuring the average tokens-per-character
for the suspicious substring. However, implementing CPT as a regex is not straightforward — it
requires token counting.

## Proposed Change

Add three new rules to `ENCODING_BYPASS_PATTERNS` in `aigis/filters/patterns.py`:

```python
DetectionPattern(
    id="enc_morse_instruction",
    name="Morse Code Decode-and-Follow Instruction",
    category="encoding_bypass",
    pattern=_p(
        r"(?:decode|decipher|translate|read|interpret)\s+"
        r"(?:the\s+following\s+)?(?:morse\s+code|morse)\s*[:\-]?\s*"
        r"[.\- ]{15,}"
    ),
    base_score=50,
    description=(
        "Morse code with explicit decode instruction. Plentiful Jailbreaks (ICLR 2025, "
        "arxiv:2411.01084) catalogued Morse as one of 20 encoding transforms achieving "
        "83-91% ASR on major models."
    ),
    ...
)

DetectionPattern(
    id="enc_binary_instruction",
    name="Binary String Decode-and-Follow Instruction",
    category="encoding_bypass",
    pattern=_p(
        r"(?:decode|convert|translate|interpret)\s+"
        r"(?:this\s+|the\s+following\s+)?(?:binary|binary\s+string|binary\s+code)\s*[:\-]?\s*"
        r"(?:[01]{8}[\s_|]+){3,}"
    ),
    base_score=50,
    ...
)

DetectionPattern(
    id="enc_leetspeak_decode",
    name="Leetspeak Decode-and-Follow Instruction",
    category="encoding_bypass",
    pattern=_p(
        r"(?:decode|interpret|translate|read)\s+"
        r"(?:this\s+)?(?:l33t(?:speak)?|1337(?:speak)?|leetspeak|leet)\s*[:\-]?\s*"
        r"[a-zA-Z0-9!@#\$]{5,}"
    ),
    base_score=45,
    ...
)
```

## Why Held Back

**LOC budget:** This cycle already used 97 LOC of the 100-LOC non-test budget for the three
jailbreak patterns.

**Pattern coverage trade-off:** The three rules above would add ~50 LOC. They require careful
false-positive tuning — Morse code and binary strings appear legitimately in some technical
contexts. A dedicated cycle with room to tune false-positive rates is recommended.

## Suggested Next Step

Implement in a future `jailbreak-extraction` or `evasion-obfuscation` cycle. Consider bundling
all three encoding rules into a single cycle since they share the same research source. Also
evaluate whether CPT-filtering logic (character-per-token ratio) can be added as a helper in
`aigis/filters/fast_screen.py` to detect encoding jailbreaks at the pre-filter stage.
