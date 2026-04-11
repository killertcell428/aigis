"""HMAC-signed, append-only audit log with hash chaining.

Provides tamper-evident logging for AI agent actions. Each entry is
signed with HMAC-SHA256 and includes the hash of the previous entry,
creating a cryptographic chain. If any entry is modified or deleted,
the chain breaks and verification fails.

Based on Aegis (arxiv 2603.16938) — Immutable Logging Kernel concept.

Usage::

    from aigis.audit import SignedAuditLog, AuditVerifier

    log = SignedAuditLog(secret_key="your-secret-key")
    log.append(event_type="tool_call", actor="agent",
               action="shell:exec", target="/bin/ls", risk_score=30)
    log.save("audit.jsonl")

    verifier = AuditVerifier(secret_key="your-secret-key")
    result = verifier.verify_file("audit.jsonl")
    print(result.valid)  # True if no tampering detected
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SignedLogEntry:
    """An immutable, HMAC-signed audit log entry."""

    sequence: int
    """Monotonic sequence number (0-based)."""

    timestamp: str
    """ISO-8601 UTC timestamp."""

    event_type: str
    """Event category: tool_call, scan_result, containment_change,
    policy_decision, capability_grant, etc."""

    actor: str
    """Who performed the action: user, agent, system, or an agent_id."""

    action: str
    """What happened (e.g. shell:exec, file:write)."""

    target: str
    """What the action was performed on."""

    risk_score: int
    """Risk score 0-100."""

    outcome: str
    """Result: allowed, blocked, warn, or error."""

    details: dict[str, Any]
    """Additional context (frozen via JSON serialization)."""

    prev_hash: str
    """SHA-256 hash of the previous entry (chain link)."""

    signature: str
    """HMAC-SHA256 signature of all above fields."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (suitable for JSON)."""
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "risk_score": self.risk_score,
            "outcome": self.outcome,
            "details": self.details,
            "prev_hash": self.prev_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignedLogEntry:
        """Deserialize from a plain dict."""
        return cls(
            sequence=data["sequence"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            actor=data["actor"],
            action=data["action"],
            target=data["target"],
            risk_score=data["risk_score"],
            outcome=data["outcome"],
            details=data.get("details", {}),
            prev_hash=data["prev_hash"],
            signature=data["signature"],
        )


# ---------------------------------------------------------------------------
# Key management helpers
# ---------------------------------------------------------------------------

_KEY_DIR = Path(".aigis")
_KEY_FILE = _KEY_DIR / "audit_key"


_key_lock = threading.Lock()


def _resolve_key(secret_key: str | None) -> bytes:
    """Resolve the HMAC key.

    Priority:
    1. Explicit ``secret_key`` argument.
    2. Existing key on disk at ``.aigis/audit_key``.
    3. Auto-generate a new key and persist it.

    Thread-safe: concurrent calls use a lock to prevent duplicate
    key generation (race condition fix).
    """
    if secret_key is not None:
        return secret_key.encode("utf-8")

    with _key_lock:
        # Re-check inside lock (another thread may have created it)
        if _KEY_FILE.exists():
            return _KEY_FILE.read_text(encoding="utf-8").strip().encode("utf-8")

        # Auto-generate
        new_key = secrets.token_hex(32)
        _KEY_DIR.mkdir(parents=True, exist_ok=True)
        _KEY_FILE.write_text(new_key, encoding="utf-8")
        try:
            _KEY_FILE.chmod(0o600)
        except OSError:
            pass  # Windows may not support POSIX permissions

        import logging

        logging.getLogger(__name__).warning(
            "AUDIT: HMAC key auto-generated at %s. "
            "For production use, provide an explicit secret_key and restrict "
            "file access to the audit_key file. On Windows, configure "
            "NTFS ACLs manually since POSIX chmod is not enforced.",
            _KEY_FILE,
        )
        return new_key.encode("utf-8")


# ---------------------------------------------------------------------------
# SignedAuditLog
# ---------------------------------------------------------------------------


class SignedAuditLog:
    """Append-only audit log with HMAC signatures and hash chaining.

    Every entry is signed with HMAC-SHA256 and includes the hash of the
    previous entry, creating a tamper-evident chain. If any entry is
    modified or deleted, the chain breaks and verification fails.

    Usage::

        log = SignedAuditLog(secret_key="your-secret-key")
        log.append(event_type="tool_call", actor="agent",
                   action="shell:exec", target="/bin/ls")
        log.save("audit.jsonl")

        # Later: verify integrity
        verifier = AuditVerifier(secret_key="your-secret-key")
        result = verifier.verify_file("audit.jsonl")
        print(result.valid)  # True if no tampering detected
    """

    def __init__(self, secret_key: str | None = None) -> None:
        self._key: bytes = _resolve_key(secret_key)
        self._entries: list[SignedLogEntry] = []
        self._sequence: int = 0
        self._lock: threading.Lock = threading.Lock()

    # -- Public API ---------------------------------------------------------

    def append(
        self,
        event_type: str,
        actor: str,
        action: str,
        target: str,
        risk_score: int = 0,
        outcome: str = "allowed",
        details: dict[str, Any] | None = None,
    ) -> SignedLogEntry:
        """Create, sign, and append a new log entry.

        Returns the newly created :class:`SignedLogEntry`.
        """
        with self._lock:
            prev_hash = self._prev_hash()
            entry_data = {
                "sequence": self._sequence,
                "timestamp": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "actor": actor,
                "action": action,
                "target": target,
                "risk_score": risk_score,
                "outcome": outcome,
                "details": details or {},
                "prev_hash": prev_hash,
            }
            sig = self._compute_signature(entry_data)
            entry_data["signature"] = sig
            entry = SignedLogEntry(**entry_data)
            self._entries.append(entry)
            self._sequence += 1
            return entry

    def entries(self) -> list[SignedLogEntry]:
        """Return a copy of all entries."""
        with self._lock:
            return list(self._entries)

    def save(self, path: Path | str) -> None:
        """Persist the log to a JSONL file (one JSON object per line)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(p, "w", encoding="utf-8") as f:
                for entry in self._entries:
                    f.write(json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    def load(self, path: Path | str) -> None:
        """Load entries from an existing JSONL log file.

        Replaces the current in-memory entries. The sequence counter is
        set to continue after the last loaded entry.
        """
        p = Path(path)
        entries: list[SignedLogEntry] = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(SignedLogEntry.from_dict(data))

        with self._lock:
            self._entries = entries
            self._sequence = entries[-1].sequence + 1 if entries else 0

    # -- Internal -----------------------------------------------------------

    def _prev_hash(self) -> str:
        """Return the hash that links to the previous entry."""
        if not self._entries:
            return "0" * 64  # genesis hash
        return self._compute_hash(self._entries[-1])

    def _compute_signature(self, entry_data: dict[str, Any]) -> str:
        """HMAC-SHA256 of the canonical JSON representation of entry data.

        ``entry_data`` must **not** contain the ``signature`` key.
        """
        canonical = json.dumps(entry_data, sort_keys=True, ensure_ascii=False)
        return hmac.new(self._key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _compute_hash(entry: SignedLogEntry) -> str:
        """SHA-256 hash of the full entry (including signature)."""
        canonical = json.dumps(entry.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
