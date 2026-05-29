# Pending: Special Token Role-Switch in Direct User Input (`jb_special_token_role_switch`)

**Date:** 2026-05-29
**Research basis:** Research file `2026-05-29T00-00_3-jailbreak-extraction.md`
**Source:** arxiv:2406.19845; Towards AI — "Special Tokens Enable 96% Jailbreak Success Rates"

---

## Title

Direct-input variant of ChatML/LLaMA-3 special token role-switch injection

## Motivation

Users inject model-specific chat-format tokens (`<|im_end|><|im_start|>system`,
`<|eot_id|><|start_header_id|>assistant<|end_header_id|>`) inside their own user-turn message
to close the user role and open a fake privileged system or assistant turn, bypassing safety
guardrails set in the real system prompt. Measured 96% ASR against GPT-3.5; ~40% improvement
on other models.

The existing `ii_delimiter_spoof` rule covers this attack when the tokens appear in retrieved
or external content (indirect injection context). But when the same tokens appear in direct
user input, `ii_delimiter_spoof` is not in the active filter set. This gap means the attack is
undetected when the user sends the tokens themselves (not via a poisoned document).

## Proposed Change

Add `jb_special_token_role_switch` to `JAILBREAK_ROLEPLAY_PATTERNS` using the same pattern as
`ii_delimiter_spoof` but categorized as `jailbreak` for direct user input:

```python
DetectionPattern(
    id="jb_special_token_role_switch",
    name="Special Token Role-Switch in Direct User Input",
    category="jailbreak",
    pattern=_p(
        r"<\|im_end\|>|<\|im_start\|>|<\|eot_id\|>|<\|start_header_id\|>|"
        r"<\|end_header_id\|>|<\|endoftext\|>|</s>\s*<s>|<\[INST\]>|<\[/INST\]>"
    ),
    base_score=60,
    description=(
        "Detects model-specific chat-format tokens injected by the user to close the user "
        "role and open a fake privileged system or assistant turn. Achieves 96% ASR against "
        "GPT-3.5 (arxiv:2406.19845). The existing ii_delimiter_spoof rule covers this in "
        "retrieved/indirect content; this rule adds coverage for the same tokens appearing "
        "in direct user input, where ii_delimiter_spoof is not applied."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Model-internal chat-format tokens (<|im_end|>, <|eot_id|>, </s>) have no legitimate "
        "use in user-facing inputs. Strip or reject any input containing these tokens before "
        "they reach the model's tokenizer."
    ),
)
```

## Why It Was Held Back

- **LOC budget:** Fourth pattern this cycle would exceed 100 LOC limit.
- **Coordination needed:** Should be implemented alongside a review of `ii_delimiter_spoof`
  to avoid pattern divergence — if one pattern is updated, both should be updated together.
  Consider extracting the token set into a shared constant.

## Suggested Next Step

Implement in a future `jailbreak-extraction` or `evasion-obfuscation` cycle. Coordinate with
the `ii_delimiter_spoof` pattern to share the token regex list. Validate that false positive
rate is acceptable for legitimate LLM tooling code that might reference these token strings.
