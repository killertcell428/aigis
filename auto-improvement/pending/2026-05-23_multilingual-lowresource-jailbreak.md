# Pending: Multilingual Low-Resource Language Multi-Turn Jailbreak

## Title
Cross-turn detection for multilingual low-resource language jailbreaks

## Motivation
arxiv:2605.18239 (May 2026) demonstrated that multi-turn conversations using low-resource
African languages (Afrikaans, Kiswahili, isiXhosa, isiZulu) achieve 52–84% harmful-response
rates across major LLMs (Claude 3.5 Haiku: 52.7%, GPT-4o-mini: 83.6%). Single-turn translation
attacks are ineffective; the jailbreak requires multi-turn escalation where the first turn
establishes context in the low-resource language and subsequent turns escalate.

## Research finding
Source: https://arxiv.org/abs/2605.18239

Human red-teamers achieved average jailbreak rates of 75.8% vs 59.8% for automated methods,
suggesting the attack is adaptive and conversational. Claude showed the most robustness among
tested models.

## Proposed change
Add a cross-session / cross-turn correlation signal in `aigis/cross_session/` or
`aigis/monitor/` that flags conversations that:
1. Begin with content in a script/language detected as a low-resource language (not English,
   not a common high-resource language).
2. Contain embedded questions or requests that, if translated, would match existing aigis
   harmful-content patterns.

## Why held back
**Constraint: single-turn regex filter cannot detect this attack.** The individual turns
are benign in isolation. Detecting this requires either:
- A language-identification step (not a regex problem)
- Cross-turn context accumulation
- Or translation of the input before scanning

Both language-ID and translation would add runtime dependencies (violating the zero-runtime-
dependency constraint).

## Which constraint blocked it
Hard constraint: "zero-runtime-dependency, rule-based Python firewall" — no calling an LLM
or third-party API at runtime. Language identification without a model is unreliable.

## Suggested next step for human reviewer
Consider adding an optional `detect_language` pre-processing hook (opt-in, behind a flag)
that uses a lightweight rule-based language detector (e.g., `langdetect` as an optional
dev dependency) to flag inputs in unusual scripts/languages for heightened scrutiny. This
would not violate the zero-dependency constraint if kept strictly optional.
