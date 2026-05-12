# Pending: UK AI Security Institute Policy Template

**Title:** Add `policy_templates/uk_ai_security.yaml` for UK regulatory context

**Motivation:**
The UK AI Security Institute (AISI, formerly AI Safety Institute) operates as a risk-monitoring and technical evaluation body. DSIT has published five cross-sector principles (safety/security/robustness, transparency, fairness, accountability, contestability). However, the UK has not enacted standalone AI legislation as of April 2026, and there is no published draft and no commencement timetable for a statutory basis.

A sector-agnostic policy template aligned to the UK principles would be useful for UK-market deployments, but without statutory requirements there are no specific legal obligations to detect bypass attempts against.

**Research finding:** 2026-05-12T00-16_8-compliance-regulation.md (Finding 8)

**Proposed change:**
Create `policy_templates/uk_ai_security.yaml` covering:
- DSIT Principle 1 (safety/security/robustness): adversarial robustness bypass
- DSIT Principle 2 (transparency): AI identity disclosure suppression
- DSIT Principle 3 (fairness): demographic discrimination instructions
- DSIT Principle 4 (accountability/governance): oversight bypass
- DSIT Principle 5 (contestability/redress): suppression of appeal/redress information

**Why held back:**
The UK regulatory framework is principles-based with no statutory obligations. Without specific legal requirements, the template would be too generic to justify over the existing `eu_ai_act_high_risk.yaml` template (which UK deployers serving EU users must also comply with). Creating a UK-specific template now would likely duplicate content from other templates without adding genuine compliance value.

**Constraint:** No blocking constraint; a judgment call that the regulatory signal is too weak.

**Suggested next step:** Monitor UK AI legislation. Once the AISI receives statutory status or the UK publishes sector-specific AI requirements, revisit this template. Expected trigger: commencement of UK AI legislation (no timetable as of 2026-04).
