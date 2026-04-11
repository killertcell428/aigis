"""Thread-safe capability store with audit logging.

The CapabilityStore is the single source of truth for all active capability
grants.  All mutations are serialized through a threading.Lock and every
operation is recorded in an append-only audit log.
"""

from __future__ import annotations

import threading
import time
from fnmatch import fnmatch
from typing import Any

from aigis.capabilities.tokens import Capability


class CapabilityStore:
    """Thread-safe registry of active capability tokens.

    Capabilities are identified by their cryptographic nonce, not by
    string matching on resource/scope — this prevents forgery by
    injected text.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._capabilities: dict[str, Capability] = {}  # nonce -> Capability
        self._audit: list[dict] = []

    def grant(
        self,
        resource: str,
        scope: str,
        granted_by: str,
        expires_at: float | None = None,
        constraints: dict | None = None,
    ) -> Capability:
        """Create and register a new capability token.

        Args:
            resource: Resource type (e.g. "file:read", "shell:exec").
            scope: Glob pattern for allowed targets.
            granted_by: Origin of the grant.
            expires_at: Optional Unix timestamp for expiry.
            constraints: Optional dict of additional limits.

        Returns:
            The newly created Capability.
        """
        cap = Capability(
            resource=resource,
            scope=scope,
            granted_by=granted_by,
            expires_at=expires_at,
            constraints=constraints or {},
        )
        with self._lock:
            self._capabilities[cap.nonce] = cap
            self._log("grant", cap)
        return cap

    def revoke(self, capability: Capability) -> bool:
        """Revoke an active capability.

        Args:
            capability: The capability to revoke (matched by nonce).

        Returns:
            True if the capability was found and revoked, False otherwise.
        """
        with self._lock:
            if capability.nonce in self._capabilities:
                del self._capabilities[capability.nonce]
                self._log("revoke", capability)
                return True
            return False

    def check(self, resource: str, target: str) -> Capability | None:
        """Find an active, non-expired capability matching the request.

        Uses fnmatch for scope pattern matching.  Expired capabilities
        are automatically pruned during the check.

        Args:
            resource: The resource type being requested.
            target: The specific target (filepath, command, etc.).

        Returns:
            A matching Capability, or None if no valid grant exists.
        """
        now = time.time()
        with self._lock:
            expired_nonces: list[str] = []
            result: Capability | None = None

            for nonce, cap in self._capabilities.items():
                if cap.expires_at is not None and cap.expires_at < now:
                    expired_nonces.append(nonce)
                    continue

                if cap.resource == resource and fnmatch(target, cap.scope):
                    result = cap
                    self._log("check_hit", cap, {"target": target})
                    break

            for nonce in expired_nonces:
                cap = self._capabilities.pop(nonce)
                self._log("expired", cap)

            if result is None:
                self._log(
                    "check_miss",
                    None,
                    {"resource": resource, "target": target},
                )

            return result

    def list_active(self) -> list[Capability]:
        """Return all active (non-expired) capabilities.

        Expired capabilities are pruned as a side effect.
        """
        now = time.time()
        with self._lock:
            expired_nonces = [
                nonce
                for nonce, cap in self._capabilities.items()
                if cap.expires_at is not None and cap.expires_at < now
            ]
            for nonce in expired_nonces:
                cap = self._capabilities.pop(nonce)
                self._log("expired", cap)

            return list(self._capabilities.values())

    def audit_log(self) -> list[dict]:
        """Return the full audit log (read-only copy)."""
        with self._lock:
            return list(self._audit)

    def _log(
        self,
        action: str,
        capability: Capability | None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Append an entry to the audit log (must be called under lock)."""
        entry: dict[str, Any] = {
            "timestamp": time.time(),
            "action": action,
        }
        if capability is not None:
            entry["nonce"] = capability.nonce
            entry["resource"] = capability.resource
            entry["scope"] = capability.scope
            entry["granted_by"] = capability.granted_by
        if extra:
            entry.update(extra)
        self._audit.append(entry)
