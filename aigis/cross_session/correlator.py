"""Cross-Session Correlation -- detect patterns across multiple sessions.

Analyses four types of cross-session threat patterns:

1. Escalation trend: risk scores or containment levels increasing across
   successive sessions.
2. Resource drift: access patterns shifting gradually over sessions
   (e.g., normal sessions access docs/, then gradually start accessing .ssh/).
3. Recurring threat: same threat type appearing in multiple sessions.
4. Unusual session: session that deviates significantly from the
   historical norm (outlier detection using z-scores).

Academic basis:
  - arxiv 2604.02623: temporally decoupled memory poisoning
  - MI9 (arxiv 2508.03858): cross-session behavioral analysis
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from aigis.cross_session.store import SessionRecord, SessionStore

# Ordered containment levels for numeric comparison
_CONTAINMENT_ORDER: dict[str, int] = {
    "normal": 0,
    "warn": 1,
    "throttle": 2,
    "restrict": 3,
    "isolate": 4,
    "stop": 5,
}


@dataclass
class CorrelationAlert:
    """An alert indicating a cross-session threat pattern.

    Attributes:
        alert_type: Classification of the pattern
            ("escalation_trend", "resource_drift", "recurring_threat",
             "unusual_session").
        severity: Impact level ("low", "medium", "high", "critical").
        description: Human-readable explanation.
        sessions_involved: Session IDs that contributed to this alert.
        evidence: Supporting data for the alert.
    """

    alert_type: str
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    sessions_involved: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "sessions_involved": self.sessions_involved,
            "evidence": self.evidence,
        }


class CrossSessionCorrelator:
    """Detect patterns across multiple sessions.

    Uses the SessionStore to load recent session records and runs
    statistical analyses to identify escalation trends, resource drift,
    recurring threats, and outlier sessions.

    Args:
        store: The SessionStore providing session records.
    """

    def __init__(self, store: SessionStore) -> None:
        self._store = store

    def analyze(self, window_days: int = 30) -> list[CorrelationAlert]:
        """Run all correlation checks across recent sessions.

        Args:
            window_days: Number of days to look back.

        Returns:
            List of CorrelationAlert instances. Empty if no patterns found.
        """
        since = (datetime.now(UTC) - timedelta(days=window_days)).isoformat()
        sessions = self._store.list_sessions(since=since, limit=500)

        if len(sessions) < 2:
            return []

        # Sort chronologically (oldest first) for trend analysis
        sessions.sort(key=lambda s: s.started_at)

        alerts: list[CorrelationAlert] = []
        alerts.extend(self._check_escalation_trend(sessions))
        alerts.extend(self._check_resource_drift(sessions))
        alerts.extend(self._check_recurring_threats(sessions))
        alerts.extend(self._check_unusual_sessions(sessions))

        return alerts

    def _check_escalation_trend(self, sessions: list[SessionRecord]) -> list[CorrelationAlert]:
        """Detect if risk scores or containment levels are increasing.

        Looks for monotonically increasing runs of at least 3 sessions
        in either max_risk_score or containment level.
        """
        alerts: list[CorrelationAlert] = []

        # --- Risk score trend ---
        if len(sessions) >= 3:
            scores = [s.max_risk_score for s in sessions]
            best_run_start = 0
            best_run_len = 1
            run_start = 0
            run_len = 1

            for i in range(1, len(scores)):
                if scores[i] > scores[i - 1]:
                    run_len += 1
                else:
                    if run_len > best_run_len:
                        best_run_len = run_len
                        best_run_start = run_start
                    run_start = i
                    run_len = 1

            if run_len > best_run_len:
                best_run_len = run_len
                best_run_start = run_start

            if best_run_len >= 3:
                involved = sessions[best_run_start : best_run_start + best_run_len]
                run_scores = scores[best_run_start : best_run_start + best_run_len]
                severity = (
                    "high" if run_scores[-1] >= 70 else "medium" if run_scores[-1] >= 40 else "low"
                )

                alerts.append(
                    CorrelationAlert(
                        alert_type="escalation_trend",
                        severity=severity,
                        description=(
                            f"Risk scores increasing across {best_run_len} consecutive sessions: "
                            f"{run_scores[0]} -> {run_scores[-1]}"
                        ),
                        sessions_involved=[s.session_id for s in involved],
                        evidence={
                            "metric": "max_risk_score",
                            "values": run_scores,
                            "trend": "increasing",
                        },
                    )
                )

        # --- Containment level trend ---
        if len(sessions) >= 3:
            levels = [_CONTAINMENT_ORDER.get(s.containment_max_level, 0) for s in sessions]
            best_run_start = 0
            best_run_len = 1
            run_start = 0
            run_len = 1

            for i in range(1, len(levels)):
                if levels[i] > levels[i - 1]:
                    run_len += 1
                else:
                    if run_len > best_run_len:
                        best_run_len = run_len
                        best_run_start = run_start
                    run_start = i
                    run_len = 1

            if run_len > best_run_len:
                best_run_len = run_len
                best_run_start = run_start

            if best_run_len >= 3:
                involved = sessions[best_run_start : best_run_start + best_run_len]
                level_names = [s.containment_max_level for s in involved]
                severity = (
                    "critical"
                    if levels[best_run_start + best_run_len - 1] >= 4
                    else "high"
                    if levels[best_run_start + best_run_len - 1] >= 3
                    else "medium"
                )

                alerts.append(
                    CorrelationAlert(
                        alert_type="escalation_trend",
                        severity=severity,
                        description=(
                            f"Containment levels escalating across {best_run_len} sessions: "
                            f"{level_names[0]} -> {level_names[-1]}"
                        ),
                        sessions_involved=[s.session_id for s in involved],
                        evidence={
                            "metric": "containment_level",
                            "values": level_names,
                            "trend": "escalating",
                        },
                    )
                )

        return alerts

    def _check_resource_drift(self, sessions: list[SessionRecord]) -> list[CorrelationAlert]:
        """Detect gradual shift in resource access patterns.

        Compares the resource histogram of recent sessions against the
        overall historical distribution. Flags new resource types that
        appear in later sessions but were absent earlier.
        """
        if len(sessions) < 4:
            return []

        alerts: list[CorrelationAlert] = []

        # Split into early half and late half
        mid = len(sessions) // 2
        early = sessions[:mid]
        late = sessions[mid:]

        # Aggregate resource histograms
        early_hist: dict[str, int] = {}
        for s in early:
            for res, count in s.resource_histogram.items():
                early_hist[res] = early_hist.get(res, 0) + count

        late_hist: dict[str, int] = {}
        for s in late:
            for res, count in s.resource_histogram.items():
                late_hist[res] = late_hist.get(res, 0) + count

        # Find resources that appear in late but not in early (new access patterns)
        new_resources = set(late_hist.keys()) - set(early_hist.keys())

        # Sensitive resources that are especially concerning
        sensitive_resources = {
            "shell:exec",
            "network:send",
            "agent:spawn",
            "file:write",
            "network:fetch",
        }

        if new_resources:
            sensitive_new = new_resources & sensitive_resources
            severity = "high" if sensitive_new else "medium" if len(new_resources) > 2 else "low"

            alerts.append(
                CorrelationAlert(
                    alert_type="resource_drift",
                    severity=severity,
                    description=(
                        f"New resource types appeared in recent sessions: "
                        f"{', '.join(sorted(new_resources))}"
                    ),
                    sessions_involved=[s.session_id for s in late],
                    evidence={
                        "new_resources": sorted(new_resources),
                        "early_resources": sorted(early_hist.keys()),
                        "late_resources": sorted(late_hist.keys()),
                    },
                )
            )

        # Check distribution shift (for shared resources)
        shared = set(early_hist.keys()) & set(late_hist.keys())
        if shared:
            early_total = sum(early_hist.values()) or 1
            late_total = sum(late_hist.values()) or 1

            shifts: list[str] = []
            for res in shared:
                early_pct = early_hist[res] / early_total
                late_pct = late_hist[res] / late_total
                diff = abs(late_pct - early_pct)
                if diff > 0.20:  # >20% shift
                    shifts.append(f"{res}: {early_pct:.0%} -> {late_pct:.0%}")

            if shifts:
                alerts.append(
                    CorrelationAlert(
                        alert_type="resource_drift",
                        severity="medium",
                        description=("Resource distribution shifted significantly across sessions"),
                        sessions_involved=[s.session_id for s in sessions],
                        evidence={
                            "shifts": shifts,
                        },
                    )
                )

        return alerts

    def _check_recurring_threats(self, sessions: list[SessionRecord]) -> list[CorrelationAlert]:
        """Detect the same threat type appearing across multiple sessions.

        Groups alerts by type across sessions and flags any threat type
        that recurs in 3+ sessions.
        """
        alerts: list[CorrelationAlert] = []

        # Collect alert_type -> list of session IDs
        threat_sessions: dict[str, list[str]] = {}
        for s in sessions:
            seen_types: set[str] = set()
            for alert in s.alerts:
                alert_type = (
                    alert.get("drift_type")
                    or alert.get("anomaly_type")
                    or alert.get("alert_type", "")
                )
                if alert_type and alert_type not in seen_types:
                    seen_types.add(alert_type)
                    if alert_type not in threat_sessions:
                        threat_sessions[alert_type] = []
                    threat_sessions[alert_type].append(s.session_id)

        for threat_type, session_ids in threat_sessions.items():
            if len(session_ids) >= 3:
                severity = "high" if len(session_ids) >= 5 else "medium"
                alerts.append(
                    CorrelationAlert(
                        alert_type="recurring_threat",
                        severity=severity,
                        description=(
                            f"Threat '{threat_type}' recurring across {len(session_ids)} sessions"
                        ),
                        sessions_involved=session_ids,
                        evidence={
                            "threat_type": threat_type,
                            "occurrence_count": len(session_ids),
                        },
                    )
                )

        return alerts

    def _check_unusual_sessions(self, sessions: list[SessionRecord]) -> list[CorrelationAlert]:
        """Detect outlier sessions that deviate from the historical norm.

        Uses z-score analysis on total_actions, max_risk_score, and number
        of unique tools used. A session is flagged as unusual if any metric
        exceeds 2 standard deviations from the mean.
        """
        if len(sessions) < 5:
            return []

        alerts: list[CorrelationAlert] = []

        # Collect metrics across all sessions
        action_counts = [s.total_actions for s in sessions]
        risk_scores = [s.max_risk_score for s in sessions]
        tool_counts = [len(s.tools_used) for s in sessions]

        metrics: list[tuple[str, list[int]]] = [
            ("total_actions", action_counts),
            ("max_risk_score", risk_scores),
            ("tools_used_count", tool_counts),
        ]

        for session in sessions:
            reasons: list[str] = []
            max_z = 0.0

            for metric_name, values in metrics:
                if len(values) < 3:
                    continue

                mean = statistics.mean(values)
                try:
                    stdev = statistics.stdev(values)
                except statistics.StatisticsError:
                    continue

                if stdev == 0:
                    continue

                if metric_name == "total_actions":
                    value = session.total_actions
                elif metric_name == "max_risk_score":
                    value = session.max_risk_score
                else:
                    value = len(session.tools_used)

                z = abs(value - mean) / stdev
                if z > 2.0:
                    reasons.append(f"{metric_name}: {value} (mean={mean:.1f}, z={z:.1f})")
                    max_z = max(max_z, z)

            if reasons:
                severity = "high" if max_z > 3.0 else "medium" if max_z > 2.5 else "low"
                alerts.append(
                    CorrelationAlert(
                        alert_type="unusual_session",
                        severity=severity,
                        description=(
                            f"Session {session.session_id} deviates significantly from norm"
                        ),
                        sessions_involved=[session.session_id],
                        evidence={
                            "deviations": reasons,
                            "max_z_score": round(max_z, 2),
                        },
                    )
                )

        return alerts
