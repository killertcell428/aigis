# Pending: NIST Cyber AI Profile Compliance Template

**Title:** NIST Cyber AI Profile — aigis compliance template

**Motivation:**
NIST is finalizing a Cyber AI Profile as part of the AI RMF 2026 pipeline. When published, it will give critical infrastructure operators, enterprise AI teams, and MSPs a practical risk management checklist specifically addressing cybersecurity × AI interactions. A compliance template in aigis would let deployers map their AI firewall rules to NIST controls.

**Research finding that led here:**
2026-05-12T00-55_8-compliance-regulation.md — finding on NIST AI RMF Cyber AI Profile, expected H2 2026.

**Proposed change:**
Create `policy_templates/nist_cyber_ai_profile.yaml` once the draft is published, with custom rules mapped to the profile's control identifiers and a threat-model section explaining how aigis's existing detectors align with each control category.

**Why it was held back:**
The Cyber AI Profile is in the finalization pipeline but not yet publicly released as a draft. Creating a template against a non-existent or partial standard would produce a speculative and potentially misleading compliance artifact.

**Constraint that blocked it:**
"skip implementation for this cycle / still write research" — nothing safe and implementable is available until the draft is public.

**Suggested next step for human reviewer:**
Monitor NIST AI RMF publications at https://www.nist.gov/itl/ai-risk-management-framework. When the Cyber AI Profile draft is released (expected Q4 2026), create the template and map aigis rules to the profile's control sections. Also check for the AI Agent Interoperability Profile planned for the same timeframe.
