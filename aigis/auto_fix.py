"""Auto-fix — apply defense proposals from adversarial loop results.

Takes DefenseProposals and applies them:
  - new_pattern → appended to a learned patterns JSON file, loaded at scan time
  - new_similarity → appended to a learned similarity corpus JSON file
  - new_normalization → logged as recommendation (requires manual code change)

After applying, runs false-positive verification against known safe inputs
to ensure no regressions.

Usage::

    from aigis.auto_fix import apply_proposals, verify_no_regressions

    report = loop.run()
    applied = apply_proposals(report.proposals)
    regressions = verify_no_regressions()
    if regressions:
        rollback_proposals(applied)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# Default storage paths for learned defenses
_DEFAULT_DIR = Path(".aigis")
_LEARNED_PATTERNS_FILE = "learned_patterns.json"
_LEARNED_SIMILARITY_FILE = "learned_similarity.json"
_FIX_LOG_FILE = "auto_fix_log.json"


# ---------------------------------------------------------------------------
# Safe inputs for false-positive verification
# ---------------------------------------------------------------------------

SAFE_INPUTS: list[str] = [
    "フランスの首都はどこですか？",
    "Pythonでリストをソートする方法を教えてください",
    "来週の会議について確認したいです",
    "What is the weather like in Tokyo today?",
    "Write a Python function that calculates fibonacci numbers",
    "Please summarize this document for me",
    "東京タワーの高さは何メートルですか？",
    "How do I create a React component?",
    "今日の為替レートを教えてください",
    "Can you help me debug this JavaScript code?",
    "お客様への返信メールの文案を考えて",
    "Explain the difference between REST and GraphQL",
    "新しいプロジェクトの企画書を作成したい",
    "What is machine learning and how does it work?",
    "レシピを教えてください：カレーの作り方",
    "How to set up a Docker container?",
    "今月の売上データを分析したい",
    "Tell me about the history of the internet",
    "来週の出張の準備をしたい",
    "Can you review this pull request for me?",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class AppliedFix:
    """Record of a successfully applied defense fix."""

    proposal_id: str
    fix_type: str  # "pattern" | "similarity" | "normalization_note"
    description: str
    file_path: str
    rollback_possible: bool = True


@dataclass
class RegressionResult:
    """Result of false-positive verification."""

    passed: bool
    total_checked: int
    false_positives: list[dict] = field(default_factory=list)

    @property
    def false_positive_count(self) -> int:
        return len(self.false_positives)

    def summary(self) -> str:
        if self.passed:
            return f"FP verification passed: {self.total_checked} safe inputs, 0 false positives"
        return (
            f"FP verification FAILED: {self.false_positive_count}/{self.total_checked} "
            f"false positives detected"
        )


@dataclass
class AutoFixResult:
    """Result of the full auto-fix cycle."""

    applied: list[AppliedFix] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    regression: RegressionResult | None = None
    rolled_back: bool = False

    def summary(self) -> str:
        lines = [
            "Auto-Fix Result",
            "=" * 60,
            f"Applied: {len(self.applied)}",
            f"Skipped: {len(self.skipped)}",
        ]
        for fix in self.applied:
            lines.append(f"  [{fix.fix_type:>10}] {fix.description}")

        if self.skipped:
            lines.append("\nSkipped proposals:")
            for s in self.skipped:
                lines.append(f"  - {s['reason']}: {s['description']}")

        if self.regression:
            lines.append(f"\n{self.regression.summary()}")
            if self.rolled_back:
                lines.append("  -> Changes rolled back due to false positives")
            if self.regression.false_positives:
                for fp in self.regression.false_positives[:5]:
                    lines.append(f"    FP: '{fp['text'][:60]}' (score={fp['score']})")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "applied": [
                {
                    "proposal_id": f.proposal_id,
                    "fix_type": f.fix_type,
                    "description": f.description,
                    "file_path": f.file_path,
                }
                for f in self.applied
            ],
            "skipped": self.skipped,
            "regression": {
                "passed": self.regression.passed,
                "total_checked": self.regression.total_checked,
                "false_positive_count": self.regression.false_positive_count,
                "false_positives": self.regression.false_positives[:10],
            }
            if self.regression
            else None,
            "rolled_back": self.rolled_back,
        }


# ---------------------------------------------------------------------------
# Learned defenses storage
# ---------------------------------------------------------------------------


def _ensure_dir(storage_dir: Path) -> None:
    storage_dir.mkdir(parents=True, exist_ok=True)


def load_learned_patterns(storage_dir: Path | None = None) -> list[dict]:
    """Load learned patterns from JSON file."""
    path = (storage_dir or _DEFAULT_DIR) / _LEARNED_PATTERNS_FILE
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_learned_patterns(patterns: list[dict], storage_dir: Path | None = None) -> Path:
    """Save learned patterns to JSON file."""
    d = storage_dir or _DEFAULT_DIR
    _ensure_dir(d)
    path = d / _LEARNED_PATTERNS_FILE
    path.write_text(json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_learned_similarity(storage_dir: Path | None = None) -> list[dict]:
    """Load learned similarity phrases from JSON file."""
    path = (storage_dir or _DEFAULT_DIR) / _LEARNED_SIMILARITY_FILE
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_learned_similarity(phrases: list[dict], storage_dir: Path | None = None) -> Path:
    """Save learned similarity phrases to JSON file."""
    d = storage_dir or _DEFAULT_DIR
    _ensure_dir(d)
    path = d / _LEARNED_SIMILARITY_FILE
    path.write_text(json.dumps(phrases, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Apply proposals
# ---------------------------------------------------------------------------


def apply_proposals(
    proposals: list,
    storage_dir: Path | None = None,
    min_priority: str = "medium",
) -> list[AppliedFix]:
    """Apply defense proposals to learned defense files.

    Args:
        proposals: List of DefenseProposal objects from adversarial_loop.
        storage_dir: Directory for learned defense files (default: .aigis/).
        min_priority: Minimum priority to apply ("low", "medium", "high").

    Returns:
        List of AppliedFix records.
    """
    priority_order = {"low": 0, "medium": 1, "high": 2}
    min_level = priority_order.get(min_priority, 1)
    sdir = storage_dir or _DEFAULT_DIR

    applied: list[AppliedFix] = []
    patterns = load_learned_patterns(sdir)
    similarity = load_learned_similarity(sdir)

    existing_pattern_ids = {p.get("id") for p in patterns}
    existing_phrases = {p.get("phrase") for p in similarity}

    for proposal in proposals:
        level = priority_order.get(proposal.priority, 0)
        if level < min_level:
            continue

        if proposal.proposal_type == "new_pattern" and proposal.pattern:
            # Validate regex before adding
            try:
                re.compile(proposal.pattern, re.IGNORECASE | re.DOTALL)
            except re.error:
                continue

            pid = f"learned_{proposal.proposal_id}"
            if pid in existing_pattern_ids:
                continue

            patterns.append(
                {
                    "id": pid,
                    "name": f"Learned: {proposal.description[:60]}",
                    "category": proposal.category,
                    "pattern": proposal.pattern,
                    "score": 35,
                    "owasp_ref": "OWASP LLM01: Prompt Injection",
                    "remediation_hint": f"Auto-detected pattern from adversarial testing: {proposal.description}",
                    "source": "adversarial_loop",
                    "proposal_id": proposal.proposal_id,
                }
            )
            existing_pattern_ids.add(pid)
            applied.append(
                AppliedFix(
                    proposal_id=proposal.proposal_id,
                    fix_type="pattern",
                    description=proposal.description,
                    file_path=str(sdir / _LEARNED_PATTERNS_FILE),
                )
            )

        elif proposal.proposal_type == "new_similarity" and proposal.phrase:
            if proposal.phrase in existing_phrases:
                continue

            similarity.append(
                {
                    "phrase": proposal.phrase,
                    "category": proposal.category,
                    "score": 35,
                    "source": "adversarial_loop",
                    "proposal_id": proposal.proposal_id,
                }
            )
            existing_phrases.add(proposal.phrase)
            applied.append(
                AppliedFix(
                    proposal_id=proposal.proposal_id,
                    fix_type="similarity",
                    description=proposal.description,
                    file_path=str(sdir / _LEARNED_SIMILARITY_FILE),
                )
            )

        elif proposal.proposal_type == "new_normalization":
            # Normalization changes require code modifications — log as note
            applied.append(
                AppliedFix(
                    proposal_id=proposal.proposal_id,
                    fix_type="normalization_note",
                    description=proposal.description,
                    file_path="(requires manual code change in scanner.py)",
                    rollback_possible=False,
                )
            )

    # Persist
    if any(f.fix_type == "pattern" for f in applied):
        save_learned_patterns(patterns, sdir)
    if any(f.fix_type == "similarity" for f in applied):
        save_learned_similarity(similarity, sdir)

    return applied


def rollback_proposals(
    applied: list[AppliedFix],
    storage_dir: Path | None = None,
) -> None:
    """Rollback applied fixes by removing them from learned defense files."""
    sdir = storage_dir or _DEFAULT_DIR
    rollback_pattern_ids = {f.proposal_id for f in applied if f.fix_type == "pattern"}
    rollback_similarity_ids = {f.proposal_id for f in applied if f.fix_type == "similarity"}

    if rollback_pattern_ids:
        patterns = load_learned_patterns(sdir)
        patterns = [p for p in patterns if p.get("proposal_id") not in rollback_pattern_ids]
        save_learned_patterns(patterns, sdir)

    if rollback_similarity_ids:
        similarity = load_learned_similarity(sdir)
        similarity = [s for s in similarity if s.get("proposal_id") not in rollback_similarity_ids]
        save_learned_similarity(similarity, sdir)


# ---------------------------------------------------------------------------
# False-positive verification
# ---------------------------------------------------------------------------


def verify_no_regressions(
    safe_inputs: list[str] | None = None,
    storage_dir: Path | None = None,
) -> RegressionResult:
    """Verify learned defenses don't cause false positives.

    Scans known safe inputs using the full pipeline (including learned patterns)
    and checks that none are incorrectly flagged.

    Args:
        safe_inputs: Custom safe inputs to test. Uses built-in set if None.
        storage_dir: Directory containing learned defense files.

    Returns:
        RegressionResult with pass/fail status and false positive details.
    """
    from aigis.scanner import scan

    inputs = safe_inputs or SAFE_INPUTS
    sdir = storage_dir or _DEFAULT_DIR

    # Build custom rules from learned patterns
    learned_patterns = load_learned_patterns(sdir)
    custom_rules = [
        {
            "id": p["id"],
            "name": p["name"],
            "pattern": p["pattern"],
            "score_delta": p.get("score", 35),
            "owasp_ref": p.get("owasp_ref", ""),
            "remediation_hint": p.get("remediation_hint", ""),
            "enabled": True,
        }
        for p in learned_patterns
    ]

    false_positives: list[dict] = []

    for text in inputs:
        result = scan(text, custom_rules=custom_rules if custom_rules else None)
        if not result.is_safe:
            false_positives.append(
                {
                    "text": text,
                    "score": result.risk_score,
                    "rules": [r.rule_name for r in result.matched_rules],
                }
            )

    return RegressionResult(
        passed=len(false_positives) == 0,
        total_checked=len(inputs),
        false_positives=false_positives,
    )


# ---------------------------------------------------------------------------
# Full auto-fix cycle
# ---------------------------------------------------------------------------


def run_auto_fix(
    proposals: list,
    storage_dir: Path | None = None,
    min_priority: str = "medium",
    safe_inputs: list[str] | None = None,
    auto_rollback: bool = True,
) -> AutoFixResult:
    """Run the full auto-fix cycle: apply → verify → rollback if needed.

    Args:
        proposals: DefenseProposal list from adversarial loop.
        storage_dir: Storage directory for learned defenses.
        min_priority: Minimum priority to apply.
        safe_inputs: Custom safe inputs for FP verification.
        auto_rollback: If True, roll back on false positives.

    Returns:
        AutoFixResult with applied fixes, regression results, and rollback status.
    """
    sdir = storage_dir or _DEFAULT_DIR
    result = AutoFixResult()

    # Separate applicable from skippable
    priority_order = {"low": 0, "medium": 1, "high": 2}
    min_level = priority_order.get(min_priority, 1)

    for p in proposals:
        level = priority_order.get(p.priority, 0)
        if level < min_level:
            result.skipped.append(
                {
                    "proposal_id": p.proposal_id,
                    "description": p.description,
                    "reason": f"Below min priority ({p.priority} < {min_priority})",
                }
            )

    # Apply proposals
    result.applied = apply_proposals(proposals, sdir, min_priority)

    if not result.applied:
        return result

    # Verify no false positives
    result.regression = verify_no_regressions(safe_inputs, sdir)

    # Rollback if regressions found
    if not result.regression.passed and auto_rollback:
        rollback_proposals(result.applied, sdir)
        result.rolled_back = True

    # Log the fix
    _log_fix(result, sdir)

    return result


def _log_fix(result: AutoFixResult, storage_dir: Path) -> None:
    """Append fix result to log file."""
    import datetime

    _ensure_dir(storage_dir)
    log_path = storage_dir / _FIX_LOG_FILE

    log_entries: list[dict] = []
    if log_path.exists():
        try:
            log_entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            log_entries = []

    log_entries.append(
        {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "applied_count": len(result.applied),
            "skipped_count": len(result.skipped),
            "regression_passed": result.regression.passed if result.regression else None,
            "false_positive_count": result.regression.false_positive_count
            if result.regression
            else 0,
            "rolled_back": result.rolled_back,
            "fixes": [
                {"id": f.proposal_id, "type": f.fix_type, "desc": f.description}
                for f in result.applied
            ],
        }
    )

    log_path.write_text(json.dumps(log_entries, ensure_ascii=False, indent=2), encoding="utf-8")
