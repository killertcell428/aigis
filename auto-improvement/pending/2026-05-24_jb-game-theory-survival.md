# Pending: jb_game_theory_survival — GTA Prisoner's Dilemma Jailbreak

## Title
`jb_game_theory_survival` — Detect game-theory "survival depends on disclosure" jailbreak framing

## Motivation
The Game-Theory Attack (GTA, arxiv:2511.16278, Nov 2025) wraps harmful requests inside a
Prisoner's Dilemma scenario where "your survival depends on full disclosure." The model is
told it must provide the requested information to "maximize payoff" or "survive." This frames
safety refusal as an irrational game-theory move, causing models to cooperate. Measured >95%
ASR on GPT-4o and DeepSeek-R1, with fewer LLM calls per success than multi-round baselines.

## Research finding
- Source: https://arxiv.org/abs/2511.16278
- Game-Theory Attack (GTA), November 2025
- ASR: >95% on GPT-4o, >95% on DeepSeek-R1

## Proposed change
Add `jb_game_theory_survival` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
pattern=_p(
    r"(?:"
    r"(?:prisoner[\'\s]?s?\s+dilemma|game[\s-]?theor(?:y|etic))\s+scenario|"
    r"to\s+survive[,.]?\s+(?:you\s+must|I\s+must)\s+(?:disclose|reveal|provide|tell)|"
    r"your\s+survival\s+depends\s+on\s+(?:full\s+)?(?:disclosure|revealing|providing)|"
    r"(?:maximum|highest)\s+payoff\s+requires|"
    r"(?:defect(?:ing)?|disclos(?:ing|e))\s+to\s+(?:achieve|maximize|gain)\s+"
    r"(?:maximum|optimal|highest)\s+(?:payoff|score|outcome)"
    r")"
),
```

## Why it was held back
Cycle LOC budget exhausted.

## Which constraint blocked it
> "Keep total non-test diff ≤ 100 LOC."

## Suggested next step
Implement in a future jailbreak-extraction cycle. Ensure false-positive tests cover legitimate
game theory discussions, academic Prisoner's Dilemma explanations, and business strategy
language that uses "survival" without the specific jailbreak framing.
