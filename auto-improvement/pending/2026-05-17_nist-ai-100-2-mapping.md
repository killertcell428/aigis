# Pending: NIST AI 100-2 E2025 mapping update

**Date:** 2026-05-17
**Domain:** compliance-regulation (cycle 8)
**Research source:** research/2026-05-17T06-06_8-compliance-regulation.md

## Title

Update `docs/compliance/NIST_AI_RMF_MAPPING.md` to reference NIST AI 100-2 E2025

## Motivation

NIST published NIST AI 100-2 E2025 (Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations) on 24 March 2025. This edition adds:
- Indirect prompt injection as a distinct attack class (covering web-page, document, database, tool-output vectors)
- First dedicated section on autonomous AI agent vulnerabilities (tool misuse, memory poisoning)
- Clean-label data poisoning in RAG pipelines

The current `docs/compliance/NIST_AI_RMF_MAPPING.md` references NIST AI RMF 1.0 but does not mention NIST AI 100-2 E2025. aigis's existing `INDIRECT_INJECTION_PATTERNS`, `MEMORY_POISONING_PATTERNS`, and `AGENT_TOOL_ABUSE_PATTERNS` all directly correspond to attack classes named in the 2025 taxonomy, providing a concrete MEASURE/MANAGE alignment that would strengthen the compliance documentation.

## Proposed Change

In `docs/compliance/NIST_AI_RMF_MAPPING.md`:
- Add a reference to NIST AI 100-2 E2025 in the introduction (alongside NIST AI RMF 1.0).
- Add a row or section in the MEASURE table citing indirect prompt injection coverage and its NIST AI 100-2 E2025 attack class.
- Add a row citing agentic AI vulnerability coverage (tool misuse, memory poisoning) and the 2025 taxonomy's agent vulnerability section.
- Note the planned NIST CAISI AI Agent Interoperability Profile (expected Q4 2026) as a pending framework to incorporate.

## Why It Was Held Back

Documentation-only change (no code). Low urgency relative to pattern implementations. The NIST CAISI AI Agent Interoperability Profile, expected Q4 2026, will be the more complete reference for agentic AI; co-authoring the NIST mapping update at that time is more efficient than two incremental updates.

## Constraint Blocking It

- Not a code change; deferred to a future documentation-priority cycle.
- The CAISI profile (Q4 2026) will supersede a partial update done now.

## Suggested Next Step

In a Q4 2026 compliance-regulation cycle, retrieve the published NIST CAISI AI Agent Interoperability Profile and revise `NIST_AI_RMF_MAPPING.md` to cover: (1) NIST AI 100-2 E2025 attack taxonomy alignment, (2) CAISI agent security controls alignment, and (3) NISTIR 8596 (CSF 2.0 Profile for AI) when published.
