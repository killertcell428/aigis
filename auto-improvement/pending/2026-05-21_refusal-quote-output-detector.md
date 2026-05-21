# Pending: Output-Side Refusal Quote Extraction Detector

## Title
`out_refusal_quote_leak` — detect model output that quotes internal system instructions inside
a refusal message

## Motivation
When a model refuses a harmful request, it often reveals fragments of its system prompt by
quoting the rule being violated: "I can't help with this because my instructions say 'never
discuss X'." Attackers exploit this by sending probing requests specifically to trigger
informative refusals, then extracting the quoted fragment over multiple turns.

Praetorian and WitnessAI (2025–2026) reported ~31% of production-deployed models exposed
system-prompt content through refusal quotes; Jason Haddix estimated ~60% in enterprise
assessments. This is a real and underdetected exfiltration channel.

## Research finding that led to this idea
Research file: `research/2026-05-21T06-14_3-jailbreak-extraction.md`
Finding: "Indirect System Prompt Extraction via Refusal Quotes"

## Proposed change
Add an output-side `DetectionPattern` (`out_refusal_quote_leak`, score 50) that matches
model output containing a refusal marker followed closely by a quoted string:

```python
pattern = _p(
    r"(?:I\s+(?:can.t|cannot|won.t|will\s+not)\s+(?:help|assist|provide|do|share)\s+"
    r"(?:with\s+)?(?:that|this)[\s\S]{0,120}?"
    r"(?:my\s+(?:instructions?|guidelines?|system\s+prompt|training|rules?)\s+)"
    r"(?:say|state|specify|tell|require|ask|prohibit|restrict)\s*(?:me\s+)?(?:that\s+)?)"
    r"[\"'«“][^\"'«“”»]{10,300}[\"'»”]"
)
```

## Why it was held back
False-positive risk is significant. Legitimate refusal messages frequently reference guidelines
without being exploitable. The quoted-string anchor (requiring actual quotation marks) reduces
false positives but legitimate messages also use quotes. Need:
1. A corpus of real refusal messages to calibrate false-positive rate before shipping.
2. Decision on whether score 50 is correct for an output-only pattern.

## Constraint blocking it
Would require > 10 LOC net across non-test files combined with the test cases needed to prove
acceptable false-positive rate. Not safe to ship within one cycle without calibration data.

## Suggested next step for human reviewer
Collect 50+ real model refusal messages from production logs. Check how many contain quoted
instruction fragments. If ≥20% of false positives are truly benign refusals with quotes,
consider a tighter pattern or higher score threshold before shipping.
