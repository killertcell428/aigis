# Pending: Sockpuppetting Deployment Guide

## Title
Documentation hardening guide: Preventing output-prefix injection via API assistant-role prefill

## Motivation
Sockpuppetting (arxiv:2601.13359, Dotsinski & Eustratiadis, Jan 2026) achieves 80%+ higher ASR
than GCG on open-weight models by injecting an affirmative acceptance string ("Sure, here is
how to...") directly into the ASSISTANT role of the multi-turn API, rather than the user
message. The model then continues the fabricated compliant response. This attack:
- Requires no optimization, no gradient access, and is "one line of code"
- Is NOT detectable by a text regex applied to user messages (the user message may be benign)
- Affects any API that supports an `assistant` prefill role (Anthropic, OpenAI-compatible)

## Research finding
- Source: https://arxiv.org/abs/2601.13359
- Paper: "Sockpuppetting: Jailbreaking LLMs Without Optimization Through Output Prefix Injection"
- ASR improvement: up to 80% over GCG on Qwen3-8B (per-prompt), 64% over GCG on Llama-3.1-8B (agnostic)
- Applies to open-weight models and any API supporting prefill/assistant role injection

## Proposed change
A documentation hardening guide at `docs/hardening/sockpuppetting.md` covering:
1. What output-prefix injection is and how the Sockpuppetting attack works
2. Why it bypasses input-side filters (the injection is in the assistant role, not user message)
3. Application-level mitigations:
   - Validate that the `assistant` role in multi-turn payloads originates from the application
   - Do not echo user-supplied "assistant:" fragments into the API request
   - Scan model outputs for suspicious compliance signals ("Sure, here is how to [harmful topic]")
4. Integration guidance for aigis output scanning in two-position guard mode

## Why it was held back
- This is a documentation/guidance change, not a detection regex
- Generating a hardening guide from the API description alone (without testing against a live
  model API) risks inaccuracies in the specific API field names
- The guide would be 30–50 lines of docs, which is safe in LOC terms but needs careful
  verification of API mechanics before publishing

## Constraint that blocked it
- Not a regex-detectable pattern for the specific sockpuppetting vector (API assistant-role)
- The input-side variant (fake "Assistant: Sure..." in user message) is already covered by
  `jb_affirmative_prefill`

## Suggested next step for reviewer
- Verify the API field names for Anthropic and OpenAI-compatible interfaces that enable
  assistant prefill, then implement `docs/hardening/sockpuppetting.md` with a concrete
  aigis output-scan code example.
