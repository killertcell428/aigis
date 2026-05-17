# Pending: NIST IR 8596 Cyber AI Profile Compliance Template

## Title
New policy template: `nist_cyber_ai_profile.yaml`

## Motivation
NIST published a preliminary draft of the Cybersecurity Framework Profile for Artificial Intelligence (NIST IR 8596, "Cyber AI Profile") on December 16, 2025. The profile structures AI security across three focus areas: Secure, Defend, Thwart — mirroring the AI RMF's Govern/Map/Measure/Manage functions but applied specifically to AI system cybersecurity. Public comment period closed January 30, 2026; initial public draft expected H2 2026.

## Research finding that led to this idea
`auto-improvement/research/2026-05-17T09-15_8-compliance-regulation.md` — Finding 5 (NIST IR 8596 Cyber AI Profile).

## Proposed change
Create `policy_templates/nist_cyber_ai_profile.yaml` modelled after the existing `nist_ai_rmf.yaml` template. The template should:
- Reference Secure/Defend/Thwart focus areas from IR 8596
- Map aigis detection categories to the three focus areas
- Add custom rules for AI-specific threats (prompt injection, model tampering, adversarial input) with score deltas tuned to the Cyber AI Profile's risk priorities
- Include NIST IR 8596 section references in each custom rule

## Why it was held back
The document is still at preliminary draft stage (Initial Public Draft comment period closed Jan 2026; final public draft expected H2 2026). Creating a template against a preliminary draft risks outdating it as NIST refines the structure. Templates in aigis should target stable or final standards.

## Which constraint blocked it
The "informative at this stage" judgment from the research — the standard is not yet stable enough to template. No hard LOC or dependency constraint.

## Suggested next step for human reviewer
Revisit when NIST publishes the initial public draft of IR 8596 (expected H2 2026). At that point, create the template based on the stable Focus Area / Subcategory structure. The companion documents IR 8605 and IR 8605A (control overlays for fine-tuning and predictive AI) may also warrant separate templates at that time.
