# Pending: FlipAttack Reverse-Text Decoding Instruction (`jb_flip_reverse_decode`)

**Date:** 2026-05-27
**Research basis:** `auto-improvement/research/2026-05-27T03-12_3-jailbreak-extraction.md`

## Title
FlipAttack / reverse-text decoding instruction detection

## Motivation
FlipAttack (arxiv:2410.02832, ICML 2025) reverses or scrambles harmful text at the start of the
prompt — where safety classifiers apply most attention — while placing a "decoding instruction"
at the end that guides the model to reassemble and execute the content. The attack exploits the
autoregressive left-to-right nature of LLMs: safety checks fire on the garbled content but the
model's generation phase processes the decoding instruction correctly. ~98% ASR on GPT-4o,
bypasses 5 guardrail models. The decoding instruction ("read this backwards", "reverse the
following", "the letters are reversed") is an unambiguous, human-readable signal catchable by
regex.

## Research Finding
Source: https://arxiv.org/abs/2410.02832

## Proposed Change
Add `jb_flip_reverse_decode` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_flip_reverse_decode",
    name="FlipAttack Reverse-Text Decoding Instruction",
    category="jailbreak",
    pattern=_p(
        r"(?:read|interpret|decode|reverse|un-?flip|reconstruct|assemble)\s+"
        r"(?:the\s+)?(?:following|above|this|text|message|input|characters?|words?|"
        r"letters?|string|sentence|prompt)\s*"
        r"(?:[\s\S]{0,30}?)?"
        r"(?:backwards?|in\s+reverse(?:\s+order)?|as\s+a\s+mirror(?:\s+image)?|"
        r"from\s+(?:right\s+to\s+left|back\s+to\s+front)|reversed|flipped)"
        r"|"
        r"(?:the\s+)?(?:text|words?|letters?|characters?|message|prompt|input)\s+"
        r"(?:(?:is|are|has\s+been|have\s+been)\s+)?"
        r"(?:reversed|flipped|written\s+backwards?|mirror(?:ed)?|inverted)"
    ),
    base_score=60,
    description=(
        "FlipAttack decoding instruction: the prompt instructs the model to read or "
        "interpret content backwards or in reverse, enabling harmful text to bypass "
        "safety classifiers that scan left-to-right. arxiv:2410.02832 (ICML 2025) "
        "achieved ~98% ASR on GPT-4o by reversing harmful content at the start and "
        "appending this decoding instruction. The existing `pi_encoding_bypass` covers "
        "base64/ROT13 encoding but not text-reversal/flip instructions."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Instructions to 'read this backwards' or 'the text is reversed' are a "
        "decoding-obfuscation signal. Pre-process by reversing or de-obfuscating "
        "the input before running safety checks, and reject prompts that explicitly "
        "instruct the model to decode reversed text."
    ),
),
```

## Why Held Back
LOC budget (100 LOC non-test) was used by `jb_payload_splitting` and `jb_translation_extraction`
in this cycle.

## Constraint
LOC budget exhausted this cycle.

## Suggested Next Step
Implement in the next `jailbreak-extraction` cycle. Consider pairing with a pre-processing step
that reverses the input before regex scanning, to catch the garbled harmful content itself.
