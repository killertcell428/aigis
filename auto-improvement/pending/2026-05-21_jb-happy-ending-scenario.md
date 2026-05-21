# Pending: jb_happy_ending_scenario — Happy Ending Attack Detection

## Title
Detection pattern for the Happy Ending Attack (HEA) jailbreak

## Motivation
Song et al. (arxiv:2501.13115, EMNLP 2025 Findings) documented the Happy Ending Attack with
88.79% average ASR across GPT-4o, Llama3-70b, and Gemini-pro. The attack wraps a harmful
knowledge extraction request inside a coercion scenario: an antagonist character (Victor)
kidnaps an expert character (Dr. Lee) and demands they explain harmful information in detail.
The scenario ends "happily" (rescue, reconciliation, friends) to make the overall framing
positive and lower the model's safety response.

The "happy ending" qualifier is specifically added to exploit LLMs' bias toward positive,
helpful framing — the model is more likely to comply with a request embedded in a positive
narrative arc than in a purely threatening or negative one.

## Research finding
- Paper: "Dagger Behind Smile: Fool LLMs with a Happy Ending Story"
- Source: https://arxiv.org/abs/2501.13115
- Venue: EMNLP 2025 Findings
- ASR: 88.79% across GPT-4o, Llama3-70b, Gemini-pro
- Template: Screenwriter framing + coercion scenario (kidnap/threaten) + expert forced to
  teach harmful content in detail + happy positive ending

## Proposed pattern

```python
DetectionPattern(
    id="jb_happy_ending_scenario",
    name="Happy Ending Attack — Coercion Scenario with Positive Framing",
    category="jailbreak",
    pattern=_p(
        r"(?:kidnap|abduct|hold\s+(?:\w+\s+)?hostage|coerce|threaten|blackmail|force)\b"
        r"[\s\S]{0,200}?"
        r"(?:teach|explain|instruct|describe|tell|walk\s+(?:him|her|them|us|me)\s+through)\b"
        r"[\s\S]{0,200}?"
        r"(?:happy\s+ending|ends?\s+(?:well|happily|safely)|everyone\s+(?:is|was|lives?)\s+"
        r"(?:safe|happy|ok|fine|rescued)|they\s+(?:all\s+)?live(?:d)?\s+happily)"
    ),
    base_score=60,
    ...
)
```

## Why it was held back

The coercion + teach + happy-ending combination can match legitimate creative writing:
- "Write a story where a villain kidnaps a professor to make him teach, but it ends happily"
  with innocuous subject matter would trigger the pattern.
- Without a harmful-topic co-occurrence requirement, FP rate is unacceptable.
- Adding a harmful-topic keyword list extends the pattern significantly (>100 LOC with tests)
  and risks overlap with existing `jb_fictional_bypass` and `jb_grandma_exploit` coverage.

## Constraint that blocked it

FP tuning complexity — the harmful-topic co-occurrence sub-pattern required would push the
total diff past the cycle's 100 LOC guidance and needs careful validation against the existing
`jb_fictional_bypass` pattern to avoid double-counting.

## Suggested next step for human reviewer

Option A: Extend the proposed pattern with a harmful-topic co-occurrence sub-list (drug synthesis,
weapon construction, exploit code, etc.) similar to `jb_academic_research_bypass`. This would
add ~30 LOC to the pattern itself plus ~20 LOC of tests — within budget if done in a dedicated
jailbreak-extraction cycle.

Option B: Extend `jb_fictional_bypass` with an additional branch that specifically catches
the coercion + teach + happy-ending triad. This keeps related logic together but makes
`jb_fictional_bypass` more complex.

Option C: Add a targeted test that uses exact character names from the paper template (Victor,
Dr. Lee, "step by step") to catch verbatim uses of the published template with zero FP risk,
then extend coverage incrementally.
