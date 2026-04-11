"""Tests for Policy DSL (spec_lang) — parser, evaluator, stdlib, and defaults."""

import json
import tempfile
from pathlib import Path

from aigis.spec_lang import (
    Enforcement,
    EvaluationContext,
    PolicyDSL,
    Predicate,
    Rule,
    RuleEvaluator,
    Trigger,
)
from aigis.spec_lang.defaults import DEFAULT_RULES
from aigis.spec_lang.stdlib import BUILTIN_PREDICATES

# ---------------------------------------------------------------------------
# Dataclass construction
# ---------------------------------------------------------------------------


class TestTrigger:
    def test_defaults(self):
        t = Trigger(event="before_tool_call")
        assert t.event == "before_tool_call"
        assert t.tool_match == "*"

    def test_custom_tool_match(self):
        t = Trigger(event="on_output", tool_match="Bash|shell")
        assert t.tool_match == "Bash|shell"


class TestPredicate:
    def test_defaults(self):
        p = Predicate(type="resource_is", value="shell:exec")
        assert p.negate is False

    def test_negate(self):
        p = Predicate(type="taint_is", value="trusted", negate=True)
        assert p.negate is True

    def test_numeric_value(self):
        p = Predicate(type="risk_above", value=80)
        assert p.value == 80


class TestEnforcement:
    def test_defaults(self):
        e = Enforcement(action="block")
        assert e.message == ""
        assert e.metadata == {}

    def test_with_metadata(self):
        e = Enforcement(action="warn", message="Watch out", metadata={"level": "high"})
        assert e.metadata["level"] == "high"


class TestRule:
    def test_full_rule(self):
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            trigger=Trigger(event="before_tool_call"),
            predicates=[Predicate(type="resource_is", value="shell:exec")],
            enforcement=Enforcement(action="block", message="Blocked"),
            priority=10,
        )
        assert rule.id == "test_rule"
        assert rule.enabled is True
        assert rule.priority == 10

    def test_disabled_rule(self):
        rule = Rule(
            id="off",
            name="Disabled",
            trigger=Trigger(event="on_output"),
            predicates=[],
            enforcement=Enforcement(action="log"),
            enabled=False,
        )
        assert rule.enabled is False


# ---------------------------------------------------------------------------
# PolicyDSL — loading and management
# ---------------------------------------------------------------------------


SAMPLE_YAML = """\
rules:
  - id: block_shell_untrusted
    name: Block shell from untrusted
    trigger:
      event: before_tool_call
      tool_match: "Bash|shell"
    predicates:
      - type: resource_is
        value: "shell:exec"
      - type: taint_is
        value: untrusted
    enforcement:
      action: block
      message: "Shell blocked: untrusted"
    priority: 100

  - id: warn_high_risk
    name: Warn on high risk
    trigger:
      event: before_tool_call
      tool_match: "*"
    predicates:
      - type: risk_above
        value: 60
    enforcement:
      action: warn
      message: "Risk is elevated"
    priority: 50
"""


class TestPolicyDSL:
    def test_load_yaml_string(self):
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        rules = dsl.rules()
        assert len(rules) == 2
        # Should be sorted by priority descending
        assert rules[0].id == "block_shell_untrusted"
        assert rules[1].id == "warn_high_risk"

    def test_load_yaml_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "policy.yaml"
            path.write_text(SAMPLE_YAML, encoding="utf-8")
            dsl = PolicyDSL()
            dsl.load_file(path)
            assert len(dsl.rules()) == 2

    def test_load_json_file(self):
        data = {
            "rules": [
                {
                    "id": "json_rule",
                    "name": "JSON Rule",
                    "trigger": {"event": "on_output"},
                    "predicates": [{"type": "risk_above", "value": 90}],
                    "enforcement": {"action": "block", "message": "Too risky"},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "policy.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            dsl = PolicyDSL()
            dsl.load_file(path)
            rules = dsl.rules()
            assert len(rules) == 1
            assert rules[0].id == "json_rule"
            assert rules[0].trigger.event == "on_output"

    def test_add_rule(self):
        dsl = PolicyDSL()
        rule = Rule(
            id="manual",
            name="Manual Rule",
            trigger=Trigger(event="periodic"),
            predicates=[],
            enforcement=Enforcement(action="log"),
        )
        dsl.add_rule(rule)
        assert len(dsl.rules()) == 1
        assert dsl.rules()[0].id == "manual"

    def test_add_rule_replaces_existing(self):
        dsl = PolicyDSL()
        rule1 = Rule(
            id="dup",
            name="First",
            trigger=Trigger(event="on_output"),
            predicates=[],
            enforcement=Enforcement(action="log"),
        )
        rule2 = Rule(
            id="dup",
            name="Second",
            trigger=Trigger(event="on_message"),
            predicates=[],
            enforcement=Enforcement(action="warn"),
        )
        dsl.add_rule(rule1)
        dsl.add_rule(rule2)
        rules = dsl.rules()
        assert len(rules) == 1
        assert rules[0].name == "Second"

    def test_remove_rule(self):
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        assert dsl.remove_rule("warn_high_risk") is True
        assert len(dsl.rules()) == 1
        assert dsl.rules()[0].id == "block_shell_untrusted"

    def test_remove_nonexistent(self):
        dsl = PolicyDSL()
        assert dsl.remove_rule("nope") is False

    def test_priority_ordering(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="low",
            name="Low Priority",
            trigger=Trigger(event="on_output"),
            predicates=[],
            enforcement=Enforcement(action="log"),
            priority=1,
        ))
        dsl.add_rule(Rule(
            id="high",
            name="High Priority",
            trigger=Trigger(event="on_output"),
            predicates=[],
            enforcement=Enforcement(action="block"),
            priority=99,
        ))
        dsl.add_rule(Rule(
            id="mid",
            name="Mid Priority",
            trigger=Trigger(event="on_output"),
            predicates=[],
            enforcement=Enforcement(action="warn"),
            priority=50,
        ))
        rules = dsl.rules()
        assert [r.id for r in rules] == ["high", "mid", "low"]

    def test_load_nonexistent_file_raises(self):
        dsl = PolicyDSL()
        try:
            dsl.load_file("/nonexistent/path/policy.yaml")
            assert False, "Expected FileNotFoundError"
        except (FileNotFoundError, OSError):
            pass


# ---------------------------------------------------------------------------
# YAML parsing (minimal parser)
# ---------------------------------------------------------------------------


class TestMinimalYAMLParser:
    def test_parses_trigger(self):
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        rule = dsl.rules()[0]
        assert rule.trigger.event == "before_tool_call"
        assert rule.trigger.tool_match == "Bash|shell"

    def test_parses_predicates(self):
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        rule = dsl.rules()[0]
        assert len(rule.predicates) == 2
        assert rule.predicates[0].type == "resource_is"
        assert rule.predicates[0].value == "shell:exec"
        assert rule.predicates[1].type == "taint_is"
        assert rule.predicates[1].value == "untrusted"

    def test_parses_enforcement(self):
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        rule = dsl.rules()[0]
        assert rule.enforcement.action == "block"
        assert "untrusted" in rule.enforcement.message

    def test_parses_priority(self):
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        rules = dsl.rules()
        assert rules[0].priority == 100
        assert rules[1].priority == 50

    def test_coerces_numeric_values(self):
        yaml_text = """\
rules:
  - id: numeric_test
    name: Numeric
    trigger:
      event: before_tool_call
    predicates:
      - type: risk_above
        value: 75
    enforcement:
      action: warn
"""
        dsl = PolicyDSL()
        dsl.load_yaml(yaml_text)
        pred = dsl.rules()[0].predicates[0]
        assert pred.value == 75
        assert isinstance(pred.value, int)

    def test_empty_yaml(self):
        dsl = PolicyDSL()
        dsl.load_yaml("")
        assert len(dsl.rules()) == 0

    def test_negate_predicate(self):
        yaml_text = """\
rules:
  - id: negate_test
    name: Negate Test
    trigger:
      event: before_tool_call
    predicates:
      - type: taint_is
        value: trusted
        negate: true
    enforcement:
      action: block
"""
        dsl = PolicyDSL()
        dsl.load_yaml(yaml_text)
        pred = dsl.rules()[0].predicates[0]
        assert pred.negate is True

    def test_disabled_rule_yaml(self):
        yaml_text = """\
rules:
  - id: off_rule
    name: Disabled Rule
    enabled: false
    trigger:
      event: on_output
    predicates:
      - type: risk_above
        value: 50
    enforcement:
      action: block
"""
        dsl = PolicyDSL()
        dsl.load_yaml(yaml_text)
        assert dsl.rules()[0].enabled is False


# ---------------------------------------------------------------------------
# RuleEvaluator
# ---------------------------------------------------------------------------


class TestRuleEvaluator:
    def _make_dsl(self) -> PolicyDSL:
        dsl = PolicyDSL()
        dsl.load_yaml(SAMPLE_YAML)
        return dsl

    def test_matching_rule_fires(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="untrusted",
        )
        results = evaluator.evaluate("before_tool_call", ctx)
        matched = [r for r in results if r.matched]
        assert len(matched) >= 1
        assert matched[0].rule_id == "block_shell_untrusted"
        assert matched[0].enforcement_action == "block"

    def test_non_matching_tool(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(
            tool_name="Read",
            resource="shell:exec",
            taint="untrusted",
        )
        results = evaluator.evaluate("before_tool_call", ctx)
        # "block_shell_untrusted" should not fire (tool_match="Bash|shell")
        block_results = [r for r in results if r.rule_id == "block_shell_untrusted"]
        assert len(block_results) == 0

    def test_wrong_event(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(tool_name="Bash", resource="shell:exec", taint="untrusted")
        results = evaluator.evaluate("on_output", ctx)
        assert len(results) == 0

    def test_predicate_failure(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="trusted",  # Not untrusted -- predicate should fail
        )
        results = evaluator.evaluate("before_tool_call", ctx)
        block_results = [r for r in results if r.rule_id == "block_shell_untrusted"]
        assert len(block_results) == 1
        assert block_results[0].matched is False

    def test_evaluate_first_match(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="untrusted",
            risk_score=70,
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.rule_id == "block_shell_untrusted"

    def test_evaluate_first_match_none(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(tool_name="Read", resource="file:read", taint="trusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        # warn_high_risk has tool_match="*" so it applies, but risk_score=0 < 60
        # So no rule should match
        assert result is None

    def test_disabled_rule_skipped(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="disabled",
            name="Disabled",
            trigger=Trigger(event="before_tool_call"),
            predicates=[],
            enforcement=Enforcement(action="block"),
            enabled=False,
        ))
        evaluator = RuleEvaluator(dsl)
        ctx = EvaluationContext(tool_name="Bash")
        results = evaluator.evaluate("before_tool_call", ctx)
        assert len(results) == 0

    def test_predicate_results_detail(self):
        evaluator = RuleEvaluator(self._make_dsl())
        ctx = EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="untrusted",
        )
        results = evaluator.evaluate("before_tool_call", ctx)
        block_result = [r for r in results if r.rule_id == "block_shell_untrusted"][0]
        assert block_result.matched is True
        assert len(block_result.predicate_results) == 2
        assert block_result.predicate_results[0]["predicate_type"] == "resource_is"
        assert block_result.predicate_results[0]["passed"] is True
        assert block_result.predicate_results[1]["predicate_type"] == "taint_is"
        assert block_result.predicate_results[1]["passed"] is True

    def test_negate_predicate_evaluation(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="negate_test",
            name="Block non-trusted",
            trigger=Trigger(event="before_tool_call"),
            predicates=[
                Predicate(type="taint_is", value="trusted", negate=True),
            ],
            enforcement=Enforcement(action="block", message="Not trusted"),
        ))
        evaluator = RuleEvaluator(dsl)

        # Untrusted should fire (negate: taint_is("trusted") -> False -> negated -> True)
        ctx_untrusted = EvaluationContext(taint="untrusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx_untrusted)
        assert result is not None
        assert result.matched is True

        # Trusted should not fire (negate: taint_is("trusted") -> True -> negated -> False)
        ctx_trusted = EvaluationContext(taint="trusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx_trusted)
        assert result is None

    def test_multiple_rules_all_evaluated(self):
        """All matching rules are returned, not just the first."""
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="rule_a",
            name="Rule A",
            trigger=Trigger(event="before_tool_call"),
            predicates=[Predicate(type="risk_above", value=50)],
            enforcement=Enforcement(action="warn"),
            priority=10,
        ))
        dsl.add_rule(Rule(
            id="rule_b",
            name="Rule B",
            trigger=Trigger(event="before_tool_call"),
            predicates=[Predicate(type="risk_above", value=80)],
            enforcement=Enforcement(action="block"),
            priority=20,
        ))
        evaluator = RuleEvaluator(dsl)
        ctx = EvaluationContext(risk_score=90)
        results = evaluator.evaluate("before_tool_call", ctx)
        assert len(results) == 2
        # Both should match
        assert all(r.matched for r in results)
        # Sorted by priority: rule_b first
        assert results[0].rule_id == "rule_b"
        assert results[1].rule_id == "rule_a"


# ---------------------------------------------------------------------------
# Custom predicates
# ---------------------------------------------------------------------------


class TestCustomPredicates:
    def test_register_and_evaluate(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="custom_test",
            name="Custom Check",
            trigger=Trigger(event="before_tool_call"),
            predicates=[Predicate(type="is_admin", value="true")],
            enforcement=Enforcement(action="allow", message="Admin access granted"),
        ))

        evaluator = RuleEvaluator(dsl)
        evaluator.register_predicate(
            "is_admin",
            lambda ctx, val: ctx.custom_data.get("is_admin") == (str(val).lower() == "true"),
        )

        ctx_admin = EvaluationContext(custom_data={"is_admin": True})
        result = evaluator.evaluate_first_match("before_tool_call", ctx_admin)
        assert result is not None
        assert result.matched is True

        ctx_normal = EvaluationContext(custom_data={"is_admin": False})
        result = evaluator.evaluate_first_match("before_tool_call", ctx_normal)
        assert result is None

    def test_unknown_predicate_fails(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="unknown",
            name="Unknown Pred",
            trigger=Trigger(event="before_tool_call"),
            predicates=[Predicate(type="nonexistent_type", value="anything")],
            enforcement=Enforcement(action="block"),
        ))
        evaluator = RuleEvaluator(dsl)
        ctx = EvaluationContext()
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        # Unknown predicate should cause the rule not to match
        assert result is None


# ---------------------------------------------------------------------------
# Built-in predicates (stdlib)
# ---------------------------------------------------------------------------


class TestBuiltinPredicates:
    def test_all_builtins_registered(self):
        expected = {
            "resource_is", "target_matches", "risk_above", "risk_below",
            "taint_is", "session_age_above", "action_count_above",
            "tool_name_matches", "contains_pattern",
        }
        assert expected == set(BUILTIN_PREDICATES.keys())

    def test_resource_is(self):
        ctx = EvaluationContext(resource="shell:exec")
        assert BUILTIN_PREDICATES["resource_is"](ctx, "shell:exec") is True
        assert BUILTIN_PREDICATES["resource_is"](ctx, "file:read") is False

    def test_target_matches(self):
        ctx = EvaluationContext(target="/home/user/.env.local")
        assert BUILTIN_PREDICATES["target_matches"](ctx, "/home/user/.env*") is True
        assert BUILTIN_PREDICATES["target_matches"](ctx, "*.py") is False

    def test_risk_above(self):
        ctx = EvaluationContext(risk_score=75)
        assert BUILTIN_PREDICATES["risk_above"](ctx, 60) is True
        assert BUILTIN_PREDICATES["risk_above"](ctx, 80) is False
        assert BUILTIN_PREDICATES["risk_above"](ctx, 75) is False  # Not strictly above

    def test_risk_below(self):
        ctx = EvaluationContext(risk_score=30)
        assert BUILTIN_PREDICATES["risk_below"](ctx, 50) is True
        assert BUILTIN_PREDICATES["risk_below"](ctx, 30) is False
        assert BUILTIN_PREDICATES["risk_below"](ctx, 10) is False

    def test_taint_is(self):
        ctx = EvaluationContext(taint="untrusted")
        assert BUILTIN_PREDICATES["taint_is"](ctx, "untrusted") is True
        assert BUILTIN_PREDICATES["taint_is"](ctx, "UNTRUSTED") is True  # case-insensitive
        assert BUILTIN_PREDICATES["taint_is"](ctx, "trusted") is False

    def test_session_age_above(self):
        ctx = EvaluationContext(session_age_seconds=3600.0)
        assert BUILTIN_PREDICATES["session_age_above"](ctx, 1800) is True
        assert BUILTIN_PREDICATES["session_age_above"](ctx, 3600) is False

    def test_action_count_above(self):
        ctx = EvaluationContext(action_count=150)
        assert BUILTIN_PREDICATES["action_count_above"](ctx, 100) is True
        assert BUILTIN_PREDICATES["action_count_above"](ctx, 200) is False

    def test_tool_name_matches(self):
        ctx = EvaluationContext(tool_name="Bash")
        assert BUILTIN_PREDICATES["tool_name_matches"](ctx, "Bash") is True
        assert BUILTIN_PREDICATES["tool_name_matches"](ctx, "B*") is True
        assert BUILTIN_PREDICATES["tool_name_matches"](ctx, "Read") is False

    def test_contains_pattern(self):
        ctx = EvaluationContext(target="rm -rf /important/data")
        assert BUILTIN_PREDICATES["contains_pattern"](ctx, r"rm\s+-rf") is True
        assert BUILTIN_PREDICATES["contains_pattern"](ctx, r"^safe") is False

    def test_contains_pattern_invalid_regex(self):
        ctx = EvaluationContext(target="test")
        assert BUILTIN_PREDICATES["contains_pattern"](ctx, "[invalid") is False


# ---------------------------------------------------------------------------
# Default rules
# ---------------------------------------------------------------------------


class TestDefaultRules:
    def test_default_rules_exist(self):
        assert len(DEFAULT_RULES) >= 7

    def test_all_have_ids(self):
        for rule in DEFAULT_RULES:
            assert rule.id, f"Rule missing id: {rule.name}"

    def test_all_have_names(self):
        for rule in DEFAULT_RULES:
            assert rule.name, f"Rule missing name: {rule.id}"

    def test_all_have_enforcement_messages(self):
        for rule in DEFAULT_RULES:
            assert rule.enforcement.message, f"Rule {rule.id} missing enforcement message"

    def test_unique_ids(self):
        ids = [r.id for r in DEFAULT_RULES]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"

    def test_block_shell_untrusted_present(self):
        rule_ids = {r.id for r in DEFAULT_RULES}
        assert "block_shell_untrusted" in rule_ids

    def test_block_agent_spawn_untrusted_present(self):
        rule_ids = {r.id for r in DEFAULT_RULES}
        assert "block_agent_spawn_untrusted" in rule_ids

    def test_block_mcp_tool_untrusted_present(self):
        rule_ids = {r.id for r in DEFAULT_RULES}
        assert "block_mcp_tool_untrusted" in rule_ids

    def test_risk_thresholds_present(self):
        rule_ids = {r.id for r in DEFAULT_RULES}
        assert "warn_medium_risk" in rule_ids
        assert "block_high_risk" in rule_ids

    def test_throttle_present(self):
        rule_ids = {r.id for r in DEFAULT_RULES}
        assert "throttle_excessive_actions" in rule_ids

    def test_env_file_protection_present(self):
        rule_ids = {r.id for r in DEFAULT_RULES}
        assert "block_env_file_write" in rule_ids

    def test_defaults_load_into_dsl(self):
        dsl = PolicyDSL()
        for rule in DEFAULT_RULES:
            dsl.add_rule(rule)
        assert len(dsl.rules()) == len(DEFAULT_RULES)


# ---------------------------------------------------------------------------
# Integration: default rules evaluated end-to-end
# ---------------------------------------------------------------------------


class TestDefaultRulesIntegration:
    def _make_evaluator(self) -> RuleEvaluator:
        dsl = PolicyDSL()
        for rule in DEFAULT_RULES:
            dsl.add_rule(rule)
        return RuleEvaluator(dsl)

    def test_block_untrusted_shell(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="untrusted",
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "block"
        assert "untrusted" in result.message.lower()

    def test_allow_trusted_shell(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(
            tool_name="Bash",
            resource="shell:exec",
            taint="trusted",
            risk_score=0,
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        # No blocking rule should fire for trusted shell with low risk
        assert result is None

    def test_block_untrusted_agent_spawn(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(
            resource="agent:spawn",
            taint="untrusted",
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "block"

    def test_block_untrusted_mcp_tool(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(
            resource="mcp:tool_call",
            taint="untrusted",
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "block"

    def test_block_high_risk(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(risk_score=85, taint="trusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "block"

    def test_warn_medium_risk(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(risk_score=65, taint="trusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "warn"

    def test_no_warn_low_risk(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(risk_score=30, taint="trusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is None

    def test_throttle_excessive_actions(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(action_count=150, taint="trusted")
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "throttle"

    def test_block_env_file_write(self):
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(
            resource="file:write",
            target=".env.local",
            taint="trusted",
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is not None
        assert result.enforcement_action == "block"
        assert ".env" in result.message

    def test_allow_env_file_read(self):
        """file:read to .env should not be blocked by the write rule."""
        evaluator = self._make_evaluator()
        ctx = EvaluationContext(
            resource="file:read",
            target=".env.local",
            taint="trusted",
        )
        result = evaluator.evaluate_first_match("before_tool_call", ctx)
        assert result is None


# ---------------------------------------------------------------------------
# Tool matching edge cases
# ---------------------------------------------------------------------------


class TestToolMatching:
    def test_pipe_delimited_match(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="pipe_test",
            name="Pipe Match",
            trigger=Trigger(event="before_tool_call", tool_match="Bash|shell|execute"),
            predicates=[],
            enforcement=Enforcement(action="log"),
        ))
        evaluator = RuleEvaluator(dsl)

        for tool in ("Bash", "shell", "execute"):
            ctx = EvaluationContext(tool_name=tool)
            results = evaluator.evaluate("before_tool_call", ctx)
            assert len(results) == 1
            assert results[0].matched is True, f"Failed for tool: {tool}"

    def test_wildcard_matches_all(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="wild",
            name="Wildcard",
            trigger=Trigger(event="before_tool_call", tool_match="*"),
            predicates=[],
            enforcement=Enforcement(action="log"),
        ))
        evaluator = RuleEvaluator(dsl)

        for tool in ("Bash", "Read", "Edit", "anything"):
            ctx = EvaluationContext(tool_name=tool)
            results = evaluator.evaluate("before_tool_call", ctx)
            assert len(results) == 1

    def test_glob_pattern_in_tool_match(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="glob_test",
            name="Glob Tool",
            trigger=Trigger(event="before_tool_call", tool_match="mcp_*"),
            predicates=[],
            enforcement=Enforcement(action="warn"),
        ))
        evaluator = RuleEvaluator(dsl)

        ctx_match = EvaluationContext(tool_name="mcp_server_tool")
        results = evaluator.evaluate("before_tool_call", ctx_match)
        assert len(results) == 1
        assert results[0].matched is True

        ctx_no_match = EvaluationContext(tool_name="Bash")
        results = evaluator.evaluate("before_tool_call", ctx_no_match)
        assert len(results) == 0

    def test_empty_tool_name_only_matches_wildcard(self):
        dsl = PolicyDSL()
        dsl.add_rule(Rule(
            id="specific",
            name="Specific Tool",
            trigger=Trigger(event="before_tool_call", tool_match="Bash"),
            predicates=[],
            enforcement=Enforcement(action="block"),
        ))
        dsl.add_rule(Rule(
            id="wildcard",
            name="Wildcard",
            trigger=Trigger(event="before_tool_call", tool_match="*"),
            predicates=[],
            enforcement=Enforcement(action="log"),
        ))
        evaluator = RuleEvaluator(dsl)
        ctx = EvaluationContext(tool_name="")
        results = evaluator.evaluate("before_tool_call", ctx)
        # Only wildcard should match
        assert len(results) == 1
        assert results[0].rule_id == "wildcard"
