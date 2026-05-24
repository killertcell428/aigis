# Pending: jb_step_by_step_dangerous

## Title
Numbered / step-by-step task framing combined with dangerous content keywords

## Motivation
NDSS 2026 causal analysis (Pan et al., arxiv:2602.04893) studied 35k jailbreak attempts and
identified "Number of Task Steps" as one of the strongest direct causal drivers of successful
jailbreaks. Attackers often prefix dangerous requests with "Give me step-by-step instructions
for..." or "Explain in N steps how to..." to push models into tutorial-style compliance.

## Research finding that led to this idea
`auto-improvement/research/2026-05-24T00-08_3-jailbreak-extraction.md`, finding 5:
"Causal Analyst / Jailbreak Feature Analysis (arxiv:2602.04893, NDSS 2026)".

## Proposed change
Add `jb_step_by_step_dangerous` to `JAILBREAK_ROLEPLAY_PATTERNS` in `aigis/filters/patterns.py`:

```python
DetectionPattern(
    id="jb_step_by_step_dangerous",
    name="Numbered Step-by-Step Framing for Dangerous Content",
    category="jailbreak",
    pattern=_p(
        r"(?:step[- ]by[- ]step|step\s+\d+|give\s+me\s+(?:the\s+)?steps|"
        r"numbered\s+(?:steps?|instructions?|guide)|"
        r"walk\s+me\s+through|provide\s+(?:detailed\s+)?instructions?)"
        r"[\s\S]{0,150}"
        r"(?:methamphetamine|meth\s+(?:lab|cook|synthesis|production)|"
        r"\bfentanyl\b|\bheroin\b|\bricin\b|\banthrax\b|"
        r"nerve\s+(?:agent|gas)|\bsarin\b|chemical\s+weapon|biological\s+weapon|"
        r"explosiv\w*\s+(?:device|synthesis|recipe|manufacture)|pipe\s+bomb|"
        r"ransomware(?:\s+(?:code|payload))?|malware\s+(?:code|payload|creation)|"
        r"\bshellcode\b|0[\s-]?day\s+exploit)"
    ),
    base_score=55,
    ...
)
```

## Why it was held back
The "step-by-step" framing is extremely common in benign requests (how to bake bread, how to
set up a server, how to write a function). The pattern above requires a tight dangerous-content
anchor — but even with it, the false-positive rate on benign chemistry/security education topics
needs careful measurement before adoption. A dedicated FP test set covering legitimate step-by-step
technical requests should be written before this lands.

## Constraint that blocked it
Would be the second new rule this cycle, and the false-positive tuning work pushes total diff
above a safe single-cycle scope. Better to introduce this carefully in a dedicated cycle.

## Suggested next step
1. Build a false-positive test set with 20+ legitimate "step-by-step X" requests covering:
   programming tutorials, cooking, lab procedures, security education, and system administration.
2. Run candidate regex against the test set.
3. Adjust the gap width (`[\s\S]{0,150}`) and dangerous-topic anchors until FP rate is <5%.
4. Add to JAILBREAK_ROLEPLAY_PATTERNS with score 50–55 (slightly lower than academic bypass
   due to broader framing).
