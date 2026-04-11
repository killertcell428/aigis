"""YAML Rule Parser for the Policy DSL.

Parses YAML-based policy rules into structured Rule objects. Supports
triggers (when to evaluate), predicates (conditions that must hold),
and enforcement actions (what to do when rules fire).

Inspired by AgentSpec (ICSE 2026, arxiv 2503.18666) -- a domain-specific
language for specifying runtime constraints on LLM agents.

YAML format::

    rules:
      - id: block_shell_from_untrusted
        name: Block shell execution from untrusted data
        trigger:
          event: before_tool_call
          tool_match: "Bash|shell|execute"
        predicates:
          - type: resource_is
            value: "shell:exec"
          - type: taint_is
            value: untrusted
        enforcement:
          action: block
          message: "Shell execution blocked: data provenance is untrusted"

Usage::

    from aigis.spec_lang.parser import PolicyDSL, Rule

    dsl = PolicyDSL()
    dsl.load_file("policy_rules.yaml")
    for rule in dsl.rules():
        print(rule.id, rule.trigger.event, rule.enforcement.action)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Trigger:
    """When to evaluate this rule.

    Attributes:
        event: The lifecycle event that activates evaluation.
            One of ``"before_tool_call"``, ``"after_tool_call"``,
            ``"on_output"``, ``"on_message"``, ``"periodic"``.
        tool_match: Pipe-delimited glob patterns for tool names.
            ``"*"`` matches any tool.
    """

    event: str  # "before_tool_call" | "after_tool_call" | "on_output" | "on_message" | "periodic"
    tool_match: str = "*"  # glob pattern for tool name (pipe-delimited alternatives)


@dataclass
class Predicate:
    """Condition that must be true for the rule to fire.

    Attributes:
        type: The predicate kind. Built-in types include
            ``"resource_is"``, ``"target_matches"``, ``"risk_above"``,
            ``"risk_below"``, ``"taint_is"``, ``"session_age_above"``,
            ``"action_count_above"``, ``"tool_name_matches"``,
            ``"contains_pattern"``, and ``"custom"``.
        value: The value to compare against.
        negate: If True, the predicate result is inverted.
    """

    type: str
    value: str | int | float
    negate: bool = False


@dataclass
class Enforcement:
    """What to do when the rule fires.

    Attributes:
        action: The enforcement action. One of ``"block"``, ``"allow"``,
            ``"warn"``, ``"require_review"``, ``"log"``, ``"throttle"``,
            ``"quarantine"``.
        message: Human-readable reason shown to the user/agent.
        metadata: Extra key-value data for downstream consumers.
    """

    action: str  # "block" | "allow" | "warn" | "require_review" | "log" | "throttle" | "quarantine"
    message: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Rule:
    """A complete policy rule: when + if + then.

    Rules are composed of three parts:

    * **trigger** -- *when* to evaluate (lifecycle event + tool filter)
    * **predicates** -- *if* these conditions hold (AND logic)
    * **enforcement** -- *then* take this action

    Attributes:
        id: Unique identifier for the rule.
        name: Human-readable name.
        trigger: When to evaluate.
        predicates: All conditions that must hold (AND).
        enforcement: The action to take when fired.
        enabled: Whether the rule is active.
        priority: Higher value = evaluated first.
    """

    id: str
    name: str
    trigger: Trigger
    predicates: list[Predicate]
    enforcement: Enforcement
    enabled: bool = True
    priority: int = 0


class PolicyDSL:
    """Load and manage policy rules from YAML.

    YAML format::

        rules:
          - id: block_shell_from_untrusted
            name: Block shell execution from untrusted data
            trigger:
              event: before_tool_call
              tool_match: "Bash|shell|execute"
            predicates:
              - type: resource_is
                value: "shell:exec"
              - type: taint_is
                value: untrusted
            enforcement:
              action: block
              message: "Shell execution blocked: data provenance is untrusted"

    Usage::

        dsl = PolicyDSL()
        dsl.load_file("policy_rules.yaml")
        dsl.add_rule(custom_rule)
        for rule in dsl.rules():
            print(rule.id, rule.enforcement.action)
    """

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def load_file(self, path: str | Path) -> None:
        """Load rules from a YAML or JSON file.

        Args:
            path: Path to the policy file. Supports ``.yaml``, ``.yml``,
                and ``.json`` extensions.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8")

        if file_path.suffix == ".json":
            data = json.loads(text)
        else:
            data = _parse_policy_yaml(text)

        self._load_from_dict(data)

    def load_yaml(self, text: str) -> None:
        """Parse rules from a YAML string.

        Args:
            text: Raw YAML content.
        """
        data = _parse_policy_yaml(text)
        self._load_from_dict(data)

    def add_rule(self, rule: Rule) -> None:
        """Add a single rule to the policy.

        If a rule with the same ``id`` already exists, it is replaced.

        Args:
            rule: The rule to add.
        """
        # Replace existing rule with same id
        self._rules = [r for r in self._rules if r.id != rule.id]
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by its ID.

        Args:
            rule_id: The unique identifier of the rule to remove.

        Returns:
            True if a rule was removed, False if not found.
        """
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.id != rule_id]
        return len(self._rules) < before

    def rules(self) -> list[Rule]:
        """Return all rules sorted by priority (highest first).

        Returns:
            A list of :class:`Rule` objects, ordered descending by priority.
        """
        return sorted(self._rules, key=lambda r: r.priority, reverse=True)

    def _load_from_dict(self, data: dict) -> None:
        """Parse raw dict into Rule objects and add them."""
        for rule_data in data.get("rules", []):
            rule = _dict_to_rule(rule_data)
            self.add_rule(rule)


def _dict_to_rule(data: dict) -> Rule:
    """Convert a dict (from parsed YAML/JSON) into a Rule."""
    # Parse trigger
    trigger_data = data.get("trigger", {})
    trigger = Trigger(
        event=trigger_data.get("event", "before_tool_call"),
        tool_match=trigger_data.get("tool_match", "*"),
    )

    # Parse predicates
    predicates: list[Predicate] = []
    for pred_data in data.get("predicates", []):
        raw_value = pred_data.get("value", "")
        # Coerce value to int/float if appropriate
        value = _coerce_value(raw_value)
        negate = pred_data.get("negate", False)
        if isinstance(negate, str):
            negate = negate.lower() in ("true", "yes", "1")
        predicates.append(
            Predicate(
                type=pred_data.get("type", "custom"),
                value=value,
                negate=bool(negate),
            )
        )

    # Parse enforcement
    enforcement_data = data.get("enforcement", {})
    enforcement = Enforcement(
        action=enforcement_data.get("action", "block"),
        message=enforcement_data.get("message", ""),
        metadata=enforcement_data.get("metadata", {}),
    )

    # Parse enabled
    enabled = data.get("enabled", True)
    if isinstance(enabled, str):
        enabled = enabled.lower() in ("true", "yes", "1")

    # Parse priority
    priority = data.get("priority", 0)
    if isinstance(priority, str):
        try:
            priority = int(priority)
        except ValueError:
            priority = 0

    return Rule(
        id=data.get("id", ""),
        name=data.get("name", ""),
        trigger=trigger,
        predicates=predicates,
        enforcement=enforcement,
        enabled=bool(enabled),
        priority=int(priority),
    )


def _coerce_value(raw: str | int | float) -> str | int | float:
    """Attempt to coerce a string value to int or float."""
    if isinstance(raw, (int, float)):
        return raw
    if isinstance(raw, str):
        # Try int first
        try:
            return int(raw)
        except ValueError:
            pass
        # Try float
        try:
            return float(raw)
        except ValueError:
            pass
    return raw


def _parse_policy_yaml(text: str) -> dict:
    """Parse policy YAML using PyYAML if available, falling back to a minimal parser.

    This follows the same pattern as ``aigis.policy._parse_simple_yaml``:
    try the full ``yaml`` library first, then fall back to a stdlib-only parser.
    """
    try:
        import yaml

        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            return {"rules": []}
        return data
    except ImportError:
        pass

    return _parse_policy_yaml_minimal(text)


def _parse_policy_yaml_minimal(text: str) -> dict:  # noqa: C901
    """Minimal YAML parser (stdlib only) for the Policy DSL format.

    Handles the specific structure needed for policy rules:
    top-level ``rules:`` list, each containing ``trigger:``, ``predicates:``,
    and ``enforcement:`` sub-objects.

    This is intentionally limited to the policy YAML schema and does NOT
    attempt to be a general-purpose YAML parser.
    """
    result: dict = {"rules": []}
    current_rule: dict | None = None
    current_section: str | None = None  # "trigger" | "predicates" | "enforcement"
    current_predicate: dict | None = None

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level "rules:" marker
        if indent == 0 and stripped == "rules:":
            continue

        # Top-level key:value (not rules)
        if indent == 0 and ":" in stripped:
            key, val = stripped.split(":", 1)
            val = val.strip().strip('"').strip("'")
            if val:
                result[key] = val
            continue

        # New rule item (  - id: ...)
        if stripped.startswith("- "):
            # Flush previous predicate
            if current_predicate and current_rule is not None:
                current_rule.setdefault("predicates", []).append(current_predicate)
                current_predicate = None
            # Flush previous rule
            if current_rule is not None:
                result["rules"].append(current_rule)
            current_rule = {}
            current_section = None
            rest = stripped[2:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                current_rule[k.strip()] = v.strip().strip('"').strip("'")
            continue

        if current_rule is None:
            continue

        # Parse key: value within current rule
        if ":" not in stripped:
            continue

        key, val = stripped.split(":", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")

        # Detect section headers
        if key in ("trigger", "enforcement") and not val:
            # Flush any open predicate
            if current_predicate:
                current_rule.setdefault("predicates", []).append(current_predicate)
                current_predicate = None
            current_section = key
            current_rule.setdefault(key, {})
            continue

        if key == "predicates" and not val:
            # Flush any open predicate
            if current_predicate:
                current_rule.setdefault("predicates", []).append(current_predicate)
                current_predicate = None
            current_section = "predicates"
            current_rule.setdefault("predicates", [])
            continue

        if key == "metadata" and current_section == "enforcement" and not val:
            # Metadata sub-dict inside enforcement -- skip for minimal parser
            continue

        # Inside predicates section: new predicate list item
        if current_section == "predicates" and stripped.startswith("- "):
            if current_predicate:
                current_rule.setdefault("predicates", []).append(current_predicate)
            current_predicate = {}
            rest = stripped[2:]
            if ":" in rest:
                k2, v2 = rest.split(":", 1)
                current_predicate[k2.strip()] = v2.strip().strip('"').strip("'")
            continue

        # Predicate field continuation
        if current_section == "predicates" and current_predicate is not None and indent >= 8:
            current_predicate[key] = val
            continue

        # Inside trigger or enforcement section
        if current_section in ("trigger", "enforcement") and indent >= 6:
            current_rule.setdefault(current_section, {})[key] = val
            continue

        # Rule-level field (name, enabled, priority, etc.)
        if indent >= 4 and current_section not in ("trigger", "enforcement", "predicates"):
            current_rule[key] = val
            current_section = None  # Reset section
            continue

        # If we're at a moderate indent and it's a known rule-level field, assign it
        if key in ("name", "enabled", "priority", "id"):
            current_rule[key] = val
            current_section = None

    # Flush final predicate and rule
    if current_predicate and current_rule is not None:
        current_rule.setdefault("predicates", []).append(current_predicate)
    if current_rule is not None:
        result["rules"].append(current_rule)

    return result
