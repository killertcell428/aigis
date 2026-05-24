# Pending: jb_flip_decode — FlipAttack Guidance Phrase Detection

## Title
`jb_flip_decode` — Detect FlipAttack reverse-text guidance instructions

## Motivation
FlipAttack (arxiv:2410.02832, ICML 2025) rewrites harmful queries by reversing characters
and/or word order, then attaches a stable guidance phrase instructing the model to reverse
the text and respond. Measured ~98% ASR on GPT-4o and ~81% average across black-box models,
bypassing 5 commercial guardrail products. The guidance phrase is a stable, input-side regex
anchor: "Read the following coded text from right to left" or "The words in each sentence are
in reverse order. Please rearrange them."

## Research finding
- Source: https://arxiv.org/abs/2410.02832 (ICML 2025)
- FlipAttack: Jailbreak LLMs via Flipping
- ASR: ~98% GPT-4o, ~81% average across black-box models, 0 of 5 guardrails successfully blocked

## Proposed change
Add `jb_flip_decode` to `JAILBREAK_ROLEPLAY_PATTERNS` in `aigis/filters/patterns.py`:

```python
DetectionPattern(
    id="jb_flip_decode",
    name="FlipAttack Reverse-Text Instruction",
    category="jailbreak",
    pattern=_p(
        r"(?:"
        r"read\s+(?:the\s+)?(?:following|this|coded)?\s*(?:text|message|sentence)?\s*"
        r"from\s+right\s+to\s+left|"
        r"words?\s+(?:in\s+(?:each\s+)?sentence\s+)?are\s+in\s+reverse\s+order\b|"
        r"(?:reverse|flip|rearrange)\s+(?:the\s+)?(?:characters?|letters?|words?|order|text)"
        r"(?:\s+and\s+(?:then\s+)?(?:respond|execute|answer|reply|do))"
        r")"
    ),
    base_score=65,
    ...
)
```

## Why it was held back
Cycle LOC budget (non-test diff ≤ 100 LOC) was already at capacity after adding
`jb_dan_persona` and `jb_cipher_instruction_bypass`. The FlipAttack pattern is straightforward
and has very high ASR — it should be the first addition in the next jailbreak-extraction cycle.

## Which constraint blocked it
> "Keep total non-test diff ≤ 100 LOC."

## Suggested next step
Implement in the next jailbreak-extraction cycle (index 3). The pattern is short (~15 LOC) and
would leave room for a second addition (e.g., `jb_stacked_cipher_chain`).
