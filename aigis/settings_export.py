"""Export Claude Code permission settings from an Aigis policy.

Aigis governs tool calls at the hook layer (`PreToolUse`), but Claude Code has
its own permission system that sits *above* hooks:

    Hook decisions don't bypass permission rules. Claude Code evaluates deny and
    ask rules regardless of what a PreToolUse hook returns.
    — https://code.claude.com/docs/en/permissions

So an organisation rolling Claude Code out needs both, and today it has to write
the permission rules by hand — which is how mistakes spread. This module derives
them from `aigis-policy.yaml` instead, so the two layers come from one source.

**The conversion is deliberately conservative.** The two rule languages are not
the same:

===================  ==========================  ==============================
                     Aigis policy                Claude Code permissions
===================  ==========================  ==============================
Match syntax         ``fnmatch`` glob            Bash: glob; Read/Edit: gitignore
``*`` across ``/``   yes                         no (``**`` crosses, ``*`` does not)
Command matching     substring-ish glob          anchored at the start of the command
===================  ==========================  ==============================

A mechanical translation would therefore sometimes emit a rule that is *looser*
than the Aigis rule it came from. For a security control, silently loosening is
the worst possible failure, so anything that cannot be translated exactly is
**excluded and reported** rather than approximated. Callers are expected to show
the exclusions — see :class:`ExportResult.excluded`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

from aigis.policy import Policy, PolicyRule

# Aigis decision -> Claude Code permission bucket.
_DECISION_TO_BUCKET: dict[str, str] = {
    "deny": "deny",
    "review": "ask",
    "allow": "allow",
}

# Aigis action prefix -> Claude Code tool names.
# `file:write` maps to two tools because Claude Code separates modifying an
# existing file (Edit) from creating one (Write); a policy that protects a path
# means both.
_ACTION_TO_TOOLS: dict[str, tuple[str, ...]] = {
    "shell:exec": ("Bash",),
    "file:read": ("Read",),
    "file:write": ("Edit", "Write"),
    "file:search": ("Glob", "Grep"),
    "file:*": ("Read", "Edit", "Write", "Glob", "Grep"),
    "network:fetch": ("WebFetch",),
    "network:search": ("WebSearch",),
    # `mcp:tool_call` is deliberately absent. Claude Code names MCP tools
    # `mcp__<server>__<tool>`, and which servers exist at all is decided by
    # managed-mcp.json rather than by a permission rule — so a profile that sets
    # `mcp: none` is reported as unconvertible instead of being approximated with
    # a wildcard that may not match what the docs specify.
}

# Shell metacharacters. Claude Code documents that a rule trying to match a
# command's content can be bypassed by a compound command, so a policy rule
# written around a pipeline cannot be honestly expressed as a Bash() specifier.
_SHELL_METACHARS: tuple[str, ...] = ("|", ";", "&", "`", "$(", ">", "<", "\n")


@dataclass
class ExcludedRule:
    """An Aigis rule that could not be expressed as a permission rule."""

    rule_id: str
    action: str
    target: str
    decision: str
    reason: str
    suggestion: str | None = None


@dataclass
class ExportResult:
    """Result of converting a policy into Claude Code permission settings."""

    permissions: dict[str, list[str]] = field(default_factory=dict)
    excluded: list[ExcludedRule] = field(default_factory=list)
    default_mode: str | None = None
    disable_auto_mode: bool = False

    def to_settings_dict(self) -> dict:
        """Render the settings.json body."""
        permissions: dict[str, object] = {
            bucket: rules for bucket, rules in self.permissions.items() if rules
        }
        if self.default_mode:
            permissions["defaultMode"] = self.default_mode
        settings: dict[str, object] = {"permissions": permissions}
        if self.disable_auto_mode:
            # Documented at the top level; `permissions.disableAutoMode` is also
            # accepted. Only meaningful in managed settings, where the user
            # cannot override it.
            settings["disableAutoMode"] = "disable"
        return settings


def _bash_specifier(target: str) -> tuple[str | None, str | None, str | None]:
    """Convert an Aigis shell target into a Bash() specifier.

    Returns ``(specifier, reason, suggestion)``; ``specifier`` is None when the
    target cannot be translated faithfully.
    """
    if target == "*":
        # `Bash(*)` is documented as equivalent to a bare `Bash` rule.
        return "Bash", None, None

    if any(ch in target for ch in _SHELL_METACHARS):
        return (
            None,
            "target contains shell metacharacters, and Claude Code documents that "
            "rules matching command content are bypassable by compound commands",
            "Block the underlying binary instead, e.g. Bash(curl:*) rather than a "
            "rule describing a pipeline.",
        )

    if target.startswith("*"):
        inner = target.strip("*").strip()
        # Only propose a concrete replacement when what remains actually looks
        # like a command name. Naively stripping the wildcards produces nonsense
        # for rules built around a flag or an argument: `*--force*` would come
        # back as `Bash(--force:*)`, which names a flag, and `*dd if=*` as
        # `Bash(dd if=:*)`, where `:*` is not even at the end of the pattern.
        if inner and " " not in inner and "=" not in inner and not inner.startswith("-"):
            suggestion = f"If you meant the command itself, anchor it: Bash({inner}:*)."
        else:
            suggestion = (
                "A Bash specifier cannot match mid-command. Name the command you want to "
                "block, or leave this rule to the Aigis hook, which matches the way this "
                "pattern was written."
            )
        return (
            None,
            "target starts with a wildcard; Bash specifiers match from the beginning "
            "of the command, so this would not match what the Aigis rule matches",
            suggestion,
        )

    return f"Bash({target})", None, None


def _path_specifiers(
    tools: tuple[str, ...], target: str
) -> tuple[list[str], str | None, str | None]:
    """Convert an Aigis file target into Read()/Edit()/Write() specifiers."""
    if target == "*":
        return list(tools), None, None

    normalised = target.replace("\\", "/")

    if "/" in normalised:
        # Aigis uses fnmatch, where `*` happily crosses `/`. Claude Code uses
        # gitignore syntax, where it does not. Emitting the pattern unchanged
        # would silently narrow (or widen) the match.
        basename = PurePosixPath(normalised).name or normalised
        directory = normalised.rstrip("/").rsplit("/", 1)[0].lstrip("*/")
        if directory and basename in ("*", ""):
            suggestion = f"{tools[0]}(**/{directory}/**)"
        else:
            suggestion = f"{tools[0]}(**/{basename})"
        return (
            [],
            "target spans a path separator; Aigis matches it with fnmatch (where `*` "
            "crosses directories) while Claude Code uses gitignore syntax (where it "
            "does not), so the translation would not be equivalent",
            f"Write the rule by hand, e.g. {suggestion}.",
        )

    # A bare filename pattern means the same thing in both languages: gitignore
    # matches it at any depth, which is what the fnmatch rule intends.
    return [f"{tool}({target})" for tool in tools], None, None


def _tools_for_action(action: str) -> tuple[str, ...] | None:
    if action in _ACTION_TO_TOOLS:
        return _ACTION_TO_TOOLS[action]
    if action == "*":
        return None
    return None


def convert_rule(rule: PolicyRule) -> tuple[str, list[str], ExcludedRule | None]:
    """Convert one policy rule.

    Returns ``(bucket, specifiers, excluded)``. When the rule cannot be
    converted, ``specifiers`` is empty and ``excluded`` explains why.
    """
    bucket = _DECISION_TO_BUCKET.get(rule.decision)
    if bucket is None:
        return (
            "",
            [],
            ExcludedRule(
                rule.id,
                rule.action,
                rule.target,
                rule.decision,
                f"unknown decision {rule.decision!r}; expected allow, deny, or review",
            ),
        )

    if rule.conditions:
        # Conditions like autonomy_level or time_window have no equivalent in
        # Claude Code permissions. Exporting the rule without them would drop the
        # qualifier and apply the decision unconditionally.
        return (
            bucket,
            [],
            ExcludedRule(
                rule.id,
                rule.action,
                rule.target,
                rule.decision,
                "rule is conditional ("
                + ", ".join(sorted(rule.conditions))
                + "), and Claude Code permission rules cannot express conditions; "
                "exporting it would apply the decision unconditionally",
                "Keep this rule in the Aigis hook layer, which does evaluate conditions.",
            ),
        )

    tools = _tools_for_action(rule.action)
    if tools is None:
        return (
            bucket,
            [],
            ExcludedRule(
                rule.id,
                rule.action,
                rule.target,
                rule.decision,
                f"action {rule.action!r} has no Claude Code tool equivalent",
                "Aigis still enforces this rule through its PreToolUse hook.",
            ),
        )

    if tools == ("Bash",):
        specifier, reason, suggestion = _bash_specifier(rule.target)
        if specifier is None:
            return (
                bucket,
                [],
                ExcludedRule(
                    rule.id, rule.action, rule.target, rule.decision, reason or "", suggestion
                ),
            )
        return bucket, [specifier], None

    specifiers, reason, suggestion = _path_specifiers(tools, rule.target)
    if not specifiers:
        return (
            bucket,
            [],
            ExcludedRule(
                rule.id, rule.action, rule.target, rule.decision, reason or "", suggestion
            ),
        )
    return bucket, specifiers, None


def export_permissions(policy: Policy, *, managed: bool = False) -> ExportResult:
    """Derive Claude Code permission settings from an Aigis policy.

    `managed` adds `disableAutoMode`, which only has force in managed settings.
    """
    result = ExportResult(permissions={"deny": [], "ask": [], "allow": []})

    for rule in policy.rules:
        bucket, specifiers, excluded = convert_rule(rule)
        if excluded is not None:
            result.excluded.append(excluded)
            continue
        for specifier in specifiers:
            if specifier not in result.permissions[bucket]:
                result.permissions[bucket].append(specifier)

    # `default_decision: allow` is the Aigis default and corresponds to Claude
    # Code's own default; only a deny-by-default policy needs stating, and
    # Claude Code expresses that as an "ask" default rather than a deny one —
    # there is no fail-closed defaultMode, so an operator wanting deny-by-default
    # must enumerate allow rules.
    if policy.default_decision == "deny":
        result.default_mode = "ask"
    elif policy.default_decision == "review":
        result.default_mode = "ask"

    result.disable_auto_mode = managed
    return result


# Where a managed settings file has to live for the OS to pick it up.
MANAGED_SETTINGS_PATHS: dict[str, str] = {
    "macos": "/Library/Application Support/ClaudeCode/managed-settings.json",
    "linux": "/etc/claude-code/managed-settings.json",
    "windows": r"C:\Program Files\ClaudeCode\managed-settings.json",
}
