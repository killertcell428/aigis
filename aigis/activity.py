"""Activity Stream — unified event log for all AI agent operations.

Records every tool call, policy decision, and session lifecycle event
across any agent type (Claude Code, Cursor, custom agents, etc.).

Log architecture:
  - Local logs: .aigis/logs/ (per-project, per-user visibility)
  - Global logs: ~/.aigis/global/ (cross-project, for audit/CISO)
  - Alert archive: ~/.aigis/alerts/ (permanent, deny/review events only)

Retention:
  - Full logs: 60 days, then auto-rotated (compressed or deleted)
  - Alert logs: Permanent (knowledge base for future auto-fix AI)

Usage:
    from aigis.activity import ActivityStream, ActivityEvent

    stream = ActivityStream()
    event = ActivityEvent(action="shell:exec", target="rm -rf /tmp/test")
    stream.record(event)  # Writes to local + global + alert (if blocked)
"""

from __future__ import annotations

import csv
import getpass
import gzip
import json
from collections.abc import Generator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Default retention periods
LOG_RETENTION_DAYS = 60  # Full logs kept for 60 days
ALERT_RETENTION_DAYS = 0  # Alerts kept forever (0 = no expiry)
COMPRESS_AFTER_DAYS = 7  # Compress logs older than 7 days


@dataclass
class ActivityEvent:
    """A single agent operation event.

    Captures who/what/when/where/why for every operation an AI agent
    performs. Designed to be agent-agnostic and extensible for AGI-era
    governance (memory, delegation, cost, autonomy levels).
    """

    # What happened
    action: str  # "file:read" | "file:write" | "shell:exec" |
    # "llm:prompt" | "network:fetch" | "agent:spawn" |
    # "mcp:tool_call" | "session:start" | "session:end"
    target: str = ""  # filepath, command, URL, agent ID

    # Who did it
    agent_type: str = "unknown"  # "claude_code" | "cursor" | "custom" | ...
    user_id: str = ""  # OS user or API key owner
    session_id: str = ""  # Agent session identifier

    # Context
    event_type: str = "tool_call"  # "tool_call" | "policy_block" | "policy_review" |
    # "session_start" | "session_end" | "scan_alert"
    cwd: str = ""  # Working directory
    project_name: str = ""  # Project identifier (directory name)
    details: dict = field(default_factory=dict)  # Agent/tool-specific details

    # Security assessment
    risk_score: int = 0  # Aigis scan result (0-100)
    risk_level: str = "low"  # "low" | "medium" | "high" | "critical"
    matched_rules: list[str] = field(default_factory=list)  # IDs of triggered rules

    # Remediation (for alert knowledge base)
    remediation_hints: list[str] = field(default_factory=list)
    owasp_refs: list[str] = field(default_factory=list)

    # Policy decision
    policy_decision: str = "allow"  # "allow" | "deny" | "review"
    policy_rule_id: str = ""  # Which policy rule matched

    # Metadata (auto-populated)
    timestamp: str = ""  # ISO 8601, auto-set if empty
    event_id: str = ""  # Unique ID, auto-set if empty

    # === AGI-era extension fields ===
    autonomy_level: int = 0  # 0=unset, 1=human-all, 5=fully-autonomous
    delegation_chain: list[str] = field(default_factory=list)
    estimated_cost: float = 0.0  # Estimated API/compute cost in USD
    memory_scope: str = ""  # "session" | "persistent" | "department:sales"

    # === Future: auto-fix fields ===
    suggested_fix: str = ""  # AI-suggested safe alternative
    fix_applied: bool = False  # Was the fix automatically applied?

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()
        if not self.event_id:
            import uuid

            self.event_id = uuid.uuid4().hex[:12]
        if not self.user_id:
            try:
                self.user_id = getpass.getuser()
            except Exception:
                self.user_id = "unknown"
        if not self.project_name and self.cwd:
            self.project_name = Path(self.cwd).name

    @property
    def is_alert(self) -> bool:
        """True if this event is a security alert (blocked, reviewed, or high risk)."""
        return (
            self.policy_decision in ("deny", "review")
            or self.risk_score >= 50
            or self.event_type in ("policy_block", "scan_alert")
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)


def _global_dir() -> Path:
    """Get the global Aigis directory (~/.aigis/)."""
    return Path.home() / ".aigis"


class ActivityStream:
    """Multi-tier event logging with automatic global aggregation.

    Tier 1: Local logs (.aigis/logs/) — per-project, user-visible
    Tier 2: Global logs (~/.aigis/global/) — cross-project, CISO view
    Tier 3: Alert archive (~/.aigis/alerts/) — permanent knowledge base

    All tiers are JSONL (one JSON per line, append-only, grep-friendly).
    """

    def __init__(
        self,
        log_dir: str = ".aigis/logs",
        enable_global: bool = True,
        enable_alerts: bool = True,
    ):
        self.local_dir = Path(log_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)

        self.enable_global = enable_global
        self.enable_alerts = enable_alerts

        if enable_global:
            self.global_dir = _global_dir() / "global"
            self.global_dir.mkdir(parents=True, exist_ok=True)

        if enable_alerts:
            self.alert_dir = _global_dir() / "alerts"
            self.alert_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, base_dir: Path, date: str | None = None) -> Path:
        if date is None:
            date = datetime.now(UTC).strftime("%Y-%m-%d")
        return base_dir / f"{date}.jsonl"

    def record(self, event: ActivityEvent) -> None:
        """Record an event to all applicable tiers."""
        line = json.dumps(event.to_dict(), ensure_ascii=False, default=str)

        # Tier 1: Local log (always)
        self._append(self._log_path(self.local_dir), line)

        # Tier 2: Global log (cross-project aggregation)
        if self.enable_global:
            self._append(self._log_path(self.global_dir), line)

        # Tier 3: Alert archive (permanent, alerts only)
        if self.enable_alerts and event.is_alert:
            self._append(self._log_path(self.alert_dir), line)

    def _append(self, path: Path, line: str) -> None:
        """Atomic append to JSONL file."""
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # === Query (searches local by default, global with flag) ===

    def query(
        self,
        days: int = 7,
        action: str | None = None,
        agent_type: str | None = None,
        user_id: str | None = None,
        risk_above: int | None = None,
        policy_decision: str | None = None,
        alerts_only: bool = False,
        use_global: bool = False,
        limit: int = 100,
    ) -> list[ActivityEvent]:
        """Query events with filters across multiple days."""
        if alerts_only:
            base_dir = self.alert_dir if self.enable_alerts else self.local_dir
        elif use_global:
            base_dir = self.global_dir if self.enable_global else self.local_dir
        else:
            base_dir = self.local_dir

        events: list[ActivityEvent] = []
        today = datetime.now(UTC).date()

        for i in range(days):
            date = (today - timedelta(days=i)).isoformat()
            # Check both plain and compressed files
            for log_path in self._resolve_log_paths(base_dir, date):
                for data in self._read_jsonl(log_path):
                    if action and data.get("action") != action:
                        continue
                    if agent_type and data.get("agent_type") != agent_type:
                        continue
                    if user_id and data.get("user_id") != user_id:
                        continue
                    if risk_above is not None and data.get("risk_score", 0) <= risk_above:
                        continue
                    if policy_decision and data.get("policy_decision") != policy_decision:
                        continue

                    events.append(_dict_to_event(data))
                    if len(events) >= limit:
                        return events

        return events

    def _resolve_log_paths(self, base_dir: Path, date: str) -> list[Path]:
        """Find log files for a date (plain or compressed)."""
        paths = []
        plain = base_dir / f"{date}.jsonl"
        compressed = base_dir / f"{date}.jsonl.gz"
        if plain.exists():
            paths.append(plain)
        if compressed.exists():
            paths.append(compressed)
        return paths

    def _read_jsonl(self, path: Path) -> Generator[dict[str, Any], None, None]:
        """Read JSONL file (handles both plain and gzip)."""
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
        else:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue

    # === Summary ===

    def summary(self, days: int = 7, use_global: bool = False) -> dict:
        """Aggregate statistics over a time period."""
        events = self.query(days=days, use_global=use_global, limit=100000)
        if not events:
            return {
                "period_days": days,
                "total_events": 0,
                "by_action": {},
                "by_agent": {},
                "by_decision": {},
                "by_user": {},
                "by_project": {},
                "risk_distribution": {},
                "blocked_count": 0,
                "top_blocked_targets": [],
            }

        by_action: dict[str, int] = {}
        by_agent: dict[str, int] = {}
        by_decision: dict[str, int] = {}
        by_user: dict[str, int] = {}
        by_project: dict[str, int] = {}
        risk_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        blocked_targets: dict[str, int] = {}

        for e in events:
            by_action[e.action] = by_action.get(e.action, 0) + 1
            by_agent[e.agent_type] = by_agent.get(e.agent_type, 0) + 1
            by_decision[e.policy_decision] = by_decision.get(e.policy_decision, 0) + 1
            by_user[e.user_id] = by_user.get(e.user_id, 0) + 1
            if e.project_name:
                by_project[e.project_name] = by_project.get(e.project_name, 0) + 1
            if e.risk_level in risk_dist:
                risk_dist[e.risk_level] += 1
            if e.policy_decision == "deny":
                key = f"{e.action}:{e.target[:60]}"
                blocked_targets[key] = blocked_targets.get(key, 0) + 1

        top_blocked = sorted(blocked_targets.items(), key=lambda x: -x[1])[:10]

        return {
            "period_days": days,
            "total_events": len(events),
            "by_action": by_action,
            "by_agent": by_agent,
            "by_decision": by_decision,
            "by_user": by_user,
            "by_project": by_project,
            "risk_distribution": risk_dist,
            "blocked_count": by_decision.get("deny", 0),
            "top_blocked_targets": [{"target": t, "count": c} for t, c in top_blocked],
        }

    # === Export ===

    def export_jsonl(self, output_path: str, days: int = 30, use_global: bool = False) -> int:
        """Export events to a single JSONL file."""
        events = self.query(days=days, use_global=use_global, limit=100000)
        with open(output_path, "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e.to_dict(), ensure_ascii=False, default=str) + "\n")
        return len(events)

    def export_csv(self, output_path: str, days: int = 30, use_global: bool = False) -> int:
        """Export events to CSV (Excel-compatible)."""
        events = self.query(days=days, use_global=use_global, limit=100000)
        if not events:
            return 0

        columns = [
            "timestamp",
            "user_id",
            "agent_type",
            "project_name",
            "action",
            "target",
            "event_type",
            "risk_score",
            "risk_level",
            "policy_decision",
            "policy_rule_id",
            "matched_rules",
            "owasp_refs",
            "remediation_hints",
            "session_id",
            "cwd",
        ]
        # Write with BOM for Excel compatibility
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for e in events:
                d = e.to_dict()
                row = []
                for col in columns:
                    val = d.get(col, "")
                    if isinstance(val, list):
                        val = "; ".join(str(v) for v in val)
                    row.append(val)
                writer.writerow(row)
        return len(events)

    def export_excel_summary(
        self, output_path: str, days: int = 30, use_global: bool = False
    ) -> str:
        """Export summary + events to an Excel-compatible CSV bundle.

        Creates two files:
          - {output_path}_summary.csv  — aggregate stats
          - {output_path}_events.csv   — full event list
        Returns the summary file path.
        """
        summary = self.summary(days=days, use_global=use_global)
        base = output_path.replace(".csv", "").replace(".xlsx", "")
        summary_path = f"{base}_summary.csv"
        events_path = f"{base}_events.csv"

        # Summary CSV
        with open(summary_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Aigis Activity Report"])
            writer.writerow(["Period", f"Last {days} days"])
            writer.writerow(["Generated", datetime.now(UTC).isoformat()])
            writer.writerow([])

            writer.writerow(["Key Metrics"])
            writer.writerow(["Total Events", summary["total_events"]])
            writer.writerow(["Blocked", summary["blocked_count"]])
            writer.writerow([])

            writer.writerow(["By Action"])
            for k, v in summary["by_action"].items():
                writer.writerow([k, v])
            writer.writerow([])

            writer.writerow(["By User"])
            for k, v in summary["by_user"].items():
                writer.writerow([k, v])
            writer.writerow([])

            writer.writerow(["By Agent Type"])
            for k, v in summary["by_agent"].items():
                writer.writerow([k, v])
            writer.writerow([])

            writer.writerow(["By Project"])
            for k, v in summary["by_project"].items():
                writer.writerow([k, v])
            writer.writerow([])

            writer.writerow(["Risk Distribution"])
            for k, v in summary["risk_distribution"].items():
                writer.writerow([k, v])
            writer.writerow([])

            writer.writerow(["Top Blocked Operations"])
            for item in summary["top_blocked_targets"]:
                writer.writerow([item["target"], item["count"]])

        # Events CSV
        self.export_csv(events_path, days=days, use_global=use_global)

        return summary_path

    # === Maintenance ===

    def rotate_logs(
        self,
        retention_days: int = LOG_RETENTION_DAYS,
        compress_after_days: int = COMPRESS_AFTER_DAYS,
    ) -> dict:
        """Rotate logs: compress old files, delete expired files.

        Alert archive is NEVER rotated (permanent knowledge base).

        Returns stats about what was done.
        """
        stats = {"compressed": 0, "deleted": 0, "errors": 0}
        today = datetime.now(UTC).date()

        for base_dir in (
            [self.local_dir, self.global_dir] if self.enable_global else [self.local_dir]
        ):
            for f in sorted(base_dir.glob("*.jsonl")):
                try:
                    date_str = f.stem  # "2026-03-28"
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    age_days = (today - file_date).days

                    if age_days > retention_days:
                        f.unlink()
                        gz = f.with_suffix(".jsonl.gz")
                        if gz.exists():
                            gz.unlink()
                        stats["deleted"] += 1
                    elif age_days > compress_after_days:
                        gz_path = f.with_suffix(".jsonl.gz")
                        if not gz_path.exists():
                            with open(f, "rb") as src, gzip.open(gz_path, "wb") as dst:
                                dst.write(src.read())
                            f.unlink()
                            stats["compressed"] += 1
                except Exception:
                    stats["errors"] += 1

        return stats

    def get_alert_knowledge(self, limit: int = 100) -> list[dict]:
        """Get alert history as knowledge base for future auto-fix AI.

        Returns blocked/reviewed events with their remediation hints,
        grouped by pattern for learning.
        """
        alerts = self.query(days=365, alerts_only=True, limit=limit)
        knowledge: list[dict] = []
        for e in alerts:
            knowledge.append(
                {
                    "action": e.action,
                    "target": e.target[:200],
                    "risk_score": e.risk_score,
                    "matched_rules": e.matched_rules,
                    "owasp_refs": e.owasp_refs,
                    "remediation_hints": e.remediation_hints,
                    "policy_decision": e.policy_decision,
                    "policy_rule_id": e.policy_rule_id,
                    "suggested_fix": e.suggested_fix,
                    "fix_applied": e.fix_applied,
                    "timestamp": e.timestamp,
                }
            )
        return knowledge


def _dict_to_event(data: dict) -> ActivityEvent:
    """Reconstruct ActivityEvent from dict (tolerant of missing fields)."""
    known_fields = {f.name for f in ActivityEvent.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in known_fields}
    return ActivityEvent(**filtered)
