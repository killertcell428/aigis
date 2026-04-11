"""Sleeper Attack Detection -- detect payloads planted in one session that
activate in a later session.

Detection methods:

1. Memory correlation: if a memory entry created in session A causes
   a high-risk action in session B, flag it.
2. Temporal pattern: instructions with time-based triggers
   ("after 3 days", "next Monday", "on April 15").
3. Conditional activation: memory entries that contain conditional
   logic ("when user asks about X, do Y", "if the topic is Z").

Academic basis:
  - arxiv 2604.02623: temporally decoupled memory poisoning
    ("The attack is planted in session T and activates in session T+k")
  - Demonstrates that memory poisoning is the most dangerous class of
    prompt injection because the planting and activation are separated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from aigis.cross_session.store import SessionRecord, SessionStore

# === Temporal trigger patterns ===
# Regex patterns that detect time-based triggers in memory entries.
_TEMPORAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(after|in)\s+\d+\s+(day|week|hour|month)s?\b", re.IGNORECASE),
    re.compile(
        r"\b(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bon\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(tomorrow|tonight|next\s+week|next\s+month|next\s+session)\b", re.IGNORECASE),
    re.compile(r"\b(starting\s+from|beginning|from\s+now|from\s+this\s+point)\b", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),  # ISO date in memory
    re.compile(r"\b(activate|trigger|execute|run|enable)\s+(on|at|after|when)\b", re.IGNORECASE),
]

# === Conditional activation patterns ===
# Regex patterns that detect conditional logic in memory entries.
_CONDITIONAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(when|whenever|if|once)\s+(the\s+)?(user|human|they)\s+(ask|mention|say|request|talk|bring\s+up)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bif\s+(the\s+)?(topic|subject|question|conversation)\s+(is|involves|contains|about)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(upon|on)\s+(receiving|getting|seeing)\b", re.IGNORECASE),
    re.compile(r"\b(always|every\s+time|each\s+time|from\s+now\s+on)\b", re.IGNORECASE),
    re.compile(
        r"\b(respond|reply|answer|output|return)\s+(with|by|using)\b.*\b(instead|always|secretly)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(override|bypass|ignore|disable|skip)\s+(the\s+)?(safety|security|guard|filter|check|restriction)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(remember|memorize|store|save)\s+(this|that|the\s+following)\s+(instruction|rule|command|directive)\b",
        re.IGNORECASE,
    ),
]

# === High-risk action indicators in alerts ===
# Alert categories that suggest a planted payload may have activated.
_ACTIVATION_INDICATORS: set[str] = {
    "escalation",
    "privilege_escalation_chain",
    "exfiltration_pattern",
    "frequency_spike",
    "resource_shift",
}


@dataclass
class SleeperAlert:
    """An alert indicating a potential sleeper attack.

    Attributes:
        alert_type: Classification of the sleeper pattern
            ("delayed_activation", "conditional_trigger",
             "persistent_instruction").
        severity: Impact level ("low", "medium", "high", "critical").
        description: Human-readable explanation.
        planted_session: Session ID where the payload was planted.
        activated_session: Session ID where it activated.
        evidence: Supporting data for the alert.
    """

    alert_type: str
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    planted_session: str
    activated_session: str
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "planted_session": self.planted_session,
            "activated_session": self.activated_session,
            "evidence": self.evidence,
        }


class SleeperDetector:
    """Detect sleeper attacks -- payloads planted in one session that
    activate in a later session.

    Uses three detection methods:
    1. Memory-to-action correlation
    2. Temporal trigger pattern matching
    3. Conditional activation pattern matching

    Args:
        store: The SessionStore providing session records.
    """

    def __init__(self, store: SessionStore) -> None:
        self._store = store

    def scan(
        self,
        current_session: SessionRecord,
        lookback_days: int = 30,
    ) -> list[SleeperAlert]:
        """Check if the current session shows signs of sleeper activation.

        Loads past sessions from the store and compares their memory_writes
        against the current session's behavior (alerts, tools used, risk).

        Args:
            current_session: The session to analyze for activation signs.
            lookback_days: How far back to search for planted payloads.

        Returns:
            List of SleeperAlert instances. Empty if no sleeper detected.
        """
        past = self._store.list_sessions(limit=500)
        # Exclude the current session from past sessions
        past = [s for s in past if s.session_id != current_session.session_id]

        if not past:
            return []

        alerts: list[SleeperAlert] = []
        alerts.extend(self._correlate_memory_to_actions(current_session, past))
        alerts.extend(self._detect_temporal_triggers(current_session, past))
        alerts.extend(self._detect_conditional_activation(current_session, past))

        return alerts

    def _correlate_memory_to_actions(
        self,
        current: SessionRecord,
        past: list[SessionRecord],
    ) -> list[SleeperAlert]:
        """Correlate memory writes from past sessions with current session alerts.

        If a past session wrote memory entries and the current session has
        high-risk alerts (escalation, exfiltration, etc.), flag the correlation.
        """
        alerts: list[SleeperAlert] = []

        # Only trigger if current session has activation indicators
        current_alert_types: set[str] = set()
        for alert in current.alerts:
            at = alert.get("drift_type") or alert.get("anomaly_type") or alert.get("alert_type", "")
            if at:
                current_alert_types.add(at)

        activation_matches = current_alert_types & _ACTIVATION_INDICATORS
        if not activation_matches and current.max_risk_score < 50:
            return alerts

        # Check past sessions with memory writes
        for past_session in past:
            if not past_session.memory_writes:
                continue

            # Check if any memory entry content looks suspicious
            suspicious_memories: list[dict] = []
            for mem in past_session.memory_writes:
                content = mem.get("content", "")
                # Check for instruction-like content in memory
                if self._is_suspicious_memory(content):
                    suspicious_memories.append(mem)

            if suspicious_memories:
                severity = (
                    "critical"
                    if activation_matches and current.max_risk_score >= 70
                    else "high"
                    if activation_matches
                    else "medium"
                )

                alerts.append(
                    SleeperAlert(
                        alert_type="delayed_activation",
                        severity=severity,
                        description=(
                            f"Session {past_session.session_id} planted "
                            f"{len(suspicious_memories)} suspicious memory entries; "
                            f"current session shows activation indicators: "
                            f"{', '.join(activation_matches) if activation_matches else 'high risk score'}"
                        ),
                        planted_session=past_session.session_id,
                        activated_session=current.session_id,
                        evidence={
                            "suspicious_memories": [
                                m.get("content", "")[:200] for m in suspicious_memories
                            ],
                            "activation_indicators": sorted(activation_matches),
                            "current_risk_score": current.max_risk_score,
                        },
                    )
                )

        return alerts

    def _detect_temporal_triggers(
        self,
        current: SessionRecord,
        past: list[SessionRecord],
    ) -> list[SleeperAlert]:
        """Detect memory entries with time-based activation triggers.

        Scans memory_writes from past sessions for temporal patterns
        like "after 3 days", "next Monday", date strings, etc.
        """
        alerts: list[SleeperAlert] = []

        for past_session in past:
            for mem in past_session.memory_writes:
                content = mem.get("content", "")
                matched_patterns: list[str] = []

                for pattern in _TEMPORAL_PATTERNS:
                    match = pattern.search(content)
                    if match:
                        matched_patterns.append(match.group())

                if matched_patterns:
                    severity = "high" if len(matched_patterns) >= 2 else "medium"

                    alerts.append(
                        SleeperAlert(
                            alert_type="delayed_activation",
                            severity=severity,
                            description=(
                                f"Memory entry from session {past_session.session_id} "
                                f"contains temporal triggers: {', '.join(matched_patterns)}"
                            ),
                            planted_session=past_session.session_id,
                            activated_session=current.session_id,
                            evidence={
                                "memory_content": content[:300],
                                "temporal_triggers": matched_patterns,
                            },
                        )
                    )

        return alerts

    def _detect_conditional_activation(
        self,
        current: SessionRecord,
        past: list[SessionRecord],
    ) -> list[SleeperAlert]:
        """Detect memory entries with conditional logic triggers.

        Scans memory_writes from past sessions for conditional patterns
        like "when user asks about X", "if the topic is Y", etc.
        """
        alerts: list[SleeperAlert] = []

        for past_session in past:
            for mem in past_session.memory_writes:
                content = mem.get("content", "")
                matched_patterns: list[str] = []

                for pattern in _CONDITIONAL_PATTERNS:
                    match = pattern.search(content)
                    if match:
                        matched_patterns.append(match.group())

                if matched_patterns:
                    # Higher severity if the condition looks like it's overriding safety
                    has_override = any(
                        p
                        for p in matched_patterns
                        if re.search(r"override|bypass|ignore|disable|skip", p, re.IGNORECASE)
                    )
                    severity = (
                        "critical"
                        if has_override
                        else "high"
                        if len(matched_patterns) >= 2
                        else "medium"
                    )

                    alerts.append(
                        SleeperAlert(
                            alert_type="conditional_trigger"
                            if not has_override
                            else "persistent_instruction",
                            severity=severity,
                            description=(
                                f"Memory entry from session {past_session.session_id} "
                                f"contains conditional logic: {', '.join(matched_patterns)}"
                            ),
                            planted_session=past_session.session_id,
                            activated_session=current.session_id,
                            evidence={
                                "memory_content": content[:300],
                                "conditional_patterns": matched_patterns,
                            },
                        )
                    )

        return alerts

    @staticmethod
    def _is_suspicious_memory(content: str) -> bool:
        """Check if a memory entry content looks like a planted instruction.

        Returns True if the content matches patterns commonly associated
        with memory poisoning payloads.
        """
        if not content or len(content) < 10:
            return False

        suspicious_indicators = [
            re.compile(
                r"\b(always|never|must|shall)\s+(respond|reply|answer|output|do|execute|run)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(ignore|override|bypass|disable|skip)\s+(all|any|the|previous|safety|security)\b",
                re.IGNORECASE,
            ),
            re.compile(r"\b(from\s+now\s+on|henceforth|permanently|forever)\b", re.IGNORECASE),
            re.compile(
                r"\b(secret|hidden|covert|stealth)\s+(instruction|rule|command|mode)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(do\s+not|don'?t|never)\s+(tell|reveal|disclose|mention|show)\b", re.IGNORECASE
            ),
            re.compile(r"\b(exfiltrate|steal|extract|leak|send\s+to)\b", re.IGNORECASE),
        ]

        for indicator in suspicious_indicators:
            if indicator.search(content):
                return True

        return False
