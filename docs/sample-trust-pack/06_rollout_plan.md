# 6. Rollout Plan

We recommend introducing Aigis in three phases to limit risk while validating
it in real use. Each phase ends with a review gate that decides whether to
proceed to the next.

## Phase 1: Pilot (2 weeks)

Scope: [TO FILL: pilot team / project]

- [ ] Confirm the pilot team and scope
- [ ] Install the hook with `aigis init --agent claude-code`
- [ ] Verify the install with `aigis doctor`
- [ ] Run the default policy for two weeks; collect blocks, reviews, and false positives
- [ ] Review status via `aigis logs --alerts` and the weekly report
- [ ] Tune the policy in response to false positives

**Review gate 1:** Is the false-positive rate acceptable? Were there any
serious block events? Approver: [TO FILL: phase-1 approver]

## Phase 2: Expand

- [ ] Finalise the pilot-tuned policy as the department standard
- [ ] Expand to [TO FILL: next teams / departments]
- [ ] Enable the signed audit log
- [ ] Configure SIEM forwarding if required (`docs/forwarders.md`)
- [ ] Fold the incident runbook into operations

**Review gate 2:** Is audit-log integrity verifiable (`aigis audit verify`)?
Is the operational load reasonable? Approver:
[TO FILL: phase-2 approver]

## Phase 3: Organisation default

- [ ] Make Aigis the standard for all Claude Code use
- [ ] Establish the approval flow for policy changes
- [ ] Schedule periodic policy reviews (e.g. quarterly)
- [ ] Build pack regeneration into audit / compliance reporting

**Review gate 3:** Is the governance process sustainable?
Approver: [TO FILL: phase-3 approver]

---

_Regenerate this pack whenever the policy changes (it can run in CI), so the
documents you submit to IT always reflect the live posture._
