# Pending: NIST AI Critical Infrastructure Profile Policy Template

## Title
New policy template: `policy_templates/nist_ai_critical_infra.yaml`

## Motivation
On April 7, 2026, NIST released a concept note for an AI RMF Profile on "Trustworthy AI in Critical Infrastructure" targeting IT/OT/ICS sectors across all 16 US critical infrastructure sectors. This profile will complement NIST AI 600-1 (GenAI Profile) with ICS/SCADA-specific risk management practices. A corresponding aigis policy template would help operators of critical infrastructure AI systems (power grids, water treatment, transportation, healthcare networks) apply aigis with appropriate thresholds and rules.

Research source: <https://www.nist.gov/programs-projects/concept-note-ai-rmf-profile-trustworthy-ai-critical-infrastructure>

## Proposed Change
Create `policy_templates/nist_ai_critical_infra.yaml` with:
- `auto_block_threshold: 45` (strict, OT environments have low tolerance for uncertainty)
- Custom rules covering: OT/ICS command injection via AI, lateral movement requests, AI bypass of safety interlocks, AI-driven firmware modification requests
- Comments mapping to NIST AI RMF subcategories from the critical infrastructure profile

## Why Held Back
The NIST concept note was released 2026-04-07. The actual profile draft has not yet been published — NIST is still forming its Community of Interest and gathering stakeholder input. A full draft is expected Q4 2026. Creating a template based on a concept note would be speculative and could mislead operators about the standard's actual content.

**Constraint:** Premature implementation (source material insufficient).

## Suggested Next Step
Check the NIST AI RMF page for a published draft profile (likely Q4 2026). When a draft is available, review ICS-specific subcategories and create the policy template in that cycle.
