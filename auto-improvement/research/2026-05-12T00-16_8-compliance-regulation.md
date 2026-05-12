# Research: compliance-regulation (index 8)

**Domain:** compliance-regulation
**Cycle index:** 8 (second pass)
**Cycle UTC:** 2026-05-12T00-16

---

## Findings

- **EU AI Act GPAI Code of Practice — final version published (2025-07-10)**
  The European AI Office published the final General-Purpose AI (GPAI) Code of Practice on 10 July 2025. The code covers three chapters: Transparency (all GPAI providers), Copyright (all GPAI providers), and Safety & Security (systemic-risk providers only, ≥10²⁵ FLOPs). Voluntary adherence creates a presumption of compliance with Art. 53-55 obligations. The Commission's enforcement powers (fines up to €15M or 3% of global turnover) activate on **2026-08-02**.
  Source: <https://www.lw.com/en/insights/eu-ai-act-gpai-model-obligations-in-force-and-final-gpai-code-of-practice-in-place>
  **aigis impact:** aigis has an `eu_ai_act_high_risk.yaml` template for Annex III deployers, but no template for GPAI *providers* (Art. 53-55). This is a coverage gap that can be closed with a new `gpai_provider.yaml` template.

- **EU AI Act Art. 53 — mandatory training data summary (in force 2025-08-02)**
  All GPAI providers must publish a training data summary using an official EU template. The summary must cover datasets, compute, energy, licensing, and copyright compliance. Data collected via web crawling must respect machine-readable copyright signals (robots.txt, TDM opt-out). A designated contact point for copyright holder complaints is required.
  Source: <https://www.mayerbrown.com/en/insights/publications/2025/08/eu-ai-act-news-rules-on-general-purpose-ai-start-applying-guidelines-and-template-for-summary-of-training-data-finalized>
  **aigis impact:** Instructions to hide training data sources, skip documentation, or bypass TDM opt-outs are directly non-compliant under Art. 53 and can be detected by a GPAI provider policy template.

- **EU AI Act Art. 55 — adversarial testing mandate for systemic-risk GPAI (enforcement from 2026-08-02)**
  Providers of models above the 10²⁵-FLOP threshold must conduct and document adversarial testing ("red-teaming") as part of model evaluation, report serious incidents to the AI Office, and implement cybersecurity measures. Prompt-level instructions to skip evaluation, underreport FLOPs, or suppress incident reporting are compliance violations.
  Source: <https://artificialintelligenceact.eu/article/55/>
  **aigis impact:** Direct candidate for custom rules in a GPAI provider policy template: model evaluation bypass, systemic risk concealment, and incident suppression detection.

- **NIST CAISI — AI Agent Standards Initiative launched (2026-02-17)**
  NIST's Center for AI Standards and Innovation formally launched the AI Agent Standards Initiative, the first US government program dedicated to interoperability and security standards for agentic AI systems. An AI Agent Interoperability Profile is planned for Q4 2026. NIST is also preparing NISTIR 8596, a Cybersecurity Framework (CSF 2.0) Profile for AI, covering AI-specific threats including prompt injection and data poisoning.
  Source: <https://labs.cloudsecurityalliance.org/research/csa-research-note-nist-caisi-ai-agent-standards-compliance-2/>
  **aigis impact:** NIST AI RMF mapping doc should reference the CAISI initiative and NISTIR 8596 when updated. Low urgency for this cycle; track for cycle 18.

- **CSA Agentic AI NIST RMF Profile published (2026-04-29)**
  The Cloud Security Alliance published a NIST AI RMF Agentic Profile, mapping agentic AI security controls to the four RMF functions (Govern, Map, Measure, Manage). The profile is aligned with EU AI Act, ISO/IEC 42001, and addresses principal-agent trust chains, memory poisoning, and tool abuse.
  Source: <https://cloudsecurityalliance.org/press-releases/2026/04/29/csai-foundation-announces-key-milestones-to-secure-the-agentic-control-plane>
  **aigis impact:** aigis's existing NIST_AI_RMF_MAPPING.md could be updated to reference the CSA Agentic Profile and mark agentic-specific controls (memory poisoning, tool abuse) as covered. Medium priority; deferred to a documentation-only cycle.

- **ISO/IEC 42001 — Fortune 500 vendor requirements expanding (2026)**
  Fortune 500 companies are now requiring vendors to be certified or show a roadmap for ISO/IEC 42001:2023 (AI Management System Standard). The standard is increasingly referenced in procurement due-diligence alongside EU AI Act Art. 17 (quality management systems for high-risk AI). The EN adaptation (EN ISO/IEC 42001:2026) was published by CEN in early 2026.
  Source: <https://enactia.com/iso-42001-certification-the-2026-roadmap-for-ai-governance/>
  **aigis impact:** A CSA STAR / ISO 42001 self-assessment mapping doc could be added under `docs/compliance/`. Low urgency; deferred.

- **EU AI Act Digital Omnibus formal adoption expected by 2026-08-02**
  The provisional political agreement reached on 2026-05-07 must still receive formal endorsement from the European Parliament and Council. Both institutions are targeting formal adoption before the 2026-08-02 enforcement milestone for Annex III systems. The agreement remains politically binding in the interim.
  Source: <https://www.hoganlovells.com/en/publications/eu-legislators-agree-to-delay-for-highrisk-ai-rules>
  **aigis impact:** The `eu_ai_act_high_risk.yaml` deadline comments remain correct per the previous cycle's update. No further changes needed for this cycle.

- **UK AI Security Institute — principles-based approach (no statute as of 2026-04)**
  The UK has not enacted standalone AI legislation. DSIT's five cross-sector principles (safety/security/robustness, transparency, fairness, accountability, contestability) apply via existing sectoral regulators. The AI Security Institute operates as a risk-monitoring body. A statutory basis for AISI is under consultation but no commencement timetable has been published.
  Source: <https://www.whitecase.com/insight-our-thinking/ai-watch-global-regulatory-tracker-united-kingdom>
  **aigis impact:** No aigis policy template warranted for UK AI regulation at this stage; the existing framework is too principles-based and fragmented for rule-based detection. Track for 2027 if statute is enacted.

---

## Candidate Hardenings

1. **[IMPLEMENTED] New `policy_templates/gpai_provider.yaml` template** — Covers EU AI Act Art. 53-55 obligations for GPAI providers. Five custom rules detect: model evaluation bypass, systemic risk concealment (FLOPs), training data documentation bypass, incident reporting suppression, and copyright circumvention in training data collection. Score deltas 50–70. Enables GPAI-provider deployments to catch prompt-level compliance violations.

2. **[PENDING] Update `docs/compliance/NIST_AI_RMF_MAPPING.md`** — Add reference to NIST CAISI initiative, NISTIR 8596, and CSA Agentic Profile. Documentation-only; low urgency. Deferred to allow the NIST AI Agent Interoperability Profile (Q4 2026) to inform the update.

3. **[PENDING] Add ISO/IEC 42001 self-assessment mapping doc** — Create `docs/compliance/ISO_42001_MAPPING.md` mapping aigis capabilities to ISO 42001 controls. Medium effort; deferred until ISO/IEC 27090 (the AI cybersecurity standard) is formally published in H2 2026 so the two docs can be co-written.

4. **[PENDING] UK AI Security Institute template** — Principles-based regulation with no statutory basis yet; too early for a rule-based policy template. Revisit when UK AI legislation is enacted (no commencement date as of 2026-04).
