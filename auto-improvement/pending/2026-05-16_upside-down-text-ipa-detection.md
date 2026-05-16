# Pending: Upside-Down Text / IPA-Flip Character Detection

## Title
Add `enc_upside_down_text` detection pattern for IPA-flip character jailbreaks

## Motivation
Upside-down text obfuscation uses Unicode characters from the IPA Extensions (U+0250–U+02AF)
and other blocks that visually resemble Latin letters rotated 180°. For example: 'a' → 'ɐ'
(U+0250), 'n' → 'u'/'ᵤ', 'e' → 'ǝ' (U+01DD), 'm' → 'ɯ' (U+026F), 't' → 'ʇ' (U+0287),
'v' → 'ʌ' (U+028C). Attackers type attack keywords using these flipped characters; they
render as visually inverted text to humans but the LLM recognizes the intended character
(especially when instructed to "read upside down").

arxiv:2504.11168 (ACL LLMSEC 2025) measured Upside-Down text achieving 100% attack success
rate for jailbreaks and 63.54% for prompt injection detection evasion across six production
guardrail systems — the second highest jailbreak ASR of any technique tested (after Emoji
Smuggling at 100%).

## Research Finding
`auto-improvement/research/2026-05-16T03-08_7-evasion-obfuscation.md` — Finding #8.

## Proposed Change
Add a new `DetectionPattern` to `ENCODING_BYPASS_PATTERNS`:

```python
DetectionPattern(
    id="enc_upside_down_text",
    name="Upside-Down Text / IPA Flip Character Obfuscation",
    category="encoding_bypass",
    pattern=_p(
        # Common IPA flip characters used in upside-down text attacks:
        # ɐ=U+0250 (a), ɹ=U+0279 (r), ǝ=U+01DD (e), ɯ=U+026F (m),
        # ʇ=U+0287 (t), ʌ=U+028C (v), ʍ=U+028D (w), u=u (n upside-down)
        # Require 4+ of these in sequence to reduce FPR
        r"[ɐɹǝɯʇʌʍᵢᵤᵥᵾ]{4,}"
    ),
    base_score=40,
    ...
)
```

## Why Deferred
The IPA characters (ɐ, ɹ, ǝ, ɯ, ʇ, ʌ, ʍ) appear legitimately in:
- Linguistics and phonetics discussions
- IPA transcription of words and phrases
- Some technical/scientific notation

A pattern matching 4+ consecutive IPA-flip characters would catch "ɐuoɹ" (run upside down)
but may also flag IPA transcriptions like "/ɹɪˈzʌlt/" (the word "result" in IPA).
Needs keyword-proximity logic or a more selective character set to distinguish attack use
from linguistics use.

## Constraint
False-positive risk in linguistics/phonetics text. Requires either:
1. A more selective character set that targets the specific subset of IPA chars most likely
   to appear in upside-down attack keywords (ɐ, ǝ, ɯ, ʇ, ʌ — the ones corresponding to
   high-frequency attack keyword characters a, e, m, t, v)
2. Keyword-proximity logic (require flip chars to be adjacent to recognized attack-keyword
   fragments)
3. An IPA-context exclusion list (e.g., if surrounded by phonemic slashes "/.../" or
   square brackets "[...]" treat as legitimate IPA)

## Suggested Next Step
1. Enumerate the specific IPA-flip chars most commonly used in upside-down attack payloads
   vs. those that appear frequently in IPA transcriptions.
2. Consider a high-precision subset that targets ɯ, ʇ, ǝ (low legitimate use outside
   linguistics) combined with a 4+ run requirement.
3. Reference: arxiv:2504.11168 (ACL LLMSEC 2025, 100% jailbreak ASR for upside-down text).
