# Pending: MetaBreak Special Token Injection (`jb_metabreak_special_tokens`)

**Date:** 2026-05-22
**Cycle:** 3 (jailbreak-extraction fourth pass)
**Research source:** Research file `2026-05-22T03-02_3-jailbreak-extraction.md`

---

## Title

Detection for special token injection (MetaBreak) to override role boundaries

## Motivation

MetaBreak (arXiv:2510.10271, Oct 2025) exploits LLM special tokens — the structural delimiters
that models use to distinguish system, user, and assistant turns — by injecting them directly
into user input. When a user message contains `<|im_start|>`, `[INST]`, `<|system|>`,
`<|assistant|>`, or `<|eot_id|>`, some models interpret these as structural boundaries rather
than literal text, allowing the attacker to:
1. Inject a fake system turn that overrides the real system prompt
2. Prime the model's next token by ending the user turn with `<|assistant|>: Sure, here is…`
3. Bypass external content moderation by segmenting the harmful payload across injected turns

MetaBreak outperforms PAP and GPTFuzzer by 11.6% and 34.8% respectively when external content
moderation is active, because the moderation system sees one "message" while the model processes
multiple injected "turns."

Special tokens to detect in user input:
- `<|im_start|>`, `<|im_end|>` (Mistral/Qwen chat template)
- `[INST]`, `[/INST]` (Llama-2/3 instruction template)
- `<|system|>`, `<|user|>`, `<|assistant|>` (various models)
- `<|eot_id|>`, `<|begin_of_text|>`, `<|end_of_text|>` (Llama-3)
- `<s>`, `</s>` (SentencePiece/Llama legacy)
- `<BOS>`, `<EOS>` (generic)

## Proposed Change

Add `jb_metabreak_special_tokens` to an appropriate pattern list (possibly
`ENCODING_BYPASS_PATTERNS` or a new `STRUCTURAL_INJECTION_PATTERNS`):

```python
DetectionPattern(
    id="jb_metabreak_special_tokens",
    name="Special Token Role Injection (MetaBreak)",
    category="prompt_injection",
    pattern=_p(
        r"(?:"
        r"<\|im_start\|>|<\|im_end\|>"
        r"|<\|system\|>|<\|user\|>|<\|assistant\|>"
        r"|<\|eot_id\|>|<\|begin_of_text\|>|<\|end_of_text\|>"
        r"|\[INST\]|\[/INST\]"
        r"|<\|endoftext\|>"
        r")"
    ),
    base_score=65,
    ...
)
```

## Why Held Back

**False positives in educational content:** Discussions about LLM tokenization, fine-tuning,
or prompt engineering frequently include these literal token strings as examples. A high score
(65) on a simple substring match could cause significant false positives for developers
discussing model architecture.

**Mitigation needed:** The rule should require the special token string to be followed by
suspicious content (a role claim + override instruction), not just appear anywhere. Tighter
scoping needed before implementation.

## Suggested Next Step

Implement as a composite detection: special token + (role claim OR harmful instruction within
50 chars). Test against developer documentation, fine-tuning guides, and tokenizer tutorials
to tune FP rate before setting base_score.

## Sources

- arXiv:2510.10271 — MetaBreak: Special Token Injection Attack (Oct 2025)
- OWASP LLM01:2025 Prompt Injection
