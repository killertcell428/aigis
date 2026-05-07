"""Shared types for the spec_lang package.

Lives in its own module so ``evaluator.py`` and ``stdlib.py`` can both
import :class:`EvaluationContext` without forming a module-level cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvaluationContext:
    """Context passed to the evaluator for each check.

    Carries all runtime data needed to evaluate predicates: the tool
    being invoked, the resource being accessed, risk scores, taint
    labels, session metrics, and arbitrary custom data.

    Attributes:
        tool_name: Name of the tool being called (e.g. ``"Bash"``).
        resource: Resource type being accessed (e.g. ``"shell:exec"``).
        target: The target of the action (e.g. file path, command).
        risk_score: Numeric risk score (0-100).
        taint: Taint label (``"trusted"`` / ``"untrusted"`` / ``"sanitized"``).
        session_age_seconds: Time since session start in seconds.
        action_count: Number of actions performed in this session.
        custom_data: Arbitrary key-value data for custom predicates.
    """

    tool_name: str = ""
    resource: str = ""
    target: str = ""
    risk_score: int = 0
    taint: str = "untrusted"
    session_age_seconds: float = 0.0
    action_count: int = 0
    custom_data: dict = field(default_factory=dict)
