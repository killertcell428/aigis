# 5. Incident Runbook

## What happens when Aigis blocks an action

A Claude Code *PreToolUse* hook runs on every tool call. When Aigis **denies**
a request, the hook exits with code **2** and Claude Code aborts that tool
execution. The reason (the matched policy rule ID, and the risk score where
relevant) is printed to standard error and simultaneously written to the
audit log.

The hook is **fail-closed**: if it cannot reach a decision — unparseable
input, Aigis not installed, an exception during scanning — it blocks on the
safe side.

## Severity levels

| Severity | Guideline | Response |
|---|---|---|
| Critical | Risk score ≥ 80, or a denied destructive op (`rm -rf`, etc.) | Immediate block. Review the record; escalate if needed |
| High | Risk score 50–79 | Block or review. A responder examines it |
| Medium | Risk score 40–49, review decision | Human approval via the review queue |
| Low | Risk score < 40 | Allowed; logged only |

## Triage steps

1. List recent alerts: `aigis logs --alerts`
2. Inspect the event details (action, target, matched rule, risk score).
3. Verify audit-log integrity: `aigis audit verify`
4. If a legitimate action was blocked, follow "Reporting false positives" below.
5. If this looks like an attack, report it using the escalation template.

## Escalation template

```
Subject: [Aigis] {severity} — detected {rule_id}

When: {ISO-8601 timestamp}
Project / host: {project name / hostname}
User: {user_id}
Action: {action} Target: {target}
Risk score: {score}  Decision: {decision}
Matched rule: {rule_id}
Audit-log verification: {result of `aigis audit verify`}

First responder: [TO FILL: first responder name]
Escalate to: security@example.com
```

## Reporting false positives

1. Capture the exact blocked input/action (`aigis logs --alerts --json`).
2. Reproduce by re-scanning the input: `aigis scan "<input>"`
3. If it is genuinely legitimate, adjust the policy (see below).
4. Record the adjustment in the commit message for the review trail.

## Updating the policy

- Inspect the current policy: `aigis policy show`
- Edit `aigis-policy.yaml` to add or adjust rules.
- Validate: `aigis policy check`
- Version-control the change and apply it with sign-off from
  [TO FILL: approver / role].
