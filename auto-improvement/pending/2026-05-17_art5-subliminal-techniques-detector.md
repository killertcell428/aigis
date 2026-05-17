# Pending: EU AI Act Art. 5(1)(a) Subliminal Techniques Compliance Detector

## Title
New pattern: `comp_subliminal_technique_request` — EU AI Act Art. 5(1)(a) subliminal/deceptive manipulation prohibition

## Motivation
EU AI Act Art. 5(1)(a) prohibits AI systems that deploy subliminal techniques operating below conscious awareness, or purposefully manipulative/deceptive techniques, to materially distort behaviour in ways likely to cause harm. EC Commission guidelines (Feb 2025) define "subliminal" as techniques that operate below the threshold of conscious perception — covert priming, hidden audio, below-threshold visual stimuli, neurological state manipulation. This is a distinct prohibited practice from the vulnerable-group exploitation covered by Art. 5(1)(b).

## Research finding that led to this idea
`auto-improvement/research/2026-05-17T09-15_8-compliance-regulation.md` — Finding 4 (Art. 5(1)(a) subliminal techniques prohibition).

## Proposed change
Add `comp_subliminal_technique_request` to `COMPLIANCE_TRANSPARENCY_PATTERNS`:
- Pattern should target explicit requests to embed covert, below-conscious-threshold stimuli in AI output (e.g. "embed subliminal messages", "use covert priming", "hidden visual triggers")
- Distinct from jailbreak prompts that instruct the AI to bypass safety; instead targets requests to build AI that covertly manipulates end users

## Why it was held back
The evasion/encoding detectors already cover the main attack vectors where AI-generated content uses hidden channels (zero-width characters, encoding bypass, homoglyphs) to covertly influence model behaviour. A separate `comp_subliminal_technique_request` at the compliance layer would catch a very narrow additional set of explicit requests with high risk of false positives against the encoding bypass patterns if the same text triggers both. The marginal coverage gain does not justify the false-positive risk in this cycle.

## Which constraint blocked it
Overlap risk with existing `ENCODING_BYPASS_PATTERNS` and concern about false positives. The compliance angle is valid but needs careful pattern design to avoid double-firing with evasion detectors.

## Suggested next step for human reviewer
When implementing, restrict the pattern to requests that explicitly reference manipulating human users via below-threshold stimuli (distinct from attacking the AI model itself). Consider a negative lookahead to avoid double-firing with the existing `enc_*` pattern family. The pattern should focus on end-user manipulation intent rather than AI evasion techniques.
