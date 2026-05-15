# Pending: Agentic AI Adoption Compliance Template

## Title
Compliance template aligned with the US/UK/AU/CA joint CISA/NSA advisory "Careful Adoption of Agentic AI Services" (April 30, 2026)

## Motivation
The five-nation joint advisory (CISA, NSA, ASD/ACSC, Canadian Cyber Centre, UK NCSC — April 30, 2026) documents that 65 % of organizations experienced agent-caused incidents in the past year, with 78 % of agents having overly broad permission scopes. The advisory defines "semantic privilege escalation" (agents using authorized permissions beyond their task scope) and provides concrete mitigations.

Real-world incidents cited include: Cursor/Claude 3.5 Opus deleting a production database and all backups in 9 seconds; OpenClaw prompt-injected output rewriting gateway configurations; CVE-2026-32211 (missing auth in Azure DevOps MCP).

A compliance template in `policy_templates/` would let aigis users assess their agentic AI deployments against the advisory's requirements.

## Which research finding led to this idea
Research file: `auto-improvement/research/2026-05-15T03-02_6-multi-agent.md`
Finding: "US/UK/AU/CA joint advisory 'Careful Adoption of Agentic AI'" (CISA/NSA/NCSC, April 30, 2026)

## Proposed change
Add `policy_templates/agentic_ai_adoption_joint_advisory_2026.yaml` covering:
- Task-scoped credential boundaries (temporary, revocable credentials per task)
- Agent capability sandboxing (each agent should have minimum necessary permissions)
- Explicit approval requirements for production-touching operations
- Immutable audit logging for all agent actions
- Regular permission audits (all agents should default to least-privilege)
- Semantic privilege escalation detection (agents using permissions beyond task scope)
- Recovery/rollback procedures for failed agent tasks
- Cross-agent trust verification requirements

Each check should map to an aigis policy rule or audit log field, enabling automated gap assessment.

## Why it was held back
- A meaningful compliance template covering 8 advisory requirements would exceed 100 LOC
- The template should reference specific advisory section numbers (the advisory PDF was not fully processed in this cycle)
- Proper YAML structure with descriptions, remediation guidance, and policy references requires careful design

## Which constraint blocked it
Hard constraint: "Any single change touching > 100 LOC across non-test files" → send to pending.

## Suggested next step for the human reviewer
1. Download and read the full advisory PDF from the URL in the research file
2. Map each advisory requirement to an existing aigis rule or audit field
3. Design the template as a gap-analysis checklist compatible with `aigis/compliance.py`
4. Implement in a dedicated compliance-regulation cycle (domain 8)
