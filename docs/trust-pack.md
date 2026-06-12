# `aigis trust-pack` — IT/Security Adoption Approval Pack

`aigis trust-pack` generates a bilingual (Japanese / English) **adoption
approval pack** — the set of documents a corporate IT or information-security
department (情報システム部門) reviews before approving Claude Code, or another
autonomous AI agent, for company use.

The whole point is honesty: every document is generated from your **live local
Aigis configuration** (the active policy, installed hooks, and on-disk audit /
activity logs), never from marketing claims. Anything that is genuinely
organisation-specific is left as an explicit fill-in field, not invented.

## Who it is for

- **Engineering leads / champions** who want to bring Claude Code into a
  company and need an artefact to hand to security review.
- **IT / security reviewers (情報システム部門)** who need to understand what an
  AI coding agent can do, what guardrails are in place, how actions are
  audited, and where the scope boundary lies — in a format they can read,
  print, and file.

## Usage

```
aigis trust-pack [-o/--output DIR] [--lang {ja,en,both}] [--format {markdown,html}] [--org NAME] [--contact EMAIL]
```

Defaults: `-o ./aigis-trust-pack --lang both --format markdown`.

| Flag | Default | Description |
|---|---|---|
| `-o`, `--output` | `./aigis-trust-pack` | Output directory |
| `--lang` | `both` | `ja`, `en`, or `both` |
| `--format` | `markdown` | `markdown` (multiple files) or `html` (one self-contained file) |
| `--org` | — | Organisation name, substituted into the documents |
| `--contact` | — | Security contact email, substituted into the documents |

### Examples

Generate the full bilingual Markdown pack into `./aigis-trust-pack/`:

```bash
aigis trust-pack
```

English-only, with your organisation details filled in:

```bash
aigis trust-pack --lang en --org "Acme Inc." --contact "security@acme.example"
```

A single printable / emailable HTML file (both languages, inline CSS, no JS):

```bash
aigis trust-pack --format html -o ./review
# -> ./review/aigis-trust-pack.html  (open in a browser, print to PDF)
```

## What each file contains

In Markdown mode, the pack is an index plus six documents per selected
language (English files use the plain stem, Japanese files use the `.ja`
suffix):

| File | Contents |
|---|---|
| `README.md` | Index, generation timestamp, Aigis version, live posture summary, list of every file in the pack, and the honesty principle |
| `01_executive_summary(.ja).md` | What Claude Code is, what Aigis adds (deterministic pre-execution guardrails + tamper-evident audit logs + org-owned policy), what the pack contains, and the **current live posture** (policy profile, hook status, log status) |
| `02_control_matrix(.ja).md` | Table of Aigis controls × framework mappings (ISO/IEC 27001:2022 Annex A, NIST AI RMF, OWASP LLM Top 10, AI事業者ガイドライン v1.2), plus an explicit **"What Aigis does NOT cover"** section |
| `03_policy_snapshot(.ja).md` | Human-readable rendering of the **active** policy, with the literal policy YAML appended |
| `04_audit_log_evidence(.ja).md` | Where logs live, the JSONL schema (field list straight off `ActivityEvent`), retention/rotation, the HMAC + hash-chain tamper-evidence design, and the exact `aigis audit verify` command |
| `05_incident_runbook(.ja).md` | What happens when Aigis blocks (the fail-closed hook exit flow), severity levels, triage steps, an escalation template, and how to report false positives / update policy |
| `06_rollout_plan(.ja).md` | A three-phase pilot template (2-week pilot → expand → org default) with checkboxes and review gates |

In `--format html` mode, all of the above is rendered into a single
self-contained `aigis-trust-pack.html` with inline CSS, anchor navigation, and
print styles — no JavaScript and no external/CDN resources, so it is safe to
email to a security team.

## Honesty principles

- **Generated from live config.** The policy snapshot is the policy actually in
  force. The posture summary reflects whether the hook is installed and whether
  logs exist *right now*. If you have not run `aigis init`, the pack says so and
  documents the built-in default policy.
- **Org-specific fields are explicit templates.** Data classification rules,
  approver names, and escalation contacts cannot be known from the codebase, so
  they appear as `[TO FILL: ...]` (English) / `【要記入: ...】` (Japanese)
  markers. Passing `--org` / `--contact` substitutes those where relevant; the
  rest remain visible placeholders for you to complete.
- **Compliance mappings are evidence, not certification.** ISO/IEC 27001 items
  are phrased as "supports evidence for". Aigis is a control *implementation*,
  not a certification body — the pack never claims to *certify* or *guarantee*
  compliance with any framework.
- **The scope boundary is stated up front.** The control matrix always includes
  a "What Aigis does NOT cover" section (model training, content-moderation
  policy, network DLP, endpoint security, Claude Code's own cloud-side
  processing, IAM).

## Related command: `aigis audit verify`

The audit-log evidence document points reviewers at the integrity-verification
command:

```bash
aigis audit verify            # verify .aigis/audit.jsonl (signature + chain + sequence + timestamp)
aigis audit verify --log PATH # verify a specific signed log
aigis audit verify --json     # machine-readable result
aigis audit status            # key present? log present? entry count
```

`aigis audit verify` runs the four integrity checks from
`aigis.audit.AuditVerifier` and exits `0` when the log is intact, `1` when
tampering (or a missing log) is detected — suitable for CI gating.

## CI usage example

Regenerate the pack automatically whenever the policy changes, so the documents
you submit to IT always reflect the live posture. Example GitHub Actions step:

```yaml
name: trust-pack
on:
  push:
    paths:
      - "aigis-policy.yaml"
      - ".claude/settings.json"
jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --all-extras
      # Fail the build if the signed audit log has been tampered with.
      - run: uv run aigis audit verify || true   # no signed log yet -> non-fatal
      # Regenerate the approval pack from the (now updated) live config.
      - run: uv run aigis trust-pack --org "Acme Inc." --contact "security@acme.example"
      - uses: actions/upload-artifact@v4
        with:
          name: aigis-trust-pack
          path: aigis-trust-pack/
```

You can also commit the regenerated pack back into the repository so reviewers
always see the current version under change control.
