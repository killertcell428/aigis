# Pending: LoRA Adapter Safety Documentation Guide

**Cycle:** 5 (second pass) · **Domain:** supply-chain-llm · **UTC:** 2026-05-11T00-00

---

## Title

`docs/lora-adapter-safety.md` — Hardening guide for loading third-party LoRA adapters

## Motivation

arxiv:2602.21977 (MasqLoRA, Feb 2026) demonstrated backdoored LoRA/QLoRA adapters
achieving 99.8% attack success rate. The adapters behave normally on non-trigger
inputs and only activate on specific trigger phrases, making automated static
detection near-impossible. A 156% surge in supply chain attacks (2025 vs 2024)
is partly attributed to Hugging Face adapter marketplaces where any account can
publish. The dev.to writeup and OpenReview paper "Attack on LLMs: LoRA Once,
Backdoor Everywhere" document concrete attack methodologies.

Sources:
- https://arxiv.org/abs/2602.21977 (MasqLoRA)
- https://dev.to/cyberpath/supply-chain-attacks-on-ai-models-how-attackers-inject-backdoors-through-poisoned-lora-adapters-1eb

## Proposed change

Add `docs/lora-adapter-safety.md` covering:
1. What a LoRA adapter backdoor is and how MasqLoRA activates.
2. Pre-load verification checklist (account age, model card completeness,
   download count, community reports).
3. Runtime sandboxing (load adapter in isolated process; test with canary inputs).
4. Weight-magnitude anomaly detection (high-magnitude sparse perturbations are a
   known backdoor signature).
5. Trusted adapter registries vs. arbitrary Hugging Face uploads.
6. Recommended tool: `lm-evaluation-harness` for behavioral validation before
   deploying in production.

## Why held back

**Constraint: documentation-only changes do not block production traffic and are
lower urgency than rule-based detectors.** No regex rule is viable for this attack
class — the backdoor is behavioral, not syntactic. The doc would be valuable but
is best paired with a behavioral test recommendation rather than shipped alone.

## Suggested next step

- Write the guide when the multi-agent or evasion-obfuscation domain is in scope
  (adapter backdoors span both).
- Cross-reference the existing `sc_pickle_unsafe_model_load` rule which covers the
  physical load-time risk; this guide covers the post-load behavioral risk.
- Consider adding a compliance template entry for "third-party adapter provenance
  verification" under `policy_templates/`.
