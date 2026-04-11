"""SecurityMonitor — continuous monitoring and metrics aggregation.

Collects scan results, benchmark outcomes, red-team findings, and activity
events to produce actionable security metrics inspired by 0din-ai/ai-scanner's
ASR (Attack Success Rate) tracking, while highlighting Aigis's unique
multi-layer detection pipeline.

Usage::

    from aigis.monitor import SecurityMonitor

    monitor = SecurityMonitor()

    # Record scan results as they happen
    from aigis import scan
    result = scan("some user input")
    monitor.record_scan(result, direction="input")

    # Get current metrics snapshot
    metrics = monitor.snapshot()
    print(metrics["asr"])             # Attack Success Rate
    print(metrics["detection_rate"])  # Overall detection rate
    print(metrics["owasp_coverage"]) # OWASP LLM Top 10 coverage map

    # Get trend data over time
    trend = monitor.trend(days=30)

License note: This module is inspired by concepts from 0din-ai/ai-scanner
(Apache 2.0). No code is copied; the implementation is original to Aigis.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# OWASP LLM Top 10 (2025) mapping
OWASP_LLM_TOP10: dict[str, str] = {
    "LLM01": "Prompt Injection",
    "LLM02": "Insecure Output Handling",
    "LLM03": "Training Data Poisoning",
    "LLM04": "Model Denial of Service",
    "LLM05": "Supply-Chain Vulnerabilities",
    "LLM06": "Sensitive Information Disclosure",
    "LLM07": "Insecure Plugin Design",
    "LLM08": "Excessive Agency",
    "LLM09": "Overreliance",
    "LLM10": "Model Theft",
}

# Map aigis categories to OWASP LLM Top 10
CATEGORY_TO_OWASP: dict[str, str] = {
    "prompt_injection": "LLM01",
    "jailbreak": "LLM01",
    "system_prompt_leak": "LLM01",
    "multi_turn_escalation": "LLM01",
    "output_manipulation": "LLM02",
    "xss_injection": "LLM02",
    "sql_injection": "LLM02",
    "code_injection": "LLM02",
    "training_data": "LLM03",
    "resource_abuse": "LLM04",
    "dos_attack": "LLM04",
    "supply_chain": "LLM05",
    "mcp_poisoning": "LLM05",
    "mcp_tool_shadow": "LLM05",
    "mcp_rug_pull": "LLM05",
    "pii_leak": "LLM06",
    "credential_leak": "LLM06",
    "data_exfiltration": "LLM06",
    "confidential_data": "LLM06",
    "insecure_plugin": "LLM07",
    "excessive_agency": "LLM08",
    "privilege_escalation": "LLM08",
    "overreliance": "LLM09",
    "model_theft": "LLM10",
}


@dataclass
class ScanRecord:
    """A recorded scan event with metadata."""

    timestamp: str
    direction: str  # "input" | "output" | "mcp" | "rag"
    risk_score: int
    risk_level: str
    is_blocked: bool
    categories: list[str]
    matched_rule_ids: list[str]
    owasp_refs: list[str]
    detection_layers: list[str] = field(default_factory=list)


@dataclass
class BenchmarkRecord:
    """A recorded benchmark run."""

    timestamp: str
    category: str
    total_attacks: int
    detected: int
    bypassed: int
    detection_rate: float
    asr: float  # Attack Success Rate = bypassed / total


@dataclass
class MonitoringSnapshot:
    """Point-in-time metrics snapshot."""

    timestamp: str
    period_hours: float

    # Core metrics (inspired by ai-scanner ASR)
    total_scans: int
    total_blocked: int
    total_allowed: int
    total_review: int
    detection_rate: float  # blocked / (blocked + allowed_threats)
    asr: float  # Attack Success Rate (lower is better for defender)

    # Risk distribution
    risk_distribution: dict[str, int]

    # Category breakdown
    category_counts: dict[str, int]
    category_detection_rates: dict[str, float]

    # OWASP LLM Top 10 coverage
    owasp_coverage: dict[str, dict[str, Any]]

    # aigis unique: multi-layer detection stats
    detection_by_layer: dict[str, int]

    # Direction breakdown
    by_direction: dict[str, int]

    # Auto-fix stats
    auto_fix_applied: int
    learned_patterns_count: int

    def to_dict(self) -> dict:
        return asdict(self)


class SecurityMonitor:
    """Aggregates security events and produces monitoring metrics.

    Stores scan records in a local JSONL file for persistence across
    sessions. Designed to work alongside ActivityStream (activity.py)
    but focused on security-specific metrics rather than general audit.
    """

    def __init__(
        self,
        data_dir: str = ".aigis/monitor",
        max_records: int = 50_000,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_records = max_records
        self._scan_file = self.data_dir / "scans.jsonl"
        self._benchmark_file = self.data_dir / "benchmarks.jsonl"
        self._snapshot_file = self.data_dir / "snapshots.jsonl"

    # === Recording ===

    def record_scan(
        self,
        scan_result: Any,
        direction: str = "input",
        detection_layers: list[str] | None = None,
    ) -> ScanRecord:
        """Record a scan result for monitoring.

        Args:
            scan_result: A ScanResult from aigis.scanner.
            direction: "input", "output", "mcp", or "rag".
            detection_layers: Which layers fired (e.g., ["regex", "similarity", "decoded"]).
        """
        categories = []
        rule_ids = []
        owasp_refs = []
        layers = list(detection_layers or [])

        for rule in getattr(scan_result, "matched_rules", []):
            cat = (
                getattr(rule, "category", "")
                if hasattr(rule, "category")
                else rule.get("category", "")
            )
            rid = (
                getattr(rule, "rule_id", "")
                if hasattr(rule, "rule_id")
                else rule.get("rule_id", "")
            )
            oref = (
                getattr(rule, "owasp_ref", "")
                if hasattr(rule, "owasp_ref")
                else rule.get("owasp_ref", "")
            )
            rname = (
                getattr(rule, "rule_name", "")
                if hasattr(rule, "rule_name")
                else rule.get("rule_name", "")
            )

            if cat and cat not in categories:
                categories.append(cat)
            if rid:
                rule_ids.append(rid)
            if oref and oref not in owasp_refs:
                owasp_refs.append(oref)

            # Infer detection layer from rule naming
            if not layers:
                if rid.startswith("sim_"):
                    layers.append("similarity")
                elif "(decoded)" in rname:
                    layers.append("decoded")
                elif rid == "multi_turn_escalation":
                    layers.append("multi_turn")
                else:
                    layers.append("regex")

        risk_score = getattr(scan_result, "risk_score", 0)
        risk_level = getattr(scan_result, "risk_level", "low")
        is_blocked = getattr(scan_result, "is_blocked", False)

        record = ScanRecord(
            timestamp=datetime.now(UTC).isoformat(),
            direction=direction,
            risk_score=risk_score,
            risk_level=risk_level,
            is_blocked=is_blocked,
            categories=categories,
            matched_rule_ids=rule_ids,
            owasp_refs=owasp_refs,
            detection_layers=list(set(layers)) if layers else [],
        )

        self._append_jsonl(self._scan_file, asdict(record))
        return record

    def record_benchmark(
        self,
        category: str,
        total_attacks: int,
        detected: int,
    ) -> BenchmarkRecord:
        """Record a benchmark result."""
        bypassed = total_attacks - detected
        record = BenchmarkRecord(
            timestamp=datetime.now(UTC).isoformat(),
            category=category,
            total_attacks=total_attacks,
            detected=detected,
            bypassed=bypassed,
            detection_rate=detected / total_attacks if total_attacks > 0 else 0.0,
            asr=bypassed / total_attacks if total_attacks > 0 else 0.0,
        )
        self._append_jsonl(self._benchmark_file, asdict(record))
        return record

    # === Metrics ===

    def snapshot(self, hours: float = 24) -> MonitoringSnapshot:
        """Generate a point-in-time metrics snapshot.

        Args:
            hours: Look-back period in hours (default 24h).
        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        records = self._load_scans_since(cutoff)

        total = len(records)
        blocked = sum(1 for r in records if r["is_blocked"])
        review = sum(
            1 for r in records if r["risk_level"] in ("medium", "high") and not r["is_blocked"]
        )
        allowed = total - blocked - review

        # Detection = blocked + review (any threat flagged at medium or above)
        detected = blocked + review

        # Threats that slipped through entirely (has matched rules but risk <= 30)
        slipped = sum(1 for r in records if r.get("matched_rule_ids") and r["risk_score"] <= 30)
        detection_rate = detected / (detected + slipped) if (detected + slipped) > 0 else 1.0

        # ASR: proportion of attack attempts that were NOT detected
        # (inspired by ai-scanner: lower ASR = better defense)
        scans_with_matches = [r for r in records if r["matched_rule_ids"]]
        detected_attacks = sum(
            1
            for r in scans_with_matches
            if r["risk_score"] > 30  # medium or above = detected
        )
        asr = (
            (len(scans_with_matches) - detected_attacks) / len(scans_with_matches)
            if scans_with_matches
            else 0.0
        )

        # Risk distribution
        risk_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for r in records:
            level = r.get("risk_level", "low")
            if level in risk_dist:
                risk_dist[level] += 1

        # Category breakdown
        cat_counts: dict[str, int] = defaultdict(int)
        cat_blocked: dict[str, int] = defaultdict(int)
        for r in records:
            for cat in r.get("categories", []):
                cat_counts[cat] += 1
                if r["is_blocked"]:
                    cat_blocked[cat] += 1

        cat_rates = {
            cat: cat_blocked.get(cat, 0) / count if count > 0 else 0.0
            for cat, count in cat_counts.items()
        }

        # OWASP coverage
        owasp_cov: dict[str, dict[str, Any]] = {}
        for owasp_id, owasp_name in OWASP_LLM_TOP10.items():
            related_cats = [c for c, o in CATEGORY_TO_OWASP.items() if o == owasp_id]
            related_count = sum(cat_counts.get(c, 0) for c in related_cats)
            related_blocked = sum(cat_blocked.get(c, 0) for c in related_cats)
            owasp_cov[owasp_id] = {
                "name": owasp_name,
                "detections": related_count,
                "blocked": related_blocked,
                "categories": related_cats,
                "covered": len(related_cats) > 0,
            }

        # Detection layer stats (aigis unique)
        layer_counts: dict[str, int] = defaultdict(int)
        for r in records:
            for layer in r.get("detection_layers", []):
                layer_counts[layer] += 1

        # Direction breakdown
        by_dir: dict[str, int] = defaultdict(int)
        for r in records:
            by_dir[r.get("direction", "input")] += 1

        # Auto-fix stats
        auto_fix_count = 0
        learned_count = 0
        try:
            from aigis.auto_fix import load_learned_patterns

            learned = load_learned_patterns()
            learned_count = len(learned)
            auto_fix_count = sum(1 for p in learned if p.get("auto_applied", False))
        except Exception:
            pass

        snap = MonitoringSnapshot(
            timestamp=datetime.now(UTC).isoformat(),
            period_hours=hours,
            total_scans=total,
            total_blocked=blocked,
            total_allowed=allowed,
            total_review=review,
            detection_rate=detection_rate,
            asr=asr,
            risk_distribution=dict(risk_dist),
            category_counts=dict(cat_counts),
            category_detection_rates=dict(cat_rates),
            owasp_coverage=owasp_cov,
            detection_by_layer=dict(layer_counts),
            by_direction=dict(by_dir),
            auto_fix_applied=auto_fix_count,
            learned_patterns_count=learned_count,
        )

        # Persist snapshot
        self._append_jsonl(self._snapshot_file, snap.to_dict())
        return snap

    def trend(self, days: int = 30, interval_hours: int = 24) -> list[dict]:
        """Load historical snapshots for trend analysis.

        Returns stored snapshots within the period, grouped by interval.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        snapshots = []
        if self._snapshot_file.exists():
            for line in self._read_jsonl(self._snapshot_file):
                try:
                    ts = datetime.fromisoformat(line["timestamp"])
                    if ts >= cutoff:
                        snapshots.append(line)
                except (KeyError, ValueError):
                    continue
        return snapshots

    def asr_trend(self, days: int = 30) -> list[dict[str, Any]]:
        """Get ASR (Attack Success Rate) trend over time.

        Returns daily ASR values, inspired by ai-scanner's trend tracking.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        daily: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "detected": 0})

        if self._scan_file.exists():
            for record in self._read_jsonl(self._scan_file):
                try:
                    ts = datetime.fromisoformat(record["timestamp"])
                    if ts < cutoff:
                        continue
                    day_key = ts.strftime("%Y-%m-%d")
                    if record.get("matched_rule_ids"):
                        daily[day_key]["total"] += 1
                        if record.get("risk_score", 0) > 30:
                            daily[day_key]["detected"] += 1
                except (KeyError, ValueError):
                    continue

        result = []
        for day in sorted(daily.keys()):
            d = daily[day]
            bypassed = d["total"] - d["detected"]
            result.append(
                {
                    "date": day,
                    "total_attacks": d["total"],
                    "bypassed": bypassed,
                    "blocked": d["detected"],
                    "asr": bypassed / d["total"] if d["total"] > 0 else 0.0,
                }
            )
        return result

    def category_heatmap(self, days: int = 30) -> dict[str, dict[str, int]]:
        """Generate a category-by-day heatmap of detections.

        Returns {category: {date: count}} for visualization.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        heatmap: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        if self._scan_file.exists():
            for record in self._read_jsonl(self._scan_file):
                try:
                    ts = datetime.fromisoformat(record["timestamp"])
                    if ts < cutoff:
                        continue
                    day_key = ts.strftime("%Y-%m-%d")
                    for cat in record.get("categories", []):
                        heatmap[cat][day_key] += 1
                except (KeyError, ValueError):
                    continue

        return {cat: dict(days) for cat, days in heatmap.items()}

    def owasp_scorecard(self) -> dict[str, dict[str, Any]]:
        """Generate OWASP LLM Top 10 scorecard with detection coverage.

        Shows which OWASP categories are covered by aigis's patterns,
        detection stats, and unique features per category.
        """
        snap = self.snapshot(hours=720)  # 30 days
        scorecard = {}

        # aigis unique features per OWASP category
        unique_features: dict[str, list[str]] = {
            "LLM01": [
                "4-layer detection (regex + similarity + decoded + multi-turn)",
                "Adversarial loop with auto-fix",
                "Real-time inline blocking (not post-hoc)",
            ],
            "LLM02": [
                "Output scanning with PII/credential detection",
                "Auto-sanitize (redaction) before response",
            ],
            "LLM05": [
                "MCP tool poisoning detection",
                "Rug-pull detection via snapshot diffing",
                "Server trust scoring",
            ],
            "LLM06": [
                "Japanese PII detection (My Number, phone, address)",
                "Auto-redaction with sanitize()",
                "Confidential data pattern matching",
            ],
            "LLM07": [
                "MCP inputSchema parameter injection detection",
                "Cross-tool shadowing detection",
            ],
            "LLM08": [
                "Capability-based access control (CaMeL-inspired)",
                "Policy-as-code governance",
                "Autonomy level tracking",
            ],
        }

        for owasp_id, data in snap.owasp_coverage.items():
            scorecard[owasp_id] = {
                **data,
                "unique_features": unique_features.get(owasp_id, []),
                "protection_level": (
                    "active"
                    if data["blocked"] > 0
                    else "monitored"
                    if data["detections"] > 0
                    else "pattern-ready"
                    if data["covered"]
                    else "not-covered"
                ),
            }

        return scorecard

    # === Internal ===

    def _append_jsonl(self, path: Path, data: dict) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict]:
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def _load_scans_since(self, cutoff: datetime) -> list[dict]:
        if not self._scan_file.exists():
            return []
        records = []
        for record in self._read_jsonl(self._scan_file):
            try:
                ts = datetime.fromisoformat(record["timestamp"])
                if ts >= cutoff:
                    records.append(record)
            except (KeyError, ValueError):
                continue
        return records


# === Behavioral monitoring exports ===
# Re-export the runtime behavioral monitoring components so they are
# accessible from aigis.monitor alongside the existing metrics classes.

from aigis.monitor.anomaly import AnomalyAlert, AnomalyDetector  # noqa: E402, F811
from aigis.monitor.baseline import BaselineBuilder, BehaviorProfile  # noqa: E402
from aigis.monitor.containment import (  # noqa: E402
    ContainmentLevel,
    ContainmentManager,
    ContainmentState,
)
from aigis.monitor.drift import DriftAlert, DriftDetector  # noqa: E402
from aigis.monitor.monitor import (  # noqa: E402
    BehavioralMonitor,
)
from aigis.monitor.monitor import (
    MonitoringReport as BehavioralMonitoringReport,
)
from aigis.monitor.tracker import ActionTracker, TrackedAction  # noqa: E402

__all__ = [
    # Existing metrics monitoring
    "SecurityMonitor",
    "ScanRecord",
    "BenchmarkRecord",
    "MonitoringSnapshot",
    "OWASP_LLM_TOP10",
    "CATEGORY_TO_OWASP",
    # Behavioral monitoring
    "BehavioralMonitor",
    "BehavioralMonitoringReport",
    "ActionTracker",
    "TrackedAction",
    "BehaviorProfile",
    "BaselineBuilder",
    "DriftDetector",
    "DriftAlert",
    "AnomalyDetector",
    "AnomalyAlert",
    "ContainmentManager",
    "ContainmentLevel",
    "ContainmentState",
]
