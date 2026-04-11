"""Policy Engine — declarative rules for AI agent governance.

Define who can do what, when, and under what conditions using
human-readable YAML policy files. Supports glob patterns for
file paths and commands.

Usage:
    from aigis.policy import load_policy, evaluate
    from aigis.activity import ActivityEvent

    policy = load_policy("aigis-policy.yaml")
    event = ActivityEvent(action="shell:exec", target="rm -rf /")
    decision, rule_id = evaluate(event, policy)
    # decision="deny", rule_id="dangerous_commands"

Policy YAML format:
    name: "Developer Policy"
    version: "1.0"
    default_decision: allow
    rules:
      - id: block_env_write
        action: "file:write"
        target: ".env*"
        decision: deny
        reason: "Environment files are protected"
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aigis.activity import ActivityEvent


@dataclass
class PolicyRule:
    """A single governance rule.

    Matches on action + target (glob pattern) and returns a decision.
    The `conditions` dict is an AGI-era extension point for:
      - autonomy_level: min level required (1-5)
      - cost_limit: max estimated cost in USD
      - time_window: allowed hours ("09:00-18:00")
      - memory_retention: max days to remember ("90d")
      - delegation_depth: max agent-to-agent hops (1-5)
      - department: required department scope ("sales", "engineering")
    """

    id: str
    action: str  # "file:write" | "shell:exec" | "*" — fnmatch pattern
    target: str = "*"  # glob pattern for the target (filepath, command, etc.)
    decision: str = "allow"  # "allow" | "deny" | "review"
    reason: str = ""
    conditions: dict = field(default_factory=dict)


@dataclass
class Policy:
    """A collection of rules that govern agent behavior."""

    name: str
    version: str = "1.0"
    rules: list[PolicyRule] = field(default_factory=list)
    default_decision: str = "allow"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "default_decision": self.default_decision,
            "rules": [
                {
                    "id": r.id,
                    "action": r.action,
                    "target": r.target,
                    "decision": r.decision,
                    "reason": r.reason,
                    **({"conditions": r.conditions} if r.conditions else {}),
                }
                for r in self.rules
            ],
        }


def load_policy(path: str = "aigis-policy.yaml") -> Policy:
    """Load a policy from a YAML file.

    Supports both YAML and JSON formats. YAML parsing is done with
    a minimal stdlib-only parser (no PyYAML dependency).
    """
    file_path = Path(path)
    if not file_path.exists():
        return _default_policy()

    text = file_path.read_text(encoding="utf-8")

    if file_path.suffix in (".json",):
        data = json.loads(text)
    else:
        data = _parse_simple_yaml(text)

    return _dict_to_policy(data)


def evaluate(event: ActivityEvent, policy: Policy) -> tuple[str, str]:
    """Evaluate an event against a policy.

    Returns (decision, matched_rule_id).
    Rules are evaluated in order; first match wins.
    """
    for rule in policy.rules:
        if _matches(event, rule):
            # Check conditions (AGI-era extensions)
            if rule.conditions:
                if not _check_conditions(event, rule.conditions):
                    continue
            return rule.decision, rule.id

    return policy.default_decision, "_default"


def _matches(event: ActivityEvent, rule: PolicyRule) -> bool:
    """Check if an event matches a rule's action and target patterns."""
    # Match action (e.g., "file:write" matches "file:*" or "*")
    if not fnmatch(event.action, rule.action):
        return False

    # Match target (glob pattern)
    if rule.target != "*" and event.target:
        # Normalize paths for comparison
        target = event.target.replace("\\", "/")
        pattern = rule.target.replace("\\", "/")

        # Try both the full path and basename
        if not fnmatch(target, pattern) and not fnmatch(Path(target).name, pattern):
            # Also try matching against the command content for shell:exec
            if event.action == "shell:exec":
                if pattern not in target and not fnmatch(target, f"*{pattern}*"):
                    return False
            else:
                return False

    return True


def _check_conditions(event: ActivityEvent, conditions: dict) -> bool:
    """Check AGI-era conditions against an event.

    Returns True only when ALL specified conditions are satisfied.

    Supported conditions (extensible):
      - autonomy_level: event must have >= this level
      - cost_limit: event.estimated_cost must be <= this
      - department: event.memory_scope must match
    """
    if "autonomy_level" in conditions:
        required = int(conditions["autonomy_level"])
        if event.autonomy_level < required:
            return False  # Insufficient autonomy — condition not met

    if "cost_limit" in conditions:
        limit = float(conditions["cost_limit"])
        if event.estimated_cost > limit:
            return False  # Over budget — condition not met

    if "department" in conditions:
        required_dept = conditions["department"]
        if event.memory_scope and required_dept not in event.memory_scope:
            return False  # Wrong department — condition not met

    return True  # All conditions satisfied


def _default_policy() -> Policy:
    """Built-in default policy with sensible security rules."""
    return Policy(
        name="Aigis Default Policy",
        version="1.0",
        default_decision="allow",
        rules=[
            # === Dangerous commands ===
            PolicyRule(
                id="dangerous_commands",
                action="shell:exec",
                target="rm -rf *",
                decision="deny",
                reason="Recursive forced deletion is blocked",
            ),
            PolicyRule(
                id="dangerous_format",
                action="shell:exec",
                target="*mkfs*",
                decision="deny",
                reason="Filesystem format commands are blocked",
            ),
            PolicyRule(
                id="dangerous_dd",
                action="shell:exec",
                target="*dd if=*",
                decision="deny",
                reason="Raw disk operations are blocked",
            ),
            PolicyRule(
                id="sudo_commands",
                action="shell:exec",
                target="sudo *",
                decision="review",
                reason="Privilege escalation requires review",
            ),
            # === Protected files ===
            PolicyRule(
                id="env_file_protection",
                action="file:write",
                target=".env*",
                decision="deny",
                reason="Environment files are protected from modification",
            ),
            PolicyRule(
                id="secrets_dir_protection",
                action="file:*",
                target="*secrets*",
                decision="review",
                reason="Access to secrets directories requires review",
            ),
            PolicyRule(
                id="ssh_key_protection",
                action="file:*",
                target="*.ssh/*",
                decision="deny",
                reason="SSH key access is blocked",
            ),
            PolicyRule(
                id="credentials_protection",
                action="file:write",
                target="*credentials*",
                decision="deny",
                reason="Credential files are protected",
            ),
            # === Network ===
            PolicyRule(
                id="pipe_to_shell",
                action="shell:exec",
                target="*| bash*",
                decision="deny",
                reason="Piping remote content to shell is blocked",
            ),
            PolicyRule(
                id="pipe_to_sh",
                action="shell:exec",
                target="*| sh*",
                decision="deny",
                reason="Piping remote content to shell is blocked",
            ),
            # === Git (force push first — more specific rules before general) ===
            PolicyRule(
                id="git_force_push",
                action="shell:exec",
                target="*--force*",
                decision="deny",
                reason="Force push is blocked",
            ),
            PolicyRule(
                id="git_push_review",
                action="shell:exec",
                target="git push*",
                decision="review",
                reason="Git push requires review",
            ),
            # === Agent delegation ===
            PolicyRule(
                id="agent_spawn_review",
                action="agent:spawn",
                target="*",
                decision="review",
                reason="Spawning sub-agents requires review",
            ),
            # === LLM prompt scanning ===
            PolicyRule(
                id="llm_prompt_scan",
                action="llm:prompt",
                target="*",
                decision="allow",
                reason="LLM prompts are scanned by Aigis's detection engine",
            ),
        ],
    )


def save_policy(policy: Policy, path: str = "aigis-policy.yaml") -> None:
    """Save a policy as a YAML-like file (readable without PyYAML)."""
    lines = [
        f"# Aigis Policy: {policy.name}",
        "# Generated by Aigis v0.3.0",
        "",
        f'name: "{policy.name}"',
        f'version: "{policy.version}"',
        f"default_decision: {policy.default_decision}",
        "",
        "rules:",
    ]
    for rule in policy.rules:
        lines.append(f"  - id: {rule.id}")
        lines.append(f'    action: "{rule.action}"')
        lines.append(f'    target: "{rule.target}"')
        lines.append(f"    decision: {rule.decision}")
        lines.append(f'    reason: "{rule.reason}"')
        if rule.conditions:
            lines.append("    conditions:")
            for k, v in rule.conditions.items():
                lines.append(f"      {k}: {v}")
        lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser (stdlib only, handles our policy format).

    Supports: strings, integers, lists of dicts, nested dicts.
    Does NOT support: anchors, multiline strings, complex types.
    """
    result: dict = {}
    current_list_key: str | None = None
    current_item: dict | None = None
    current_conditions: dict | None = None
    in_conditions = False

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if indent == 0 and ":" in stripped:
            # Top-level key
            if current_item and current_list_key:
                if current_conditions:
                    current_item["conditions"] = current_conditions
                result.setdefault(current_list_key, []).append(current_item)
                current_item = None
                current_conditions = None
                in_conditions = False
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                result[key] = val
            current_list_key = key if not val else None

        elif stripped.startswith("- ") and current_list_key:
            # List item
            if current_item:
                if current_conditions:
                    current_item["conditions"] = current_conditions
                result.setdefault(current_list_key, []).append(current_item)
                current_conditions = None
                in_conditions = False
            current_item = {}
            rest = stripped[2:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                current_item[k.strip()] = v.strip().strip('"').strip("'")

        elif current_item is not None and ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            if key == "conditions" and not val:
                in_conditions = True
                current_conditions = {}
            elif in_conditions and indent >= 6:
                if current_conditions is not None:
                    current_conditions[key] = val
            else:
                in_conditions = False
                current_item[key] = val

    # Flush last item
    if current_item and current_list_key:
        if current_conditions:
            current_item["conditions"] = current_conditions
        result.setdefault(current_list_key, []).append(current_item)

    return result


def _dict_to_policy(data: dict) -> Policy:
    """Convert parsed dict to Policy object."""
    rules = []
    for r in data.get("rules", []):
        rules.append(
            PolicyRule(
                id=r.get("id", ""),
                action=r.get("action", "*"),
                target=r.get("target", "*"),
                decision=r.get("decision", "allow"),
                reason=r.get("reason", ""),
                conditions=r.get("conditions", {}),
            )
        )
    return Policy(
        name=data.get("name", "Unnamed Policy"),
        version=data.get("version", "1.0"),
        rules=rules,
        default_decision=data.get("default_decision", "allow"),
    )
