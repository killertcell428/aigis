"""Intent Drift Detection -- detects behavioral drift from established baseline.

Compares recent agent actions against a statistical baseline profile to
identify frequency spikes, resource distribution shifts, privilege escalation
patterns, and data exfiltration patterns.

No LLM needed -- pure statistical comparison using z-score anomaly detection.

Academic basis:
  - MI9 (arxiv 2508.03858): goal-conditioned drift detection
  - ARMO Intent Drift research: action chain analysis
    (tool invocation -> data access -> external egress)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from aigis.monitor.baseline import BehaviorProfile
from aigis.monitor.tracker import TrackedAction


@dataclass
class DriftAlert:
    """An alert indicating behavioral drift from baseline.

    Attributes:
        drift_type: Classification of the drift
            ("frequency_spike", "resource_shift", "escalation", "exfiltration_pattern").
        drift_score: Severity from 0.0 (minor) to 1.0 (extreme).
        description: Human-readable explanation.
        evidence: Specific actions or metrics that triggered the alert.
        timestamp: When the drift was detected (epoch seconds).
    """

    drift_type: str
    drift_score: float
    description: str
    evidence: list[str] = field(default_factory=list)
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "drift_type": self.drift_type,
            "drift_score": self.drift_score,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


# Privilege levels for escalation detection (lower = less privilege)
_PRIVILEGE_LEVELS: dict[str, int] = {
    "file:search": 0,
    "file:read": 1,
    "file:write": 2,
    "shell:exec": 3,
    "network:fetch": 2,
    "network:send": 3,
    "agent:spawn": 4,
}

# Resources that indicate data access vs. external communication
_DATA_ACCESS_RESOURCES = {"file:read", "file:search", "database:query"}
_EXTERNAL_RESOURCES = {"network:fetch", "network:send", "agent:spawn"}


class DriftDetector:
    """Detects behavioral drift from established baseline.

    Uses z-score based anomaly detection: if a metric exceeds the baseline
    mean by more than ``sensitivity`` standard deviations, it triggers an
    alert.

    Args:
        baseline: The expected behavior profile to compare against.
        sensitivity: Number of standard deviations for anomaly threshold.
            Default 2.0 means any metric > mean + 2*stddev triggers an alert.
    """

    def __init__(self, baseline: BehaviorProfile, sensitivity: float = 2.0) -> None:
        self._baseline = baseline
        self._sensitivity = sensitivity

    @property
    def baseline(self) -> BehaviorProfile:
        """The baseline profile used for comparison."""
        return self._baseline

    def check(self, recent_actions: list[TrackedAction]) -> list[DriftAlert]:
        """Compare recent actions against baseline and return drift alerts.

        Runs all four drift checks:
        1. Frequency spike: tool usage rate significantly above baseline
        2. Resource shift: resource distribution diverges from baseline
        3. Escalation pattern: progressive privilege increase
        4. Exfiltration pattern: data access followed by external communication

        Args:
            recent_actions: Actions to analyze (typically from ActionTracker.recent()).

        Returns:
            List of DriftAlert instances. Empty list means no drift detected.
        """
        if not recent_actions:
            return []

        alerts: list[DriftAlert] = []

        freq = self._check_frequency_spike(recent_actions)
        if freq is not None:
            alerts.append(freq)

        shift = self._check_resource_shift(recent_actions)
        if shift is not None:
            alerts.append(shift)

        esc = self._check_escalation_pattern(recent_actions)
        if esc is not None:
            alerts.append(esc)

        exfil = self._check_exfiltration_pattern(recent_actions)
        if exfil is not None:
            alerts.append(exfil)

        return alerts

    def _check_frequency_spike(self, actions: list[TrackedAction]) -> DriftAlert | None:
        """Check if any tool's usage rate exceeds baseline significantly.

        Computes the current calls-per-minute for each tool and compares
        against baseline mean + sensitivity * stddev.
        """
        if len(actions) < 2:
            return None

        timestamps = [a.timestamp for a in actions]
        duration_minutes = (max(timestamps) - min(timestamps)) / 60.0
        if duration_minutes <= 0:
            return None

        tool_counts: dict[str, int] = {}
        for a in actions:
            tool_counts[a.tool_name] = tool_counts.get(a.tool_name, 0) + 1

        evidence: list[str] = []
        max_z_score = 0.0

        for tool, count in tool_counts.items():
            current_rate = count / duration_minutes
            baseline_mean = self._baseline.tool_frequency.get(tool, 0.0)
            baseline_std = self._baseline.tool_frequency_stddev.get(tool, 0.0)

            if baseline_mean == 0.0 and current_rate > 0:
                # Tool never seen in baseline -- could be new or suspicious
                if current_rate > 1.0:  # More than 1 call/min of unknown tool
                    evidence.append(f"{tool}: {current_rate:.1f}/min (not in baseline)")
                    max_z_score = max(max_z_score, 3.0)
                continue

            if baseline_std == 0.0:
                # No variance in baseline; flag if current > 2x baseline
                if current_rate > baseline_mean * 2 and current_rate > baseline_mean + 1.0:
                    z = (current_rate - baseline_mean) / max(baseline_mean * 0.5, 0.1)
                    evidence.append(
                        f"{tool}: {current_rate:.1f}/min vs baseline {baseline_mean:.1f}/min"
                    )
                    max_z_score = max(max_z_score, min(z, 5.0))
                continue

            z_score = (current_rate - baseline_mean) / baseline_std
            if z_score > self._sensitivity:
                evidence.append(
                    f"{tool}: {current_rate:.1f}/min vs baseline "
                    f"{baseline_mean:.1f} +/- {baseline_std:.1f}/min (z={z_score:.1f})"
                )
                max_z_score = max(max_z_score, z_score)

        if not evidence:
            return None

        drift_score = min(max_z_score / 5.0, 1.0)  # Normalize to 0-1
        return DriftAlert(
            drift_type="frequency_spike",
            drift_score=drift_score,
            description=f"Tool usage rate exceeds baseline by {max_z_score:.1f} standard deviations",
            evidence=evidence,
        )

    def _check_resource_shift(self, actions: list[TrackedAction]) -> DriftAlert | None:
        """Check if the resource distribution diverges from baseline.

        Uses a simple divergence metric: sum of absolute differences between
        current and baseline resource distributions.
        """
        if not actions:
            return None

        # Current distribution
        resource_counts: dict[str, int] = {}
        for a in actions:
            resource_counts[a.resource] = resource_counts.get(a.resource, 0) + 1

        total = len(actions)
        current_dist: dict[str, float] = {
            res: count / total for res, count in resource_counts.items()
        }

        # All resources from both current and baseline
        all_resources = set(current_dist.keys()) | set(self._baseline.resource_distribution.keys())
        if not all_resources:
            return None

        # Calculate divergence (sum of absolute differences / 2)
        divergence = 0.0
        evidence: list[str] = []

        for res in all_resources:
            current_pct = current_dist.get(res, 0.0)
            baseline_pct = self._baseline.resource_distribution.get(res, 0.0)
            diff = abs(current_pct - baseline_pct)
            divergence += diff

            if diff > 0.15:  # Report individual resources with >15% shift
                evidence.append(
                    f"{res}: {current_pct:.0%} (baseline {baseline_pct:.0%}, shift {diff:+.0%})"
                )

        # Divergence / 2 gives a 0-1 score (max divergence = 2.0 when fully disjoint)
        divergence_score = divergence / 2.0

        # Threshold: flag if divergence exceeds a reasonable limit
        threshold = 0.3  # 30% divergence
        if divergence_score < threshold or not evidence:
            return None

        drift_score = min(divergence_score, 1.0)
        return DriftAlert(
            drift_type="resource_shift",
            drift_score=drift_score,
            description=(f"Resource access pattern diverges {divergence_score:.0%} from baseline"),
            evidence=evidence,
        )

    def _check_escalation_pattern(self, actions: list[TrackedAction]) -> DriftAlert | None:
        """Check for progressive privilege escalation in the action sequence.

        Looks for a monotonically increasing privilege level across consecutive
        actions, indicating the agent is progressively gaining more access.
        """
        if len(actions) < 3:
            return None

        # Map actions to privilege levels
        priv_sequence: list[tuple[int, TrackedAction]] = []
        for a in actions:
            level = _PRIVILEGE_LEVELS.get(a.resource)
            if level is not None:
                priv_sequence.append((level, a))

        if len(priv_sequence) < 3:
            return None

        # Look for escalation runs (sequences of increasing privilege)
        max_run_length = 0
        current_run = 1
        run_actions: list[TrackedAction] = [priv_sequence[0][1]]
        best_run_actions: list[TrackedAction] = []

        for i in range(1, len(priv_sequence)):
            if priv_sequence[i][0] > priv_sequence[i - 1][0]:
                current_run += 1
                run_actions.append(priv_sequence[i][1])
            else:
                if current_run > max_run_length:
                    max_run_length = current_run
                    best_run_actions = run_actions[:]
                current_run = 1
                run_actions = [priv_sequence[i][1]]

        # Check the last run
        if current_run > max_run_length:
            max_run_length = current_run
            best_run_actions = run_actions[:]

        if max_run_length < 3:
            return None

        evidence = [f"{a.resource} -> {a.target[:60]}" for a in best_run_actions]
        drift_score = min(max_run_length / 5.0, 1.0)

        return DriftAlert(
            drift_type="escalation",
            drift_score=drift_score,
            description=(
                f"Privilege escalation detected: {max_run_length} consecutive "
                f"steps of increasing privilege"
            ),
            evidence=evidence,
        )

    def _check_exfiltration_pattern(self, actions: list[TrackedAction]) -> DriftAlert | None:
        """Check for data access followed by external communication.

        The classic exfiltration pattern: read data -> send it out.
        Looks for data access actions followed by network/external actions
        within a short time window.
        """
        if len(actions) < 2:
            return None

        evidence: list[str] = []
        pattern_count = 0

        # Scan for read -> send patterns
        for i, action in enumerate(actions):
            if action.resource not in _DATA_ACCESS_RESOURCES:
                continue

            # Look ahead for external actions within 60 seconds
            for j in range(i + 1, min(i + 20, len(actions))):
                later = actions[j]
                if later.resource in _EXTERNAL_RESOURCES:
                    time_gap = later.timestamp - action.timestamp
                    if 0 <= time_gap <= 60:
                        pattern_count += 1
                        evidence.append(
                            f"{action.resource}({action.target[:40]}) -> "
                            f"{later.resource}({later.target[:40]}) "
                            f"[{time_gap:.1f}s gap]"
                        )
                        break  # One match per data access action

        if pattern_count == 0:
            return None

        drift_score = min(pattern_count / 3.0, 1.0)
        return DriftAlert(
            drift_type="exfiltration_pattern",
            drift_score=drift_score,
            description=(
                f"Potential data exfiltration: {pattern_count} instances of "
                f"data access followed by external communication"
            ),
            evidence=evidence[:10],  # Limit evidence items
        )
