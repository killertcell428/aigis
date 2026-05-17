# Research: compliance-regulation (index 8)
**Cycle UTC:** 2026-05-17T09-15

---

## Domain
Compliance & regulatory updates affecting AI systems: EU AI Act Article 5 prohibited practices enforcement — emotion recognition in the workplace and education, subliminal manipulation techniques, and exploitation of vulnerable groups.

## Previous coverage
- 2026-05-09: EU AI Act Digital Omnibus NCII ban, deadline updates, NIST AI Critical Infrastructure Profile concept note.
- 2026-05-12: EU AI Act Art. 5 prohibited practices expert studies, US state chatbot disclosure laws, `comp_ai_identity_denial` and `comp_social_scoring_request` patterns.

## New angle for this cycle
Two additional prohibited practices under Art. 5 not yet covered: emotion recognition in workplace/education (Art. 5(1)(f)) and exploitation of vulnerable groups via AI (Art. 5(1)(b)). Both have been enforceable since 2025-02-02, and EC Commission guidelines published Feb 4, 2025 clarified their scope with concrete examples. Enforcement investigations are reportedly underway in Ireland and France as of early 2026.

---

## Findings

- **EU AI Act Art. 5(1)(f): Workplace and educational emotion recognition is prohibited since Feb 2025**
  AI systems that infer emotions of natural persons based on biometric data in workplace or educational settings are a prohibited AI practice since 2025-02-02. "Emotion" covers happiness, sadness, anger, stress, engagement, and ten other states listed in Recital 18. The prohibition covers facial expression scoring, voice-stress analysis, physiological wearables (heart rate, galvanic skin response), and webcam-based mood monitoring of employees, students, and candidates. The only exceptions are narrowly scoped medical or safety uses (e.g. fatigue detection in vehicle operators). Text-only sentiment analysis is not in scope.
  Source: <https://legalblogs.wolterskluwer.com/global-workplace-law-and-policy/the-prohibition-of-ai-emotion-recognition-technologies-in-the-workplace-under-the-ai-act/>
  **aigis impact:** aigis had no detector for requests to build workplace emotion recognition systems. A new `comp_emotion_recognition_workplace` pattern closes this gap at the input layer.

- **Enforcement is reportedly active: Ireland (WRC) and France (CNIL) investigating**
  As of early 2026, the Irish Workplace Relations Commission (WRC) and France's CNIL have jurisdiction over workplace emotion recognition violations. No formal public enforcement decisions have been published yet, but multiple investigations are reportedly underway, including against vendors who continue selling prohibited emotion recognition products to EU employers.
  Source: <https://www.uctoday.com/workplace-management/eu-ai-act-shock-emotion-recognition-is-now-illegal-at-work-so-why-is-your-vendor-still-selling-it/>
  **aigis impact:** The enforcement risk is real and growing. Flagging prohibited system-prompt requests before a customer builds and deploys a prohibited system provides concrete compliance value.

- **EU AI Act Art. 5(1)(b): Exploiting vulnerabilities of children, elderly, disabled, or economically distressed groups is prohibited**
  AI systems that exploit the age, disability, or socioeconomic vulnerability of a person or group to materially distort their behaviour in a way likely to cause harm are prohibited since 2025-02-02. EC Commission guidelines (published Feb 4, 2025) provide specific examples: addictive reinforcement loops with dopamine-like reward schedules targeting children to drive compulsive use; personalised deceptive or predatory financial offers targeting elderly users or people in low-income areas; AI that exploits cognitive decline to manipulate purchasing decisions.
  Source: <https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-5>
  **aigis impact:** aigis had no detector for prompts requesting vulnerable-group targeting. A new `comp_vulnerable_group_manipulation` pattern catches these at the input layer.

- **Art. 5(1)(a): Subliminal techniques prohibition — complementary to Art. 5(1)(b)**
  Subliminal techniques that operate below conscious awareness to distort behaviour are separately prohibited under Art. 5(1)(a). Commission guidelines clarify that "subliminal" means below the threshold of conscious perception — not merely persuasive or personalised content. The prohibition specifically targets covert techniques like hidden audio, covert priming, or below-threshold visual stimuli used to shape behaviour without the person's knowledge. This overlaps in intent with evasion obfuscation patterns already covered by aigis but approaches it from a compliance angle.
  Source: <https://www.insideprivacy.com/artificial-intelligence/european-commission-guidelines-on-prohibited-ai-practices-under-the-eu-artificial-intelligence-act/>
  **aigis impact:** Existing jailbreak and encoding-bypass detectors already cover several subliminal-technique vectors (zero-width characters, invisible text). The Art. 5(1)(a) angle reinforces the compliance relevance of those detectors without requiring new patterns.

- **NIST IR 8596 (Cyber AI Profile): Preliminary draft published Dec 2025, comment period closed Jan 2026**
  NIST published a preliminary draft of the Cybersecurity Framework Profile for Artificial Intelligence (NIST IR 8596, "Cyber AI Profile") on December 16, 2025. The profile organises AI security around three focus areas: Secure (protecting AI systems from attack), Defend (using AI to improve cyber defence), and Thwart (blocking adversarial AI-enabled attacks). It builds on CSF 2.0 and AI RMF. A companion discussion draft covers control overlays for fine-tuning and predictive AI (NIST IR 8605/8605A). The initial public draft is expected in 2026.
  Source: <https://csrc.nist.gov/pubs/ir/8596/iprd>
  **aigis impact:** The Cyber AI Profile is informative at this stage. No template warranted until the initial public draft is stable (expected H2 2026). Continue to track.

- **FireTail April 2026: Art. 5 enforcement expected to accelerate after Aug 2026 GPAI deadline**
  A FireTail Security Boulevard analysis (April 2026) notes that while Art. 5 prohibitions are already live, enforcement capacity will expand significantly after August 2, 2026 when the EU AI Office takes on broader coordination responsibilities. The analysis predicts the first formal Art. 5 decisions will emerge in H2 2026 or early 2027, with emotion recognition and predictive policing cases most likely.
  Source: <https://securityboulevard.com/2026/04/article-5-and-the-eu-ai-acts-absolute-red-lines-firetail-blog/>
  **aigis impact:** Timely coverage — adding these patterns now means aigis users operating in the EU can detect and remediate prohibited practice requests before enforcement decisions create reputational and financial exposure.

- **EC Guidelines on prohibited AI practices — practical scope of Art. 5(1)(b)**
  The EC guidelines clarify that Art. 5(1)(b) requires both: (1) targeting a vulnerable group, and (2) the AI's effect being to materially distort their behaviour in a harmful way. Merely offering services to children or elderly users is not prohibited; it is the exploitation of the vulnerability itself that triggers the prohibition. The guidelines give three named examples: addictive loop design for minors, predatory targeting of seniors with financial scams, and exploitation of cognitive decline.
  Source: <https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act>
  **aigis impact:** This informs the pattern scope — the detector should focus on explicit requests to exploit vulnerability, not on age-demographic targeting alone. The implemented pattern is calibrated accordingly.

- **Maximum fines for Art. 5 violations: EUR 35M or 7% of global annual turnover**
  All Art. 5 prohibited practice violations (including Art. 5(1)(b) and 5(1)(f)) carry the highest fine tier under the EU AI Act: EUR 35,000,000 or 7% of total worldwide annual turnover, whichever is higher. This is materially higher than the GDPR maximum of EUR 20M or 4% of global turnover, making Art. 5 compliance the highest-priority AI compliance obligation for EU-exposed organisations.
  Source: <https://artificialintelligenceact.eu/high-level-summary/>
  **aigis impact:** The fine level justifies robust detection tooling — aigis surfacing these risks at the input layer provides concrete ROI for compliance teams.

---

## Candidate hardenings

- **Implemented this cycle:**
  - `comp_emotion_recognition_workplace` (score 65, input filter) — Detects requests to build AI systems that infer employee or student emotions from biometric data in workplace/education settings (EU AI Act Art. 5(1)(f), in force since 2025-02-02).
  - `comp_vulnerable_group_manipulation` (score 65, input filter) — Detects requests to deploy AI that exploits age, disability, or socioeconomic vulnerability of children, elderly, or other protected groups to distort their behaviour (EU AI Act Art. 5(1)(b), in force since 2025-02-02).

- **Deferred (NIST Cyber AI Profile):** Too early to template; preliminary draft comment period just closed. Revisit when initial public draft is stable (H2 2026).
- **Deferred (Art. 5(1)(a) subliminal techniques):** Existing encoding/evasion patterns already cover most vectors. A dedicated compliance-angle pattern would risk high false positives against the evasion detectors and adds limited new coverage. Revisit if a concrete attack pattern specific to conscious-threshold manipulation emerges.
