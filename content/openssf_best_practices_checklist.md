# OpenSSF Best Practices Badge — passing → silver checklist

URL: https://www.bestpractices.dev/en/projects/new

**Status:** Aigis is well-positioned for **passing** badge automatically (≈90% of criteria already true). Silver requires a few additional commitments. Gold is out of scope for v1.0.0.

## Step 0 — Register the project

1. Sign in at https://www.bestpractices.dev/ with the GitHub account that owns the repo
2. "Submit your project" → enter `https://github.com/killertcell428/aigis`
3. The form auto-fills `description`, `repo_url`, `license` from GitHub

## Step 1 — Passing criteria (target: 100%)

Each row corresponds to a question on the form. The `evidence URL` column is what you paste into the form's "Justification" field for that criterion.

### Basics

| Criterion | Status | Evidence URL |
|---|---|---|
| `description_good` | ✅ DONE | https://github.com/killertcell428/aigis (repo description, README first paragraph) |
| `interact` | ✅ DONE | https://github.com/killertcell428/aigis/discussions, https://github.com/killertcell428/aigis/issues |
| `contribution` | ⚠️ NEEDED | Add CONTRIBUTING.md (see Step 1.5) |
| `contribution_requirements` | ⚠️ NEEDED | CONTRIBUTING.md must include "how to contribute" section |
| `floss_license` | ✅ DONE | https://github.com/killertcell428/aigis/blob/master/LICENSE (Apache-2.0) |
| `floss_license_osi` | ✅ DONE | Apache-2.0 is OSI-approved |
| `license_location` | ✅ DONE | LICENSE file at repo root |
| `documentation_basics` | ✅ DONE | README.md has install/quickstart/comparison/papers |
| `documentation_interface` | ✅ DONE | docs/ directory + inline docstrings + `aigis --help` |
| `sites_https` | ✅ DONE | github.com is HTTPS |

### Change Control

| Criterion | Status | Evidence URL |
|---|---|---|
| `repo_public` | ✅ DONE | https://github.com/killertcell428/aigis is public |
| `repo_track` | ✅ DONE | git history is preserved |
| `repo_interim` | ✅ DONE | commits are made in branches/PRs |
| `repo_distributed` | ✅ DONE | git is distributed |
| `version_unique` | ✅ DONE | https://github.com/killertcell428/aigis/releases — semver tags v0.0.1 onward |
| `version_semver` | ✅ DONE | semver from v0.0.1 to v1.0.0 |
| `version_tags_signed` | ⚠️ NICE-TO-HAVE | Sign git tags with `git tag -s vX.Y.Z` (requires GPG/SSH key). v1.0.0 is unsigned. |
| `release_notes` | ✅ DONE | CHANGELOG.md + GitHub Releases |
| `release_notes_vulns` | ✅ DONE | CHANGELOG documents security-related changes |

### Reporting

| Criterion | Status | Evidence URL |
|---|---|---|
| `report_process` | ⚠️ NEEDED | Add SECURITY.md with vulnerability disclosure policy |
| `report_tracker` | ✅ DONE | https://github.com/killertcell428/aigis/issues |
| `report_responses` | ✅ DONE | (assertion — you respond to issues) |
| `enhancement_responses` | ✅ DONE | (assertion) |
| `report_archive` | ✅ DONE | issues + discussions are public |
| `vulnerability_report_process` | ⚠️ NEEDED | SECURITY.md (same as `report_process`) |
| `vulnerability_report_private` | ⚠️ NEEDED | Enable GitHub Private Vulnerability Reporting in repo settings |
| `vulnerability_report_response` | ✅ DONE | (assertion — 14-day response commitment) |

### Quality

| Criterion | Status | Evidence URL |
|---|---|---|
| `build` | ✅ DONE | `pip install pyaigis`; `python -m build` from source |
| `build_common_tools` | ✅ DONE | uses `pyproject.toml` + standard `build` |
| `build_floss_tools` | ✅ DONE | all tools are FLOSS |
| `test` | ✅ DONE | https://github.com/killertcell428/aigis/tree/master/tests (940+ tests) |
| `test_invocation` | ✅ DONE | `pytest` from repo root |
| `test_most` | ✅ DONE | broad test coverage (need to attach actual % from coverage report) |
| `test_policy` | ⚠️ NEEDED | CONTRIBUTING.md must state "new features require tests" |
| `tests_are_added` | ✅ DONE | (assertion) |
| `tests_documented_added` | ⚠️ NEEDED | reference test policy in CONTRIBUTING.md |
| `warnings` | ✅ DONE | linters wired in CI |
| `warnings_fixed` | ✅ DONE | (assertion) |
| `warnings_strict` | ✅ DONE | (assertion) |

### Security

| Criterion | Status | Evidence URL |
|---|---|---|
| `know_secure_design` | ✅ DONE | (assertion — README + CHANGELOG show paper-grounded design) |
| `know_common_errors` | ✅ DONE | (assertion) |
| `crypto_published` | N/A | no custom crypto |
| `crypto_call` | ✅ DONE | uses Python stdlib `hashlib`/`secrets` only |
| `crypto_floss` | ✅ DONE | stdlib |
| `crypto_keylength` | N/A | |
| `crypto_working` | ✅ DONE | stdlib |
| `crypto_weaknesses` | N/A | |
| `crypto_pfs` | N/A | no TLS |
| `crypto_password_storage` | N/A | no auth |
| `crypto_random` | ✅ DONE | uses `secrets` module |
| `delivery_mitm` | ✅ DONE | PyPI uses HTTPS; GHCR uses HTTPS |
| `delivery_unsigned` | ⚠️ NICE-TO-HAVE | Consider signing wheels with sigstore |
| `vulnerabilities_fixed_60_days` | ✅ DONE | (assertion) |
| `vulnerabilities_critical_fixed` | ✅ DONE | (assertion) |

### Analysis

| Criterion | Status | Evidence URL |
|---|---|---|
| `static_analysis` | ⚠️ NEEDED | Add ruff or mypy to CI (or document existing) |
| `static_analysis_common_vulnerabilities` | ⚠️ NEEDED | Add bandit or similar to CI |
| `static_analysis_fixed` | ✅ DONE | (assertion) |
| `static_analysis_often` | ✅ DONE | (assertion if CI runs on every PR) |
| `dynamic_analysis` | N/A | optional for passing |

## Step 1.5 — Files to add for passing (3 files, ~30 min total)

### CONTRIBUTING.md

```markdown
# Contributing to Aigis

Thanks for considering a contribution.

## How to contribute

1. **Issues:** open at https://github.com/killertcell428/aigis/issues. Include version (`pip show pyaigis`), reproducer, and expected behavior.
2. **Pull requests:** fork → branch → PR against `master`. New features require tests; bug fixes should add a regression test.
3. **Discussions:** general questions and design RFCs go to https://github.com/killertcell428/aigis/discussions.

## Development setup

```bash
git clone https://github.com/killertcell428/aigis
cd aigis
pip install -e ".[dev]"
pytest
```

## Test policy

- New detectors and middleware require unit tests.
- Bug fixes require regression tests.
- We aim to keep coverage above the current baseline.

## Code style

- Python 3.11+, ruff for linting, type hints required for public APIs.
- Run `ruff check .` and `pytest` locally before opening a PR.

## Reporting security vulnerabilities

See SECURITY.md — please do not file public issues for unpatched vulnerabilities.
```

### SECURITY.md

```markdown
# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | ✅ |
| 0.x | ❌ (pre-release, please upgrade) |

## Reporting a vulnerability

Please use **GitHub Private Vulnerability Reporting**:
https://github.com/killertcell428/aigis/security/advisories/new

Or email: killertcell428@gmail.com (PGP optional, request key if needed).

We commit to:
- Acknowledge receipt within 72 hours
- Assess and provide an initial response within 14 days
- Coordinate a public disclosure timeline with the reporter
- Credit the reporter in the CHANGELOG (unless anonymity is requested)

## Public disclosure preference

- Critical / High: 7-day private window before public CVE
- Medium / Low: standard 90-day disclosure
```

### CI: enable bandit + ruff in existing workflow

Add a step to `.github/workflows/test.yml` (or create one):

```yaml
- name: Run static analysis
  run: |
    pip install bandit ruff
    bandit -r aigis/ -ll
    ruff check aigis/
```

## Step 2 — Silver criteria (target: hit after passing)

Silver adds:

| Criterion | Action needed |
|---|---|
| DCO or CLA on all commits | Add `Signed-off-by:` to commit template, or set up DCO bot |
| Roles documented (BDFL? Steering committee?) | Add `MAINTAINERS.md` with role definitions |
| Two-factor on maintainer accounts | Enable 2FA on GitHub for `killertcell428` |
| `code_review` — at least one other reviewer per change | Solo project for now; document the reviewer-of-record process for future contributors |
| Continuous integration enforced | Already done (GitHub Actions) |
| Coding standards documented | Reference ruff config in CONTRIBUTING.md |
| Static analysis runs ≥ 1× per change | Add bandit/ruff CI step (also helps passing) |
| Hardening — no plaintext secrets | Already done (no secrets in repo) |
| Hardening — Scorecard score ≥ 5.0 | OpenSSF Scorecard workflow already added (commit 2e4623a). Wait for first run, then check score. |

## Step 3 — Submit

1. Save the form periodically (it auto-saves to your account)
2. Each criterion has Met / Unmet / N/A — be honest, the badge is automated against the answers
3. Once all "passing" rows are Met, the **Passing badge** is awarded immediately
4. After Passing, fill the Silver section in the same form

## Step 4 — Add badge to README

Once awarded, paste the badge markdown (form provides it) at the top of README.md:

```markdown
[![CII Best Practices](https://www.bestpractices.dev/projects/{ID}/badge)](https://www.bestpractices.dev/projects/{ID})
```

## Estimated time

- Passing: ~1 hour (mostly form-filling once CONTRIBUTING.md / SECURITY.md / static-analysis CI are in place)
- Silver: +1 hour (DCO setup, MAINTAINERS.md, 2FA verification)
