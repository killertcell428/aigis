# Pending: AI Framework File/Image Loader SSRF Hardening Guide

**Title:** Hardening guide for AI framework file/image loader SSRF attack class

## Motivation

Three CVEs in Q1 2026 demonstrate a shared attack pattern: AI framework APIs designed to
load files or images for agents can be abused as SSRF or arbitrary-file-read primitives:

- **Chainlit CVE-2026-22218** (CVSS 7.1): custom element file-read → `/proc/self/environ`
- **Chainlit CVE-2026-22219** (CVSS 8.3): element URL fetch → AWS IMDS 169.254.169.254
- **LMDeploy CVE-2026-33626** (CVSS 7.5): `load_image()` used as SSRF probe → IAM credentials
- **LangChain CVE-2026-34070** (CVSS 7.5): `load_prompt()` path traversal → sensitive files

A hardening guide in `docs/hardening/ai-framework-loader-ssrf.md` would document:
1. How loaders become SSRF/file-read primitives
2. Per-framework mitigation steps (Chainlit 2.9.4, langchain-core 1.2.22, LMDeploy 0.12.3)
3. Network-level controls (egress filtering, IMDSv2 enforcement, metadata IP blocking)
4. Input validation patterns aigis can catch vs. what requires infrastructure controls

## Research Finding

`auto-improvement/research/2026-05-12T07-00_9-incident-postmortems.md` — Candidate hardening #3.

## Why Deferred

The 100-LOC non-test limit was fully consumed by the two new detection patterns
(`afe_sensitive_file_read` and `sc_langchain_load_prompt_path`). A meaningful hardening
guide would require ~150–200 LOC of Markdown to cover the four CVEs properly.

## Constraint

> Any single change touching > 100 LOC across non-test files

## Suggested Next Step

Implement in a standalone cycle (low implementation risk — documentation only). Combine with
any pending documentation hardenings to make the cycle worth a release bump.
