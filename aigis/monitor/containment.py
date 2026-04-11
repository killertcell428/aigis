"""Graduated Containment -- adaptive response to detected behavioral anomalies.

Implements a graduated escalation model where the containment level
automatically increases as more alerts accumulate, and decreases
(or is manually reset) when the situation stabilizes.

Inspired by MI9's graduated containment tiers:
  NORMAL -> WARN -> THROTTLE -> RESTRICT -> ISOLATE -> STOP

Academic basis:
  - MI9 (arxiv 2508.03858): graduated containment
  - AgentSpec (arxiv 2503.18666): runtime constraint enforcement
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ContainmentLevel(StrEnum):
    """Graduated containment levels.

    Each level progressively restricts agent capabilities:

    - NORMAL: All operations allowed.
    - WARN: Log warnings, continue.
    - THROTTLE: Rate limit operations.
    - RESTRICT: Block high-risk operations, allow low-risk.
    - ISOLATE: Block all tool calls except read-only.
    - STOP: Block everything.
    """

    NORMAL = "normal"
    WARN = "warn"
    THROTTLE = "throttle"
    RESTRICT = "restrict"
    ISOLATE = "isolate"
    STOP = "stop"


# Ordered levels for comparison
_LEVEL_ORDER: list[ContainmentLevel] = [
    ContainmentLevel.NORMAL,
    ContainmentLevel.WARN,
    ContainmentLevel.THROTTLE,
    ContainmentLevel.RESTRICT,
    ContainmentLevel.ISOLATE,
    ContainmentLevel.STOP,
]


@dataclass
class ContainmentState:
    """Current containment state.

    Attributes:
        level: The current containment level.
        reason: Why we are at this level.
        escalated_at: Timestamp of last escalation.
        alert_count: Total alert count driving this state.
        alerts: The alerts that contributed to escalation.
    """

    level: ContainmentLevel
    reason: str
    escalated_at: float
    alert_count: int
    alerts: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "level": str(self.level),
            "reason": self.reason,
            "escalated_at": self.escalated_at,
            "alert_count": self.alert_count,
            "alert_types": [
                getattr(a, "drift_type", None) or getattr(a, "anomaly_type", "unknown")
                for a in self.alerts
            ],
        }


# Resources allowed at each containment level
_ALLOWED_RESOURCES: dict[ContainmentLevel, set[str] | None] = {
    ContainmentLevel.NORMAL: None,  # Everything allowed
    ContainmentLevel.WARN: None,  # Everything allowed (just log warnings)
    ContainmentLevel.THROTTLE: None,  # Everything allowed (rate limited externally)
    ContainmentLevel.RESTRICT: {
        "file:read",
        "file:search",
        "database:query",
    },
    ContainmentLevel.ISOLATE: {
        "file:read",
    },
    ContainmentLevel.STOP: set(),  # Nothing allowed
}


class ContainmentManager:
    """Graduated response to detected anomalies.

    Auto-escalates through containment levels based on alert accumulation.
    Supports manual reset for admin override.

    Args:
        thresholds: Custom alert count thresholds per level. Defaults to
            sensible values that progressively restrict the agent.
        auto_escalate: If True (default), automatically escalate when
            alert thresholds are crossed.
    """

    # Default escalation thresholds (number of alerts to trigger each level)
    DEFAULT_THRESHOLDS: dict[ContainmentLevel, int] = {
        ContainmentLevel.WARN: 1,  # 1 alert -> start warning
        ContainmentLevel.THROTTLE: 3,  # 3 alerts -> rate limit
        ContainmentLevel.RESTRICT: 5,  # 5 alerts -> restrict to low-risk
        ContainmentLevel.ISOLATE: 8,  # 8 alerts -> read-only
        ContainmentLevel.STOP: 12,  # 12 alerts -> full stop
    }

    def __init__(
        self,
        thresholds: dict[ContainmentLevel, int] | None = None,
        auto_escalate: bool = True,
        max_auto_level: ContainmentLevel = ContainmentLevel.RESTRICT,
    ) -> None:
        self._thresholds = dict(thresholds or self.DEFAULT_THRESHOLDS)
        self._auto_escalate = auto_escalate
        self._max_auto_level = max_auto_level
        self._alert_count = 0
        self._all_alerts: list[Any] = []
        self._state = ContainmentState(
            level=ContainmentLevel.NORMAL,
            reason="No alerts",
            escalated_at=time.time(),
            alert_count=0,
        )

    def process_alerts(self, alerts: list) -> ContainmentState:
        """Process new alerts and potentially escalate containment.

        Args:
            alerts: New DriftAlert or AnomalyAlert instances.

        Returns:
            Current ContainmentState after processing.
        """
        if not alerts:
            return self._state

        self._alert_count += len(alerts)
        self._all_alerts.extend(alerts)

        if self._auto_escalate:
            self._evaluate_escalation()

        return self._state

    def current_level(self) -> ContainmentLevel:
        """Return the current containment level."""
        return self._state.level

    def current_state(self) -> ContainmentState:
        """Return the full current containment state."""
        return self._state

    def should_allow(self, resource: str) -> bool:
        """Check if a resource access should be allowed under current containment.

        Based on the current containment level, decides if a resource type
        is permitted.

        - NORMAL, WARN, THROTTLE: All resources allowed.
        - RESTRICT: Only file:read, file:search, database:query allowed.
        - ISOLATE: Only file:read allowed.
        - STOP: Nothing allowed.

        Args:
            resource: Resource type string (e.g. "file:read", "shell:exec").

        Returns:
            True if the resource is allowed, False if blocked.
        """
        allowed = _ALLOWED_RESOURCES.get(self._state.level)
        if allowed is None:
            return True  # No restrictions at this level
        return resource in allowed

    def escalate_manual(self, level: ContainmentLevel, reason: str = "") -> ContainmentState:
        """Manually escalate to any level (including ISOLATE/STOP).

        Auto-escalation is capped at RESTRICT by default. Use this method
        when human confirmation has been obtained for higher levels.

        Args:
            level: Target containment level.
            reason: Human-provided reason for the escalation.

        Returns:
            Updated ContainmentState.
        """
        self._state = ContainmentState(
            level=level,
            reason=reason or f"Manual escalation to {level}",
            escalated_at=time.time(),
            alert_count=self._alert_count,
            alerts=self._all_alerts[:],
        )
        return self._state

    def reset(self) -> None:
        """Admin override to reset containment to NORMAL.

        Clears all accumulated alerts and resets the containment level.
        """
        self._alert_count = 0
        self._all_alerts = []
        self._state = ContainmentState(
            level=ContainmentLevel.NORMAL,
            reason="Admin reset",
            escalated_at=time.time(),
            alert_count=0,
        )

    def to_dict(self) -> dict:
        """Convert current state to JSON-serializable dict."""
        return self._state.to_dict()

    def _evaluate_escalation(self) -> None:
        """Evaluate whether to escalate based on accumulated alert count.

        Walks through thresholds from highest to lowest, selecting the
        highest level that the current alert count qualifies for.
        Auto-escalation is capped at ``max_auto_level`` (default: RESTRICT).
        Levels above the cap (ISOLATE, STOP) require manual escalation
        via ``escalate_manual()``.
        """
        target_level = ContainmentLevel.NORMAL

        # Walk through levels in order, pick the highest one we qualify for
        for level in _LEVEL_ORDER:
            threshold = self._thresholds.get(level)
            if threshold is not None and self._alert_count >= threshold:
                target_level = level

        # Cap auto-escalation at the configured maximum
        max_idx = _LEVEL_ORDER.index(self._max_auto_level)
        if _LEVEL_ORDER.index(target_level) > max_idx:
            target_level = self._max_auto_level

        # Only escalate (never auto-de-escalate)
        if _LEVEL_ORDER.index(target_level) > _LEVEL_ORDER.index(self._state.level):
            reasons: list[str] = []
            for alert in self._all_alerts[-5:]:  # Last 5 alerts
                if hasattr(alert, "drift_type"):
                    reasons.append(f"drift:{alert.drift_type}")
                elif hasattr(alert, "anomaly_type"):
                    reasons.append(f"anomaly:{alert.anomaly_type}")

            self._state = ContainmentState(
                level=target_level,
                reason=f"Auto-escalated: {self._alert_count} alerts [{', '.join(reasons)}]",
                escalated_at=time.time(),
                alert_count=self._alert_count,
                alerts=self._all_alerts[:],
            )
