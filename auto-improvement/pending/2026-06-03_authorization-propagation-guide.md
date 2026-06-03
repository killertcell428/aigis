# Pending: Authorization Propagation Hardening Guide

## Title
Hardening guide: per-agent credential scoping to prevent authorization propagation failures

## Motivation
Research and incident data from 2026 documents a structural vulnerability distinct from prompt injection: in multi-agent systems, authorization does not automatically propagate correctly between agents even when prompt injection is solved. Key data points:
- 45.6% of enterprises use shared API keys for agent-to-agent authentication (AI Automation Global, 2026)
- OWASP ASI03 ("Identity & Privilege Abuse") and ASI07 ("Insecure inter-agent communication") both address this gap
- Shared credentials eliminate per-agent accountability and prevent scoped revocation

An agent that shares credentials with all peers becomes a blast-radius multiplier: compromising one agent gives the attacker the credentials to impersonate all others.

## Research finding that led to this idea
Cycle 6 (2026-06-03T00-00) research finding 6: "Authorization propagation failures in multi-agent systems" (Adversa AI / OWASP ASI03 / ASI07, 2026).

## Proposed change
Create `docs/hardening/multi-agent-credential-scoping.md` documenting:
1. Why shared API keys create structural risk in multi-agent pipelines
2. Per-agent credential patterns (scoped JWT claims, short-lived tokens, per-agent OAuth clients)
3. How to audit existing deployments with aigis's `AgentTopology` module
4. Recommended architecture patterns for LangGraph, CrewAI, and AutoGen
5. Link to OWASP ASI03 / ASI07 and relevant NIST AI RMF guidance

## Why it was held back
Documentation-only change with no code modification — the value is real but the implementation is straightforward prose rather than a security rule. Better suited to a cycle with lower implementation burden, or combined with a compliance-regulation or incident-postmortems cycle that is focused on documentation.

## Constraint that blocked it
Not a detection rule or hardening to existing code — purely documentation. Lower priority than pattern-based detections in cycles where implementation is feasible.

## Suggested next step for human reviewer
Add to the `docs/hardening/` directory in a compliance-regulation or incident-postmortems cycle. Could also be combined with the OWASP Agentic Top 10 compliance template work.
