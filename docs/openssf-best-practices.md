# OpenSSF Best Practices — Self-Assessment

This document is a self-assessment of how the Aigis project currently maps
to the [OpenSSF Best Practices Badge program](https://www.bestpractices.dev/)
criteria. It is the working notes used when filling in the BadgeApp form at
<https://www.bestpractices.dev/projects/new>.

- **Project:** Aigis
- **Repository:** <https://github.com/killertcell428/aigis>
- **Target tier:** Passing → Silver → (Gold, future)
- **Last reviewed:** 2026-05-07
- **Reviewer:** maintainer

Each row records: criterion, current evidence (file path, URL, or commit),
and status — `met` / `partial` / `unmet` / `n/a`.

---

## Passing Tier

### Basics

| Criterion | Evidence | Status |
| --- | --- | --- |
| Project website exists | `README.md`, GitHub repo page | met |
| Project documents what it does | `README.md` (one-line + sections), `ARCHITECTURE.md`, `docs/getting-started.md` | met |
| Project provides interaction info | `CONTRIBUTING.md`, GitHub Discussions enabled | met |
| Project license is OSI-approved | `LICENSE` (Apache-2.0), GitHub API `license.spdx_id == "Apache-2.0"` | met |
| License location is `LICENSE` (or equivalent) | `LICENSE` at repo root, `NOTICE` for attribution | met |
| Documentation explains how to install | `README.md` Quick Start (3 paths: pip / Docker / CLI) | met |
| Documentation explains how to use | `README.md`, `docs/getting-started.md`, `docs/api-reference.md` | met |

### Change Control

| Criterion | Evidence | Status |
| --- | --- | --- |
| Public version-controlled source | <https://github.com/killertcell428/aigis> | met |
| Interim versions visible | git history (full commits since v0.0.1) | met |
| Unique version numbering | Semantic versioning, latest tag `v1.0.0` | met |
| Release notes for each release | `CHANGELOG.md`, GitHub Releases page | met |

### Reporting

| Criterion | Evidence | Status |
| --- | --- | --- |
| Bug-reporting process | GitHub Issues, GitHub Discussions, `CONTRIBUTING.md` | met |
| Vulnerability reporting process | `SECURITY.md` — Private Security Advisory + email channel, 72h ack | met |
| Coordinated disclosure timeline | `SECURITY.md` — 90-day grace period documented | met |

### Quality

| Criterion | Evidence | Status |
| --- | --- | --- |
| Working build system | `pyproject.toml`, `python -m build`, GitHub Actions release workflow | met |
| Automated test suite | `pytest tests/` — 940+ tests passing in `.github/workflows/ci.yml` | met |
| Tests for new functionality | `CONTRIBUTING.md` PR checklist requires positive + negative tests | met |
| Tests run in CI | `.github/workflows/ci.yml` runs ruff + pytest on push and PR | met |

### Security

| Criterion | Evidence | Status |
| --- | --- | --- |
| Secure development knowledge | Maintainer is the author of 7-paper survey shipped in this repo (Mirror, StruQ, MI9, MemoryGraft, MSB, DataFilter, AdvJudge-Zero) | met |
| Basic cryptographic practices | Project does not roll its own crypto; HTTP delivery via PyPI / GHCR is TLS-only | n/a |
| Secured delivery | PyPI (`pyaigis`) + GHCR (`ghcr.io/killertcell428/aigis`) — both HTTPS-only, registry-signed | met |
| Publicly known vulnerabilities fixed | No open advisories on this repo; depends only on stdlib for the core | met |
| Other users' data not improperly exposed | Library is in-process; no telemetry; offline by default | met |

### Analysis

| Criterion | Evidence | Status |
| --- | --- | --- |
| Static code analysis | `ruff check aigis/ tests/` runs in CI; `mypy aigis/` documented in `CONTRIBUTING.md` | met |
| All medium+ static-analysis findings fixed before release | CI gate blocks PRs on lint failures | met |
| Dynamic code analysis | Optional at Passing tier; not yet added | n/a (Passing) / partial (Silver) |
| OpenSSF Scorecard supply-chain analysis | `.github/workflows/scorecard.yml` runs weekly + on push | met |

**Passing-tier verdict (self):** all criteria `met` or `n/a`. Ready to submit
the BadgeApp form.

---

## Silver Tier (gap analysis)

| Criterion | Evidence | Status |
| --- | --- | --- |
| Project has a code of conduct | `CODE_OF_CONDUCT.md` adopting Contributor Covenant 2.1 | met |
| Roles and responsibilities documented | `GOVERNANCE.md` — roles, decision-making, maintainer add/remove | met |
| At least 2 unrelated regular committers | Currently single-maintainer | unmet (project state) |
| Style guide for code | `CONTRIBUTING.md` — ruff + mypy + pytest sections | met |
| Tests cover ≥ 80% of statements | `pytest --cov-fail-under=68` enforced in CI; current floor 69%, ratchet target 80% | partial — ratchet plan documented |
| Coordinated disclosure timeline (≤ 60 days for fix) | `SECURITY.md` — 90-day grace, fix targets within that window | partial — tighten to 60 days |
| All required tests pass on supported platforms | CI matrix: ubuntu-latest × Python 3.11/3.12 + windows-latest + macos-latest smoke | met |
| Reproducible build is desirable | Pure-Python wheel, deterministic with `pyproject.toml`; not yet attested | partial |
| Cryptographic algorithms only use accepted/standard | n/a (no crypto in core) | n/a |

**Silver-tier verdict (self):** the project can submit Passing now and
backfill Silver as the gaps below close.

---

## Gold Tier (future)

Tracked here so we know what is left when we plan a v2.x push:

- 2+ unrelated maintainers actively committing.
- BadgeApp Silver achieved and stable.
- Reproducible build with attestations (e.g., Sigstore + SLSA L3 via
  `actions/attest-build-provenance`).
- 100% of public APIs covered by automated tests.
- Independent security review of the core (`Guard`, walls, server).

---

## Action Items (next steps to close Silver gaps)

1. ~~**`GOVERNANCE.md`** — document maintainer role, decision-making process,
   tiebreaker, and how to become a maintainer.~~ **Done 2026-05-07.**
2. ~~**CI test matrix** — extend `.github/workflows/ci.yml` to run on
   `ubuntu-latest`, `macos-latest`, `windows-latest`.~~ **Done — already in
   place.**
3. ~~**Coverage gate** — add `--cov-fail-under` to CI.~~ **Done 2026-05-07
   at 68% floor (current 69%); ratchet plan: bump by ~5% per minor release
   until 80%.**
4. **`SECURITY.md` tightening** — change "90-day grace" to "fix target ≤ 60
   days, public disclosure ≤ 90 days".
5. **Build provenance** — wire
   `actions/attest-build-provenance@v2` into `release.yml` and
   `docker-publish.yml`; publish Sigstore-signed attestations.
6. **Coverage ratchet** — climb from 69% → 80% by adding tests for the
   currently-uncovered modules: `aigis/safety/*` (240 lines, 0%),
   `aigis/weekly_report.py` (264 lines, 0%), `aigis/redteam.py` (27%),
   `aigis/spec_lang/parser.py` (51%).
7. **BadgeApp submission** — register the project at
   <https://www.bestpractices.dev/projects/new> using this self-assessment
   as the source for each row.

---

## Notes

- This file lives at `docs/openssf-best-practices.md` so reviewers can find
  it from the BadgeApp form's "documentation" links.
- When a row's evidence URL changes (e.g., a workflow file is renamed),
  update this file in the same PR.
