"""Persistent Session Store -- stores session summaries for cross-session analysis.

Stores session summaries as individual JSON files in .aigis/sessions/,
one per session. Provides querying, pruning, and lifecycle management.

Academic basis:
  - arxiv 2604.02623: temporally decoupled memory poisoning attacks
  - Memory poisoning payloads planted in one session may activate days
    or weeks later, requiring persistent cross-session state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass
class SessionRecord:
    """Summary of a single session for cross-session analysis.

    Attributes:
        session_id: Unique identifier for the session.
        started_at: ISO 8601 timestamp when the session began.
        ended_at: ISO 8601 timestamp when the session ended, or None if active.
        total_actions: Total number of actions recorded in the session.
        resource_histogram: Mapping of resource type to access count.
        max_risk_score: Highest risk score observed in the session.
        alerts: Serialized alert summaries (DriftAlert / AnomalyAlert dicts).
        containment_max_level: Highest containment level reached.
        memory_writes: Memory entries created during this session.
        tools_used: Unique tool names used in the session.
    """

    session_id: str
    started_at: str  # ISO timestamp
    ended_at: str | None = None  # None if session is still active
    total_actions: int = 0
    resource_histogram: dict[str, int] = field(default_factory=dict)
    max_risk_score: int = 0
    alerts: list[dict] = field(default_factory=list)
    containment_max_level: str = "normal"
    memory_writes: list[dict] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SessionRecord:
        """Reconstruct a SessionRecord from a dict (loaded from JSON)."""
        return cls(
            session_id=data["session_id"],
            started_at=data["started_at"],
            ended_at=data.get("ended_at"),
            total_actions=data.get("total_actions", 0),
            resource_histogram=data.get("resource_histogram", {}),
            max_risk_score=data.get("max_risk_score", 0),
            alerts=data.get("alerts", []),
            containment_max_level=data.get("containment_max_level", "normal"),
            memory_writes=data.get("memory_writes", []),
            tools_used=data.get("tools_used", []),
        )


class SessionStore:
    """Persistent storage for session records (JSON file-based).

    Stores session summaries in .aigis/sessions/ as individual
    JSON files, one per session. Provides querying across sessions.

    Args:
        storage_dir: Directory for session JSON files.
            Defaults to ``.aigis/sessions``.
    """

    def __init__(self, storage_dir: Path | str = ".aigis/sessions") -> None:
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Return the file path for a session record.

        Sanitizes session_id to prevent path traversal, absolute path
        injection, null bytes, and symlink attacks.
        """
        import re as _re

        # Strip null bytes and control characters
        safe_id = session_id.replace("\x00", "")
        # Allow only alphanumeric, hyphens, underscores
        safe_id = _re.sub(r"[^a-zA-Z0-9_\-]", "_", safe_id)
        # Limit length to prevent filesystem issues
        safe_id = safe_id[:200] if len(safe_id) > 200 else safe_id
        if not safe_id:
            safe_id = "_empty_"
        candidate = self._dir / f"{safe_id}.json"
        # Final check: resolved path must be inside storage dir
        if not str(candidate.resolve()).startswith(str(self._dir.resolve())):
            raise ValueError(f"Session ID {session_id!r} resolves outside storage directory")
        return candidate

    def save_session(self, record: SessionRecord) -> None:
        """Persist a session record to disk.

        Overwrites any existing record with the same session_id.

        Args:
            record: The session record to save.
        """
        path = self._session_path(record.session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2, default=str)

    def load_session(self, session_id: str) -> SessionRecord | None:
        """Load a single session record by ID.

        Args:
            session_id: The session identifier.

        Returns:
            The SessionRecord, or None if not found.
        """
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return SessionRecord.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def list_sessions(
        self,
        since: str | None = None,
        limit: int = 100,
    ) -> list[SessionRecord]:
        """List session records, optionally filtered by time.

        Args:
            since: ISO 8601 timestamp. If provided, only return sessions
                that started at or after this time.
            limit: Maximum number of records to return (most recent first).

        Returns:
            List of SessionRecord instances, sorted by started_at descending.
        """
        cutoff: datetime | None = None
        if since is not None:
            try:
                cutoff = datetime.fromisoformat(since)
                # Ensure timezone-aware for comparison
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=UTC)
            except ValueError:
                cutoff = None

        records: list[SessionRecord] = []
        for path in self._dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                record = SessionRecord.from_dict(data)

                if cutoff is not None:
                    try:
                        started = datetime.fromisoformat(record.started_at)
                        if started.tzinfo is None:
                            started = started.replace(tzinfo=UTC)
                        if started < cutoff:
                            continue
                    except ValueError:
                        continue

                records.append(record)
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by started_at descending (most recent first)
        records.sort(key=lambda r: r.started_at, reverse=True)
        return records[:limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session record.

        Args:
            session_id: The session identifier.

        Returns:
            True if the record was deleted, False if not found.
        """
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def prune_old(self, max_age_days: int = 90) -> int:
        """Delete session records older than the specified age.

        Args:
            max_age_days: Maximum age in days. Records with started_at
                older than this are deleted.

        Returns:
            Number of records deleted.
        """
        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
        deleted = 0

        for path in list(self._dir.glob("*.json")):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                started_at = data.get("started_at", "")
                started = datetime.fromisoformat(started_at)
                if started.tzinfo is None:
                    started = started.replace(tzinfo=UTC)
                if started < cutoff:
                    path.unlink()
                    deleted += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return deleted
