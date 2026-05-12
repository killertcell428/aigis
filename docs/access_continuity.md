# Access Continuity & Key Custody

> Last updated: 2026-05-12
>
> This document satisfies the OpenSSF Best Practices Silver tier
> `access_continuity` criterion. It records which credentials,
> accounts, and access tokens are required to keep the project running,
> where they live, and how the project would recover if the current
> maintainer were suddenly unavailable.

---

## 1. Inventory of Project Secrets

| Asset | Used for | Storage | Rotation | Recovery |
| --- | --- | --- | --- | --- |
| **GitHub repository** | Source of truth, issue tracker, Actions | <https://github.com/killertcell428/aigis> | n/a | Owned by GitHub account; recovery via GitHub account recovery codes (stored offline) |
| **PyPI project `pyaigis`** | Distribution to end users | <https://pypi.org/project/pyaigis> | n/a | Owner+maintainer accounts on PyPI; recovery via PyPI account 2FA recovery codes |
| **PyPI Trusted Publishing (OIDC)** | Token-less release from GitHub Actions | Configured at <https://pypi.org/manage/project/pyaigis/settings/publishing/> — no long-lived secret to leak | Auto-rotated per-workflow-run (OIDC) | Re-configure publisher binding from PyPI UI |
| **GHCR (`ghcr.io/killertcell428/aigis`)** | Container distribution | GitHub Container Registry — uses `GITHUB_TOKEN` per workflow | Per-run | Tied to GitHub repo permissions |
| **Sigstore (cosign keyless)** | Release artifact signing | OIDC, no long-lived key | Per-run | Re-runs from any maintainer with `id-token: write` permission |
| **`security@killertcell428.dev`** | Vulnerability intake | Email forwarder, 2FA-enabled mailbox | Password every 12 months | Domain registrar account holds DNS; documented below |
| **Domain `killertcell428.dev`** | Security contact email, future docs site | Registrar account (Cloudflare Registrar) | Auto-renew, multi-year | Registrar recovery codes stored offline |
| **`CHANGELOG.md` automation token** | None — uses `GITHUB_TOKEN` | n/a | n/a | n/a |

No long-lived PyPI API tokens, no long-lived GHCR tokens, and no
private signing keys are stored in repository secrets. All release-
path credentials are short-lived OIDC tokens minted per workflow run.

The `GITHUB_TOKEN` secrets used by workflows are issued per-job by
GitHub and expire when the job ends.

## 2. Maintainer Account Hygiene

The maintainer's GitHub and PyPI accounts:

- have 2FA enforced (hardware key + TOTP backup),
- have recovery codes printed and stored offline,
- use unique passphrases stored in a password manager with a separate
  master passphrase,
- have `git config user.signingkey` configured for signed commits
  where applicable.

GitHub recovery codes and PyPI recovery codes are stored in two
separate, geographically distinct, offline locations.

## 3. Bus-Factor Plan

The project is currently maintained by a single individual
(`killertcell428`). This is acknowledged as a bus-factor-of-1 risk and
is tracked in [openssf-best-practices.md](openssf-best-practices.md)
as a known Silver-tier gap.

### Short-term mitigations (in effect now)

- **No private keys.** Every release-path credential is short-lived
  OIDC. There is no key custody to transfer.
- **Self-contained repository.** All build steps, tests, infra-as-code
  (workflows, Dockerfile, `pyproject.toml`) live in this repo. A new
  maintainer can fork and continue without contacting anyone.
- **Documentation.** `ARCHITECTURE.md`, `GOVERNANCE.md`,
  `ROADMAP.md`, `SECURITY.md`, `CONTRIBUTING.md`, this file, and
  `docs/openssf-best-practices.md` collectively describe how to run
  and govern the project end-to-end.
- **Permissive license.** Apache-2.0 — anyone may fork and continue.
- **Pinned action SHAs.** Workflows pin every action by SHA so
  reproducibility does not depend on the maintainer.

### Medium-term plan

- **Active maintainer recruitment.** Tracked in `GOVERNANCE.md`
  ("Becoming a Maintainer"). Target: ≥ 2 unrelated regular committers
  before declaring Silver `bus_factor` met.
- **Dead-man's switch documentation.** Should this maintainer be
  unreachable for 90+ days with no commits and no advisory response,
  the next-highest-commit contributor at that time may post a public
  issue requesting maintainership transfer. If no objection from the
  current maintainer is received within 30 additional days, GitHub's
  "transferring a repository" or "fork takeover" mechanisms apply.
- **PyPI takeover.** PyPI's [PEP 541 process][pep541] covers project
  abandonment. The next maintainer would file a PEP 541 request once
  the maintainer has been unresponsive per PyPI's policy.

[pep541]: https://peps.python.org/pep-0541/

### Onboarding a new maintainer (when one is identified)

The current maintainer will:

1. Open a PR adding the new maintainer to `GOVERNANCE.md`.
2. Invite them to the GitHub repo with `Maintain` role (not `Admin`)
   for a probation period.
3. Add them as a PyPI maintainer (not Owner) on `pyaigis`.
4. After 90 days of active contribution, promote to Owner on PyPI and
   `Admin` on GitHub via a second PR.
5. Add them to `security@killertcell428.dev` as a forwarder
   recipient.

## 4. Disaster Scenarios

| Scenario | Detection | Response |
| --- | --- | --- |
| Maintainer GitHub account compromised | GitHub security alert, unexpected pushes | Revoke sessions, rotate password & 2FA, audit recent merges, force-push protected branches back to known-good if necessary |
| Maintainer PyPI account compromised | PyPI emails about new tokens, unexpected releases | Rotate password & 2FA, yank malicious releases, post advisory linking to last-known-good version, rotate Trusted Publishing binding |
| Maintainer unavailable (illness, etc.) | No commits / advisory replies for 30 days | Followers may post a public issue; after 90 days of silence, see §3 dead-man's switch |
| Domain `killertcell428.dev` lapses | Renewal failure email | Multi-year auto-renew + registrar account 2FA make this unlikely; in worst case, security reporting falls back to GitHub Private Security Advisory only, and `SECURITY.md` is updated |
| Repository deleted by mistake | n/a — pushes fail | Restore from any maintainer's local clone or any fork; full history is preserved in git |
| Pre-1.0 / 1.0 release retracted | PyPI emails to maintainer | Yanked version remains visible but is not installed by `pip install pyaigis`; a patched release is cut |

## 5. Review

This document is reviewed at every minor release alongside
[assurance_case.md](assurance_case.md) and updated whenever the
inventory in §1 changes.
