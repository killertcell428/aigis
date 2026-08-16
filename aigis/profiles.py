"""Compose a role profile from capabilities, and derive a policy from it.

A company rolling Claude Code out has to answer "who may do what" for each
department. Shipping fixed profiles named `marketing` or `engineering` would ship
*our* assumptions: marketing means one thing where marketers query the warehouse
and another where they write copy.

What is stable across companies is not the role name but what a person needs to
be able to *do*. Six axes cover it, and a role is a combination of them:

    web       may the agent fetch external content?
    files     what may it read and write?
    shell     may it run commands?
    git       may it commit, push, force-push?
    packages  may it install dependencies?
    mcp       may it connect external tools?

Underneath sits a baseline that no combination can weaken — credential files,
SSH keys, recursive deletion, piping a download into a shell. So a generated
policy is two layers: a floor nobody can lower, and a role-shaped layer above it.

**Generated rules never use `review`.** A review decision puts a prompt in front
of someone mid-task, and in practice a non-engineer who cannot judge the prompt
either approves everything (which defeats it) or refuses everything (which stops
the work). The judgement belongs at profile-design time, where someone can think
about it once, with context, for the whole department.

The capability layer therefore emits only `deny` and `allow`. The `allow` case is
not a way to widen the baseline — it cancels a baseline *review* for something the
profile explicitly granted. `git: push` is the example: the baseline sends
`git push` for review, but a profile that grants push has already answered that
question, so prompting again asks someone to re-decide it with less context.
Because capability rules are evaluated *before* the baseline, an `allow` here can
in principle reach past a baseline deny. That is why the only allow this module
emits is `git push*`, paired with denies for the force variants placed ahead of
it — and why the `git` axis has no `unrestricted` value. Any future allow needs
the same treatment: deny the dangerous shape first, in the capability layer, and
do not rely on the baseline to catch it afterwards.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from aigis.policy import Policy, PolicyRule, _default_policy

# Allowed values per axis. Kept deliberately small: a profile that takes three
# minutes to write is one a company will actually maintain.
CAPABILITY_VALUES: dict[str, tuple[str, ...]] = {
    "web": ("none", "read"),
    "files": ("none", "read", "workspace", "unrestricted"),
    "shell": ("none", "unrestricted"),
    # No `unrestricted`: force-push stays denied for every profile. Allowing it
    # would mean emitting an allow for `git push*` that sits *in front of* the
    # baseline's own `*--force*` deny, which would make the floor reachable-past
    # — the one property this two-layer design exists to guarantee.
    "git": ("none", "local", "push"),
    "packages": ("none", "unrestricted"),
    "mcp": ("none", "approved", "unrestricted"),
}

# What a profile gets if it does not name an axis: the most restrictive value.
# Silence should not grant capability.
CAPABILITY_DEFAULTS: dict[str, str] = {
    axis: values[0] for axis, values in CAPABILITY_VALUES.items()
}

# Package managers whose install command `packages: none` blocks.
_INSTALL_COMMANDS: tuple[str, ...] = (
    "npm install*",
    "npm i *",
    "pnpm add*",
    "pnpm install*",
    "yarn add*",
    "pip install*",
    "pip3 install*",
    "uv add*",
    "uv pip install*",
    "gem install*",
    "cargo add*",
    "go install*",
)


@dataclass
class Profile:
    """A role expressed as a combination of capabilities."""

    name: str
    description: str = ""
    capabilities: dict[str, str] = field(default_factory=dict)
    allow: dict[str, list[str]] = field(default_factory=dict)

    def capability(self, axis: str) -> str:
        """Resolved value for an axis, falling back to the safest default."""
        return self.capabilities.get(axis, CAPABILITY_DEFAULTS[axis])


class ProfileError(ValueError):
    """Raised when a profile names an unknown axis or an invalid value."""


def validate(profile: Profile) -> None:
    """Reject unknown axes and values.

    A typo like `shel: unrestricted` would otherwise fall through to the default
    (`shell: none`) and quietly produce a profile that blocks everything, which
    the author would then debug at rollout time instead of here.
    """
    for axis, value in profile.capabilities.items():
        if axis not in CAPABILITY_VALUES:
            known = ", ".join(sorted(CAPABILITY_VALUES))
            raise ProfileError(f"unknown capability axis {axis!r}; expected one of: {known}")
        if value not in CAPABILITY_VALUES[axis]:
            allowed = ", ".join(CAPABILITY_VALUES[axis])
            raise ProfileError(f"invalid value {value!r} for {axis!r}; expected one of: {allowed}")


# --- per-axis rule generation ------------------------------------------------
#
# Each returns the rules that *restrict* the axis. The permissive end of every
# axis contributes nothing, because the baseline already covers what must never
# be allowed.


def _web_rules(value: str) -> list[PolicyRule]:
    if value == "none":
        return [
            PolicyRule(
                id="cap_web_fetch_denied",
                action="network:fetch",
                target="*",
                decision="deny",
                reason="This role does not fetch external content",
            ),
            PolicyRule(
                id="cap_web_search_denied",
                action="network:search",
                target="*",
                decision="deny",
                reason="This role does not search the web",
            ),
        ]
    return []


def _files_rules(value: str) -> list[PolicyRule]:
    if value == "none":
        return [
            PolicyRule(
                id="cap_files_read_denied",
                action="file:read",
                target="*",
                decision="deny",
                reason="This role does not read files",
            ),
            PolicyRule(
                id="cap_files_write_denied",
                action="file:write",
                target="*",
                decision="deny",
                reason="This role does not write files",
            ),
        ]
    if value == "read":
        return [
            PolicyRule(
                id="cap_files_write_denied",
                action="file:write",
                target="*",
                decision="deny",
                reason="This role reads files but does not modify them",
            ),
        ]
    # `workspace` is Claude Code's own default — reads and writes stay inside the
    # working directory without Aigis adding anything. `unrestricted` widens that
    # at the settings layer (additionalDirectories), not here.
    return []


def _shell_rules(value: str) -> list[PolicyRule]:
    if value == "none":
        return [
            PolicyRule(
                id="cap_shell_denied",
                action="shell:exec",
                target="*",
                decision="deny",
                reason="This role does not run shell commands",
            ),
        ]
    return []


def _git_rules(value: str) -> list[PolicyRule]:
    if value == "none":
        return [
            PolicyRule(
                id="cap_git_denied",
                action="shell:exec",
                target="git *",
                decision="deny",
                reason="This role does not use git",
            ),
        ]
    if value == "local":
        return [
            PolicyRule(
                id="cap_git_push_denied",
                action="shell:exec",
                target="git push*",
                decision="deny",
                reason="This role commits locally; publishing is done by someone else",
            ),
        ]
    if value == "push":
        # Force-push rewrites history others depend on. Denied rather than sent
        # for review: nobody mid-task is in a position to judge it.
        #
        # The trailing allow cancels the baseline's `git push*` review. This role
        # was explicitly granted push, so leaving the baseline to prompt would put
        # a question in front of someone who cannot act on it — the decision was
        # already made, here, at profile-design time. Order matters: the denies
        # come first, and `evaluate()` returns on first match.
        return [
            PolicyRule(
                id="cap_git_force_push_denied",
                action="shell:exec",
                target="git push --force*",
                decision="deny",
                reason="Force-push rewrites shared history",
            ),
            PolicyRule(
                id="cap_git_force_push_short_denied",
                action="shell:exec",
                target="git push -f*",
                decision="deny",
                reason="Force-push rewrites shared history",
            ),
            PolicyRule(
                id="cap_git_push_allowed",
                action="shell:exec",
                target="git push*",
                decision="allow",
                reason="This role is granted push access",
            ),
        ]
    return []


def _packages_rules(value: str) -> list[PolicyRule]:
    if value == "none":
        return [
            PolicyRule(
                id=f"cap_packages_denied_{i}",
                action="shell:exec",
                target=command,
                decision="deny",
                reason="This role does not install dependencies",
            )
            for i, command in enumerate(_INSTALL_COMMANDS)
        ]
    return []


def _mcp_rules(value: str) -> list[PolicyRule]:
    if value == "none":
        return [
            PolicyRule(
                id="cap_mcp_denied",
                action="mcp:tool_call",
                target="*",
                decision="deny",
                reason="This role does not use MCP tools",
            ),
        ]
    # `approved` and `unrestricted` generate the same policy. The difference is
    # enforced one layer up, by listing servers in managed-mcp.json — which is an
    # administrator writing a list, not an end user answering a prompt.
    return []


_AXIS_BUILDERS = {
    "web": _web_rules,
    "files": _files_rules,
    "shell": _shell_rules,
    "git": _git_rules,
    "packages": _packages_rules,
    "mcp": _mcp_rules,
}


def build_policy(profile: Profile) -> Policy:
    """Derive a policy: the baseline, then the capability layer on top.

    Capability rules come first in the list so they are evaluated before the
    baseline's broader patterns; `evaluate()` returns on first match. The
    baseline still cannot be widened, because every capability rule is a deny.
    """
    validate(profile)

    capability_rules: list[PolicyRule] = []
    for axis, builder in _AXIS_BUILDERS.items():
        capability_rules.extend(builder(profile.capability(axis)))

    baseline = _default_policy()
    return Policy(
        name=f"Aigis Profile — {profile.name}",
        version="1.0",
        rules=capability_rules + baseline.rules,
        default_decision=baseline.default_decision,
    )


def load_profile(path: str | Path) -> Profile:
    """Load a profile from JSON.

    YAML support rides on the optional `yaml` extra; JSON always works so that a
    zero-dependency install can still build profiles.
    """
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")

    if file_path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # noqa: PLC0415 — optional dependency, imported on demand
        except ImportError as exc:  # pragma: no cover - depends on install extras
            raise ProfileError(
                f"{file_path} is YAML, which needs the optional extra: "
                "pip install 'pyaigis[yaml]' — or write the profile as JSON"
            ) from exc
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ProfileError(f"{file_path}: expected a mapping at the top level")

    profile = Profile(
        name=str(data.get("name") or file_path.stem),
        description=str(data.get("description") or ""),
        capabilities=dict(data.get("capabilities") or {}),
        allow={k: list(v) for k, v in (data.get("allow") or {}).items()},
    )
    validate(profile)
    return profile


# --- human-readable summary ---------------------------------------------------

_DESCRIPTIONS: dict[tuple[str, str], str] = {
    ("web", "none"): "Cannot fetch web pages or search the web",
    ("web", "read"): "Can fetch web pages and search the web",
    ("files", "none"): "Cannot read or write files",
    ("files", "read"): "Can read files, cannot modify them",
    ("files", "workspace"): "Can read and write inside the working directory",
    ("files", "unrestricted"): "Can read and write outside the working directory too",
    ("shell", "none"): "Cannot run shell commands",
    ("shell", "unrestricted"): "Can run shell commands, except those the baseline blocks",
    ("git", "none"): "Cannot use git",
    ("git", "local"): "Can commit locally, cannot push",
    ("git", "push"): "Can commit and push; force-push is blocked",
    ("packages", "none"): "Cannot install dependencies",
    ("packages", "unrestricted"): "Can install dependencies",
    ("mcp", "none"): "Cannot use MCP tools",
    ("mcp", "approved"): "Can use MCP servers the administrator listed",
    ("mcp", "unrestricted"): "Can use any MCP server",
}


def describe(profile: Profile) -> list[str]:
    """One line per axis, in plain language, for the people approving this."""
    lines = []
    for axis in CAPABILITY_VALUES:
        value = profile.capability(axis)
        lines.append(f"{axis:<9} {value:<13} {_DESCRIPTIONS[(axis, value)]}")
    return lines
