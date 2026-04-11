"""SecurityMonitor (Behavioral) -- main orchestrator for runtime behavioral monitoring.

Ties together action tracking, drift detection, anomaly detection, and
graduated containment into a single, easy-to-use API.

This is the behavioral monitoring layer that complements the existing
SecurityMonitor (metrics aggregation in __init__.py). While the metrics
monitor records scan results for reporting, this behavioral monitor
watches agent *actions* in real-time to detect intent drift, anomalies,
and escalation patterns.

Usage::

    from aigis.monitor.monitor import BehavioralMonitor

    monitor = BehavioralMonitor()

    # Record every tool call
    monitor.record_action("Bash", "shell:exec", "ls -la", risk_score=0)

    # Check for anomalies
    alerts = monitor.check()

    # Check containment before allowing an action
    if not monitor.should_allow("shell:exec"):
        return "Blocked by containment"

    # Get full report
    report = monitor.report()

Academic basis:
  - MI9 (arxiv 2508.03858): FSM-based conformance, graduated containment
  - AgentSpec (arxiv 2503.18666): runtime constraint enforcement
  - ARMO Intent Drift: action chain analysis
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aigis.monitor.anomaly import AnomalyAlert, AnomalyDetector
from aigis.monitor.baseline import BaselineBuilder, BehaviorProfile
from aigis.monitor.containment import ContainmentLevel, ContainmentManager, ContainmentState
from aigis.monitor.drift import DriftAlert, DriftDetector
from aigis.monitor.tracker import ActionTracker, TrackedAction


@dataclass
class MonitoringReport:
    """Report summarizing the behavioral monitoring state.

    Note: This is the *behavioral* MonitoringReport, distinct from the
    *metrics* MonitoringReport in aigis.report. The metrics report
    covers scan results and OWASP coverage; this one covers runtime
    agent behavior.

    Attributes:
        session_id: Unique session identifier.
        duration_seconds: How long the session has been running.
        total_actions: Number of actions recorded.
        drift_alerts: Drift alerts detected in this session.
        anomaly_alerts: Anomaly alerts detected in this session.
        containment_state: Current containment state.
        action_summary: Resource histogram for the session.
        risk_summary: Risk score statistics.
        timestamp: ISO 8601 timestamp of report generation.
    """

    session_id: str
    duration_seconds: float
    total_actions: int
    drift_alerts: list[DriftAlert]
    anomaly_alerts: list[AnomalyAlert]
    containment_state: ContainmentState
    action_summary: dict[str, int]
    risk_summary: dict[str, Any]
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "session_id": self.session_id,
            "duration_seconds": self.duration_seconds,
            "total_actions": self.total_actions,
            "drift_alerts": [a.to_dict() for a in self.drift_alerts],
            "anomaly_alerts": [a.to_dict() for a in self.anomaly_alerts],
            "containment_state": self.containment_state.to_dict(),
            "action_summary": self.action_summary,
            "risk_summary": self.risk_summary,
            "timestamp": self.timestamp,
        }


class BehavioralMonitor:
    """Main orchestrator for runtime behavioral monitoring.

    Ties together:
    - ActionTracker: records tool calls in a sliding window
    - DriftDetector: compares current behavior against baseline
    - AnomalyDetector: finds dangerous action sequences
    - ContainmentManager: graduated response to alerts

    Usage::

        monitor = BehavioralMonitor()

        # Record every tool call
        monitor.record_action("Bash", "shell:exec", "ls -la", risk_score=0)

        # Check for anomalies (call periodically or after each action)
        alerts = monitor.check()

        # Check if an action should be allowed under current containment
        if not monitor.should_allow("shell:exec"):
            return "Blocked by containment"

        # Get full report
        report = monitor.report()

    Args:
        baseline: Optional behavioral baseline for drift detection.
            If None, drift detection is disabled until a baseline is
            learned or loaded.
        containment_thresholds: Custom alert thresholds for containment
            escalation. See ContainmentManager.DEFAULT_THRESHOLDS.
        window_size: Action tracker window size (default 200).
        sensitivity: Drift detection sensitivity in standard deviations
            (default 2.0).
    """

    def __init__(
        self,
        baseline: BehaviorProfile | None = None,
        containment_thresholds: dict[ContainmentLevel, int] | None = None,
        window_size: int = 200,
        sensitivity: float = 2.0,
    ) -> None:
        self._tracker = ActionTracker(window_size=window_size)
        self._drift: DriftDetector | None = (
            DriftDetector(baseline, sensitivity=sensitivity) if baseline else None
        )
        self._anomaly = AnomalyDetector(baseline)
        self._containment = ContainmentManager(containment_thresholds)
        self._baseline = baseline
        self._all_drift_alerts: list[DriftAlert] = []
        self._all_anomaly_alerts: list[AnomalyAlert] = []

    @property
    def tracker(self) -> ActionTracker:
        """Access the underlying ActionTracker."""
        return self._tracker

    @property
    def containment(self) -> ContainmentManager:
        """Access the underlying ContainmentManager."""
        return self._containment

    def record_action(
        self,
        tool_name: str,
        resource: str,
        target: str,
        risk_score: int = 0,
        outcome: str = "allowed",
    ) -> TrackedAction:
        """Record an agent action.

        Args:
            tool_name: Name of the tool (e.g. "Bash", "Read", "Write").
            resource: Resource type (e.g. "file:read", "shell:exec").
            target: Specific target (file path, command, URL).
            risk_score: Risk score from 0-100.
            outcome: Outcome ("allowed", "blocked", "error").

        Returns:
            The recorded TrackedAction.
        """
        return self._tracker.record(
            tool_name=tool_name,
            resource=resource,
            target=target,
            risk_score=risk_score,
            outcome=outcome,
        )

    def check(self) -> list[DriftAlert | AnomalyAlert]:
        """Run all detectors on recent actions and update containment.

        Returns:
            Combined list of drift and anomaly alerts.
        """
        recent = self._tracker.recent(100)
        if not recent:
            return []

        alerts: list[DriftAlert | AnomalyAlert] = []

        # Drift detection (requires baseline)
        if self._drift is not None:
            drift_alerts = self._drift.check(recent)
            alerts.extend(drift_alerts)
            self._all_drift_alerts.extend(drift_alerts)

        # Anomaly detection (always active)
        anomaly_alerts = self._anomaly.analyze(recent)
        alerts.extend(anomaly_alerts)
        self._all_anomaly_alerts.extend(anomaly_alerts)

        # Update containment
        if alerts:
            self._containment.process_alerts(alerts)

        return alerts

    def should_allow(self, resource: str) -> bool:
        """Check if a resource access should be allowed under current containment.

        Args:
            resource: Resource type string (e.g. "file:read", "shell:exec").

        Returns:
            True if allowed, False if blocked by containment.
        """
        return self._containment.should_allow(resource)

    def report(self) -> MonitoringReport:
        """Generate a comprehensive monitoring report.

        Returns:
            MonitoringReport with session statistics, alerts, and containment.
        """
        summary = self._tracker.session_summary()
        actions = self._tracker.recent(200)

        # Risk summary
        risk_scores = [a.risk_score for a in actions]
        if risk_scores:
            risk_summary = {
                "avg_risk_score": sum(risk_scores) / len(risk_scores),
                "max_risk_score": max(risk_scores),
                "min_risk_score": min(risk_scores),
                "high_risk_count": sum(1 for s in risk_scores if s >= 70),
                "medium_risk_count": sum(1 for s in risk_scores if 30 <= s < 70),
                "low_risk_count": sum(1 for s in risk_scores if s < 30),
            }
        else:
            risk_summary = {
                "avg_risk_score": 0.0,
                "max_risk_score": 0,
                "min_risk_score": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
            }

        return MonitoringReport(
            session_id=self._tracker.session_id,
            duration_seconds=summary["duration_seconds"],
            total_actions=summary["total_actions"],
            drift_alerts=self._all_drift_alerts[:],
            anomaly_alerts=self._all_anomaly_alerts[:],
            containment_state=self._containment.current_state(),
            action_summary=self._tracker.resource_histogram(window_seconds=3600),
            risk_summary=risk_summary,
        )

    def learn_baseline(self) -> BehaviorProfile:
        """Build a baseline from the current session's recorded actions.

        Returns:
            BehaviorProfile built from current session data.
        """
        actions = self._tracker.recent(200)
        builder = BaselineBuilder()
        if actions:
            builder.observe(actions)
        profile = builder.build()

        # Install the new baseline
        self._baseline = profile
        self._drift = DriftDetector(profile)
        self._anomaly = AnomalyDetector(profile)

        return profile

    def save_baseline(self, path: Path) -> None:
        """Save the current baseline to a JSON file.

        Args:
            path: Destination file path.

        Raises:
            RuntimeError: If no baseline has been learned or loaded.
        """
        if self._baseline is None:
            raise RuntimeError("No baseline to save. Call learn_baseline() first.")

        builder = BaselineBuilder()
        builder._observations = []  # Empty -- we already have the profile
        path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._baseline.to_dict(), f, indent=2, ensure_ascii=False)

    def load_baseline(self, path: Path) -> None:
        """Load a baseline from a JSON file.

        Args:
            path: Path to the JSON file.
        """
        profile = BaselineBuilder.load(path)
        self._baseline = profile
        self._drift = DriftDetector(profile)
        self._anomaly = AnomalyDetector(profile)
