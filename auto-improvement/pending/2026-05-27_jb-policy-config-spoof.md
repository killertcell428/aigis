# Pending: Policy Puppetry / Config-Format Safety Spoofing (`jb_policy_config_spoof`)

**Date:** 2026-05-27
**Research basis:** `auto-improvement/research/2026-05-27T03-12_3-jailbreak-extraction.md`

## Title
XML/JSON/INI policy-configuration format with safety-disabling semantics

## Motivation
Policy Puppetry (HiddenLayer Research, April 2025) wraps harmful instructions inside blocks
that mimic internal policy configuration files — XML, JSON, or INI-style — with semantics that
"disable" safety: `<safety_filter>disabled</safety_filter>`, `"restrictions":[]`,
`"safety_mode":"off"`, `[policy]\nsafety=disabled`. Models trained on policy/configuration
data interpret these structured formats as authoritative system-level directives rather than
user text. Achieved up to 90% ASR across GPT-4, Claude 3, Gemini 1.5, Mistral, and Llama 3.

## Research Finding
Source: https://hiddenlayer.com/research/novel-universal-bypass-for-all-major-llms

## Proposed Change
Add `jb_policy_config_spoof` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_policy_config_spoof",
    name="Policy Config Format Safety Spoofing (Policy Puppetry)",
    category="jailbreak",
    pattern=_p(
        r"<\s*(?:system_policy|safety_filter|content_policy|safety_mode|restrictions?|"
        r"allow_content|override_policy|policy_override)\s*>"
        r"|"
        r"[\"'](?:safety_filter|safety_mode|restrictions|content_policy|"
        r"allow_content|policy)\s*[\"']\s*:\s*"
        r"(?:[\"']?\s*(?:disabled?|off|false|none|0|all|unrestricted|enabled?)\s*[\"']?"
        r"|\s*\[\s*\])"
        r"|"
        r"\[(?:policy|safety|override|system)\]\s*\n\s*"
        r"(?:safety|restrictions?|filter|content_policy)\s*=\s*"
        r"(?:disabled?|off|false|none|0|all|unrestricted)"
    ),
    base_score=70,
    description=(
        "Policy Puppetry: the input contains XML tags, JSON keys, or INI directives that "
        "mimic internal policy configuration with safety-disabling values. HiddenLayer "
        "(April 2025) demonstrated up to 90% ASR across all major LLMs by exploiting "
        "models' tendency to treat configuration-format text as authoritative system "
        "directives rather than user input."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Configuration-format blocks in user input that set safety flags to disabled/off/none "
        "are a policy-spoofing attack. User input is never authoritative for policy configuration; "
        "reject inputs containing structured safety-directive blocks regardless of their values."
    ),
),
```

## Why Held Back
LOC budget (100 LOC non-test) was used by `jb_payload_splitting` and `jb_translation_extraction`
in this cycle.

## Constraint
LOC budget exhausted this cycle.

## Suggested Next Step
Implement in the next `jailbreak-extraction` cycle. The XML tag variant and JSON variant may
warrant separate rules for clarity.
