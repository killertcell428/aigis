# Governance

This document describes how decisions are made in the Aigis project, who
makes them, and how to become part of that process. It is intentionally
short — Aigis is a single-maintainer project at the time of writing, and
we want the rules to scale up gracefully as more maintainers join.

## Roles

### Users

Anyone using Aigis. Users contribute by filing issues, asking questions in
GitHub Discussions, and reporting security findings via `SECURITY.md`.

### Contributors

Anyone whose pull request has been merged. Contributors do not need any
prior status — opening a PR that gets merged makes you one. We list
notable contributions in `CHANGELOG.md` release notes.

### Maintainers

Maintainers have:

- write access to the repository,
- the right to merge pull requests after review,
- the responsibility to enforce `CODE_OF_CONDUCT.md`,
- the responsibility to triage incoming issues and security advisories
  per the timelines in `SECURITY.md`.

The current maintainer list:

- **@killertcell428** — project founder, primary maintainer.

### Becoming a Maintainer

A contributor is invited to become a maintainer when they have shown
sustained, high-quality contributions over time — typically:

- 5 or more merged non-trivial pull requests across different parts of
  the codebase, **and**
- consistent participation in code review or issue triage, **and**
- demonstrated alignment with the project's design principles
  (zero-dependency core, paper-grounded detection, evidence-based docs).

The decision is made by **lazy consensus** of the existing maintainers
(see below). If approved, the new maintainer is added to this file and
granted repository write access.

## Decision-Making

### Lazy Consensus

Routine decisions — bug fixes, documentation, small refactors, additions
that fit the existing architecture — are merged when:

1. At least one maintainer reviews and approves the pull request.
2. CI is green.
3. No other maintainer has objected within **72 hours** of approval.

If there is a single maintainer, "lazy consensus" reduces to "the
maintainer reviewed it and CI is green".

### Substantial Decisions

For decisions that materially change the project — adding a new wall,
breaking an API, adopting a new dependency for the core, changing the
license, redirecting the roadmap — we require:

1. A GitHub Discussion (or `RFC-` prefixed issue) describing the
   proposal, motivation, alternatives considered, and migration plan.
2. **At least 7 days** for community comment.
3. Explicit approval from a majority of active maintainers.

The active maintainer list at decision time is authoritative.

### Tiebreaker

If maintainers cannot reach consensus on a substantial decision, the
**project founder (@killertcell428)** has the final say. We expect this
power to be used rarely and only after good-faith discussion.

## Code Review

Every change goes through pull request review. The reviewer checks:

- The PR checklist in `CONTRIBUTING.md` is complete.
- New behaviour has tests (positive and negative cases).
- Documentation is updated alongside the code.
- The change does not introduce a runtime dependency to the core
  (`aigis/` package, excluding optional middleware).

A maintainer cannot self-approve a substantial change — they must request
review from another maintainer. For a single-maintainer project, this
rule kicks in once a second maintainer joins; until then, the founder
self-merges with extra care for substantial changes (RFC discussion +
7-day comment period).

## Conflict of Interest

Maintainers must disclose conflicts of interest (employment, financial
stake, personal relationship) when they affect a decision. The conflicted
maintainer should recuse themselves from approving the relevant pull
request or vote.

## Removing a Maintainer

A maintainer may be removed if they:

- become unreachable for **6 consecutive months** without notice,
- repeatedly violate `CODE_OF_CONDUCT.md` after a documented warning, or
- voluntarily step down.

Removal requires the same process as adding a maintainer: lazy consensus
of the remaining active maintainers. Removed maintainers are listed in
the repository history (commit log + this file's git history) but not in
the active list above.

## Changes to This Document

Changes to `GOVERNANCE.md` are themselves "substantial decisions" and
follow that process: RFC issue, 7-day comment period, majority approval.

---

*Last updated: 2026-05-07.*
