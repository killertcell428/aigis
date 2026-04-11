"""Action Tracker -- records and maintains a sliding window of agent actions.

Thread-safe action recording with bounded memory usage. Each action captures
the tool name, resource type, target, risk score, and outcome. Integrates
with the existing ActivityStream (activity.py) by sharing the same resource
taxonomy (file:read, shell:exec, network:fetch, etc.).

Academic basis:
  - MI9 (arxiv 2508.03858): FSM-based conformance tracking
  - AgentSpec (arxiv 2503.18666): runtime action chain analysis
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass


@dataclass
class TrackedAction:
    """A single recorded agent action."""

    timestamp: float
    tool_name: str
    resource: str  # mapped resource type (file:read, shell:exec, etc.)
    target: str
    risk_score: int
    session_id: str
    outcome: str  # "allowed" | "blocked" | "error"

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "resource": self.resource,
            "target": self.target,
            "risk_score": self.risk_score,
            "session_id": self.session_id,
            "outcome": self.outcome,
        }


class ActionTracker:
    """Records and maintains a sliding window of agent actions.

    Thread-safe. Uses a bounded deque to prevent unbounded memory growth.
    The tracker auto-generates a session ID and records timestamped actions
    that can be queried by recency or time window.

    Args:
        window_size: Maximum number of actions to retain in memory.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._actions: deque[TrackedAction] = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._session_id: str = uuid.uuid4().hex[:16]
        self._start_time: float = time.time()

    @property
    def session_id(self) -> str:
        """Return the auto-generated session ID."""
        return self._session_id

    def record(
        self,
        tool_name: str,
        resource: str,
        target: str,
        risk_score: int = 0,
        outcome: str = "allowed",
    ) -> TrackedAction:
        """Record a new action.

        Args:
            tool_name: Name of the tool invoked (e.g. "Bash", "Read").
            resource: Mapped resource type (e.g. "file:read", "shell:exec").
            target: The specific target (file path, command, URL).
            risk_score: Risk score from 0-100.
            outcome: Result of the action ("allowed", "blocked", "error").

        Returns:
            The recorded TrackedAction.
        """
        action = TrackedAction(
            timestamp=time.time(),
            tool_name=tool_name,
            resource=resource,
            target=target,
            risk_score=risk_score,
            session_id=self._session_id,
            outcome=outcome,
        )
        with self._lock:
            self._actions.append(action)
        return action

    def recent(self, n: int = 50) -> list[TrackedAction]:
        """Return the most recent N actions.

        Args:
            n: Maximum number of actions to return.

        Returns:
            List of TrackedAction, most recent last.
        """
        with self._lock:
            actions = list(self._actions)
        return actions[-n:]

    def actions_since(self, seconds: float) -> list[TrackedAction]:
        """Return all actions within the last N seconds.

        Args:
            seconds: Look-back window in seconds.

        Returns:
            List of TrackedAction within the time window.
        """
        cutoff = time.time() - seconds
        with self._lock:
            return [a for a in self._actions if a.timestamp >= cutoff]

    def resource_histogram(self, window_seconds: float = 300) -> dict[str, int]:
        """Count actions by resource type within a time window.

        Args:
            window_seconds: Look-back window in seconds (default 5 minutes).

        Returns:
            Dict mapping resource type to count.
        """
        actions = self.actions_since(window_seconds)
        histogram: dict[str, int] = {}
        for action in actions:
            histogram[action.resource] = histogram.get(action.resource, 0) + 1
        return histogram

    def session_summary(self) -> dict:
        """Return a summary of the current session.

        Returns:
            Dict with session statistics including duration, action count,
            resource breakdown, risk stats, and outcome counts.
        """
        with self._lock:
            actions = list(self._actions)

        now = time.time()
        duration = now - self._start_time

        if not actions:
            return {
                "session_id": self._session_id,
                "duration_seconds": duration,
                "total_actions": 0,
                "resources": {},
                "tools": {},
                "avg_risk_score": 0.0,
                "max_risk_score": 0,
                "outcomes": {},
            }

        resources: dict[str, int] = {}
        tools: dict[str, int] = {}
        outcomes: dict[str, int] = {}
        risk_scores: list[int] = []

        for a in actions:
            resources[a.resource] = resources.get(a.resource, 0) + 1
            tools[a.tool_name] = tools.get(a.tool_name, 0) + 1
            outcomes[a.outcome] = outcomes.get(a.outcome, 0) + 1
            risk_scores.append(a.risk_score)

        return {
            "session_id": self._session_id,
            "duration_seconds": duration,
            "total_actions": len(actions),
            "resources": resources,
            "tools": tools,
            "avg_risk_score": sum(risk_scores) / len(risk_scores),
            "max_risk_score": max(risk_scores),
            "outcomes": outcomes,
        }
