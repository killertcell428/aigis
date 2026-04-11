"""Policy DSL — AgentSpec-inspired runtime constraint language for LLM agents.

A YAML-based domain-specific language for specifying when, under what
conditions, and how to enforce security policies on AI agent actions.
Inspired by AgentSpec (ICSE 2026, arxiv 2503.18666).

Exports:
    PolicyDSL: Load and manage policy rules from YAML/JSON.
    Rule: A complete policy rule (trigger + predicates + enforcement).
    Trigger: When to evaluate a rule (lifecycle event + tool filter).
    Predicate: A condition that must hold for the rule to fire.
    Enforcement: The action to take when a rule fires.
    RuleEvaluationResult: The outcome of evaluating a rule.

Quick start::

    from aigis.spec_lang import PolicyDSL, RuleEvaluator, EvaluationContext

    dsl = PolicyDSL()
    dsl.load_file("policy_rules.yaml")

    evaluator = RuleEvaluator(dsl)
    result = evaluator.evaluate_first_match(
        event="before_tool_call",
        context=EvaluationContext(tool_name="Bash", resource="shell:exec", taint="untrusted"),
    )
    if result and result.enforcement_action == "block":
        print(f"Blocked: {result.message}")
"""

from aigis.spec_lang.evaluator import (
    EvaluationContext,
    RuleEvaluationResult,
    RuleEvaluator,
)
from aigis.spec_lang.parser import (
    Enforcement,
    PolicyDSL,
    Predicate,
    Rule,
    Trigger,
)

__all__ = [
    "EvaluationContext",
    "Enforcement",
    "PolicyDSL",
    "Predicate",
    "Rule",
    "RuleEvaluationResult",
    "RuleEvaluator",
    "Trigger",
]
