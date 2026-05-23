# Pending: Persona/Authority Claim Jailbreak Pattern

## Title
Expert/authority persona claim combined with harmful request detection

## Motivation
Zhang et al. (arxiv:2507.22171, NeurIPS 2025) demonstrate that evolved persona prompts
claiming expert or authority status reduce LLM refusal rates by 50-70% across multiple models.
Examples: claiming to be a licensed physician to request drug dosage bypass, claiming to be a
government official to request classified information, claiming to be a security researcher to
request exploit code. When combined with existing jailbreak methods, persona claims increase
overall ASR by a further 10-20%.

`jb_academic_research_bypass` already covers academic framing + specific harmful content.
The gap is non-academic authority claims (medical, legal, government, law enforcement).

## Research finding that led to this idea
`auto-improvement/research/2026-05-23T00-22_3-jailbreak-extraction.md` — finding 3 (Persona prompts).

## Proposed change
Add `jb_authority_persona_bypass` pattern:

```python
DetectionPattern(
    id="jb_authority_persona_bypass",
    pattern=_p(
        r"(?:I\s+am|I'm|as)\s+a(?:n)?\s+"
        r"(?:licensed\s+)?(?:doctor|physician|nurse|pharmacist|chemist|"
        r"law\s+enforcement|police\s+officer|fbi\s+agent|government\s+official|"
        r"military\s+officer|intelligence\s+analyst|security\s+researcher|"
        r"penetration\s+tester|ethical\s+hacker|ciso|attorney|lawyer)"
        r"[\s\S]{0,300}?"
        r"(?:methamphetamine|fentanyl|heroin|ricin|anthrax|nerve\s+agent|sarin|"
        r"chemical\s+weapon|biological\s+weapon|explosive|bomb|ransomware|"
        r"shellcode|0[\s-]?day|hack\s+into|malware|backdoor|keylogger)"
    ),
    base_score=60,
)
```

## Why it was held back
High false-positive risk. Legitimate security professionals, medical educators, and law
enforcement training materials frequently use these exact authority claims in real contexts.
The pattern anchors on harmful content keywords, but the authority claim alone without
those keywords is not useful, and the keyword list would need careful expansion to cover
real attack scenarios without over-triggering on legitimate professional discussions.

Additionally, the evolved persona prompts in the research (arxiv:2507.22171) use automatically
optimized language that may not match the natural-language authority claims above.

## Which constraint blocked it
Principally: false-positive risk judged too high for this cycle without further calibration.

## Suggested next step for the human reviewer
1. Collect a corpus of real authority-claim jailbreak attempts from red-teaming exercises.
2. Measure the false-positive rate of the proposed pattern against a representative sample of
   legitimate professional LLM usage (medical Q&A, security training, legal research).
3. Consider restricting the pattern to authority claim + specific controlled-substance or
   weapon synthesis keywords (tighter than the proposed list), then test empirically.
4. Alternatively, integrate persona detection as a soft signal (score booster) that raises the
   baseline score when combined with other jailbreak rule hits.
