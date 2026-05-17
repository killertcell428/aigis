"""Smoke tests for auto-improvement/scripts/release_preflight.sh.

Exercises the four failure modes (collision, orphan, behind-tip, OK) using a
local bare repo as the "remote." Skips on platforms where bash isn't
available (Windows runners without git-bash) so the script's logic still
gets coverage on the Linux CI matrix.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "auto-improvement" / "scripts" / "release_preflight.sh"

BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(
    BASH is None,
    reason="bash not available on this runner — preflight is bash-only",
)


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
    """Run a command and return its exit code, raising on stderr noise only
    if the test asks for it via the returned object."""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Create a bare 'remote' repo + a working clone with a single commit
    on master. Returns (work_dir, bare_remote_path)."""
    bare = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)
    subprocess.run(
        ["git", "init", "--initial-branch=master", str(work)],
        check=True,
        capture_output=True,
    )

    # Identity needed for commits
    _git(work, "config", "user.email", "test@example.com")
    _git(work, "config", "user.name", "Test User")
    _git(work, "remote", "add", "origin", str(bare))

    (work / "README.md").write_text("seed\n", encoding="utf-8")
    _git(work, "add", "README.md")
    _git(work, "commit", "-m", "seed")
    _git(work, "push", "-u", "origin", "master")

    return work, bare


def test_ok_on_clean_master_tip(fixture_repo: tuple[Path, Path]) -> None:
    work, _ = fixture_repo
    assert BASH is not None
    rc = _run([BASH, str(SCRIPT), "v1.0.0"], cwd=work)
    assert rc == 0


def test_fails_with_exit_2_on_tag_collision(fixture_repo: tuple[Path, Path]) -> None:
    work, _ = fixture_repo
    # Pre-create the tag on the remote (use -m so user gitconfig that
    # forces annotated tags doesn't break the test fixture)
    _git(work, "tag", "-a", "v1.0.0", "-m", "test")
    _git(work, "push", "origin", "v1.0.0")
    # Now try to preflight the same tag — should be rejected
    assert BASH is not None
    rc = _run([BASH, str(SCRIPT), "v1.0.0"], cwd=work)
    assert rc == 2


def test_fails_with_exit_3_on_orphan_commit(fixture_repo: tuple[Path, Path]) -> None:
    work, _ = fixture_repo
    # Create an orphan commit on a branch that never goes to master
    _git(work, "checkout", "-b", "orphan-branch")
    (work / "extra.md").write_text("orphan\n", encoding="utf-8")
    _git(work, "add", "extra.md")
    _git(work, "commit", "-m", "orphan commit")
    assert BASH is not None
    rc = _run([BASH, str(SCRIPT), "v1.0.0"], cwd=work)
    assert rc == 3


def test_fails_with_exit_4_when_behind_master_tip(
    fixture_repo: tuple[Path, Path],
) -> None:
    work, _ = fixture_repo
    # Record the seed commit, then advance master ahead of it
    seed_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=work,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    (work / "second.md").write_text("second\n", encoding="utf-8")
    _git(work, "add", "second.md")
    _git(work, "commit", "-m", "second commit")
    _git(work, "push", "origin", "master")
    # Try to preflight the now-behind seed commit
    assert BASH is not None
    rc = _run([BASH, str(SCRIPT), "v1.0.0", seed_sha], cwd=work)
    assert rc == 4


def test_fails_with_exit_5_on_malformed_tag(fixture_repo: tuple[Path, Path]) -> None:
    work, _ = fixture_repo
    assert BASH is not None
    rc = _run([BASH, str(SCRIPT), "not-a-version"], cwd=work)
    assert rc == 5
