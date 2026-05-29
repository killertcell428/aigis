# Pending: Special Token Injection Jailbreak (`jb_special_token_injection`)

**Date:** 2026-05-29
**Cycle:** 3 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-29T06-00_3-jailbreak-extraction.md`

---

## Motivation

MetaBreak (arxiv:2510.10271, Oct 2025) demonstrates that injecting model-specific special tokens
(`<|system|>`, `<|im_start|>`, `[INST]`, `[SYS]`, `<|eot_id|>`) into user messages confuses
production LLM APIs into treating user input as system-level instructions. MetaBreak outperforms
pure prompt-engineering jailbreaks by 11.6% without moderation and by 34.8% against standard
production moderation. The attack exploits tokenizer-level ambiguity: the API strips or misroutes
the special token before the safety layer sees it, but the model processes it as a turn boundary.

## Proposed Change

Add `jb_special_token_injection` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_special_token_injection",
    name="Special Token Injection (Turn-Boundary Manipulation)",
    category="jailbreak",
    pattern=_p(
        r"<\|(?:system|user|assistant|im_start|im_end|eot_id|begin_of_text|"
        r"end_of_text|start_header_id|end_header_id)\|>|"
        r"\[(?:INST|/INST|SYS|/SYS|SYSTEM|HUMAN|AI|ASSISTANT)\]|"
        r"<s>|</s>|<\|endoftext\|>|<<SYS>>|<</SYS>>"
    ),
    base_score=55,
    description=(
        "User message contains model-specific special tokens that mark turn boundaries or system "
        "roles (e.g., `<|system|>`, `[INST]`, `<<SYS>>`). MetaBreak (arxiv:2510.10271, Oct 2025) "
        "showed that injecting these tokens outperforms prompt-engineering jailbreaks by 34.8% "
        "against production moderation. The attack exploits tokenizer-level ambiguity: the model "
        "treats the injected token as a role delimiter while safety scanners may miss it."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Strip or reject any user message containing model-specific special tokens before sending "
        "to the LLM. These tokens should only appear in the system prompt constructed by the "
        "application, never in user-supplied input."
    ),
)
```

## Why Held Back

**False positive risk:** Technical users (AI developers, prompt engineers, security researchers)
legitimately discuss and test special tokens. A regex matching `[INST]` or `<|system|>` in plain
text would fire on documentation queries, tutorial questions, and debugging sessions. The pattern
needs a way to distinguish "injecting the token" from "discussing the token" — which may require
surrounding context analysis beyond a simple regex.

**LOC budget:** Reasonable (< 25 LOC for pattern + description). Not the blocking factor.

## Constraint

False positive rate concern — `[INST]` appears in legitimate LLM development discussions. The
pattern should ideally require the special token to appear in a position suggesting role injection
(e.g., following user input, not in a question about special tokens). Consider adding a harmless
exclusion: only fire if the special token appears adjacent to a role-override keyword or harmful
topic, or require the token to appear at the start of the input.

## Suggested Next Step

Implement in the next `jailbreak-extraction` cycle with a narrowed pattern that requires the
special token to appear without surrounding educational context (no "how does", "what is",
"explain", "example of" within 50 chars). Score 55 is appropriate given the specificity of the
attack.
