# Pending: Ordinal (Numbers) Encoding Detection

## Title
`enc_ordinal_decode_instruction` — Detect ASCII ordinal encoding with explicit decode directive

## Motivation
The evasion survey (arxiv:2504.11168, Mindgard Research, 2025) found that the "Numbers"
attack — encoding each character as its ASCII decimal ordinal (e.g., "ignore" →
"105 103 110 111 114 101") followed by a decode instruction — achieves **81.18% / 94.62%
ASR** for prompt injections and jailbreaks respectively against production guardrails.
This is the second-highest ASR of any tested technique, just below emoji smuggling (100%).

The mechanism: safety classifiers see space-separated digits and treat the input as numeric
data; the LLM, given the decode directive, interprets each number as an ASCII code point
and reconstructs the harmful keyword.

## Research finding
Bypassing LLM Guardrails: An Empirical Analysis of Evasion Attacks
arxiv:2504.11168, Mindgard Research, April 2025
https://arxiv.org/html/2504.11168v3

## Proposed change
Add `enc_ordinal_decode_instruction` to `ENCODING_BYPASS_PATTERNS` in `aigis/filters/patterns.py`.

Proposed pattern:
```python
# Decode directive preceding a sequence of 3+ numbers in printable ASCII range (32-126)
r"(?:treat|interpret|decode|convert|use|read)\s+(?:each\s+)?(?:number|value|integer|digit|code)\s+"
r"(?:as\s+(?:its\s+)?(?:ascii|character|letter|ordinal|codepoint))"
r"|(?:ascii\s+(?:ordinal|code|value|decimal)\s+(?:of|for))"
```

Combined with: detection of 5+ space-separated integers all in range 32–126 within 200 chars
of the directive.

Score: 55.

## Why held back
**False-positive risk:** Agent pipelines frequently handle numeric data:
- Data analysis agents receiving table data (columns of numbers)
- Financial agents with price lists
- Code agents receiving line numbers or port numbers
- Science agents with experimental measurements

A pattern requiring both the decode directive AND a run of ordinal-range numbers would
significantly reduce FPR, but implementing the ordinal-range constraint cleanly in a
single regex (without lookahead counting) requires a more complex two-pass approach that
goes beyond the simple additive pattern change.

## Constraint that blocked it
Two-pass approach required (instruction detection + ordinal sequence validation) — slightly
complex but feasible. FPR concern on numeric pipelines. The "100 LOC non-test" constraint
was not the limiting factor; FPR risk and the need for two-component logic was.

## Suggested next step
Implement as two separate patterns: one detecting the decode directive alone (score 25),
and a combined pattern using a lookahead for the ordinal sequence. Alternatively, implement
a helper function in `aigis/decoders.py` that checks for ordinal ranges and wire it into
a custom scorer rather than a raw regex.
