# Pending: Control-Plane Structured-Output Jailbreak Defense

## Title
Hardening guide / infrastructure-level defense for JSON Schema enum and grammar-level jailbreaks

## Motivation
Arxiv:2503.24191 (Mar 2025) and BreakFun (arxiv:2510.17904) document attacks that embed harmful
intent inside JSON Schema enum constraints or grammar rules (control-plane), while keeping the
prompt text benign (data-plane). DictAttack achieves 94–99% ASR on GPT-5, Gemini 2.5 Pro,
DeepSeek-R1, and gpt-oss-120b. The attack bypasses regex-based safety checks because the
malicious content is encoded in the schema structure, not in the prompt string.

## Research Finding
`auto-improvement/research/2026-05-13T08-30_3-jailbreak-extraction.md`

Sources:
- https://arxiv.org/abs/2503.24191
- https://arxiv.org/abs/2510.17904

## Proposed Change
Write `docs/hardening/structured-output-jailbreak.md` explaining:
1. What control-plane jailbreaks are and why they bypass prompt-level detection.
2. How to audit JSON Schema enum values and grammar rules before passing them to constrained decoding.
3. Recommended mitigations: schema validation, enum value content screening, operator allowlisting.
4. How aigis's existing filters complement (but cannot fully replace) schema-level auditing.

## Why Held Back
- Documentation-only; no new code pattern needed.
- The attack is at the API/infrastructure layer, not the prompt layer.
- A compliance or docs cycle is a better fit.

## Suggested Next Step
Pick up in a future compliance-regulation or incident-postmortems cycle as a hardening guide.
