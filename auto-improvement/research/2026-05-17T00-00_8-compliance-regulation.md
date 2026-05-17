# Research: compliance-regulation (index 8)

**Domain:** compliance-regulation
**Cycle index:** 8 (fourth pass)
**Cycle UTC:** 2026-05-17T00-00

---

## Previous coverage

- 2026-05-09T05-00: EU AI Act Digital Omnibus NCII ban, Annex III deadline deferral, NIST AI RMF Critical Infrastructure Profile, ISO/IEC 27090/42001.
- 2026-05-12T00-16: EU AI Act GPAI Code of Practice (Art. 53–55), training data summary template, NIST CAISI, ISO 42001 vendor requirements.
- 2026-05-12T00-55: EU AI Act Art. 5 expert studies (social scoring, emotion recognition, predictive policing), Art. 52 transparency consultation, US state chatbot disclosure laws (CA, WA, NE, OR), CHATBOT Act.

## New angle for this cycle

EU AI Act Art. 5(1)(g) biometric categorisation prohibition (not yet covered in aigis detectors);
NIST IR 8596 Cyber AI Profile (December 2025 preliminary draft, planned 2026 initial public draft);
UK FCA AI governance expectations under existing frameworks;
China GB/T 45654-2025 generative AI security standard.

---

## Findings

- **EU AI Act Art. 5(1)(g): Biometric categorisation for sensitive attributes — enforceable since Feb 2025**
  Article 5(1)(g) prohibits AI systems that categorise individuals based on biometric data to deduce or infer their race, political opinions, trade union membership, religious or philosophical beliefs, sex life, or sexual orientation. The prohibition is absolute — no lawful-basis exception exists — and has been in force since 2 February 2025 (the same date as the social scoring ban). Maximum fine: EUR 35M or 7% of global annual turnover (highest tier). The FPF analysis "Red Lines under the EU AI Act" (April 2025) and Security Boulevard's "Article 5 and the EU AI Act's Absolute Red Lines" (April 2026) both call Art. 5(1)(g) one of the most clearly scoped prohibitions in the Act.
  Source: <https://artificialintelligenceact.eu/article/5/>; <https://fpf.org/blog/red-lines-under-the-eu-ai-act-understanding-the-prohibition-of-biometric-categorization-for-certain-sensitive-characteristics/>; <https://securityboulevard.com/2026/04/article-5-and-the-eu-ai-acts-absolute-red-lines-firetail-blog/>
  **aigis impact:** aigis had no detection pattern for this prohibited practice. A new `comp_biometric_sensitive_categ` pattern catches requests to build or deploy AI that infers race, political opinion, religious belief, sexual orientation, or union membership from face images, voice, gait, fingerprints, or other biometric modalities.

- **EU AI Act GPAI enforcement milestone: Commission powers activate 2 August 2026**
  GPAI model obligations came into force on 2 August 2025. From 2 August 2026, the Commission's enforcement powers activate: it can request documentation, conduct evaluations, order corrective measures, restrict market access, and impose fines (up to EUR 15M or 3% of global turnover). Providers of models released before August 2025 have until August 2027 to comply.
  Source: <https://artificialintelligenceact.eu/enforcement-of-chapter-v-under-the-eu-ai-act/>; <https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers>
  **aigis impact:** The `gpai_provider.yaml` template already addresses Art. 53–55 obligations. No new patterns needed this cycle; the enforcement deadline commentary remains accurate.

- **NIST IR 8596 Cyber AI Profile — preliminary draft (December 2025), initial public draft expected 2026**
  NIST published a preliminary draft of the Cybersecurity Framework Profile for AI (NISTIR 8596) in December 2025 with a 45-day comment period (closed January 2026). An initial public draft is planned for mid-2026. The profile applies CSF 2.0 to AI-specific risks across three focus areas: securing AI systems, AI-enabled cyber defense, and thwarting AI-enabled attacks. It explicitly covers prompt injection, data poisoning, supply chain attacks, and agentic AI threats. NIST aims a summer 2026 release for the initial public draft.
  Source: <https://csrc.nist.gov/pubs/ir/8596/iprd>; <https://www.nextgov.com/artificial-intelligence/2026/05/nist-aims-summer-release-ai-cyber-guidelines/413559/>; <https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8596.iprd.pdf>
  **aigis impact:** NIST IR 8596 validates aigis's existing coverage of prompt injection, data poisoning, and supply chain patterns. No implementation action needed this cycle; the NIST_AI_RMF_MAPPING.md could reference NISTIR 8596 when the initial public draft is finalized (deferred to cycle 18+).

- **UK FCA — AI governance via existing frameworks, Mills Review 2026**
  The FCA does not plan standalone AI regulation; instead it expects firms to demonstrate that Consumer Duty, the Senior Managers and Certification Regime (SM&CR), SYSC, and operational resilience requirements already cover their AI use. On 27 January 2026, the FCA launched the Mills Review examining how AI will reshape retail financial services through 2030; recommendations are due to the FCA Board summer 2026. The Treasury Committee recommended that by end 2026 the FCA publish comprehensive guidance on accountability and consumer protection for AI.
  Source: <https://www.fca.org.uk/firms/innovation/ai-approach>; <https://www.insideglobaltech.com/2026/04/09/uk-financial-services-regulators-approach-to-artificial-intelligence-in-2026/>
  **aigis impact:** No aigis policy template warranted for UK FCA AI governance at this stage; the existing framework is principles-based and relies on existing conduct rules that aigis does not model. Track for 2027 if sectoral guidance materialises.

- **China GB/T 45654-2025 — generative AI security standard (effective November 2025)**
  On 25 April 2025, China released three national standards for generative AI services: GB/T 45654-2025 (basic security requirements for generative AI services), GB/T 45674-2025 (data annotation security), and GB/T 45652-2025 (pre-training and fine-tuning data security). All three took effect 1 November 2025. The basic requirements standard mandates training data security, model security, and security measures for services offered within China or to Chinese users. AI-generated content must be labelled; content prohibited under Chinese law must be blocked.
  Source: <https://cset.georgetown.edu/publication/china-gen-ai-safety-standard-draft/>; <https://iclg.com/practice-areas/cybersecurity-laws-and-regulations/01-generative-ai-and-cyber-risk-in-china>
  **aigis impact:** GB/T 45654-2025 is prescriptive but largely addresses provider-side obligations (training data, labelling). A China-focused compliance template is a plausible future addition; deferred to a future cycle as the standard's English-language analysis is still maturing.

- **EU AI Act Art. 9 risk management system — high-risk AI deadline 2 August 2026**
  All high-risk AI systems (Annex III) must comply with core requirements including risk management (Art. 9), data governance (Art. 10), technical documentation (Art. 11), transparency (Art. 13), human oversight (Art. 14), accuracy and robustness (Art. 15), and conformity assessment by 2 August 2026 (extended from 2027 for Annex III by the Digital Omnibus provisional agreement, now targeting August 2026 for GPAI enforcement; Annex III deployers have until 2027 per the Omnibus deferral).
  Source: <https://artificialintelligenceact.eu/article/9/>; <https://www.legalnodes.com/article/eu-ai-act-2026-updates-compliance-requirements-and-business-risks>
  **aigis impact:** The `eu_ai_act_high_risk.yaml` template covers Art. 9–15 obligations. No new patterns needed this cycle.

- **US OCC SR 11-7 and federal banking AI governance**
  The Federal Reserve and OCC's foundational AI governance framework (SR 11-7) requires rigorous development documentation, independent validation, and ongoing monitoring for AI models processing customer data. In 2026, political scrutiny is intensifying, with regulators expecting firms to review governance, explainability, and oversight for AI systems, especially agentic capabilities.
  Source: <https://fin.ai/learn/evaluate-ai-agent-compliance-financial-services>; <https://www.globalpolicywatch.com/2026/04/uk-financial-services-regulators-approach-to-artificial-intelligence-in-2026/>
  **aigis impact:** US banking AI governance is model-validation focused (SR 11-7). No new aigis patterns warranted; the `finance.yaml` policy template already covers relevant risk areas.

---

## Candidate hardenings

1. **[IMPLEMENTED] `comp_biometric_sensitive_categ`** — Detection pattern for EU AI Act Art. 5(1)(g): requests to build AI that uses biometric data (facial recognition, voice, gait, fingerprints, iris) to infer or deduce race, political opinions, religious beliefs, sexual orientation, or trade union membership. Highest-penalty prohibited practice (EUR 35M / 7% turnover). Clear gap in existing coverage; pattern is narrow enough to avoid false positives on legitimate face-recognition use cases (age verification, liveness detection).

2. **[DEFERRED] China GB/T 45654-2025 compliance template** — A `china_genai_provider.yaml` policy template covering the November 2025 Chinese generative AI security standard. Deferred: English-language analysis of the technical requirements is still sparse; implementing a policy template prematurely risks inaccuracy. Revisit when CSET or equivalent publishes a detailed English breakdown.

3. **[DEFERRED] NIST IR 8596 mapping update** — Update `docs/NIST_AI_RMF_MAPPING.md` to reference NISTIR 8596 once the initial public draft is published (summer 2026). Deferred: preliminary draft only; final structure may change.
