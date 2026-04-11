"""Behavioral Baseline -- statistical profile of normal agent behavior.

Learns what "normal" looks like from observed actions: tool call frequencies,
resource distribution, typical risk scores. Used by DriftDetector and
AnomalyDetector to identify deviations from expected behavior.

Pure statistics -- no ML dependencies required. Uses only stdlib (statistics,
json, collections).

Academic basis:
  - MI9 (arxiv 2508.03858): goal-conditioned drift detection
  - ARMO Intent Drift research: behavioral profiling
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from aigis.monitor.tracker import TrackedAction


@dataclass
class BehaviorProfile:
    """Statistical profile of normal agent behavior.

    Captures the expected distribution of tool usage, resource access patterns,
    and risk scores observed during normal operation.

    Attributes:
        tool_frequency: Tool name to average calls per minute.
        tool_frequency_stddev: Tool name to standard deviation of calls per minute.
        resource_distribution: Resource type to percentage (0.0 - 1.0).
        typical_risk_scores: Resource type to (mean, stddev) of risk scores.
        session_count: Number of sessions used to build this profile.
        total_actions: Total number of actions observed.
    """

    tool_frequency: dict[str, float] = field(default_factory=dict)
    tool_frequency_stddev: dict[str, float] = field(default_factory=dict)
    resource_distribution: dict[str, float] = field(default_factory=dict)
    typical_risk_scores: dict[str, tuple[float, float]] = field(default_factory=dict)
    session_count: int = 0
    total_actions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict.

        Tuple values in typical_risk_scores are converted to lists for JSON.
        """
        d = asdict(self)
        # Convert tuples to lists for JSON serialization
        d["typical_risk_scores"] = {k: list(v) for k, v in self.typical_risk_scores.items()}
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BehaviorProfile:
        """Reconstruct from a dict (e.g. loaded from JSON).

        List values in typical_risk_scores are converted back to tuples.
        """
        risk_scores = data.get("typical_risk_scores", {})
        converted_risk = {
            k: (v[0], v[1]) if isinstance(v, (list, tuple)) and len(v) == 2 else (0.0, 0.0)
            for k, v in risk_scores.items()
        }
        return cls(
            tool_frequency=data.get("tool_frequency", {}),
            tool_frequency_stddev=data.get("tool_frequency_stddev", {}),
            resource_distribution=data.get("resource_distribution", {}),
            typical_risk_scores=converted_risk,
            session_count=data.get("session_count", 0),
            total_actions=data.get("total_actions", 0),
        )


@dataclass
class _SessionObservation:
    """Internal: raw data from a single observation window."""

    actions: list[TrackedAction]
    duration_seconds: float
    tool_counts: dict[str, int] = field(default_factory=dict)
    resource_counts: dict[str, int] = field(default_factory=dict)
    risk_by_resource: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))


class BaselineBuilder:
    """Learns normal behavior patterns from observed actions.

    Pure statistics -- no ML dependencies. Collects observations over
    multiple sessions and builds a statistical profile for comparison.

    Usage::

        builder = BaselineBuilder()
        builder.observe(actions_from_session_1)
        builder.observe(actions_from_session_2)
        profile = builder.build()
        builder.save(Path("baseline.json"))
    """

    def __init__(self) -> None:
        self._observations: list[_SessionObservation] = []

    def observe(self, actions: list[TrackedAction]) -> None:
        """Add a batch of actions as one observation window.

        Args:
            actions: List of TrackedAction from a session or time window.
        """
        if not actions:
            return

        # Calculate duration from first to last action
        timestamps = [a.timestamp for a in actions]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 60.0
        # Ensure minimum 1 second to avoid division by zero
        duration = max(duration, 1.0)

        tool_counts: dict[str, int] = {}
        resource_counts: dict[str, int] = {}
        risk_by_resource: dict[str, list[int]] = defaultdict(list)

        for action in actions:
            tool_counts[action.tool_name] = tool_counts.get(action.tool_name, 0) + 1
            resource_counts[action.resource] = resource_counts.get(action.resource, 0) + 1
            risk_by_resource[action.resource].append(action.risk_score)

        obs = _SessionObservation(
            actions=actions,
            duration_seconds=duration,
            tool_counts=tool_counts,
            resource_counts=resource_counts,
            risk_by_resource=dict(risk_by_resource),
        )
        self._observations.append(obs)

    def build(self) -> BehaviorProfile:
        """Build a BehaviorProfile from all recorded observations.

        Computes mean and standard deviation of tool call rates, resource
        distributions, and risk scores across all observation windows.

        Returns:
            BehaviorProfile with statistical aggregates.
        """
        if not self._observations:
            return BehaviorProfile()

        # Collect per-session tool rates (calls per minute)
        all_tools: set[str] = set()
        all_resources: set[str] = set()
        for obs in self._observations:
            all_tools.update(obs.tool_counts.keys())
            all_resources.update(obs.resource_counts.keys())

        # Tool frequency: calls per minute across sessions
        tool_rates: dict[str, list[float]] = {t: [] for t in all_tools}
        for obs in self._observations:
            minutes = obs.duration_seconds / 60.0
            for tool in all_tools:
                count = obs.tool_counts.get(tool, 0)
                tool_rates[tool].append(count / minutes if minutes > 0 else 0.0)

        tool_frequency = {
            t: statistics.mean(rates) if rates else 0.0 for t, rates in tool_rates.items()
        }
        tool_frequency_stddev = {
            t: statistics.stdev(rates) if len(rates) > 1 else 0.0 for t, rates in tool_rates.items()
        }

        # Resource distribution: percentage across all actions
        total_actions = sum(sum(obs.resource_counts.values()) for obs in self._observations)
        resource_totals: dict[str, int] = {}
        for obs in self._observations:
            for res, count in obs.resource_counts.items():
                resource_totals[res] = resource_totals.get(res, 0) + count

        resource_distribution = {
            res: count / total_actions if total_actions > 0 else 0.0
            for res, count in resource_totals.items()
        }

        # Risk scores by resource
        all_risk_scores: dict[str, list[int]] = defaultdict(list)
        for obs in self._observations:
            for res, scores in obs.risk_by_resource.items():
                all_risk_scores[res].extend(scores)

        typical_risk_scores: dict[str, tuple[float, float]] = {}
        for res, scores in all_risk_scores.items():
            mean = statistics.mean(scores) if scores else 0.0
            stddev = statistics.stdev(scores) if len(scores) > 1 else 0.0
            typical_risk_scores[res] = (mean, stddev)

        return BehaviorProfile(
            tool_frequency=tool_frequency,
            tool_frequency_stddev=tool_frequency_stddev,
            resource_distribution=resource_distribution,
            typical_risk_scores=typical_risk_scores,
            session_count=len(self._observations),
            total_actions=total_actions,
        )

    def save(self, path: Path) -> None:
        """Build and save the profile to a JSON file.

        Args:
            path: Destination file path.
        """
        profile = self.build()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(path: Path) -> BehaviorProfile:
        """Load a BehaviorProfile from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Loaded BehaviorProfile.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return BehaviorProfile.from_dict(data)
