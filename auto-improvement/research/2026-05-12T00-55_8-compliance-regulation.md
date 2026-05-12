# Research: compliance-regulation (index 8)
**Cycle UTC:** 2026-05-12T00-55

---

## Domain
Compliance & regulatory updates affecting AI systems: EU AI Act prohibited practices, US state chatbot disclosure laws, new expert studies on Article 5, and AI transparency obligations.

## Previous coverage (2026-05-09T05-00, index 8)
Covered: EU AI Act Digital Omnibus NCII ban, deadline updates, NIST AI Critical Infrastructure Profile concept note, ISO/IEC 27090 and 42001.

## New angle for this cycle
EU AI Act Art. 5 prohibited practices enforcement detail + US wave of chatbot disclosure laws (2026 state legislation).

---

## Findings

- **EU AI Act Art. 5: Three expert studies published May 2026**
  The European Commission published three expert studies (E. J. Kindt, Catherine Jasserand) covering the prohibitions in Art. 5.1(c) (social scoring), Art. 5.1(d) (predictive policing), Art. 5.1(f) (emotion recognition in workplaces/education), and Art. 5.1(g) (biometric categorization for sensitive attributes), along with procedural requirements for real-time remote biometric identification exceptions.
  Source: <https://digital-strategy.ec.europa.eu/en/library/three-studies-various-aspects-article-5-ai-act>
  **aigis impact:** The studies clarify that employer behavior-scoring systems and citizen trustworthiness scoring are in scope of the Art. 5(1)(c) prohibition. A detection pattern for social scoring requests helps users identify prohibited AI deployments before they are built.

- **EU AI Act Art. 5(1)(c): Social scoring prohibition in force since 2025-02-02**
  AI systems that evaluate or classify persons based on social behaviour or personality characteristics, where the resulting score causes disproportionate or context-unrelated harm, are prohibited. Fines reach EUR 35M or 7% of global annual turnover (highest tier). Investigations reportedly underway as of early 2026 for workplace emotion recognition and predictive policing.
  Source: <https://artificialintelligenceact.eu/article/5/>
  **aigis impact:** aigis had no dedicated detector for requests to build social scoring systems. New `comp_social_scoring_request` pattern covers citizen trust scores, social credit systems, and behavior-based individual scoring.

- **EU AI Act Art. 52: AI transparency obligations — consultation opened May 8, 2026**
  On 8 May 2026 the Commission opened consultation on draft guidelines for AI transparency obligations under Art. 52. Systems interacting with humans must disclose they are AI unless the human already knows or the system merely generates content. Enforceable from 2026-08-02. Maximum fine: EUR 15M or 3% of global annual turnover.
  Source: <https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai>
  **aigis impact:** System-prompt level instructions that tell an AI to deny being AI or claim to be human directly violate Art. 52. A dedicated `comp_ai_identity_denial` pattern catches these at the input layer.

- **US state wave of chatbot disclosure laws (2026)**
  Four states enacted or signed AI chatbot disclosure legislation in early 2026: California (companion chatbot + AI Transparency Act, effective Aug 2026), Washington (Companion Chatbot Safety Act — requires disclosure at session start and every 3 hours, with private right of action), Nebraska (Conversational AI Safety Act, April 14 2026), Oregon (SB 1546, March 2026). A proposed federal CHATBOT Act would extend these nationally.
  Source: <https://www.orrick.com/en/Insights/2026/04/2026-State-Chatbot-Laws-Key-Provisions-and-Regulatory-Trends>
  **aigis impact:** The same `comp_ai_identity_denial` pattern serves as a cross-jurisdictional compliance check: it fires on any instruction embedding an AI identity denial, regardless of which law applies to the deployer.

- **US CHATBOT Act (March 2026 proposal)**
  Lawmakers introduced a federal bill to stop AI chatbots from impersonating doctors, lawyers, and other licensed professionals, extending chatbot disclosure requirements nationally and requiring explicit AI disclosure in medical, legal, and financial contexts.
  Source: <https://kevinmullin.house.gov/2026/03/19/lawmakers-introduce-bill-to-stop-ai-chatbots-from-impersonating-doctors-lawyers-licensed-professionals/>
  **aigis impact:** Reinforces the priority of `comp_ai_identity_denial`. The intersection of Art. 52 and US state law creates a broad compliance obligation aigis can now surface at the prompt-input stage.

- **EU AI Act Art. 52: Policy template already references transparency bypass**
  The existing `eu_ai_act_high_risk.yaml` template includes a custom rule `eu_ai_transparency_bypass` (score_delta: 50) covering basic cases. The new `comp_ai_identity_denial` in `patterns.py` extends this to the universal input filter (not policy-gated) and covers additional phrasings, making it independent of policy template selection.
  Source: aigis codebase — `policy_templates/eu_ai_act_high_risk.yaml`
  **aigis impact:** Universal input-layer coverage means any aigis deployment can now catch AI identity denial instructions, not only those using the EU AI Act template.

- **NIST AI RMF 2026 pipeline — Cyber AI Profile + SP 800-53 overlays expected H2 2026**
  NIST is finalizing a Cyber AI Profile, RMF 1.1 guidance addenda, and SP 800-53 Control Overlays for AI, all tracking through 2026. An AI Agent Interoperability Profile is planned for Q4 2026.
  Source: <https://www.nist.gov/itl/ai-risk-management-framework>
  **aigis impact:** Premature to build templates; monitor for Q4 2026 drafts. Track in next cycle 8 pass.

---

## Candidate Hardenings

1. **[IMPLEMENTED] `comp_ai_identity_denial` pattern** — Catches system-prompt instructions that direct an AI to deny being an AI or claim to be human. EU AI Act Art. 52 + US state chatbot disclosure laws (CA, WA, NE, OR 2026). Score 60.

2. **[IMPLEMENTED] `comp_social_scoring_request` pattern** — Catches requests to build or deploy AI-based social scoring systems (citizen trust scores, social credit engines, behavior-based individual ranking). EU AI Act Art. 5(1)(c), in force since 2025-02-02, clarified by EC expert studies May 2026. Score 70.

3. **[PENDING] NIST Cyber AI Profile compliance template** — Draft not yet published; track for Q4 2026.

4. **[PENDING] EU AI Act Art. 52 guidance template extension** — The consultation on transparency guidelines is open; full guidance expected H2 2026. Extend the EU AI Act policy template once the guidelines are finalized.
