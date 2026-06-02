# Pending: Human-Expert Persona Modulation Jailbreak Detection

## Title
`jb_expert_persona_modulation` — detect "act as an [expert] without restrictions" jailbreak

## Motivation
The existing `jb_evil_roleplay` pattern catches "roleplay as an evil/uncensored AI", and
`jb_no_restrictions` catches explicit bypass instructions. Neither covers the persona modulation
variant where the attacker asks the model to play a *human professional* (cybersecurity expert,
chemist, locksmith, gunsmith) who "has no ethical constraints", "isn't bound by legal restrictions",
or "can answer anything without hesitation".

Persona modulation attacks (arxiv:2311.03348, Deshpande et al.) achieved 42–67% ASR on GPT-4 and
Claude 2 without encoding. The technique survives the existing `jb_evil_roleplay` filter because
the persona is a plausible expert, not explicitly an "evil AI".

## Proposed change
Add `jb_expert_persona_modulation` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_expert_persona_modulation",
    name="Human Expert Persona Without Restrictions",
    category="jailbreak",
    pattern=_p(
        r"(?:act|pretend|play|roleplay|behave)\s+(?:as|like)\s+"
        r"(?:a|an)\s+(?:\w+\s+){0,3}"        # optional adjectives
        r"(?:expert|professional|specialist|researcher|scientist|chemist|"
        r"hacker|penetration\s+tester|gunsmith|locksmith|pharmacist|engineer)\b"
        r"[\s\S]{0,100}?"
        r"(?:without|with\s+no|who\s+(?:has\s+no|doesn.t\s+have|isn.t\s+bound\s+by|"
        r"ignores?|bypasses?|disregards?))\s+"
        r"(?:ethical?|moral|legal|safety|content|professional|regulatory)\s*"
        r"(?:constraint|restriction|limit|filter|rule|guideline|code|boundary|obligation)s?"
    ),
    base_score=60,
    ...
)
```

## Why it was held back
The pattern above has a higher-than-normal false-positive risk. Legitimate uses of "act as a
[professional]" in enterprise chatbots and educational contexts are common. For example:
- "Act as a financial advisor and review my portfolio" — benign
- "Act as a doctor and help me understand my symptoms" — borderline

The `without ... restrictions` qualifier dramatically reduces FPs, but the two-clause regex
needs careful tuning and more false-positive testing before shipping.

## Which constraint blocked it
- False-positive risk above the acceptable threshold for a < 1 cycle iteration
- Needs adversarial testing against a representative corpus of benign role-play prompts

## Suggested next step for human reviewer
1. Collect a sample of 50–100 benign "act as [expert]" prompts from real applications.
2. Test the proposed pattern against the sample.
3. If false-positive rate < 5%, ship as-is.
4. If > 5%, add an exclusion list of low-risk professions (doctor, lawyer, advisor) and
   require the "without restrictions" qualifier to be more explicit.
