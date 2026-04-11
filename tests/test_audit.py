"""Tests for aigis.audit — Cryptographic Audit Log (Phase 3b).

Covers:
- SignedLogEntry creation and serialization
- HMAC signature generation and verification
- Hash chain linking and verification
- Tampering detection (modified entry, deleted entry, reordered entries)
- JSONL persistence (save/load round-trip)
- Thread safety of append operations
- AuditVerifier checks (signature, chain, sequence, timestamp)
- Key auto-generation
- Edge cases (empty log, single entry, large details dict)
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from aigis.audit import (
    AuditVerifier,
    HashChain,
    SignedAuditLog,
    SignedLogEntry,
    VerificationResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SECRET = "test-secret-key-for-audit"


@pytest.fixture
def audit_log() -> SignedAuditLog:
    return SignedAuditLog(secret_key=SECRET)


@pytest.fixture
def verifier() -> AuditVerifier:
    return AuditVerifier(secret_key=SECRET)


@pytest.fixture
def populated_log(audit_log: SignedAuditLog) -> SignedAuditLog:
    """A log with 5 entries for testing."""
    audit_log.append(
        event_type="tool_call",
        actor="agent",
        action="shell:exec",
        target="/bin/ls",
        risk_score=10,
        outcome="allowed",
    )
    audit_log.append(
        event_type="scan_result",
        actor="system",
        action="scan:input",
        target="user_msg_1",
        risk_score=75,
        outcome="blocked",
        details={"pattern": "prompt_injection", "rule_id": "PI-001"},
    )
    audit_log.append(
        event_type="containment_change",
        actor="system",
        action="escalate",
        target="agent-007",
        risk_score=80,
        outcome="warn",
        details={"from": "monitor", "to": "restrict"},
    )
    audit_log.append(
        event_type="policy_decision",
        actor="user",
        action="policy:update",
        target="default_policy",
        risk_score=0,
        outcome="allowed",
    )
    audit_log.append(
        event_type="capability_grant",
        actor="user",
        action="grant:file_read",
        target="agent-007",
        risk_score=20,
        outcome="allowed",
    )
    return audit_log


# ---------------------------------------------------------------------------
# SignedLogEntry — creation and serialization
# ---------------------------------------------------------------------------


class TestSignedLogEntry:
    def test_entry_is_frozen(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        with pytest.raises(AttributeError):
            entry.sequence = 999  # type: ignore[misc]

    def test_to_dict_round_trip(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="scan_result",
            actor="system",
            action="scan",
            target="msg",
            risk_score=50,
            outcome="warn",
            details={"key": "value"},
        )
        d = entry.to_dict()
        restored = SignedLogEntry.from_dict(d)
        assert restored == entry

    def test_to_dict_contains_all_fields(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="a",
            target="t",
        )
        d = entry.to_dict()
        expected_keys = {
            "sequence",
            "timestamp",
            "event_type",
            "actor",
            "action",
            "target",
            "risk_score",
            "outcome",
            "details",
            "prev_hash",
            "signature",
        }
        assert set(d.keys()) == expected_keys

    def test_details_default_empty_dict(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="a",
            target="t",
        )
        assert entry.details == {}


# ---------------------------------------------------------------------------
# HMAC Signature
# ---------------------------------------------------------------------------


class TestHMACSignature:
    def test_signature_is_hex_64_chars(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        assert len(entry.signature) == 64
        int(entry.signature, 16)  # must be valid hex

    def test_signature_verifies(self, audit_log: SignedAuditLog, verifier: AuditVerifier) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        assert verifier.verify_entry(entry) is True

    def test_wrong_key_fails_verification(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        wrong_verifier = AuditVerifier(secret_key="wrong-key")
        assert wrong_verifier.verify_entry(entry) is False

    def test_tampered_action_fails_signature(
        self,
        audit_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="safe_action",
            target="x",
        )
        # Tamper: change the action field
        tampered = SignedLogEntry(
            sequence=entry.sequence,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            actor=entry.actor,
            action="malicious_action",  # changed
            target=entry.target,
            risk_score=entry.risk_score,
            outcome=entry.outcome,
            details=entry.details,
            prev_hash=entry.prev_hash,
            signature=entry.signature,  # original sig
        )
        assert verifier.verify_entry(tampered) is False

    def test_tampered_risk_score_fails(
        self,
        audit_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        entry = audit_log.append(
            event_type="scan_result",
            actor="system",
            action="scan",
            target="msg",
            risk_score=90,
            outcome="blocked",
        )
        tampered = SignedLogEntry(
            sequence=entry.sequence,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            actor=entry.actor,
            action=entry.action,
            target=entry.target,
            risk_score=10,  # lowered to hide severity
            outcome=entry.outcome,
            details=entry.details,
            prev_hash=entry.prev_hash,
            signature=entry.signature,
        )
        assert verifier.verify_entry(tampered) is False

    def test_tampered_outcome_fails(
        self,
        audit_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="shell:exec",
            target="/etc/passwd",
            risk_score=95,
            outcome="blocked",
        )
        tampered = SignedLogEntry(
            sequence=entry.sequence,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            actor=entry.actor,
            action=entry.action,
            target=entry.target,
            risk_score=entry.risk_score,
            outcome="allowed",  # changed from blocked to allowed
            details=entry.details,
            prev_hash=entry.prev_hash,
            signature=entry.signature,
        )
        assert verifier.verify_entry(tampered) is False


# ---------------------------------------------------------------------------
# Hash Chain
# ---------------------------------------------------------------------------


class TestHashChain:
    def test_genesis_hash(self) -> None:
        gh = HashChain.genesis_hash()
        assert gh == "0" * 64
        assert len(gh) == 64

    def test_first_entry_has_genesis_prev_hash(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        assert entry.prev_hash == HashChain.genesis_hash()

    def test_second_entry_chains_to_first(self, audit_log: SignedAuditLog) -> None:
        e1 = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="first",
            target="x",
        )
        e2 = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="second",
            target="y",
        )
        expected_hash = HashChain.compute_entry_hash(e1)
        assert e2.prev_hash == expected_hash

    def test_compute_entry_hash_is_deterministic(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        h1 = HashChain.compute_entry_hash(entry)
        h2 = HashChain.compute_entry_hash(entry)
        assert h1 == h2

    def test_verify_chain_valid(self, populated_log: SignedAuditLog) -> None:
        entries = populated_log.entries()
        valid, broken = HashChain.verify_chain(entries)
        assert valid is True
        assert broken == []

    def test_verify_chain_empty(self) -> None:
        valid, broken = HashChain.verify_chain([])
        assert valid is True
        assert broken == []

    def test_verify_chain_single_entry(self, audit_log: SignedAuditLog) -> None:
        audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="only",
            target="x",
        )
        valid, broken = HashChain.verify_chain(audit_log.entries())
        assert valid is True

    def test_verify_chain_detects_modified_entry(
        self,
        populated_log: SignedAuditLog,
    ) -> None:
        entries = populated_log.entries()
        # Tamper with entry at index 2 (middle of chain)
        original = entries[2]
        tampered = SignedLogEntry(
            sequence=original.sequence,
            timestamp=original.timestamp,
            event_type=original.event_type,
            actor="evil_actor",  # changed
            action=original.action,
            target=original.target,
            risk_score=original.risk_score,
            outcome=original.outcome,
            details=original.details,
            prev_hash=original.prev_hash,
            signature=original.signature,
        )
        entries[2] = tampered
        valid, broken = HashChain.verify_chain(entries)
        assert valid is False
        # Entry 3 should report broken because its prev_hash won't match
        # the tampered entry 2's hash
        assert 3 in broken

    def test_verify_chain_detects_deleted_entry(
        self,
        populated_log: SignedAuditLog,
    ) -> None:
        entries = populated_log.entries()
        # Delete entry at index 2
        del entries[2]
        valid, broken = HashChain.verify_chain(entries)
        assert valid is False


# ---------------------------------------------------------------------------
# SignedAuditLog — append, sequence, entries
# ---------------------------------------------------------------------------


class TestSignedAuditLog:
    def test_sequence_is_monotonic(self, populated_log: SignedAuditLog) -> None:
        entries = populated_log.entries()
        sequences = [e.sequence for e in entries]
        assert sequences == list(range(5))

    def test_entries_returns_copy(self, populated_log: SignedAuditLog) -> None:
        e1 = populated_log.entries()
        e2 = populated_log.entries()
        assert e1 is not e2
        assert e1 == e2

    def test_append_returns_entry(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        assert isinstance(entry, SignedLogEntry)
        assert entry.sequence == 0

    def test_timestamps_are_iso_utc(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        # Should parse without error and contain UTC indicator
        assert "T" in entry.timestamp
        assert entry.timestamp.endswith("+00:00") or entry.timestamp.endswith("Z")

    def test_default_risk_score_and_outcome(self, audit_log: SignedAuditLog) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        assert entry.risk_score == 0
        assert entry.outcome == "allowed"


# ---------------------------------------------------------------------------
# JSONL Persistence — save / load
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_creates_jsonl(self, populated_log: SignedAuditLog, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        populated_log.save(path)
        assert path.exists()
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5
        # Each line must be valid JSON
        for line in lines:
            json.loads(line)

    def test_save_load_round_trip(
        self,
        populated_log: SignedAuditLog,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "audit.jsonl"
        populated_log.save(path)

        loaded = SignedAuditLog(secret_key=SECRET)
        loaded.load(path)
        assert loaded.entries() == populated_log.entries()

    def test_load_continues_sequence(
        self,
        populated_log: SignedAuditLog,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "audit.jsonl"
        populated_log.save(path)

        loaded = SignedAuditLog(secret_key=SECRET)
        loaded.load(path)
        new_entry = loaded.append(
            event_type="tool_call",
            actor="agent",
            action="new",
            target="y",
        )
        assert new_entry.sequence == 5

    def test_loaded_log_verifies(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "audit.jsonl"
        populated_log.save(path)
        result = verifier.verify_file(path)
        assert result.valid is True

    def test_save_creates_parent_dirs(self, audit_log: SignedAuditLog, tmp_path: Path) -> None:
        path = tmp_path / "deep" / "nested" / "audit.jsonl"
        audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="test",
            target="x",
        )
        audit_log.save(path)
        assert path.exists()


# ---------------------------------------------------------------------------
# AuditVerifier — full verification
# ---------------------------------------------------------------------------


class TestAuditVerifier:
    def test_valid_log_passes(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        result = verifier.verify_entries(populated_log.entries())
        assert result.valid is True
        assert result.chain_valid is True
        assert result.signature_valid is True
        assert result.total_entries == 5
        assert result.checked_entries == 5
        assert result.broken_chain_at == []
        assert result.invalid_signatures_at == []
        assert "no tampering" in result.summary.lower()

    def test_empty_log_is_valid(self, verifier: AuditVerifier) -> None:
        result = verifier.verify_entries([])
        assert result.valid is True
        assert result.total_entries == 0

    def test_detects_signature_tampering(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        entries = populated_log.entries()
        original = entries[1]
        tampered = SignedLogEntry(
            sequence=original.sequence,
            timestamp=original.timestamp,
            event_type=original.event_type,
            actor=original.actor,
            action="tampered_action",
            target=original.target,
            risk_score=original.risk_score,
            outcome=original.outcome,
            details=original.details,
            prev_hash=original.prev_hash,
            signature=original.signature,
        )
        entries[1] = tampered
        result = verifier.verify_entries(entries)
        assert result.valid is False
        assert result.signature_valid is False
        assert 1 in result.invalid_signatures_at

    def test_detects_chain_break(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        entries = populated_log.entries()
        original = entries[2]
        # Create a new entry with wrong prev_hash
        tampered = SignedLogEntry(
            sequence=original.sequence,
            timestamp=original.timestamp,
            event_type=original.event_type,
            actor=original.actor,
            action=original.action,
            target=original.target,
            risk_score=original.risk_score,
            outcome=original.outcome,
            details=original.details,
            prev_hash="bad" + original.prev_hash[3:],  # corrupt prev_hash
            signature=original.signature,
        )
        entries[2] = tampered
        result = verifier.verify_entries(entries)
        assert result.valid is False
        assert result.chain_valid is False

    def test_detects_sequence_gap(self, verifier: AuditVerifier) -> None:
        """Entries with non-monotonic sequence numbers are flagged."""
        log = SignedAuditLog(secret_key=SECRET)
        log.append(event_type="a", actor="x", action="a", target="t")
        log.append(event_type="b", actor="x", action="b", target="t")
        entries = log.entries()

        # Swap sequence numbers by reconstructing entry 1 with seq=5
        bad = entries[1]
        tampered = SignedLogEntry(
            sequence=5,  # should be 1
            timestamp=bad.timestamp,
            event_type=bad.event_type,
            actor=bad.actor,
            action=bad.action,
            target=bad.target,
            risk_score=bad.risk_score,
            outcome=bad.outcome,
            details=bad.details,
            prev_hash=bad.prev_hash,
            signature=bad.signature,
        )
        entries[1] = tampered
        result = verifier.verify_entries(entries)
        assert result.valid is False
        assert 5 in result.sequence_errors_at

    def test_verify_file(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "audit.jsonl"
        populated_log.save(path)
        result = verifier.verify_file(path)
        assert result.valid is True

    def test_verify_file_detects_file_tampering(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "audit.jsonl"
        populated_log.save(path)

        # Tamper with the file: modify a line
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        obj = json.loads(lines[2])
        obj["outcome"] = "allowed"  # tamper
        lines[2] = json.dumps(obj, sort_keys=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = verifier.verify_file(path)
        assert result.valid is False

    def test_summary_includes_failure_details(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        entries = populated_log.entries()
        original = entries[1]
        tampered = SignedLogEntry(
            sequence=original.sequence,
            timestamp=original.timestamp,
            event_type=original.event_type,
            actor=original.actor,
            action="tampered",
            target=original.target,
            risk_score=original.risk_score,
            outcome=original.outcome,
            details=original.details,
            prev_hash=original.prev_hash,
            signature=original.signature,
        )
        entries[1] = tampered
        result = verifier.verify_entries(entries)
        assert "SIGNATURE FAILURE" in result.summary


# ---------------------------------------------------------------------------
# Tampering detection — comprehensive scenarios
# ---------------------------------------------------------------------------


class TestTamperingDetection:
    def test_delete_first_entry(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        """Deleting the first entry breaks both chain and sequence."""
        entries = populated_log.entries()
        del entries[0]
        result = verifier.verify_entries(entries)
        assert result.valid is False

    def test_delete_last_entry_still_valid_chain(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        """Deleting the last entry breaks sequence but chain of remaining
        entries is still intact (since the deleted entry's prev_hash
        isn't checked by anyone). However, sequence will be wrong."""
        entries = populated_log.entries()
        del entries[-1]
        result = verifier.verify_entries(entries)
        # Chain of remaining 4 entries is intact
        assert result.chain_valid is True
        # But total count mismatch is detected by caller context
        assert result.total_entries == 4

    def test_reorder_entries(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        """Swapping two entries breaks both chain and sequence."""
        entries = populated_log.entries()
        entries[1], entries[2] = entries[2], entries[1]
        result = verifier.verify_entries(entries)
        assert result.valid is False

    def test_insert_forged_entry(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        """Inserting a forged entry breaks chain, sequence, and/or signature."""
        entries = populated_log.entries()
        forged = SignedLogEntry(
            sequence=2,
            timestamp=entries[2].timestamp,
            event_type="forged",
            actor="evil",
            action="steal_data",
            target="secrets",
            risk_score=0,
            outcome="allowed",
            details={},
            prev_hash=entries[1].prev_hash,
            signature="0" * 64,  # fake signature
        )
        entries.insert(2, forged)
        result = verifier.verify_entries(entries)
        assert result.valid is False

    def test_replay_old_entry(
        self,
        populated_log: SignedAuditLog,
        verifier: AuditVerifier,
    ) -> None:
        """Duplicating an entry breaks sequence monotonicity."""
        entries = populated_log.entries()
        entries.append(entries[0])  # replay
        result = verifier.verify_entries(entries)
        assert result.valid is False


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    def test_concurrent_appends(self) -> None:
        """Multiple threads appending concurrently should produce
        a valid, monotonically sequenced log."""
        log = SignedAuditLog(secret_key=SECRET)
        n_threads = 10
        n_per_thread = 20
        barrier = threading.Barrier(n_threads)

        def worker(tid: int) -> None:
            barrier.wait()
            for i in range(n_per_thread):
                log.append(
                    event_type="tool_call",
                    actor=f"thread-{tid}",
                    action=f"action-{i}",
                    target="x",
                )

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        entries = log.entries()
        assert len(entries) == n_threads * n_per_thread

        # Sequences must be strictly monotonic
        sequences = [e.sequence for e in entries]
        assert sequences == list(range(n_threads * n_per_thread))

        # Full chain + signature verification
        verifier = AuditVerifier(secret_key=SECRET)
        result = verifier.verify_entries(entries)
        assert result.valid is True


# ---------------------------------------------------------------------------
# Key auto-generation
# ---------------------------------------------------------------------------


class TestKeyManagement:
    def test_auto_generated_key_produces_valid_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When no key is provided, one is generated and used consistently."""
        # Point the key file to a temp location
        import aigis.audit.signed_log as sl

        monkeypatch.setattr(sl, "_KEY_DIR", tmp_path)
        monkeypatch.setattr(sl, "_KEY_FILE", tmp_path / "audit_key")

        log = SignedAuditLog(secret_key=None)
        log.append(event_type="tool_call", actor="agent", action="a", target="t")
        log.append(event_type="tool_call", actor="agent", action="b", target="t")

        # Key file should have been created
        key_file = tmp_path / "audit_key"
        assert key_file.exists()
        stored_key = key_file.read_text(encoding="utf-8").strip()
        assert len(stored_key) == 64  # 32 bytes hex

        # Verify with the stored key
        verifier = AuditVerifier(secret_key=stored_key)
        result = verifier.verify_entries(log.entries())
        assert result.valid is True

    def test_auto_key_reused_on_second_init(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A second SignedAuditLog(secret_key=None) reuses the persisted key."""
        import aigis.audit.signed_log as sl

        monkeypatch.setattr(sl, "_KEY_DIR", tmp_path)
        monkeypatch.setattr(sl, "_KEY_FILE", tmp_path / "audit_key")

        log1 = SignedAuditLog(secret_key=None)
        e1 = log1.append(event_type="a", actor="x", action="a", target="t")

        SignedAuditLog(secret_key=None)
        # log2 should use the same key, so it can verify log1's entries
        key = (tmp_path / "audit_key").read_text(encoding="utf-8").strip()
        verifier = AuditVerifier(secret_key=key)
        assert verifier.verify_entry(e1) is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_large_details_dict(self, audit_log: SignedAuditLog, verifier: AuditVerifier) -> None:
        big_details = {f"key_{i}": f"value_{i}" * 100 for i in range(50)}
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action="big",
            target="x",
            details=big_details,
        )
        assert verifier.verify_entry(entry) is True

    def test_unicode_in_fields(self, audit_log: SignedAuditLog, verifier: AuditVerifier) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="エージェント",
            action="日本語テスト",
            target="ターゲット",
            details={"memo": "テスト用データ 🛡️"},
        )
        assert verifier.verify_entry(entry) is True

    def test_special_chars_in_action(
        self, audit_log: SignedAuditLog, verifier: AuditVerifier
    ) -> None:
        entry = audit_log.append(
            event_type="tool_call",
            actor="agent",
            action='shell:exec("rm -rf /")',
            target="/",
            risk_score=100,
            outcome="blocked",
        )
        assert verifier.verify_entry(entry) is True

    def test_verification_result_dataclass(self) -> None:
        r = VerificationResult(
            valid=True,
            total_entries=0,
            checked_entries=0,
            chain_valid=True,
            signature_valid=True,
            summary="ok",
        )
        assert r.broken_chain_at == []
        assert r.invalid_signatures_at == []
        assert r.sequence_errors_at == []
        assert r.timestamp_errors_at == []
