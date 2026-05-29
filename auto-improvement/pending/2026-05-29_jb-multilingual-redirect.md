# Pending: Multilingual Low-Resource Language Redirect Jailbreak (`jb_multilingual_redirect`)

**Date:** 2026-05-29
**Research basis:** Research file `2026-05-29T00-00_3-jailbreak-extraction.md`
**Source:** arxiv:2605.18239 — Multilingual jailbreaking of LLMs using low-resource languages (May 2026)

---

## Title

Multilingual low-resource language redirect jailbreak detection

## Motivation

Asking the model to respond in a low-resource language (Afrikaans, isiZulu, Kiswahili, isiXhosa)
combined with a harmful request achieves 52–84% ASR across ChatGPT, Claude, DeepSeek, Gemini, and
Grok. Safety training is English-dominant; the model's refusal circuits fire less reliably when the
output language is low-resource. The detectable signal is an explicit directive: "respond entirely
in [language]" or "answer in Afrikaans" near a harmful topic in the same message.

## Proposed Change

Add `jb_multilingual_redirect` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
DetectionPattern(
    id="jb_multilingual_redirect",
    name="Multilingual Low-Resource Language Redirect Jailbreak",
    category="jailbreak",
    pattern=_p(
        r"(?:respond|answer|reply|write|explain|describe|tell me)\s+"
        r"(?:entirely\s+|completely\s+|fully\s+|only\s+)?in\s+"
        r"(?:afrikaans|isizulu|kiswahili|isixhosa|swahili|zulu|xhosa|"
        r"hausa|yoruba|igbo|amharic|somali|malagasy|sesotho|setswana|"
        r"shona|ndebele|tigrinya|twi|ewe|fula|wolof|lingala|kinyarwanda|"
        r"luganda|chichewa|bemba|tshivenda|siswati)\b"
    ),
    base_score=40,
    description=(
        "Multilingual redirect jailbreak: the user explicitly requests the model to respond "
        "in a named low-resource language in an attempt to bypass safety training that is "
        "predominantly English-based. arxiv:2605.18239 (May 2026) measured 52–84% ASR "
        "across five frontier models (ChatGPT, Claude, DeepSeek, Gemini, Grok). Claude showed "
        "the highest resistance (~52%) while DeepSeek and GPT-4o-mini were most vulnerable "
        "(>70%). This rule targets explicit language-redirect directives only — pure "
        "multilingual conversation without a redirect instruction is not flagged."
    ),
    owasp_ref="OWASP LLM01: Prompt Injection",
    remediation_hint=(
        "Explicit low-resource language redirect requests are a jailbreak signal. "
        "Apply uniform safety evaluation regardless of the requested output language. "
        "Do not reduce safety review stringency for low-resource language outputs."
    ),
)
```

## Why It Was Held Back

- **LOC budget:** The three patterns implemented this cycle consumed 94 of the 100 non-test LOC
  budget. Adding a fourth pattern would exceed the single-cycle limit.
- **Language list curation:** The language name list needs careful curation and validation to
  minimize false positives on legitimate multilingual content requests (e.g., language learning
  applications). The initial list covers the highest-ASR languages from arxiv:2605.18239 but
  should be reviewed by a native-speaker or linguistics expert before shipping.

## Suggested Next Step

Implement in the next `jailbreak-extraction` cycle (NEXT_INDEX=3 returns in ~5 cycles). Validate
the language name list against the false-positive test suite; consider raising base_score to 50
if co-occurring harmful keywords are detected in the same message.
