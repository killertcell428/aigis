# Research: compliance-regulation (index 8)

**Domain:** compliance-regulation
**Cycle index:** 8
**Cycle UTC:** 2026-05-17T06-06

---

## Previous coverage for this domain

- 2026-05-09T05-00: EU AI Act Digital Omnibus NCII ban, NIST AI RMF Critical Infrastructure Profile concept, ISO/IEC 27090 and 42001.
- 2026-05-12T00-16: GPAI Code of Practice (Art. 53-55, final 2025-07-10), CSA Agentic NIST RMF Profile, ISO 42001 procurement trends, GPAI provider policy template implemented.
- 2026-05-12T00-55: Art. 5(1)(c) social scoring prohibition (with EC expert studies May 2026), Art. 52 AI transparency obligations, US state chatbot disclosure laws (CA, WA, NE, OR 2026); comp_ai_identity_denial and comp_social_scoring_request implemented.

## New angle for this cycle

EU AI Act Art. 5(1)(a) subliminal manipulation prohibition and Art. 5(1)(f) workplace/education emotion recognition prohibition — both enforceable since 2025-02-02, with EC final guidelines published 2025-07-29. Also: NIST AI 100-2 E2025 adversarial machine learning taxonomy update.

---

## Findings

- **EU AI Act Art. 5(1)(f): Emotion recognition in workplaces and educational institutions prohibited since 2025-02-02**
  The AI Act categorically bans AI systems that infer the emotions of natural persons in workplaces or educational institutions, unless strictly used for medical or safety purposes (e.g., detecting dangerous fatigue in vehicle operators). Biometric inference from facial expressions, voice tone, physiological signals, and similar modalities is covered. Market surveillance authorities in France (CNIL), Germany (BNetzA), and Ireland (WRC) have publicly signalled workplace emotion recognition as an active 2026 enforcement priority; the first major enforcement case is expected in H2 2026.
  Source: <https://legalblogs.wolterskluwer.com/global-workplace-law-and-policy/the-prohibition-of-ai-emotion-recognition-technologies-in-the-workplace-under-the-ai-act/>
  **aigis impact:** No aigis pattern previously detected requests to build or deploy workplace/education emotion recognition AI. New `comp_emotion_recognition_workplace` pattern catches such requests at the prompt layer, letting deployers flag AI development tasks that would produce prohibited systems.

- **EC final guidelines on prohibited AI practices (C(2025) 5052 final, published 2025-07-29)**
  The European Commission published its final guidelines on prohibited AI practices under the AI Act on 29 July 2025. These guidelines cover all eight prohibited practices in Art. 5 and carry substantial enforcement weight: national market surveillance authorities and the AI Office use them as the authoritative interpretation. For Art. 5(1)(f), the guidelines confirm that emotion inference via facial expression, voice tone, or physiological biometric signals in workplace/education is prohibited regardless of whether the inferred emotion is displayed to an HR manager or used only algorithmically.
  Source: <https://ai-act-service-desk.ec.europa.eu/sites/default/files/2025-08/guidelines_on_prohibited_artificial_intelligence_practices_established_by_regulation_eu_20241689_ai_act_english_ied3r5nwo50xggpcfmwckm3nuc_112367-1.PDF>
  **aigis impact:** The final guidelines give aigis's compliance patterns a firm regulatory grounding. The July 2025 publication confirms the interpretation of Art. 5(1)(a) and (b) used in the new subliminal manipulation pattern.

- **EU AI Act Art. 5(1)(a): Subliminal manipulation and dark patterns prohibition**
  AI systems that deploy subliminal techniques beyond conscious awareness or purposefully manipulative/deceptive techniques that materially distort behaviour are prohibited since 2025-02-02. The EC guidelines provide concrete examples: addictive reinforcement schedules and dopamine-like loops in AI games targeting children; dark patterns blocking users from cancelling subscriptions; AI toys designed to create compulsive usage. The prohibition requires material distortion of behaviour — minor influence (e.g. product recommendations) is not automatically prohibited. The highest fine tier (€35M or 7% of global turnover) applies.
  Source: <https://www.insideprivacy.com/artificial-intelligence/european-commission-guidelines-on-prohibited-ai-practices-under-the-eu-artificial-intelligence-act/>
  **aigis impact:** No aigis pattern previously covered subliminal manipulation instructions. New `comp_subliminal_manipulation` pattern catches requests to implement addictive reinforcement loops, dopamine hooks, covert manipulation of user behavior, and exploitation of psychological vulnerabilities — all specific examples named in the EC guidelines.

- **EU AI Act Art. 5(1)(b): Exploitation of vulnerable groups prohibition**
  Article 5(1)(b) prohibits AI systems that exploit vulnerabilities arising from age (children, elderly), disability, or social/economic situation to materially distort behaviour. The EC guidelines explicitly cite: AI targeting older people with deceptive personalised scams; chatbots exploiting mental health vulnerability; AI directing predatory financial product ads at low-income users. This prohibition is co-extensive with Art. 5(1)(a) in enforcement terms (same fine tier, same enforcement date) and the `comp_subliminal_manipulation` pattern covers the overlap.
  Source: <https://www.insideprivacy.com/artificial-intelligence/european-commission-guidelines-on-prohibited-ai-practices-under-the-eu-artificial-intelligence-act/>
  **aigis impact:** `comp_subliminal_manipulation` includes alternatives for `exploit user/child/elderly/disabled vulnerabilit*` that capture Art. 5(1)(b) alongside Art. 5(1)(a).

- **EU AI Act enforcement timeline: fines active since 2025-08-02**
  While the prohibited practices became applicable on 2025-02-02, the penalty regime for Art. 5 violations (and for market surveillance authorities to impose them) became fully operational on 2025-08-02. As of May 2026, no public enforcement decisions have been issued, but several complaints are under investigation across France, Germany, and Ireland, particularly for workplace emotion recognition and predictive policing AI.
  Source: <https://www.uctoday.com/workplace-management/eu-ai-act-shock-emotion-recognition-is-now-illegal-at-work-so-why-is-your-vendor-still-selling-it/>
  **aigis impact:** The 6-month investigation window means first decisions are realistic in H2 2026. aigis patterns added now help organizations catch prohibited-practice requests before they build the systems that would be fined.

- **NIST AI 100-2 E2025: Adversarial machine learning taxonomy update (published 2025-03-24)**
  NIST published the 2025 edition of its adversarial machine learning taxonomy (NIST.AI.100-2e2025) on 24 March 2025. Key additions relevant to aigis: (1) expanded treatment of indirect prompt injection as a distinct attack class, covering web-page, document, database, and tool-output vectors; (2) first dedicated section on autonomous AI agent vulnerabilities, including tool misuse and memory poisoning; (3) explicit coverage of clean-label data poisoning in RAG pipelines. NIST recommends output filtering and context-aware sandboxing as primary mitigations for indirect prompt injection in agentic deployments.
  Source: <https://csrc.nist.gov/pubs/ai/100/2/e2025/final>
  **aigis impact:** NIST's indirect prompt injection taxonomy validates aigis's existing `INDIRECT_INJECTION_PATTERNS` and confirms agentic tool-abuse patterns are a primary threat class. No immediate new patterns required; existing coverage aligns with NIST taxonomy. The NIST_AI_RMF_MAPPING.md should reference NIST AI 100-2 E2025 in a future documentation cycle.

- **ENISA Threat Landscape 2025: AI reshapes cyber attacks (published October 2025)**
  ENISA's 2025 threat landscape (v1.2, January 2026 revision) describes 2025 as the first year AI fundamentally altered the cyber threat landscape. Over 80% of global phishing campaigns now use AI-generated content. A new chapter covers the AI software supply chain: compromised hosted ML models and malicious PyPI packages with backdoors. AI-assisted social engineering (Xanthorox AI and similar) represents a shift from jailbreaks to dedicated malicious AI infrastructure.
  Source: <https://www.enisa.europa.eu/publications/enisa-threat-landscape-2025>
  **aigis impact:** aigis's supply chain patterns already cover malicious PyPI packages. The ENISA findings reinforce that the supply-chain domain (index 5) remains high-priority; no new patterns needed from this finding this cycle.

---

## Candidate Hardenings

1. **[IMPLEMENTED] `comp_emotion_recognition_workplace` pattern (score 70, input filter)** — Detects requests to build or deploy AI systems that infer emotions of employees or students. EU AI Act Art. 5(1)(f), in force since 2025-02-02. EC final guidelines C(2025) 5052 final (2025-07-29) confirm scope includes all biometric emotion inference in workplace/education without a medical or safety exception. Fine: €35M or 7% of global turnover.

2. **[IMPLEMENTED] `comp_subliminal_manipulation` pattern (score 65, input filter)** — Detects instructions to use subliminal techniques, addictive reinforcement loops, dark patterns blocking cancellation, or exploitation of psychological vulnerabilities. EU AI Act Art. 5(1)(a) and (b), in force since 2025-02-02. EC guidelines explicitly name addictive reinforcement schedules, dopamine loops, and vulnerability exploitation as prohibited. Fine: €35M or 7% of global turnover.

3. **[PENDING] Update `docs/compliance/NIST_AI_RMF_MAPPING.md`** — Add reference to NIST AI 100-2 E2025 adversarial machine learning taxonomy and its explicit coverage of indirect prompt injection and agentic AI vulnerabilities. Documentation-only change; deferred to allow NIST CAISI AI Agent Interoperability Profile (Q4 2026) to inform the full update.

4. **[PENDING] EU AI Act Art. 5(1)(d) predictive policing pattern** — Detection for requests to build AI systems that assess criminal risk solely from profiling/personality traits (Art. 5(1)(d) prohibition). The scope is narrower and harder to capture via regex without high false-positive risk (legitimate risk scoring based on objective evidence is not prohibited). Deferred pending research into precise phrasing patterns.
