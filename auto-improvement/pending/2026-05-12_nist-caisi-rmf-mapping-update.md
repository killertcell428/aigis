# Pending: NIST AI RMF Mapping Update (CAISI + NISTIR 8596)

**Title:** Update `docs/compliance/NIST_AI_RMF_MAPPING.md` with NIST CAISI and NISTIR 8596 references

**Motivation:**
NIST launched the AI Agent Standards Initiative (CAISI) on 2026-02-17, the first US government program dedicated to agentic AI interoperability and security standards. NIST also published a draft Cybersecurity Framework Profile for AI (NISTIR 8596, Dec 2025) that maps CSF 2.0 controls to AI-specific threats including prompt injection and data poisoning.

The current `docs/compliance/NIST_AI_RMF_MAPPING.md` references only AI RMF 1.0 (Jan 2023) and NIST AI 600-1 (Jul 2024). It does not mention CAISI, NISTIR 8596, or the CSA Agentic AI NIST RMF Profile (Apr 2026).

**Research finding:** 2026-05-12T00-16_8-compliance-regulation.md (Findings 4 and 5)

**Proposed change:**
- Add a section on NIST CAISI and the planned AI Agent Interoperability Profile (expected Q4 2026)
- Add a reference row for NISTIR 8596 (CSF 2.0 Profile for AI) noting prompt-injection coverage
- Add a note on the CSA Agentic AI NIST RMF Profile and its alignment with aigis's agentic threat models
- Update "Last updated" date

**Why held back:**
The NIST AI Agent Interoperability Profile is expected in Q4 2026. Updating the doc before that profile is published would result in an incomplete reference. It is better to wait so the update covers CAISI, NISTIR 8596, and the Agent Interoperability Profile in a single doc revision.

**Constraint:** No blocking constraint; purely a timing decision.

**Suggested next step:** Revisit after NIST publishes the AI Agent Interoperability Profile (expected Q4 2026). At that point, update NIST_AI_RMF_MAPPING.md to cover all three new references in a single commit.
