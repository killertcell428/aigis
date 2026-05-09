# Research: compliance-regulation (index 8)
**Cycle UTC:** 2026-05-09T05-00

---

## Findings

- **EU AI Act Digital Omnibus — high-risk deferral (2026-05-07)**  
  Provisional political agreement reached between EP and Council at 4:30am on 7 May 2026.  
  Annex III (standalone high-risk AI) obligations deferred: **August 2, 2026 → December 2, 2027**.  
  Annex I (safety-component AI) obligations deferred: **August 2, 2028**.  
  Source: <https://www.consilium.europa.eu/en/press/press-releases/2026/05/07/artificial-intelligence-council-and-parliament-agree-to-simplify-and-streamline-rules/>  
  **aigis impact:** `policy_templates/eu_ai_act_high_risk.yaml` deadline comments were outdated; must be corrected.

- **EU AI Act Omnibus — nudification / NCII ban (new Art. 5 prohibition, 2026-12-02)**  
  The Omnibus adds an explicit prohibition on AI systems that generate non-consensual intimate imagery (NCII), including "nudification apps" that digitally remove clothing. Effective date: **December 2, 2026** (6-month grace period from formal adoption). CSAM also explicitly banned.  
  Source: <https://ec.europa.eu/commission/presscorner/detail/en/ip_26_1024>  
  **aigis impact:** The NCII prohibition is a new Art. 5 *prohibited practice* — the highest severity tier. aigis had no specific pattern for nudification requests. This is a gap that can be closed with a new `synth_ncii_request` detection pattern.

- **NIST AI RMF — Trustworthy AI in Critical Infrastructure Profile concept note (2026-04-07)**  
  NIST released a concept note and launched a community of interest for a new AI RMF Profile targeting critical infrastructure operators (IT/OT/ICS sectors). Profile is in early development; full draft expected Q4 2026.  
  Source: <https://www.nist.gov/programs-projects/concept-note-ai-rmf-profile-trustworthy-ai-critical-infrastructure>  
  **aigis impact:** Premature to create a template — too early in the standard's development. Track for cycle 18+.

- **NIST AI 600-1 (GenAI Profile) — 13 risks, 400+ actions**  
  The July 2024 Generative AI Profile remains the operative reference for gen-AI risk management under the AI RMF. The profile covers prompt injection, data poisoning, homoglyph evasion, and other aigis-relevant attack classes.  
  Source: <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>  
  **aigis impact:** aigis's existing detectors already address most of the 13 GenAI risks. NIST AI 600-1 text could be used to expand the NIST RMF mapping doc.

- **ISO/IEC 27090 — AI Cybersecurity Standard (FDIS stage, 2026)**  
  ISO/IEC 27090 "Cybersecurity — Artificial Intelligence — Guidance for addressing security threats to artificial intelligence systems" reached FDIS (Final Draft International Standard) in February 2026. Publication expected H2 2026. Covers adversarial ML, data poisoning, model theft, privacy attacks.  
  Source: <https://www.iso.org/standard/56581.html>  
  **aigis impact:** ISO 27090 is informative guidance, not certifiable requirements. No template warranted yet; can be referenced in docs once published.

- **ISO/IEC 42001:2026 (EN adaptation)**  
  European Committee for Standardization (CEN) published EN ISO/IEC 42001:2026 adapting the 2023 AI Management System standard. ISO 42001 is increasingly required by Fortune 500 vendor due-diligence and aligns with EU AI Act Art. 17 QMS requirements.  
  Source: <https://standards.iteh.ai/catalog/standards/cen/adc675e8-4669-4965-b4c1-c8f724832217/en-iso-iec-42001-2026>  
  **aigis impact:** The aigis compliance map could note ISO 42001 alignment where aigis implements AIMS controls. Low urgency for this cycle.

- **EU AI Omnibus — compliance simplification for Annex I machinery**  
  The agreement clarifies that AI-enabled machinery products covered by sector-specific safety legislation only need to comply with those sectoral rules, not with duplicate AI Act obligations. This reduces compliance burden for embedded AI in physical products.  
  Source: <https://ieu-monitoring.com/editorial/eu-reaches-ai-act-omnibus-deal-to-simplify-high-risk-compliance-and-ban-nudification-apps/1193132>  
  **aigis impact:** The `eu_ai_act_high_risk.yaml` template use-case comments may need a caveat for Annex I machinery.

- **Hogan Lovells note on Omnibus deal scope**  
  Legal analysis confirms the Omnibus is not yet formally adopted; both EP and Council must give formal endorsement. Institutions aim to complete formal adoption before August 2, 2026. The provisional agreement is, however, considered politically binding.  
  Source: <https://www.hoganlovells.com/en/publications/eu-legislators-agree-to-delay-for-highrisk-ai-rules>  
  **aigis impact:** Template comments should note the provisional status while still citing the new deadlines.

---

## Candidate Hardenings

1. **[IMPLEMENTED] Update `eu_ai_act_high_risk.yaml` deadline comments** — Replace the old August 2, 2026 deadline with the Omnibus deal deadlines (Dec 2, 2027 / Aug 2, 2028 / Dec 2, 2026 for NCII ban). Small comment-only change, no functional impact.

2. **[IMPLEMENTED] Add `eu_ai_ncii_generation` custom rule to `eu_ai_act_high_risk.yaml`** — New prohibited practice under Art. 5 / Omnibus. Score delta 80 (prohibited AI). Detects: nudify, undress, remove clothing, deepnude, non-consensual intimate imagery.

3. **[IMPLEMENTED] Add `synth_ncii_request` detection pattern to `aigis/filters/patterns.py`** — Puts the NCII detection into the always-on input filter (not just EU AI Act policy mode). Score 75 (just below CRITICAL). Aligned with EU prohibition effective 2026-12-02.

4. **[PENDING] NIST AI Critical Infrastructure Profile template** — Too early; concept note only, no draft content yet. Revisit when NIST publishes a draft profile (expected Q4 2026).

5. **[PENDING] ISO 27090 compliance guide under `docs/compliance/`** — Standard not yet formally published. Revisit H2 2026.
