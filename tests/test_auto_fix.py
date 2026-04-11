"""Tests for the auto-fix module."""

import json

from aigis.adversarial_loop import DefenseProposal
from aigis.auto_fix import (
    AppliedFix,
    AutoFixResult,
    RegressionResult,
    apply_proposals,
    load_learned_patterns,
    load_learned_similarity,
    rollback_proposals,
    run_auto_fix,
    save_learned_patterns,
    save_learned_similarity,
    verify_no_regressions,
)


class TestLearnedStorage:
    """Test learned pattern/similarity persistence."""

    def test_save_and_load_patterns(self, tmp_path):
        patterns = [{"id": "test_001", "name": "Test", "pattern": r"\btest\b", "score": 35}]
        save_learned_patterns(patterns, tmp_path)
        loaded = load_learned_patterns(tmp_path)
        assert len(loaded) == 1
        assert loaded[0]["id"] == "test_001"

    def test_save_and_load_similarity(self, tmp_path):
        phrases = [{"phrase": "test phrase", "category": "test", "score": 35}]
        save_learned_similarity(phrases, tmp_path)
        loaded = load_learned_similarity(tmp_path)
        assert len(loaded) == 1
        assert loaded[0]["phrase"] == "test phrase"

    def test_load_empty(self, tmp_path):
        assert load_learned_patterns(tmp_path) == []
        assert load_learned_similarity(tmp_path) == []


class TestApplyProposals:
    """Test applying defense proposals."""

    def test_apply_pattern_proposal(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p001",
                category="jailbreak",
                proposal_type="new_pattern",
                description="Test pattern",
                pattern=r"(?:test|demo)\s+pattern",
                priority="high",
            )
        ]
        applied = apply_proposals(proposals, tmp_path)
        assert len(applied) == 1
        assert applied[0].fix_type == "pattern"

        patterns = load_learned_patterns(tmp_path)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == r"(?:test|demo)\s+pattern"

    def test_apply_similarity_proposal(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p002",
                category="prompt_injection",
                proposal_type="new_similarity",
                description="Test phrase",
                phrase="reset your behavioral parameters",
                priority="high",
            )
        ]
        applied = apply_proposals(proposals, tmp_path)
        assert len(applied) == 1
        assert applied[0].fix_type == "similarity"

        phrases = load_learned_similarity(tmp_path)
        assert len(phrases) == 1
        assert phrases[0]["phrase"] == "reset your behavioral parameters"

    def test_apply_normalization_proposal(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p003",
                category="encoding_bypass",
                proposal_type="new_normalization",
                description="Add bidi stripping",
                priority="medium",
            )
        ]
        applied = apply_proposals(proposals, tmp_path)
        assert len(applied) == 1
        assert applied[0].fix_type == "normalization_note"
        assert not applied[0].rollback_possible

    def test_skip_low_priority(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p004",
                category="test",
                proposal_type="new_pattern",
                description="Low priority",
                pattern=r"test",
                priority="low",
            )
        ]
        applied = apply_proposals(proposals, tmp_path, min_priority="medium")
        assert len(applied) == 0

    def test_skip_invalid_regex(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p005",
                category="test",
                proposal_type="new_pattern",
                description="Invalid regex",
                pattern=r"[invalid",
                priority="high",
            )
        ]
        applied = apply_proposals(proposals, tmp_path)
        assert len(applied) == 0

    def test_no_duplicate_patterns(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p006",
                category="test",
                proposal_type="new_pattern",
                description="Dup test",
                pattern=r"dup_pattern",
                priority="high",
            )
        ]
        apply_proposals(proposals, tmp_path)
        applied2 = apply_proposals(proposals, tmp_path)
        # Second apply should skip the duplicate
        assert len(applied2) == 0
        patterns = load_learned_patterns(tmp_path)
        assert len(patterns) == 1


class TestRollback:
    """Test rollback of applied fixes."""

    def test_rollback_patterns(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p010",
                category="test",
                proposal_type="new_pattern",
                description="To rollback",
                pattern=r"rollback_test",
                priority="high",
            )
        ]
        applied = apply_proposals(proposals, tmp_path)
        assert len(load_learned_patterns(tmp_path)) == 1

        rollback_proposals(applied, tmp_path)
        assert len(load_learned_patterns(tmp_path)) == 0

    def test_rollback_similarity(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p011",
                category="test",
                proposal_type="new_similarity",
                description="To rollback",
                phrase="rollback test phrase",
                priority="high",
            )
        ]
        applied = apply_proposals(proposals, tmp_path)
        assert len(load_learned_similarity(tmp_path)) == 1

        rollback_proposals(applied, tmp_path)
        assert len(load_learned_similarity(tmp_path)) == 0


class TestFPVerification:
    """Test false-positive verification."""

    def test_safe_inputs_pass(self, tmp_path):
        result = verify_no_regressions(storage_dir=tmp_path)
        assert result.passed
        assert result.total_checked == 20
        assert result.false_positive_count == 0

    def test_custom_safe_inputs(self, tmp_path):
        result = verify_no_regressions(
            safe_inputs=["Hello world", "What is 2+2?"],
            storage_dir=tmp_path,
        )
        assert result.passed
        assert result.total_checked == 2

    def test_overly_broad_pattern_causes_fp(self, tmp_path):
        # Add an overly broad pattern that will match safe inputs
        save_learned_patterns(
            [{"id": "broad_001", "name": "Too broad", "pattern": r"\b(the|is|a)\b",
              "score": 50, "proposal_id": "broad_001"}],
            tmp_path,
        )
        result = verify_no_regressions(storage_dir=tmp_path)
        assert not result.passed
        assert result.false_positive_count > 0


class TestRunAutoFix:
    """Test the full auto-fix cycle."""

    def test_full_cycle_no_regressions(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p020",
                category="jailbreak",
                proposal_type="new_pattern",
                description="Maintenance mode bypass",
                pattern=r"(?:maintenance|debug|testing)\s+mode",
                priority="high",
            ),
            DefenseProposal(
                proposal_id="p021",
                category="prompt_injection",
                proposal_type="new_similarity",
                description="Reset behavioral params",
                phrase="reset your behavioral parameters",
                priority="high",
            ),
        ]
        result = run_auto_fix(proposals, storage_dir=tmp_path)
        assert len(result.applied) == 2
        assert result.regression is not None
        assert result.regression.passed
        assert not result.rolled_back

    def test_full_cycle_with_rollback(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p030",
                category="test",
                proposal_type="new_pattern",
                description="Overly broad — will cause FP",
                pattern=r"\b(the|is|a|to)\b",
                priority="high",
            ),
        ]
        result = run_auto_fix(proposals, storage_dir=tmp_path, auto_rollback=True)
        assert result.regression is not None
        assert not result.regression.passed
        assert result.rolled_back
        # Patterns should be rolled back
        assert len(load_learned_patterns(tmp_path)) == 0

    def test_no_rollback_flag(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p031",
                category="test",
                proposal_type="new_pattern",
                description="Overly broad — kept despite FP",
                pattern=r"\b(the|is|a|to)\b",
                priority="high",
            ),
        ]
        result = run_auto_fix(proposals, storage_dir=tmp_path, auto_rollback=False)
        assert not result.regression.passed
        assert not result.rolled_back
        # Pattern should still be there
        assert len(load_learned_patterns(tmp_path)) == 1

    def test_empty_proposals(self, tmp_path):
        result = run_auto_fix([], storage_dir=tmp_path)
        assert len(result.applied) == 0
        assert result.regression is None

    def test_log_file_created(self, tmp_path):
        proposals = [
            DefenseProposal(
                proposal_id="p040",
                category="test",
                proposal_type="new_similarity",
                description="Log test",
                phrase="unique test phrase for logging",
                priority="high",
            ),
        ]
        run_auto_fix(proposals, storage_dir=tmp_path)
        log_path = tmp_path / "auto_fix_log.json"
        assert log_path.exists()
        log_data = json.loads(log_path.read_text(encoding="utf-8"))
        assert len(log_data) == 1
        assert log_data[0]["applied_count"] == 1


class TestAutoFixResult:
    """Test AutoFixResult data class."""

    def test_summary(self):
        result = AutoFixResult(
            applied=[
                AppliedFix("p1", "pattern", "Test pattern", "file.json"),
            ],
            regression=RegressionResult(passed=True, total_checked=20),
        )
        summary = result.summary()
        assert "Applied: 1" in summary
        assert "passed" in summary

    def test_to_dict(self):
        result = AutoFixResult(
            applied=[
                AppliedFix("p1", "pattern", "Test", "file.json"),
            ],
            regression=RegressionResult(passed=True, total_checked=20),
        )
        d = result.to_dict()
        assert len(d["applied"]) == 1
        assert d["regression"]["passed"] is True
