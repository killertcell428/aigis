"""Public type definitions for ai-guardian."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class MatchedRule:
    """A detection rule that matched during filtering."""

    rule_id: str
    rule_name: str
    category: str
    score_delta: int
    matched_text: str
    owasp_ref: str = ""
    remediation_hint: str = ""


@dataclass
class CheckResult:
    """Result of a Guard.check_input() / check_output() call."""

    risk_score: int
    risk_level: RiskLevel
    blocked: bool
    reasons: list[str] = field(default_factory=list)
    matched_rules: list[MatchedRule] = field(default_factory=list)
    remediation: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        """True if the request was NOT blocked (safe to proceed)."""
        return not self.blocked


@dataclass
class AuthorizationResult:
    """Result of a capability-based tool authorization check.

    Returned by ``Guard.authorize_tool()`` and ``CapabilityEnforcer.authorize_tool_call()``.
    """

    allowed: bool
    capability_used: str | None  # nonce of the capability that authorized the call
    reason: str
    taint_level: str
    scan_result: CheckResult | None = None

    def __bool__(self) -> bool:
        """True if the tool call is allowed."""
        return self.allowed
