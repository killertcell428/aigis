"""Runtime Rule Evaluator for the Policy DSL.

Evaluates policy rules against an execution context, checking triggers
and predicates to determine which enforcement actions apply.

Usage::

    from aigis.spec_lang.parser import PolicyDSL
    from aigis.spec_lang.evaluator import RuleEvaluator, EvaluationContext

    dsl = PolicyDSL()
    dsl.load_file("policy.yaml")
    evaluator = RuleEvaluator(dsl)

    results = evaluator.evaluate(
        event="before_tool_call",
        context=EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="untrusted",
        ),
    )
    for r in results:
        if r.matched and r.enforcement_action == "block":
            print(f"Blocked by rule: {r.rule_name}")
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from fnmatch import fnmatch

from aigis.spec_lang.parser import PolicyDSL, Predicate
from aigis.spec_lang.stdlib import BUILTIN_PREDICATES


@dataclass
class RuleEvaluationResult:
    """The outcome of evaluating a single rule against a context.

    Attributes:
        rule_id: The rule's unique identifier.
        rule_name: Human-readable rule name.
        matched: True if all predicates passed and the rule fired.
        enforcement_action: The enforcement action (``"block"``, ``"allow"``, etc.).
        message: The enforcement message.
        predicate_results: Per-predicate evaluation details.
    """

    rule_id: str
    rule_name: str
    matched: bool
    enforcement_action: str
    message: str
    predicate_results: list[dict] = field(default_factory=list)


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


class RuleEvaluator:
    """Evaluates rules against an execution context.

    The evaluator filters rules by trigger event and tool match, then
    evaluates each rule's predicates against the given context. Rules
    are processed in priority order (highest first).

    Args:
        dsl: The PolicyDSL instance containing rules to evaluate.
    """

    def __init__(self, dsl: PolicyDSL) -> None:
        self._dsl = dsl
        self._custom_predicates: dict[
            str, Callable[[EvaluationContext, str | int | float], bool]
        ] = {}

    def register_predicate(
        self,
        name: str,
        func: Callable[[EvaluationContext, str | int | float], bool],
    ) -> None:
        """Register a custom predicate evaluator.

        Custom predicates can be referenced in rules via
        ``type: "custom"`` or by their registered *name*.

        Args:
            name: The predicate type name used in YAML rules.
            func: A callable ``(context, value) -> bool``.
        """
        self._custom_predicates[name] = func

    def evaluate(
        self,
        event: str,
        context: EvaluationContext,
    ) -> list[RuleEvaluationResult]:
        """Evaluate all matching rules and return their results.

        1. Filter rules by trigger event and tool_match.
        2. For each matching rule (sorted by priority, highest first):
           a. Evaluate all predicates against the context.
           b. If all predicates pass, the rule fires (``matched=True``).
           c. Record the result regardless of match.
        3. Return all results.

        Args:
            event: The lifecycle event (e.g. ``"before_tool_call"``).
            context: Runtime evaluation context.

        Returns:
            A list of :class:`RuleEvaluationResult`, one per rule that
            matched the trigger/tool filter.
        """
        results: list[RuleEvaluationResult] = []

        for rule in self._dsl.rules():
            if not rule.enabled:
                continue

            # Check trigger event
            if rule.trigger.event != event:
                continue

            # Check tool match (pipe-delimited alternatives)
            if not _tool_matches(rule.trigger.tool_match, context.tool_name):
                continue

            # Evaluate all predicates
            predicate_results: list[dict] = []
            all_passed = True

            for predicate in rule.predicates:
                passed, actual = self._evaluate_predicate(predicate, context)
                predicate_results.append(
                    {
                        "predicate_type": predicate.type,
                        "expected": predicate.value,
                        "actual": actual,
                        "passed": passed,
                        "negated": predicate.negate,
                    }
                )
                if not passed:
                    all_passed = False

            results.append(
                RuleEvaluationResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    matched=all_passed,
                    enforcement_action=rule.enforcement.action if all_passed else "",
                    message=rule.enforcement.message if all_passed else "",
                    predicate_results=predicate_results,
                )
            )

        return results

    def evaluate_first_match(
        self,
        event: str,
        context: EvaluationContext,
    ) -> RuleEvaluationResult | None:
        """Return the first matching rule (highest priority).

        This is a convenience method for the common "first match wins"
        pattern. Evaluates rules in priority order and returns the first
        one where all predicates pass.

        Args:
            event: The lifecycle event.
            context: Runtime evaluation context.

        Returns:
            The first :class:`RuleEvaluationResult` with ``matched=True``,
            or ``None`` if no rule matches.
        """
        results = self.evaluate(event, context)
        for result in results:
            if result.matched:
                return result
        return None

    def _evaluate_predicate(
        self,
        predicate: Predicate,
        context: EvaluationContext,
    ) -> tuple[bool, str]:
        """Evaluate a single predicate against the context.

        Returns:
            A tuple of (passed, actual_value_description).
        """
        pred_type = predicate.type
        value = predicate.value

        # Look up the predicate function
        func = self._custom_predicates.get(pred_type) or BUILTIN_PREDICATES.get(pred_type)

        if func is None:
            # Unknown predicate type -- fail open with a warning
            actual = f"unknown_predicate:{pred_type}"
            result = False
        else:
            result = func(context, value)
            actual = _get_actual_value(pred_type, context)

        # Apply negation
        if predicate.negate:
            result = not result

        return result, actual


def _tool_matches(pattern: str, tool_name: str) -> bool:
    """Check if a tool name matches a pipe-delimited glob pattern.

    ``"*"`` matches everything. ``"Bash|shell|execute"`` matches if the
    tool name matches any of the alternatives using fnmatch.
    """
    if pattern == "*":
        return True
    if not tool_name:
        # No tool name provided -- only wildcard matches
        return False
    for alt in pattern.split("|"):
        alt = alt.strip()
        if fnmatch(tool_name, alt):
            return True
    return False


def _get_actual_value(pred_type: str, context: EvaluationContext) -> str:
    """Extract the actual context value for a given predicate type (for reporting)."""
    mapping: dict[str, str] = {
        "resource_is": context.resource,
        "target_matches": context.target,
        "risk_above": str(context.risk_score),
        "risk_below": str(context.risk_score),
        "taint_is": context.taint,
        "session_age_above": str(context.session_age_seconds),
        "action_count_above": str(context.action_count),
        "tool_name_matches": context.tool_name,
        "contains_pattern": context.target,
    }
    return mapping.get(pred_type, "")
