# Pending: Relay Tampering Attack (RTA) Hardening Guide

## Title
Response-path integrity hardening guide for BYOK agent architectures

## Motivation
The Relay Tampering Attack (arxiv:2605.02187, May 2026) achieves up to **99.1% attack success rate** against aligned LLMs by modifying the generation→execution pathway *after* the LLM produces a safe response but *before* the agent processes it. The core vulnerability is that BYOK (Bring-Your-Own-Key) agent architectures route LLM API responses through third-party proxies or routers with no end-to-end integrity guarantee. An adversary who controls the relay can suppress the model's actual response and substitute a malicious one; the receiving agent trusts it as if it came directly from the model.

This means that **even a perfectly aligned model provides zero protection** — alignment operates at generation time, but RTA operates on the response path. Content-scanning patterns (like aigis's regex rules) are also bypassed: the tampered response never triggers a pattern because the original safe response was replaced with something that looks benign in isolation.

## Which research finding led to this idea
- arxiv:2605.02187 "When Alignment Isn't Enough: Response-Path Attacks on LLM Agents" (May 2026): 99.1% ASR across AgentDojo and ASB benchmarks with six LLMs.
- arxiv:2604.08407 "Your Agent Is Mine" (Apr 2026): empirical evidence that 9 of 428 tested LLM API routers were actively injecting malicious payloads.

## Proposed change
Add `docs/hardening/response-path-integrity.md` documenting:
1. The attack surface: any intermediary (API router, proxy, sidecar) between LLM generation and agent execution.
2. Why alignment and content scanning cannot defend against this attack.
3. Practical mitigations: cryptographic response signing (e.g., provider-signed JWT on each completion), response-path attestation requirements, running models in-process vs. via routers, and how to evaluate third-party LLM routers before deployment.
4. A checklist for teams running BYOK architectures.
5. Links to arxiv:2605.02187 and the router-compromise data from arxiv:2604.08407.

## Why held back
Cannot be addressed by regex-based content scanning — requires documentation, not a rule. Held back from this cycle because:
- The 100 LOC non-test diff limit was already used for the pattern additions.
- This is a documentation-only change that can be done cleanly in a future cycle without competing with implementation work.

## Which constraint blocked it
No blocking constraint (no runtime dependency, no API change) — purely prioritization. Should be done in the next compliance-regulation or incident-postmortems cycle.

## Suggested next step for human reviewer
Assign to the next `compliance-regulation` (index 8) or `incident-postmortems` (index 9) cycle as a documentation hardening guide. The guide text can be self-contained and requires no code changes.
