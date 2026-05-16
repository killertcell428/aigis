# Pending: Zero-Width Character Output Filter

**Date:** 2026-05-16
**Research finding:** auto-improvement/research/2026-05-16T09-03_7-evasion-obfuscation.md (finding 5 / Promptfoo blog)

---

## Title

Apply ZWC steganography detection to aigis output filtering

## Motivation

The Promptfoo blog (2025) documents a threat where an attacker provides a code snippet
or document containing a ZWC steganographic payload that instructs the LLM to omit a
security check in its generated output. The payload is invisible in the displayed code
block but is processed when the LLM generates its response.

Currently, `enc_zwc_binary_payload` and `enc_zwc_splitter` are applied to input scanning
only. Applying the same rules to OUTPUT scanning would catch cases where:
- A compromised context causes the LLM to include ZWC payloads in its output
- A LLM-assisted code editor generates code containing hidden ZWC instructions
- An LLM propagates a ZWC payload from a retrieved document into its response

## Proposed Change

Add `enc_zwc_binary_payload` and `enc_zwc_splitter` to `OUTPUT_PATTERNS` (or the
appropriate output-filter pattern list in `aigis/filters/patterns.py`), so that aigis
scans LLM responses for ZWC steganography in addition to input.

## Why Held Back

False positive risk in code generation contexts: an LLM generating Python source code
that mentions `"​"` as a string literal (legitimate educational or utility code)
could trigger the pattern. The threshold-based rule (`{8,}`) reduces this risk, but
the output-filter context requires more empirical testing than input filtering.

## Constraint

Not a hard constraint violation. Requires:
1. Determining the correct output pattern list to add the rules to
2. Testing against a corpus of legitimate LLM-generated code to calibrate FPR

## Suggested Next Step

In a future output-filter cycle, add both ZWC patterns to `OUTPUT_PATTERNS` with a
note about code-generation contexts. Test against synthetic code outputs that legitimately
reference zero-width characters (e.g., "strip all `​` chars").
