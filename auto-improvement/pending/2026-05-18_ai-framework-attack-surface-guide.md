# Pending: AI Framework Attack Surface Minimization Hardening Guide

## Title

Hardening guide for AI framework attack surface minimization (network isolation, authentication,
and CVE monitoring for Langflow, PraisonAI, LMDeploy, Chainlit).

## Motivation

The Q1–Q2 2026 incident record shows a consistent pattern: AI framework CVEs are being exploited
within hours to days of advisory publication (Langflow: 20h, LMDeploy: 12.5h, PraisonAI: 3.75h).
Three separate CVEs involved unauthenticated or insufficiently protected endpoints in AI frameworks
that developers run in production without reading the security guidance.

A hardening guide at `docs/hardening/ai-framework-attack-surface.md` would document:
- Which endpoints to never expose to the internet (Langflow `/build_public_tmp/`, PraisonAI
  `/chat` and `/agents`, LMDeploy `/generate`)
- Authentication requirements for AI framework API servers
- Network isolation patterns (reverse proxy, firewall rules, VPC-only access)
- Monitoring for CVE-Detector-style automated scanning (distinguish from legitimate traffic)
- Framework-specific upgrade guidance for the documented CVEs

## Research Finding

Derived from: `auto-improvement/research/2026-05-18T03-06_9-incident-postmortems.md`

Key sources:
- CVE-2026-33017 Langflow RCE (Sysdig, March 2026)
- CVE-2026-44338 PraisonAI auth bypass (Sysdig, May 2026)
- CVE-2026-33626 LMDeploy SSRF (Sysdig, April 2026)
- Chainlit CVE-2026-22218/22219 (Kodem, January 2026)

## Proposed Change

New file: `docs/hardening/ai-framework-attack-surface.md`
~200 LOC markdown. No code changes.

## Why It Was Held Back

The two new patterns (`sc_langflow_build_exec`, `sc_ai_framework_auth_disabled`) plus the 24 test
cases together already use most of the available per-cycle budget, and a documentation-only addition
would be better scoped to a docs-focused cycle where it can be written properly without competing
with pattern additions.

## Blocking Constraint

Step 5 rule: "Keep total non-test diff ≤ 100 LOC." The two patterns + tests already account for
~100 LOC; adding a 200-LOC markdown file would exceed the limit.

(Note: markdown files are non-test files for the purposes of this constraint, per the rule "Keep
total non-test diff ≤ 100 LOC." Documentation changes count.)

## Suggested Next Step

Assign to a future docs-domain cycle or a dedicated documentation cycle. The content is largely
written in the research file; converting to a polished guide is the main task.
