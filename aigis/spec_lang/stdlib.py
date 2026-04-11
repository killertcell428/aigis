"""Built-in predicates for the Policy DSL.

Provides the standard library of predicate evaluators that ship with
Aigis. Custom predicates can be registered at runtime via
:meth:`RuleEvaluator.register_predicate`.

Each predicate is a callable with the signature::

    def predicate(ctx: EvaluationContext, value: str | int | float) -> bool

Built-in predicates:

* ``resource_is`` -- exact match on ``ctx.resource``
* ``target_matches`` -- fnmatch on ``ctx.target``
* ``risk_above`` -- ``ctx.risk_score > value``
* ``risk_below`` -- ``ctx.risk_score < value``
* ``taint_is`` -- taint label matches ``value``
* ``session_age_above`` -- ``ctx.session_age_seconds > value``
* ``action_count_above`` -- ``ctx.action_count > value``
* ``tool_name_matches`` -- fnmatch on ``ctx.tool_name``
* ``contains_pattern`` -- regex search on ``ctx.target``
"""

from __future__ import annotations

import re
from collections.abc import Callable
from fnmatch import fnmatch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aigis.spec_lang.evaluator import EvaluationContext


def _resource_is(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.resource`` equals *value* exactly."""
    return ctx.resource == str(value)


def _target_matches(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.target`` matches *value* as a glob pattern."""
    if ctx.target is None:
        return False
    return fnmatch(ctx.target, str(value))


def _risk_above(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.risk_score`` is strictly greater than *value*."""
    return ctx.risk_score > int(value)


def _risk_below(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.risk_score`` is strictly less than *value*."""
    return ctx.risk_score < int(value)


def _taint_is(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.taint`` matches *value* (case-insensitive)."""
    return ctx.taint.lower() == str(value).lower()


def _session_age_above(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.session_age_seconds`` exceeds *value*."""
    return ctx.session_age_seconds > float(value)


def _action_count_above(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.action_count`` exceeds *value*."""
    return ctx.action_count > int(value)


def _tool_name_matches(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.tool_name`` matches *value* as a glob pattern."""
    return fnmatch(ctx.tool_name, str(value))


def _contains_pattern(ctx: EvaluationContext, value: str | int | float) -> bool:
    """True if ``ctx.target`` contains a match for the regex *value*.

    Input is capped at 50,000 characters to mitigate ReDoS on
    user-supplied regex patterns.
    """
    if ctx.target is None:
        return False
    try:
        safe_target = ctx.target[:50_000]
        return bool(re.search(str(value), safe_target))
    except re.error:
        return False


BUILTIN_PREDICATES: dict[str, Callable[[EvaluationContext, str | int | float], bool]] = {
    "resource_is": _resource_is,
    "target_matches": _target_matches,
    "risk_above": _risk_above,
    "risk_below": _risk_below,
    "taint_is": _taint_is,
    "session_age_above": _session_age_above,
    "action_count_above": _action_count_above,
    "tool_name_matches": _tool_name_matches,
    "contains_pattern": _contains_pattern,
}
