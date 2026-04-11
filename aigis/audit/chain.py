"""Hash chain utilities for linking and verifying audit log entries.

Provides static methods for computing entry hashes, verifying the
integrity of the hash chain, and producing the genesis hash used as
the ``prev_hash`` for the very first entry.
"""

from __future__ import annotations

import hashlib
import json

from aigis.audit.signed_log import SignedLogEntry


class HashChain:
    """Hash chain operations for linking log entries."""

    @staticmethod
    def compute_entry_hash(entry: SignedLogEntry) -> str:
        """SHA-256 hash of a log entry (used as ``prev_hash`` for the next entry).

        The hash covers all fields including the HMAC signature, so any
        modification to any field will produce a different hash and break
        the chain.
        """
        canonical = json.dumps(entry.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_chain(entries: list[SignedLogEntry]) -> tuple[bool, list[int]]:
        """Verify the hash chain is unbroken.

        Returns:
            A tuple ``(valid, broken_indices)`` where *valid* is ``True``
            when the entire chain is intact, and *broken_indices* lists the
            **sequence numbers** of entries whose ``prev_hash`` does not
            match the computed hash of the preceding entry.
        """
        if not entries:
            return True, []

        broken: list[int] = []

        # First entry must reference the genesis hash
        if entries[0].prev_hash != HashChain.genesis_hash():
            broken.append(entries[0].sequence)

        for i in range(1, len(entries)):
            expected = HashChain.compute_entry_hash(entries[i - 1])
            if entries[i].prev_hash != expected:
                broken.append(entries[i].sequence)

        return len(broken) == 0, broken

    @staticmethod
    def genesis_hash() -> str:
        """The ``prev_hash`` for the very first entry in a chain."""
        return "0" * 64
