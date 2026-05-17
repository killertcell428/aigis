#!/usr/bin/env bash
# release_preflight.sh — gatekeeper the auto-improvement loop MUST call
# before pushing a release tag. Implements the rules CLAUDE.md spells out
# under "Tag ordering — never tag before merging to master" and addresses
# the v1.1.2 / v1.1.3 orphan-release incident (Issue #56).
#
# Exit codes:
#   0  — safe to push the tag
#   2  — tag already exists on the remote (collision); abort, DO NOT bump
#   3  — release commit is not reachable from origin/master (orphan); abort
#   4  — local branch is not on the master tip (so the tag would point
#         somewhere humans haven't reviewed); abort
#   5  — usage error
#
# Usage:
#   ./release_preflight.sh vX.Y.Z              # checks current HEAD
#   ./release_preflight.sh vX.Y.Z <commit-sha> # checks the given sha
#
# The script never modifies the repo. It only reads. Run it from inside
# a working checkout (it uses `git fetch origin --tags`).

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  cat >&2 <<USAGE
release_preflight.sh — verify a tag is safe to push.

Usage: $0 vX.Y.Z [commit-sha]
USAGE
  exit 5
fi

TAG="$1"
SHA="${2:-HEAD}"

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([ab][0-9]+)?$ ]]; then
  echo "[preflight] FAIL — tag $TAG does not match the release tag pattern vX.Y.Z" >&2
  exit 5
fi

echo "[preflight] checking $TAG against $SHA"

# 1. Refresh remote view of tags + master.
git fetch --quiet origin --tags
git fetch --quiet origin master

RESOLVED_SHA=$(git rev-parse --verify "$SHA^{commit}" 2>/dev/null || true)
if [[ -z "$RESOLVED_SHA" ]]; then
  echo "[preflight] FAIL — could not resolve commit $SHA" >&2
  exit 5
fi

# 2. Collision check — remote tag already exists?
if git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1; then
  EXISTING=$(git ls-remote --tags origin "refs/tags/$TAG" | awk '{print $1}')
  cat >&2 <<MSG
[preflight] FAIL (exit 2) — tag $TAG already exists on the remote.
            Existing tag points to: $EXISTING
            Local release commit:   $RESOLVED_SHA

DO NOT bump the version and retry. That is the pattern that produced
the v1.1.1 → v1.1.2 → v1.1.3 orphan-release cascade (Issue #56).

Recovery:
  1. Stop the release run. Do not push any tag.
  2. Inspect the existing tag:
       git fetch --tags && git log $EXISTING --oneline -5
  3. If the existing tag is itself orphaned (not reachable from master),
     escalate to a human — the right fix is to either:
       a) Land THIS release commit on master and re-tag with a fresh
          version number that skips the burned numbers, or
       b) Delete the orphan tag from the remote (only if no PyPI
          release was published for it).
  4. The auto-improvement loop must not retry until a human resolves
     the collision.
MSG
  exit 2
fi

# 3. Orphan check — release commit must be reachable from origin/master.
if ! git merge-base --is-ancestor "$RESOLVED_SHA" origin/master; then
  cat >&2 <<MSG
[preflight] FAIL (exit 3) — release commit $RESOLVED_SHA is NOT reachable
            from origin/master. Tagging it would produce an orphan release
            that the release.yml guard will reject — but the bad tag will
            still pollute the remote tag namespace.

Recovery:
  1. Merge the release commit's PR into master via the normal review flow.
  2. Re-run preflight against the master HEAD that contains the release.
  3. Only then push the tag.
MSG
  exit 3
fi

# 4. Master-tip check — tagging behind master invites confusion (the
#    release would not include subsequent fixes that landed first). The
#    loop should always tag the master tip, not an old commit.
MASTER_HEAD=$(git rev-parse origin/master)
if [[ "$RESOLVED_SHA" != "$MASTER_HEAD" ]]; then
  cat >&2 <<MSG
[preflight] FAIL (exit 4) — release commit $RESOLVED_SHA is reachable from
            origin/master but is NOT the master tip ($MASTER_HEAD).
            Tagging this commit would skip changes that landed on master
            between the release commit and now.

Recovery:
  1. Either rebase / cherry-pick the release commit onto master HEAD, or
  2. Confirm with a human that you really want to tag the older commit
     (e.g. cutting a patch release for a previous minor).
MSG
  exit 4
fi

echo "[preflight] OK — $TAG can be pushed against $RESOLVED_SHA"
exit 0
