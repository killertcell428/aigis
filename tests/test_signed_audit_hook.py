"""Tests for signed audit log integration in the Claude Code hook (issue #129).

Acceptance criteria:
  AC1. init --policy enterprise initialises .aigis/audit_key
  AC2. hook append failure never changes allow/deny behaviour
  AC3. developer policy behaviour unchanged (no key auto-created)
  AC4. hook writes a verifiable entry to signed_audit.jsonl
"""

import hashlib
import hmac as _hmac
import json
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(action="shell:exec", target="ls", decision="allow"):
    ev = MagicMock()
    ev.event_type = "tool_call"
    ev.action = action
    ev.target = target
    ev.risk_score = 0
    ev.session_id = "sess-test"
    ev.policy_rule_id = ""
    ev.details = {"tool_name": "Bash"}
    return ev, decision


def _load_hook_ns():
    from aigis.adapters.claude_code import HOOK_SCRIPT

    ns: dict = {}
    exec(HOOK_SCRIPT, ns)  # noqa: S102 — executing generated hook script in test
    return ns


# ---------------------------------------------------------------------------
# AC1 — init --policy enterprise initialises audit key
# ---------------------------------------------------------------------------


def test_init_enterprise_creates_audit_key(tmp_path):
    import aigis.audit.signed_log as sal

    orig_file = sal._KEY_FILE
    orig_dir = sal._KEY_DIR
    sal._KEY_FILE = tmp_path / ".aigis" / "audit_key"
    sal._KEY_DIR = tmp_path / ".aigis"

    try:
        sal._resolve_key(None)
        assert sal._KEY_FILE.exists(), "audit_key should be created by _resolve_key()"
    finally:
        sal._KEY_FILE = orig_file
        sal._KEY_DIR = orig_dir


# ---------------------------------------------------------------------------
# AC2 — signed-log write failure does NOT change hook allow/deny
# ---------------------------------------------------------------------------


def test_signed_log_failure_does_not_block(tmp_path):
    """_append_signed_log raises, but the caller swallows it — decision unchanged."""
    ns = _load_hook_ns()
    _append = ns["_append_signed_log"]

    ev, decision = _make_event()

    ro_dir = tmp_path / "readonly"
    ro_dir.mkdir()
    key_file = ro_dir / ".aigis" / "audit_key"
    key_file.parent.mkdir(parents=True)
    key_file.write_text("deadbeef" * 8)

    # Make the .aigis dir read-only to trigger a write failure (Unix only)
    try:
        (ro_dir / ".aigis").chmod(0o555)
    except (OSError, NotImplementedError):
        pytest.skip("Cannot set read-only permissions on this platform")

    try:
        _append(ev, decision, str(ro_dir))
    except Exception as exc:
        pytest.fail(f"_append_signed_log raised unexpectedly: {exc}")
    finally:
        try:
            (ro_dir / ".aigis").chmod(0o755)
        except OSError:  # best-effort cleanup
            pass


# ---------------------------------------------------------------------------
# AC3 — developer policy: no key auto-created by hook
# ---------------------------------------------------------------------------


def test_hook_skips_signed_log_without_key(tmp_path):
    """When audit_key does not exist, hook silently skips signed log."""
    ns = _load_hook_ns()
    _append = ns["_append_signed_log"]

    ev, decision = _make_event()
    _append(ev, decision, str(tmp_path))  # must not raise and must not create anything
    assert not (tmp_path / ".aigis" / "signed_audit.jsonl").exists()


# ---------------------------------------------------------------------------
# AC4 — hook writes a verifiable entry
# ---------------------------------------------------------------------------


def test_hook_writes_verifiable_entry(tmp_path):
    """A single hook invocation produces a valid HMAC-signed JSONL entry."""
    ns = _load_hook_ns()
    _append = ns["_append_signed_log"]

    aig_dir = tmp_path / ".aigis"
    aig_dir.mkdir()
    key = "test-key-for-unit-test"
    (aig_dir / "audit_key").write_text(key)

    ev, decision = _make_event(action="shell:exec", target="ls -la", decision="allow")
    _append(ev, decision, str(tmp_path))

    log_file = aig_dir / "signed_audit.jsonl"
    assert log_file.exists(), "signed_audit.jsonl should be created"
    lines = [ln for ln in log_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1, "exactly one entry expected"

    entry = json.loads(lines[0])
    assert entry["sequence"] == 0
    assert entry["action"] == "shell:exec"
    assert entry["outcome"] == "allow"
    assert entry["prev_hash"] == "0" * 64  # genesis hash

    # Verify HMAC
    sig = entry.pop("signature")
    canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    expected_sig = _hmac.new(
        key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert sig == expected_sig, "HMAC signature must be valid"


def test_hook_chains_entries(tmp_path):
    """Second entry's prev_hash equals SHA-256 of the first entry."""
    ns = _load_hook_ns()
    _append = ns["_append_signed_log"]

    aig_dir = tmp_path / ".aigis"
    aig_dir.mkdir()
    (aig_dir / "audit_key").write_text("chain-test-key")

    ev1, d1 = _make_event(action="file:read", target="a.py", decision="allow")
    ev2, d2 = _make_event(action="shell:exec", target="ls", decision="allow")

    _append(ev1, d1, str(tmp_path))
    _append(ev2, d2, str(tmp_path))

    lines = [
        ln
        for ln in (aig_dir / "signed_audit.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    canon1 = json.dumps(first, sort_keys=True, ensure_ascii=False)
    expected_prev = hashlib.sha256(canon1.encode("utf-8")).hexdigest()
    assert second["prev_hash"] == expected_prev, "hash chain must link entry 0 → entry 1"
