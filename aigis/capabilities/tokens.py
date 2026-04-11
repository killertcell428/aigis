"""Capability tokens: unforgeable, immutable grants for specific resources.

Inspired by CaMeL (arXiv 2503.18813) — capability tokens separate control
flow from data flow so untrusted data can never forge access grants.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Capability:
    """An unforgeable capability token granting access to a specific resource.

    Frozen (immutable) so tokens cannot be mutated after creation.
    The nonce is generated via ``secrets.token_hex`` so injected text
    cannot predict or forge valid capabilities.

    Args:
        resource: Resource type identifier (e.g. "file:read", "shell:exec").
        scope: Glob pattern constraining the target (e.g. "/tmp/*", "git *").
        granted_by: Origin of the grant ("system_prompt", "user_confirm", etc.).
        expires_at: Unix timestamp after which the capability is invalid, or None.
        nonce: Cryptographically random hex string for unforgeable identity.
        constraints: Additional limits such as max_calls, cost_limit, etc.
    """

    resource: str
    scope: str
    granted_by: str
    expires_at: float | None = None
    nonce: str = field(default_factory=lambda: secrets.token_hex(16))
    constraints: dict = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.nonce)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Capability):
            return NotImplemented
        return self.nonce == other.nonce
