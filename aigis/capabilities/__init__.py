"""Capability-based access control (Layer 4) for ai-guardian.

Implements the CaMeL separation principle (arXiv 2503.18813): control
flow is decoupled from data flow so untrusted data can never influence
which tools get called.

Public API::

    from aigis.capabilities import (
        Capability,
        CapabilityStore,
        TaintLabel,
        TaintedValue,
        CapabilityEnforcer,
        AuthorizationResult,
    )
"""

from aigis.capabilities.enforcer import AuthorizationResult, CapabilityEnforcer
from aigis.capabilities.policy_bridge import (
    capabilities_from_policy,
    load_policy_into_store,
)
from aigis.capabilities.store import CapabilityStore
from aigis.capabilities.taint import TaintedValue, TaintLabel
from aigis.capabilities.tokens import Capability

__all__ = [
    "AuthorizationResult",
    "Capability",
    "CapabilityEnforcer",
    "CapabilityStore",
    "TaintLabel",
    "TaintedValue",
    "capabilities_from_policy",
    "load_policy_into_store",
]
