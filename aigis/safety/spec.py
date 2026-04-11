"""Safety Specification — declarative definitions of allowed/forbidden effects.

Inspired by the "Guaranteed Safe AI" framework (Bengio, Russell et al., 2024):
define what effects are allowed as formal specs, verify before execution,
produce proof certificates.

Usage::

    spec = SafetySpec(
        name="my-project",
        allowed_effects=[EffectSpec("file:read", "*")],
        forbidden_effects=[EffectSpec("file:write", ".env*")],
        invariants=[Invariant("no_secrets", "check_no_secrets_in_output", "No secrets in output")],
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EffectSpec:
    """A single allowed or forbidden effect.

    Attributes:
        effect_type: The action category, e.g. ``"file:create"``, ``"file:write"``,
            ``"file:read"``, ``"network:send"``, ``"network:fetch"``,
            ``"shell:exec"``, ``"data:read"``, ``"data:write"``.
        scope: Glob pattern describing the target, e.g. ``"*.py"``,
            ``"/tmp/*"``, ``"*.example.com"``.
        conditions: Optional key-value conditions that further restrict
            when this effect applies (reserved for future use).
    """

    effect_type: str
    scope: str
    conditions: dict = field(default_factory=dict)


@dataclass
class Invariant:
    """A property that must hold before and after execution.

    Attributes:
        name: Human-readable identifier for the invariant.
        check: Name of a registered check function (see
            :meth:`SafetyVerifier.register_check`).
        description: Explanation of what the invariant enforces.
    """

    name: str
    check: str
    description: str


@dataclass
class SafetySpec:
    """Declarative specification of what effects are allowed.

    A safety spec collects three kinds of constraints:

    * **allowed_effects** -- whitelist of effect patterns.  An action that
      does not match any allowed effect is denied.
    * **forbidden_effects** -- blacklist of effect patterns.  Forbidden
      effects take priority over allowed effects.
    * **invariants** -- named checks that must pass for every action.

    Attributes:
        name: Identifier for this spec (e.g. ``"default"`` or ``"strict"``).
        version: Semantic version string.
        allowed_effects: Effects explicitly permitted by this spec.
        forbidden_effects: Effects explicitly denied by this spec.
        invariants: Properties that must hold for every action.
    """

    name: str
    version: str = "1.0"
    allowed_effects: list[EffectSpec] = field(default_factory=list)
    forbidden_effects: list[EffectSpec] = field(default_factory=list)
    invariants: list[Invariant] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the spec to a plain dictionary (JSON-safe)."""
        return {
            "name": self.name,
            "version": self.version,
            "allowed_effects": [
                {
                    "effect_type": e.effect_type,
                    "scope": e.scope,
                    **({"conditions": e.conditions} if e.conditions else {}),
                }
                for e in self.allowed_effects
            ],
            "forbidden_effects": [
                {
                    "effect_type": e.effect_type,
                    "scope": e.scope,
                    **({"conditions": e.conditions} if e.conditions else {}),
                }
                for e in self.forbidden_effects
            ],
            "invariants": [
                {"name": inv.name, "check": inv.check, "description": inv.description}
                for inv in self.invariants
            ],
        }
