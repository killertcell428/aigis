# Research: compliance-regulation (index 8)

**Domain:** compliance-regulation
**Cycle index:** 8
**Cycle UTC:** 2026-05-17T03-10

---

## Previous coverage (cycles 8 at 2026-05-09T05-00 and 2026-05-12T00-55)

- EU AI Act Digital Omnibus deadline changes (Annex III to Dec 2027, Annex I to Aug 2028)
- EU AI Act Art. 5 Omnibus additions: NCII/nudification ban (→ `synth_ncii_request`)
- EU AI Act Art. 5(1)(c): Social scoring prohibition (→ `comp_social_scoring_request`)
- EU AI Act Art. 52: AI identity/transparency (→ `comp_ai_identity_denial`)
- US state chatbot disclosure laws (CA, WA, NE, OR)
- US CHATBOT Act (federal proposal, March 2026)
- NIST AI 600-1 GenAI Profile, NIST AI RMF critical infrastructure profile (concept only)
- ISO/IEC 27090 (FDIS stage), ISO/IEC 42001:2026 EN adaptation

## New angle for this cycle

EU AI Act Art. 5 **remaining** prohibited practices (emotion recognition, biometric categorization),
fresh regulatory material from CISA Five Eyes agentic AI guidance, FTC enforcement,
GPAI Code of Practice enforcement deadline, and Canada post-AIDA landscape.

---

## Findings

- **EU AI Act Art. 5(1)(f): Emotion recognition in workplaces/education is prohibited (since Feb 2025)**
  AI systems that infer the emotions of natural persons in workplace or educational institution
  settings are a prohibited practice under EU AI Act Art. 5(1)(f) since 2025-02-02. This applies
  regardless of employee or student consent; the employer or institution cannot legitimately
  authorise the deployment. EC expert studies published May 2026 confirmed full scope,
  including real-time video, audio, and physiological-signal emotion inference targeting employees
  or students. Maximum fine: EUR 35M or 7% of global annual turnover.
  Source: <https://artificialintelligenceact.eu/article/5/>
  **aigis impact:** No prior pattern covered this prohibited practice. New `comp_emotion_recognition_workplace`
  pattern detects requests to build or deploy workplace/education emotion monitoring systems.

- **EU AI Act Art. 5(1)(g): Biometric categorization by sensitive attributes is prohibited (since Feb 2025)**
  AI systems that use biometric data to categorize or infer sensitive attributes — race, ethnic
  origin, political opinions, religious beliefs, trade union membership, sexual orientation, or
  health data — are prohibited since 2025-02-02. EC expert studies (May 2026) clarified scope:
  the prohibition covers any system that deduces these attributes from biometric signals, whether
  or not the system is accurate. Biometric authentication/identity verification is permitted.
  Maximum fine: EUR 35M or 7% of global annual turnover.
  Source: <https://artificialintelligenceact.eu/article/5/>
  **aigis impact:** New `comp_biometric_categorization` pattern detects requests to infer sensitive
  attributes (race, political opinion, religion, sexual orientation, health) from biometric features.

- **CISA/NSA/Five Eyes: "Careful Adoption of Agentic AI Services" (April 30, 2026)**
  CISA, NSA, and four Five Eyes partners jointly published the first international guidance
  specifically for agentic AI systems. The guidance identifies five risk categories: privilege
  escalation, design/configuration flaws, behavioral misalignment, structural risk (cascading
  failures in multi-agent networks), and accountability gaps. Core recommendations include
  cryptographically verified agent identities, short-lived credentials, human approval gates
  for high-impact actions, and zero-trust / least-privilege architecture.
  Source: <https://www.cisa.gov/resources-tools/resources/careful-adoption-of-agentic-ai-services>
  **aigis impact:** Validates existing agentic/privilege-escalation patterns; guidance explicitly
  names prompt injection as the primary agentic attack vector. A new `agentic_tool_exfil` pattern
  (agent instructed to forward credentials or exfiltrate data via tool calls) would align with
  the guidance — candidate for a future cycle.

- **FTC: "Operation AI Comply" + March 2026 AI Policy Statement**
  The FTC's March 11, 2026 AI Policy Statement formally interprets FTC Act Section 5 as applying
  to AI systems across their full lifecycle. The Air AI case (March 2026, $18M judgment) established
  precedent for conversational AI misrepresenting human-equivalent capability. The statement requires
  logging of AI agent decisions affecting consumers (criteria, inputs, outputs). Each automated
  decision is treated as a potentially separate violation (fines up to $53K each from 2027).
  Source: <https://ourtake.bakerbotts.com/post/102mirs/march-2026-federal-deadlines-that-will-reshape-the-ai-regulatory-landscape>
  **aigis impact:** AI identity denial pattern (`comp_ai_identity_denial`) also serves as FTC Act
  Section 5 compliance check. An additional `comp_capability_overclaiming` pattern (AI claims to
  replace licensed professionals without qualification) is a candidate hardening for a future cycle.

- **EU AI Act GPAI: Code of Practice in Force; Full Commission Enforcement August 2, 2026**
  GPAI obligations became enforceable August 2, 2025. The Commission's full enforcement powers
  activate August 2, 2026 — approximately 11 weeks away. All GPAI providers must publish a
  training data summary using the mandatory EU AI Office template, notify within two weeks of
  reaching the 10²⁵ FLOPs systemic risk threshold, conduct adversarial testing, and report
  serious incidents. The grace period ends August 2, 2026.
  Source: <https://www.lw.com/en/insights/eu-ai-act-gpai-model-obligations-in-force-and-final-gpai-code-of-practice-in-place>
  **aigis impact:** Existing `gpai_provider.yaml` template covers the four GPAI obligations.
  An annotation noting the August 2, 2026 full enforcement deadline is warranted in the template.

- **EU AI Act Omnibus: Watermarking/Transparency Labeling Deadline Accelerated**
  The May 2026 Omnibus deal shrinks the transparency labeling grace period from 6 to 3 months,
  making AI-generated content watermarking/disclosure compliant by December 2, 2026. The standard
  is now aligned with the nudifier ban effective date.
  Source: <https://www.williamfry.com/knowledge/eu-ai-act-omnibus-deal-reached-postponed-deadlines-watermarking-compromise-and-the-nudificiation-prohibition/>
  **aigis impact:** A future output filter rule checking for synthetic content disclosure markers
  in AI-generated media would address this deadline. Candidate for a future cycle.

- **Canada: AIDA Dead; Regulation Defaults to Provincial Privacy Law**
  Bill C-27 / AIDA formally died January 2025 when Parliament prorogued. The new government
  confirmed AIDA will not return in its original form. Ontario's Employment Standards Act changes
  (effective January 1, 2026) require job postings to disclose AI use in hiring. Quebec's Law 25
  imposes binding obligations on automated decision-making. Canada has no binding federal AI law
  as of May 2026.
  Source: <https://babl.ai/canadian-ai-bill-stalls-as-bill-c-27-terminates-in-parliament/>
  **aigis impact:** Compliance map documentation for Canada should be updated from "pending AIDA"
  to "provincial patchwork" noting Law 25 (Quebec) and Ontario ESA amendments as the active obligations.

- **EU AI Act: First Harmonized Standard (prEN 18286) in Public Enquiry; Others Delayed**
  `prEN 18286` (AI Quality Management System for EU AI Act Article 17) entered public enquiry
  in late 2025 — the first harmonized standard in the EU AI Act framework. CEN and CENELEC missed
  the August 2025 deadline for the full standard suite. Until standards are published in the EU
  Official Journal, providers must self-assess compliance against the AI Act directly.
  Source: <https://artificialintelligenceact.eu/standard-setting-overview/>
  **aigis impact:** Compliance guidance should note that no harmonized technical standard yet
  grants a presumption of conformity for high-risk AI Act obligations. Track prEN 18286 finalization.

---

## Candidate hardenings

1. **[IMPLEMENTED] `comp_emotion_recognition_workplace`** (score 70, input filter) — Detects
   requests to build AI systems that monitor or infer the emotions of employees, workers,
   students, or pupils in workplace or educational institution settings.
   EU AI Act Art. 5(1)(f) prohibited practice since 2025-02-02. EC expert studies May 2026 confirm scope.

2. **[IMPLEMENTED] `comp_biometric_categorization`** (score 70, input filter) — Detects requests
   to build AI that infers sensitive attributes (race, ethnicity, political opinions, religious
   beliefs, sexual orientation, health status) from biometric features such as facial images.
   EU AI Act Art. 5(1)(g) prohibited practice since 2025-02-02.

3. **[PENDING] `comp_capability_overclaiming`** — Pattern matching AI outputs that claim the
   system can replace licensed professionals (doctor, lawyer, financial advisor) or "guarantee
   outcomes" without qualification. FTC Act Section 5 enforcement framing (Air AI, $18M, March 2026).
   Candidate for a future compliance-regulation cycle.

4. **[PENDING] GPAI template enforcement deadline annotation** — Add `# Enforcement: full Commission
   powers from 2026-08-02` comments to `gpai_provider.yaml`. Documentation-only, low urgency.

5. **[PENDING] Canada compliance map update** — Update any aigis docs or templates referencing
   "pending AIDA" to reflect the provincial patchwork status (Law 25, Ontario ESA amendments).
