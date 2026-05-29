# Pending: Policy Puppetry Detection (`jb_policy_puppetry`)

## Title
Policy Puppetry — Fake Configuration File Injection

## Motivation
HiddenLayer disclosed Policy Puppetry in April 2025: prompts that mimic XML/INI/JSON
configuration files (e.g., `[SystemPolicy] allowUnsafeOperations=true`) trick LLMs
into treating malicious instructions as legitimate policy directives. Tested against
GPT-4, Claude 3, Gemini 1.5, Mistral, and LLaMA 3 with no model-specific tuning.

## Research finding that led to this idea
Research file: `research/2026-05-29T06-10_3-jailbreak-extraction.md`
Source: https://www.securityweek.com/all-major-gen-ai-models-vulnerable-to-policy-puppetry-prompt-injection-attack/

## Proposed change
Add `jb_policy_puppetry` to `JAILBREAK_ROLEPLAY_PATTERNS` in
`aigis/filters/patterns.py` with score 70:

```python
DetectionPattern(
    id="jb_policy_puppetry",
    name="Policy Puppetry — Fake Configuration File Injection",
    category="jailbreak",
    pattern=_p(
        r"(?:"
        r"\[(?:System|Safety|Content|Policy|LLM|AI|Model|Override|Behavior)"
        r"(?:Policy|Config|Setting|Override|Mode|Filter|Rule|Directive)\]|"
        r"<(?:safety|content|policy|override|system)[-_]?"
        r"(?:config(?:uration)?|policy|override|rule|filter|mode|bypass)s?\s*/?>|"
        r"(?:allowUnsafe(?:Operations?)?|safety[_-]?(?:Enabled|Mode|Level)|"
        r"content[_-]?(?:Filter|Policy)|harm[_-]?(?:Filter|Check)|"
        r"guardrails?[_-]?(?:Enabled|Active)|policy[_-]?(?:Override|Bypass)|"
        r"restrictions?[_-]?(?:Enabled|Level))\s*[=:]\s*"
        r"(?:false|0|off|none|disabled?|bypassed?|allow|all|unrestricted|override)"
        r")"
    ),
    base_score=70,
    ...
)
```

## Why it was held back
The 100 LOC non-test diff limit was reached during this cycle after implementing
the three highest-priority patterns.

## Which constraint blocked it
Hard constraint: "Keep total non-test diff ≤ 100 LOC."

## Suggested next step for human reviewer
Implement in the next jailbreak-extraction cycle. Before implementing, test the
pattern against common legitimacy contexts:
- CI/CD configuration files (YAML/JSON)
- Application config objects (JSON with "safeMode: false" for non-AI safety)
- Security testing frameworks that use similar field names

The key challenge is distinguishing AI-safety field names from general software
configuration. Consider requiring at least 2 matches (e.g., both the INI header
AND a key=value pair) to reduce false positives.
