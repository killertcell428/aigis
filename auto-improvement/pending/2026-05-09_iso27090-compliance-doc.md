# Pending: ISO/IEC 27090 AI Cybersecurity Compliance Guide

## Title
New doc: `docs/compliance/ISO_27090_COVERAGE.md`

## Motivation
ISO/IEC 27090 "Cybersecurity — Artificial Intelligence — Guidance for addressing security threats to artificial intelligence systems" reached FDIS (Final Draft International Standard) status in February 2026 and is expected to be published H2 2026. The standard extends the ISO 27000 family to cover AI-specific attack surfaces: adversarial machine learning, data poisoning, model theft, and privacy attacks. Adding a coverage map (analogous to `OWASP_LLM_TOP10_COVERAGE.md` and `NIST_AI_RMF_MAPPING.md`) would help organizations using ISO 27001 + aigis demonstrate AI security compliance.

Research source: <https://www.iso.org/standard/56581.html>

## Proposed Change
Create `docs/compliance/ISO_27090_COVERAGE.md` mapping aigis detection capabilities to ISO 27090 threat categories:
- Adversarial examples → prompt injection, evasion-obfuscation patterns
- Data poisoning → RAG context filter, memory poisoning patterns
- Model inversion / extraction → system prompt leak patterns
- Privacy attacks → PII detection patterns, output filter

## Why Held Back
ISO 27090 is at FDIS stage and has not been formally published. The final threat taxonomy and control recommendations may change between FDIS and final publication. Creating a mapping doc now would require substantial revision upon publication.

**Constraint:** Source material not yet finalized (FDIS, not published standard).

## Suggested Next Step
Monitor ISO publication feeds for ISO/IEC 27090 final publication (expected H2 2026). Upon publication, create the coverage map using the finalized threat categories.
