"""Regression tests for the paper-review loop's failure handling.

These tests cover the fix for issues #93 / #95 / #96, where every paper
review run produced a misleading "0 candidates" issue because all judge
calls were failing with an Anthropic auth error and the script swallowed
the exception as ``relevant=False``.

Run with:
    python -m pytest auto-improvement/scripts/test_paper_review.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

# Make the script importable as a module.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import paper_review  # noqa: E402


@pytest.fixture
def tmp_state(monkeypatch, tmp_path: Path) -> Path:
    state_path = tmp_path / "state.json"
    pending_dir = tmp_path / "pending"
    research_dir = tmp_path / "research"
    pending_dir.mkdir()
    research_dir.mkdir()
    monkeypatch.setattr(paper_review, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(paper_review, "STATE_PATH", state_path)
    monkeypatch.setattr(paper_review, "PENDING_DIR", pending_dir)
    monkeypatch.setattr(paper_review, "RESEARCH_DIR", research_dir)
    return state_path


def _fake_entries(n: int) -> list[paper_review.Entry]:
    return [
        paper_review.Entry(
            section="test",
            title=f"Paper {i}",
            venue="arXiv",
            date="2026.01.0" + str(i + 1),
            url=f"https://arxiv.org/abs/0000.{i:04d}",
        )
        for i in range(n)
    ]


def test_auth_error_aborts_without_writing_state(tmp_state, monkeypatch):
    """When the first judge call fails with an auth error, the script must:

    - exit non-zero (raise JudgeAuthError → SystemExit(4) at the entry point);
    - not write paper_review_state.json;
    - not open the misleading "0 candidates" GitHub issue.

    This is the exact failure mode that produced #93/#95/#96.
    """
    entries = _fake_entries(3)
    monkeypatch.setattr(paper_review, "fetch_source", lambda url: "")
    monkeypatch.setattr(paper_review, "parse_entries", lambda text: entries)

    def boom(_entry):
        raise RuntimeError(
            "Could not resolve authentication method. Expected one of api_key, "
            "auth_token, or credentials to be set."
        )

    monkeypatch.setattr(paper_review, "judge_with_anthropic", boom)
    issue_opener = mock.MagicMock()
    monkeypatch.setattr(paper_review, "open_issue", issue_opener)

    with pytest.raises(paper_review.JudgeAuthError):
        paper_review.run(["--max-papers", "3"])

    assert not tmp_state.exists(), "state.json must not be written when auth fails"
    issue_opener.assert_not_called()


def test_per_paper_error_does_not_mark_seen(tmp_state, monkeypatch):
    """A non-auth exception on one paper must skip that paper (no `seen` entry)
    while still letting the rest of the batch proceed.

    Previous behaviour marked the failed paper as `seen` with relevant=False,
    silently retiring it from future runs once the credential was fixed.
    """
    entries = _fake_entries(3)
    monkeypatch.setattr(paper_review, "fetch_source", lambda url: "")
    monkeypatch.setattr(paper_review, "parse_entries", lambda text: entries)

    calls = {"n": 0}

    def flaky(entry):
        calls["n"] += 1
        if entry.title == "Paper 1":
            raise ValueError("transient parse error")
        return paper_review.Verdict(
            relevant=False,
            rule_id=None,
            rule_category=None,
            one_line="not relevant",
            blocked_example=None,
            source_evidence="",
        )

    monkeypatch.setattr(paper_review, "judge_with_anthropic", flaky)
    monkeypatch.setattr(paper_review, "open_issue", lambda *a, **k: None)

    rc = paper_review.run(["--max-papers", "3"])
    assert rc == 0, "Run should succeed when at least one paper was judged"

    state = json.loads(tmp_state.read_text(encoding="utf-8"))
    seen_titles = {v["title"] for v in state["seen"].values()}
    assert seen_titles == {"Paper 0", "Paper 2"}, (
        "Only successfully-judged papers should be marked seen; "
        f"got {seen_titles}"
    )


def test_all_papers_error_returns_nonzero(tmp_state, monkeypatch):
    """If every paper fails with a non-auth error, exit non-zero and skip
    the issue write — don't spam a misleading '0 candidates' issue."""
    entries = _fake_entries(2)
    monkeypatch.setattr(paper_review, "fetch_source", lambda url: "")
    monkeypatch.setattr(paper_review, "parse_entries", lambda text: entries)

    def always_fail(_entry):
        raise ValueError("transient")

    monkeypatch.setattr(paper_review, "judge_with_anthropic", always_fail)
    issue_opener = mock.MagicMock()
    monkeypatch.setattr(paper_review, "open_issue", issue_opener)

    rc = paper_review.run(["--max-papers", "2"])
    assert rc == 3
    issue_opener.assert_not_called()


def test_is_auth_error_matches_real_sdk_message():
    """Smoke check on the heuristic used to detect SDK auth errors."""
    real = RuntimeError(
        "Could not resolve authentication method. Expected one of api_key, "
        "auth_token, or credentials to be set. Or for one of the `X-Api-Key` "
        "or `Authorization` headers to be explicitly omitted"
    )
    assert paper_review._is_auth_error(real)

    class AuthenticationError(Exception):
        pass

    assert paper_review._is_auth_error(AuthenticationError("bad key"))
    assert not paper_review._is_auth_error(ValueError("totally unrelated"))
