# Pending: EU AI Act Art. 52 Transparency Guidelines — Policy Template Extension

**Title:** Extend `eu_ai_act_high_risk.yaml` with Art. 52 guidance once EC guidelines are finalized

**Motivation:**
The European Commission opened consultation on draft guidelines for EU AI Act Article 52 transparency obligations on 2026-05-08. When the guidelines are finalized (expected H2 2026), aigis's EU AI Act policy template should be updated to reflect the specific requirements: disclosure wording, timing (start of interaction), frequency requirements for ongoing sessions, and exceptions for context where users clearly know they are dealing with AI.

**Research finding that led here:**
2026-05-12T00-55_8-compliance-regulation.md — finding on Art. 52 consultation opened May 2026.

**Proposed change:**
1. Add more comprehensive custom rules to `eu_ai_act_high_risk.yaml` for Art. 52 patterns once the guidelines clarify the exact requirements.
2. Optionally add a new `eu_ai_act_transparency.yaml` template targeting Art. 52-only deployments (limited-risk systems, not high-risk), so deployers with non-Annex III systems have a lighter-weight template.
3. Update the existing `eu_ai_transparency_bypass` custom rule with any additional phrasings identified in the official guidelines.

**Why it was held back:**
The guidelines are in consultation; the final text is not yet available. Building template rules against a draft that may change would require rework.

**Constraint that blocked it:**
The consultation period is open; implementing against unfinished regulatory guidance would produce speculative compliance artifacts.

**Suggested next step for human reviewer:**
Monitor https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai for finalized Art. 52 guidelines. Expected H2 2026. Once published, update the EU AI Act template and consider adding a lighter-weight transparency-only template for limited-risk systems.
