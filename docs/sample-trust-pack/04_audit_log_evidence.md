# 4. Audit Log Evidence

## Where logs live

Aigis keeps audit logs in three tiers (all append-only JSONL, one event per line):

- **Local logs:** `.aigis\logs` (per-project, developer-visible)
- **Global logs:** `~/.aigis/global/` (cross-project, for audit / CISO)
- **Alert archive:** `~/.aigis/alerts/` (deny / review events, permanent)

Current state: local logs are not yet created, with 0 events in the last 7 days and 0 in 30 days.

## Event schema (JSONL fields)

Each event is recorded as an `aigis.activity.ActivityEvent` with these fields:

- `action`
- `target`
- `agent_type`
- `user_id`
- `session_id`
- `event_type`
- `cwd`
- `project_name`
- `details`
- `risk_score`
- `risk_level`
- `matched_rules`
- `remediation_hints`
- `owasp_refs`
- `policy_decision`
- `policy_rule_id`
- `timestamp`
- `event_id`
- `autonomy_level`
- `delegation_chain`
- `estimated_cost`
- `memory_scope`
- `suggested_fix`
- `fix_applied`

## Retention / rotation

- Full logs are retained for 60 days by default, then auto-rotated
  (compressed or deleted).
- Alert logs (`~/.aigis/alerts/`) are kept permanently and never deleted.
- Run rotation/compression with: `aigis maintenance`

## Tamper-evidence design

The signed audit log (`aigis.audit.SignedAuditLog`) does two things per entry:

1. **HMAC-SHA256 signature** — every field of the entry is canonicalised to
   JSON and signed with a secret key. The signature depends on the entry's
   content, so changing a single byte fails signature verification.
2. **Hash chain** — each entry stores the SHA-256 hash of the previous entry
   (`prev_hash`), so deleting, reordering, or inserting entries is detectable.

Integrity is checked with four tests: signature, chain, sequence, and
timestamp ordering.

**Verify command:**

```
aigis audit verify
```

Use `--log PATH` to point at a specific log file and `--json` for a
machine-readable result. Use `aigis audit status` for a quick health check.
Current state: signed audit log is
enabled.

## Key management — read this before relying on tamper-evidence

The HMAC key is resolved in this order (see `aigis/audit/signed_log.py`):

1. An explicit `secret_key` supplied by the caller.
2. An existing key file at `.aigis/audit_key`.
3. Otherwise a fresh key is generated (`secrets.token_hex(32)`) and written there.

**What this means for a reviewer.** In the default configuration the signing key
sits on the same machine as the agent and the logs, owned by the same user. The
signature therefore detects tampering by anything *other than* the log's own
author — a later process, another user, file corruption. It does **not** detect
the author editing an entry and re-signing it, because they hold the key.

If your threat model includes the developer whose activity is being recorded —
which is usually the reason an audit trail exists at all — combine the signed log
with at least one of the following:

- **SIEM forwarding** (next section). Events mirrored to Splunk, Sentinel, Elastic,
  or Datadog land outside the developer's reach. This is the strongest option
  available today, and it requires no change to Aigis.
- **An externally-held key.** Pass `secret_key` from a secret manager the developer
  cannot read, so local forgery is not possible.
- **Off-box export** of `~/.aigis/alerts/` to storage the developer cannot write to.

One platform note: the key file is set to `0600` on POSIX, but Windows does not
enforce POSIX permissions — set NTFS ACLs explicitly there.

## SIEM forwarding

Events can optionally be forwarded to an external SIEM (Elastic Common Schema,
over HTTP). Forwarding is non-blocking and never delays an agent tool call. A
PII redactor can run before any event leaves the process. See
`docs/forwarders.md`. Current state: not detected (forwarders are configured in code; see docs/forwarders.md).
