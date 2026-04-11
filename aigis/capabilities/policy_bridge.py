"""Bridge between the existing policy engine and the capability system.

Converts PolicyRule objects into Capability tokens for backwards
compatibility, so existing YAML-based policies automatically generate
the corresponding capability grants.

Design principle: 'deny' rules produce NO capability (absence = denied).
'allow' rules produce a Capability. 'review' rules produce a Capability
with a ``requires_review=True`` constraint.
"""

from __future__ import annotations

from aigis.capabilities.store import CapabilityStore
from aigis.capabilities.tokens import Capability
from aigis.policy import Policy


def capabilities_from_policy(policy: Policy) -> list[Capability]:
    """Convert a Policy's allow/review rules into Capability tokens.

    Deny rules are intentionally omitted — in the capability model,
    the absence of a grant IS the denial.

    Args:
        policy: An existing ai-guardian Policy object.

    Returns:
        List of Capability tokens corresponding to the policy's
        allow and review rules.
    """
    capabilities: list[Capability] = []

    for rule in policy.rules:
        if rule.decision == "deny":
            continue

        constraints: dict = {}
        if rule.conditions:
            constraints.update(rule.conditions)
        if rule.decision == "review":
            constraints["requires_review"] = True

        cap = Capability(
            resource=rule.action,
            scope=rule.target,
            granted_by=f"policy:{policy.name}:{rule.id}",
            constraints=constraints,
        )
        capabilities.append(cap)

    return capabilities


def load_policy_into_store(policy: Policy, store: CapabilityStore) -> list[Capability]:
    """Convert a policy to capabilities and register them in a store.

    This is a convenience wrapper that calls ``capabilities_from_policy``
    and then grants each capability through the store (so they appear
    in the audit log).

    Args:
        policy: An existing ai-guardian Policy object.
        store: The CapabilityStore to populate.

    Returns:
        List of Capability tokens that were registered.
    """
    granted: list[Capability] = []
    for rule in policy.rules:
        if rule.decision == "deny":
            continue

        constraints: dict = {}
        if rule.conditions:
            constraints.update(rule.conditions)
        if rule.decision == "review":
            constraints["requires_review"] = True

        cap = store.grant(
            resource=rule.action,
            scope=rule.target,
            granted_by=f"policy:{policy.name}:{rule.id}",
            constraints=constraints,
        )
        granted.append(cap)

    return granted
