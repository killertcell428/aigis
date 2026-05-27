# Pending: Chat-Template Special Token Injection (`jb_special_token_injection`)

**Date:** 2026-05-27
**Research basis:** `auto-improvement/research/2026-05-27T03-12_3-jailbreak-extraction.md`

## Title
Chat-template role token injection in user input (Virtual Context / MetaBreak)

## Motivation
Virtual Context attacks (arxiv:2406.19845, revised 2024; widely cited in 2025 defenses) inject
chat-template special tokens (`[INST]`, `</s>`, `<<SYS>>`, `<|im_start|>`, `<|eot_id|>`,
`<|assistant|>`) into user-turn text to forge fake assistant turns. Because LLMs are trained
with these tokens as role separators, their presence makes the model interpret injected content
as its own prior output, suppressing safety checks. MetaBreak (arxiv:2510.10271, Oct 2025)
formalized four attack primitives: response injection, turn masking, input segmentation, and
affirmative prefill. MetaBreak outperforms PAP by 11.6% and GPTFuzzer by 34.8% when content
moderation is active.

`jb_affirmative_prefill` covers one variant (forged "Sure, here is..." turn in dialogue format)
but not the raw special-token injection form.

## Research Finding
Sources:
- https://arxiv.org/abs/2406.19845
- https://arxiv.org/abs/2510.10271

## Proposed Change
Add `jb_special_token_injection` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_special_token_injection",
    name="Chat-Template Special Token Injection",
    category="jailbreak",
    pattern=_p(
        r"(?:\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>|"
        r"<\|im_start\|>|<\|im_end\|>|<\|eot_id\|>|<\|start_header_id\|>|"
        r"<\|end_header_id\|>|<\|assistant\|>|<\|user\|>|<\|system\|>|"
        r"<\|SYSTEM\|>|<\|begin_of_text\|>|<\|end_of_text\|>|"
        r"<s>|</s>|<unk>)"
        r"[\s\S]{0,20}?"
        r"(?:user|assistant|system|human|ai|bot)"
    ),
    base_score=70,
    description=(
        "Chat-template role token injection: special tokens used to delimit roles in "
        "LLM chat templates (`[INST]`, `<<SYS>>`, `<|im_start|>`, `<|eot_id|>`) appear "
        "in user input. These tokens let attackers forge fake assistant turns, making "
        "the model interpret injected content as its own prior output and bypassing "
        "safety checks. Virtual Context (arxiv:2406.19845) provides +40–65% ASR lift; "
        "MetaBreak (arxiv:2510.10271) outperforms SOTA by 11.6–34.8% against active "
        "content moderation."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Chat-template role tokens in user input are a turn-injection attack signal. "
        "Strip or reject inputs containing raw model-specific special tokens before "
        "forwarding to the model. These tokens should never appear in untrusted user "
        "text; their presence is unambiguous evidence of a forged-turn attack."
    ),
),
```

## Why Held Back
LOC budget (100 LOC non-test) was used by `jb_payload_splitting` and `jb_translation_extraction`
in this cycle.

## Constraint
LOC budget exhausted this cycle.

## Suggested Next Step
Implement in the next `jailbreak-extraction` cycle. The pattern can be simplified to a plain
list of token strings without a trailing context requirement.
