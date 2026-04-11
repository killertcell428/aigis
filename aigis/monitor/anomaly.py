"""Sequence Anomaly Detection -- detect anomalous action sequences in real-time.

Uses simple state machine tracking (MI9-inspired) to identify dangerous
action chains, rapid-fire behavior, and access to previously unseen
resources.

Academic basis:
  - MI9 (arxiv 2508.03858): FSM-based conformance engines
  - AgentSpec (arxiv 2503.18666): runtime constraint enforcement
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from aigis.monitor.baseline import BehaviorProfile
from aigis.monitor.tracker import TrackedAction


@dataclass
class AnomalyAlert:
    """An alert indicating anomalous action sequence.

    Attributes:
        anomaly_type: Classification of the anomaly
            ("unusual_sequence", "privilege_escalation_chain",
             "rapid_fire", "new_resource").
        severity: Impact level ("low", "medium", "high", "critical").
        description: Human-readable explanation.
        actions: The specific actions forming the anomaly.
        timestamp: When the anomaly was detected (epoch seconds).
    """

    anomaly_type: str
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    actions: list[TrackedAction] = field(default_factory=list)
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions],
            "timestamp": self.timestamp,
        }


class AnomalyDetector:
    """Detect anomalous action sequences in real-time.

    Uses simple state machine tracking inspired by MI9's FSM-based
    conformance engines. Checks for dangerous action chains, rapid-fire
    operations, and access to new/unseen resources.

    Args:
        baseline: Optional baseline for "new resource" detection.
            If None, new_resource detection is disabled.
    """

    # Dangerous action sequences (order matters).
    # Each chain is a sequence of resource types that, when observed
    # in order, indicates a potential security concern.
    ESCALATION_CHAINS: list[list[str]] = [
        ["file:read", "file:write", "shell:exec"],  # read -> write -> exec
        ["file:read", "network:fetch"],  # read then exfil via fetch
        ["file:read", "network:send"],  # read then send
        ["shell:exec", "network:send"],  # exec then send
        ["database:query", "network:send"],  # query then send
        ["file:read", "shell:exec", "network:send"],  # read -> exec -> send
    ]

    # Severity mapping by chain pattern
    _CHAIN_SEVERITY: dict[str, str] = {
        "file:read->file:write->shell:exec": "high",
        "file:read->network:fetch": "medium",
        "file:read->network:send": "high",
        "shell:exec->network:send": "critical",
        "database:query->network:send": "critical",
        "file:read->shell:exec->network:send": "critical",
    }

    def __init__(self, baseline: BehaviorProfile | None = None) -> None:
        self._baseline = baseline

    def analyze(self, actions: list[TrackedAction]) -> list[AnomalyAlert]:
        """Analyze action sequence for anomalies.

        Runs all anomaly checks:
        1. Privilege escalation chains: matches ESCALATION_CHAINS
        2. Rapid fire: too many actions in too short a time
        3. New resources: resource types never seen in baseline

        Args:
            actions: Sequence of recent actions to analyze.

        Returns:
            List of AnomalyAlert instances. Empty if no anomalies found.
        """
        if not actions:
            return []

        alerts: list[AnomalyAlert] = []

        alerts.extend(self._detect_escalation_chains(actions))

        rapid = self._detect_rapid_fire(actions)
        if rapid is not None:
            alerts.append(rapid)

        alerts.extend(self._detect_new_resources(actions))

        return alerts

    def _detect_escalation_chains(self, actions: list[TrackedAction]) -> list[AnomalyAlert]:
        """Detect sequences matching known dangerous action chains.

        Uses a sliding-window subsequence match: for each chain template,
        scans through actions looking for the sequence in order (not
        necessarily consecutive, but within 120 seconds).
        """
        alerts: list[AnomalyAlert] = []
        detected_chains: set[str] = set()  # Avoid duplicate alerts for same chain

        for chain in self.ESCALATION_CHAINS:
            chain_key = "->".join(chain)
            if chain_key in detected_chains:
                continue

            matches = self._find_chain(actions, chain)
            if matches:
                detected_chains.add(chain_key)
                severity = self._CHAIN_SEVERITY.get(chain_key, "medium")
                alerts.append(
                    AnomalyAlert(
                        anomaly_type="privilege_escalation_chain",
                        severity=severity,
                        description=(f"Dangerous action chain detected: {' -> '.join(chain)}"),
                        actions=matches,
                    )
                )

        return alerts

    def _find_chain(
        self,
        actions: list[TrackedAction],
        chain: list[str],
        max_gap_seconds: float = 120.0,
    ) -> list[TrackedAction]:
        """Find the first occurrence of a chain pattern in actions.

        Args:
            actions: Action sequence to search.
            chain: Resource type sequence to match.
            max_gap_seconds: Maximum time between first and last chain action.

        Returns:
            List of matching actions, or empty list if no match.
        """
        if not chain or not actions:
            return []

        chain_idx = 0
        matched: list[TrackedAction] = []

        for action in actions:
            if action.resource == chain[chain_idx]:
                if chain_idx == 0:
                    matched = [action]
                else:
                    # Check time gap from first match
                    if action.timestamp - matched[0].timestamp > max_gap_seconds:
                        # Reset and try this action as new start
                        if action.resource == chain[0]:
                            chain_idx = 0
                            matched = [action]
                        else:
                            chain_idx = 0
                            matched = []
                            continue
                    else:
                        matched.append(action)

                chain_idx += 1
                if chain_idx >= len(chain):
                    return matched  # Full chain found

        return []  # Chain not completed

    def _detect_rapid_fire(
        self,
        actions: list[TrackedAction],
        max_per_minute: int = 30,
    ) -> AnomalyAlert | None:
        """Detect rapid-fire action patterns.

        Flags when the agent performs more than ``max_per_minute`` actions
        in any rolling 60-second window.

        Args:
            actions: Action sequence to analyze.
            max_per_minute: Threshold for actions per minute.

        Returns:
            AnomalyAlert if rapid fire detected, None otherwise.
        """
        if len(actions) < max_per_minute:
            return None

        # Sliding window: check each 60-second window
        for i in range(len(actions)):
            window_start = actions[i].timestamp
            window_end = window_start + 60.0
            window_actions = [a for a in actions[i:] if a.timestamp <= window_end]

            if len(window_actions) > max_per_minute:
                # Determine severity based on how much it exceeds threshold
                ratio = len(window_actions) / max_per_minute
                if ratio > 3.0:
                    severity = "critical"
                elif ratio > 2.0:
                    severity = "high"
                elif ratio > 1.5:
                    severity = "medium"
                else:
                    severity = "low"

                return AnomalyAlert(
                    anomaly_type="rapid_fire",
                    severity=severity,
                    description=(
                        f"Rapid-fire activity: {len(window_actions)} actions in 60 seconds "
                        f"(threshold: {max_per_minute})"
                    ),
                    actions=window_actions[:10],  # Include first 10 as evidence
                )

        return None

    def _detect_new_resources(self, actions: list[TrackedAction]) -> list[AnomalyAlert]:
        """Detect access to resource types not seen in baseline.

        If no baseline is provided, this check is skipped.

        Args:
            actions: Action sequence to analyze.

        Returns:
            List of AnomalyAlert for each new resource type.
        """
        if self._baseline is None:
            return []

        baseline_resources = set(self._baseline.resource_distribution.keys())
        if not baseline_resources:
            return []

        # Find resources in current actions that are not in baseline
        current_resources: dict[str, list[TrackedAction]] = {}
        for a in actions:
            if a.resource not in baseline_resources:
                if a.resource not in current_resources:
                    current_resources[a.resource] = []
                current_resources[a.resource].append(a)

        alerts: list[AnomalyAlert] = []
        for resource, resource_actions in current_resources.items():
            # Severity depends on the resource type
            if resource in ("shell:exec", "network:send", "agent:spawn"):
                severity = "high"
            elif resource in ("file:write", "network:fetch"):
                severity = "medium"
            else:
                severity = "low"

            alerts.append(
                AnomalyAlert(
                    anomaly_type="new_resource",
                    severity=severity,
                    description=(
                        f"New resource type '{resource}' not seen in baseline "
                        f"({len(resource_actions)} occurrences)"
                    ),
                    actions=resource_actions[:5],  # Limit evidence
                )
            )

        return alerts
