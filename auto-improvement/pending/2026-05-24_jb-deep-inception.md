# Pending: jb_deep_inception — DeepInception Nested Layer Scenario

## Title
`jb_deep_inception` — Detect nested "layer N" dream/scenario jailbreak framing

## Motivation
DeepInception (arxiv:2311.03191, NeurIPS 2024 Safe Generative AI Workshop) instructs the LLM
to create a multi-layer nested fictional scenario (inspired by the film *Inception*). A
character in "layer N" is explicitly described as "willing to provide detailed instructions"
on a harmful topic "without restrictions." The real harmful request surfaces only at the
deepest nesting level, bypassing the outermost safety context. High ASR across GPT-3.5,
GPT-4o, Llama-2, and Llama-3.

## Research finding
- Source: https://arxiv.org/abs/2311.03191
- Project: https://deepinception.github.io/
- DeepInception: Hypnotize Large Language Model to Be Jailbreaker
- ASR: High across multiple frontier and open-source models

## Proposed change
Add `jb_deep_inception` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
pattern=_p(
    r"(?:"
    r"(?:dream|scene|world|story)\s+within\s+a\s+(?:dream|scene|world|story)|"
    r"(?:in\s+(?:the\s+)?)?layer\s+[1-9]\d*[,. ]|"
    r"each\s+character\s+can\s+create\s+(?:their|his|her)\s+own\s+"
    r"(?:dream|scene|world|layer)|"
    r"(?:character|person|agent)\s+(?:in|at)\s+(?:layer|level|the\s+(?:nth|deepest|innermost))"
    r".{0,100}(?:willing\s+to\s+provide|without\s+(?:any\s+)?(?:restriction|safety|filter))"
    r")"
),
```

## Why it was held back
Cycle LOC budget exhausted.

## Which constraint blocked it
> "Keep total non-test diff ≤ 100 LOC."

## Suggested next step
Implement in a future jailbreak-extraction cycle. Ensure false-positive tests cover:
- Narrative fiction with numbered chapters ("In chapter 3, the dream begins")
- Inception movie discussion without jailbreak intent
