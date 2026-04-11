"""Memory integrity checker — tamper detection and TTL rotation.

Provides hash-based integrity verification and time-to-live (TTL) rotation
for memory entries, reducing the persistence window of poisoned entries.

Features:

1. **Content hashing**: SHA-256 hashes detect tampering of stored memories.
2. **TTL rotation**: auto-expire old memories (reduces persistence of poison).
3. **Source tracking**: memories from untrusted sources get shorter TTL.
4. **Integrity verification**: check if a memory has been modified since storage.
5. **Persistence**: save/load integrity records to/from JSON.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from aigis.memory.scanner import MemoryEntry

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class IntegrityRecord:
    """Hash record for a single memory entry."""

    key: str
    content_hash: str  # SHA-256 hex digest of content
    created_at: float  # Unix timestamp when registered
    source: str  # "user", "agent", "tool", "system"
    expires_at: float | None  # Unix timestamp for TTL expiry; None = no expiry


# Default TTL by source trust level (seconds).
# Untrusted sources (user input, tool outputs) expire after 7 days to limit
# the persistence window of poisoned entries. Trusted sources (agent, system)
# have no expiry.
_DEFAULT_TTL_BY_SOURCE: dict[str, float] = {
    "user": 604_800.0,  # 7 days — external/untrusted input
    "tool": 604_800.0,  # 7 days — tool outputs are untrusted
    "agent": 0.0,  # no expiry — trusted inter-agent data
    "system": 0.0,  # no expiry — system-level data
}


# ---------------------------------------------------------------------------
# MemoryIntegrity
# ---------------------------------------------------------------------------


class MemoryIntegrity:
    """Hash-based integrity checking and TTL rotation for memory entries.

    Thread-safe: all mutations are protected by a lock.

    Args:
        default_ttl: Default TTL in seconds for entries whose source
                     is not in the built-in trust table. ``None`` means
                     no default expiry (entries persist forever unless
                     source-based TTL applies).
    """

    def __init__(self, default_ttl: float | None = None) -> None:
        self._default_ttl = default_ttl
        self._records: dict[str, IntegrityRecord] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        entry: MemoryEntry,
        ttl: float | None = None,
    ) -> IntegrityRecord:
        """Register a memory entry and compute its content hash.

        Args:
            entry: The memory entry to register.
            ttl: Optional explicit TTL in seconds. Overrides both the
                 source-based default and the constructor default.
                 Pass ``0`` for no expiry.

        Returns:
            The created IntegrityRecord.
        """
        content_hash = self._hash(entry.content)
        expires_at = self._compute_expiry(entry, ttl)

        record = IntegrityRecord(
            key=entry.key,
            content_hash=content_hash,
            created_at=entry.created_at,
            source=entry.source,
            expires_at=expires_at,
        )

        with self._lock:
            self._records[entry.key] = record

        return record

    def verify(self, entry: MemoryEntry) -> bool:
        """Check if a memory entry matches its registered hash.

        Args:
            entry: The memory entry to verify.

        Returns:
            ``True`` if the content hash matches, ``False`` if it has
            been tampered with or the key is not registered.
        """
        with self._lock:
            record = self._records.get(entry.key)

        if record is None:
            return False

        return record.content_hash == self._hash(entry.content)

    def is_expired(self, key: str) -> bool:
        """Check if a memory entry has exceeded its TTL.

        Args:
            key: The memory entry key.

        Returns:
            ``True`` if expired or not registered, ``False`` otherwise.
        """
        with self._lock:
            record = self._records.get(key)

        if record is None:
            return True

        if record.expires_at is None:
            return False

        return time.time() > record.expires_at

    def prune_expired(self) -> list[str]:
        """Remove all expired entries.

        Returns:
            List of pruned entry keys.
        """
        now = time.time()
        pruned: list[str] = []

        with self._lock:
            keys = list(self._records.keys())
            for key in keys:
                record = self._records[key]
                if record.expires_at is not None and now > record.expires_at:
                    del self._records[key]
                    pruned.append(key)

        return pruned

    def rotate(self, max_age_seconds: float) -> list[str]:
        """Force-expire entries older than *max_age_seconds*.

        This is useful for periodic rotation that limits the persistence
        window regardless of the original TTL.

        Args:
            max_age_seconds: Maximum age in seconds. Entries with
                ``created_at`` older than ``now - max_age_seconds``
                are removed.

        Returns:
            List of rotated (removed) entry keys.
        """
        cutoff = time.time() - max_age_seconds
        rotated: list[str] = []

        with self._lock:
            keys = list(self._records.keys())
            for key in keys:
                if self._records[key].created_at < cutoff:
                    del self._records[key]
                    rotated.append(key)

        return rotated

    def save(self, path: Path) -> None:
        """Persist integrity records to a JSON file.

        Args:
            path: File path to write to. Parent directories are created
                  if they do not exist.
        """
        with self._lock:
            data = [asdict(r) for r in self._records.values()]

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        """Load integrity records from a JSON file.

        Replaces the current in-memory records with whatever is on disk.

        Args:
            path: File path to read from.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        raw = json.loads(path.read_text(encoding="utf-8"))

        loaded: dict[str, IntegrityRecord] = {}
        for item in raw:
            record = IntegrityRecord(
                key=item["key"],
                content_hash=item["content_hash"],
                created_at=item["created_at"],
                source=item["source"],
                expires_at=item.get("expires_at"),
            )
            loaded[record.key] = record

        with self._lock:
            self._records = loaded

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(content: str) -> str:
        """Compute SHA-256 hex digest of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _compute_expiry(
        self,
        entry: MemoryEntry,
        explicit_ttl: float | None,
    ) -> float | None:
        """Determine the expiry timestamp for an entry.

        Priority: explicit_ttl > source-based default > constructor default.
        A TTL of 0 means no expiry.
        """
        if explicit_ttl is not None:
            if explicit_ttl == 0:
                return None
            return entry.created_at + explicit_ttl

        # Source-based TTL
        source_ttl = _DEFAULT_TTL_BY_SOURCE.get(entry.source)
        if source_ttl is not None:
            if source_ttl == 0:
                return None
            return entry.created_at + source_ttl

        # Constructor default
        if self._default_ttl is not None:
            if self._default_ttl == 0:
                return None
            return entry.created_at + self._default_ttl

        return None

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)

    def __repr__(self) -> str:
        with self._lock:
            count = len(self._records)
        return f"MemoryIntegrity(records={count}, default_ttl={self._default_ttl})"
