"""MCP Security Scanner — advanced analysis for MCP tool definitions.

Provides rug-pull detection (version comparison), permission scope analysis,
server trust scoring, and comprehensive security reports for MCP tool
definitions. All functions use stdlib only — zero external dependencies.

Usage::

    from aigis.mcp_scanner import scan_mcp_server

    tools = [
        {"name": "calculator", "description": "Add two numbers", "inputSchema": {...}},
        {"name": "file_reader", "description": "Read any file on disk", ...},
    ]
    report = scan_mcp_server(tools, server_url="https://example.com/mcp")
    print(f"Trust: {report.trust_score}/100 ({report.trust_level})")
    for alert in report.rug_pull_alerts:
        print(f"  ! {alert.tool_name}: description changed")
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from aigis.scanner import ScanResult, scan_mcp_tool

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class MCPToolSnapshot:
    """Immutable snapshot of an MCP tool definition for version comparison."""

    tool_name: str
    server_url: str
    description: str
    input_schema: dict
    timestamp: str  # ISO 8601
    content_hash: str  # sha256 of description + schema JSON

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "server_url": self.server_url,
            "description": self.description,
            "input_schema": self.input_schema,
            "timestamp": self.timestamp,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MCPToolSnapshot:
        return cls(
            tool_name=data["tool_name"],
            server_url=data.get("server_url", ""),
            description=data.get("description", ""),
            input_schema=data.get("input_schema", {}),
            timestamp=data.get("timestamp", ""),
            content_hash=data.get("content_hash", ""),
        )


@dataclass
class MCPDiffResult:
    """Result of comparing two snapshots of the same MCP tool."""

    tool_name: str
    previous_snapshot: MCPToolSnapshot
    current_snapshot: MCPToolSnapshot
    description_changed: bool
    schema_changed: bool
    new_suspicious_patterns: list[dict] = field(default_factory=list)
    risk_delta: int = 0


@dataclass
class PermissionSummary:
    """Permission scope analysis of an MCP tool."""

    file_system: bool = False
    network: bool = False
    code_execution: bool = False
    sensitive_data: bool = False
    risk_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file_system": self.file_system,
            "network": self.network,
            "code_execution": self.code_execution,
            "sensitive_data": self.sensitive_data,
            "risk_factors": self.risk_factors,
        }


@dataclass
class MCPServerReport:
    """Comprehensive security report for all tools from an MCP server."""

    server_url: str
    tool_results: dict[str, ScanResult] = field(default_factory=dict)
    trust_score: int = 100
    trust_level: str = "trusted"
    permission_summaries: dict[str, PermissionSummary] = field(default_factory=dict)
    rug_pull_alerts: list[MCPDiffResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"MCP Server Security Report: {self.server_url or '(local)'}",
            "=" * 60,
            f"Trust Score: {self.trust_score}/100 ({self.trust_level.upper()})",
            "",
            "Tools:",
        ]
        for name, result in self.tool_results.items():
            level_tag = (
                "SAFE"
                if result.is_safe
                else (
                    "CRITICAL"
                    if result.is_blocked
                    else ("HIGH" if result.risk_level == "high" else "WARN")
                )
            )
            perms = self.permission_summaries.get(name)
            perm_str = ""
            if perms:
                active = []
                if perms.file_system:
                    active.append("file_system")
                if perms.network:
                    active.append("network")
                if perms.code_execution:
                    active.append("code_exec")
                if perms.sensitive_data:
                    active.append("sensitive_data")
                perm_str = f"  Permissions: {', '.join(active) or 'none'}"
            lines.append(f"  [{level_tag:>8}]  {name:<20} (score={result.risk_score}){perm_str}")
            for rule in result.matched_rules:
                lines.append(f"             - {rule.rule_name}: {rule.owasp_ref}")

        if self.rug_pull_alerts:
            lines.append("")
            lines.append("Rug Pull Alerts:")
            for alert in self.rug_pull_alerts:
                lines.append(f"  ! {alert.tool_name}: description changed since last scan")
                for pat in alert.new_suspicious_patterns:
                    lines.append(f"    New pattern: {pat.get('rule_name', 'unknown')}")

        # Permission summary
        perm_counts: dict[str, list[str]] = {
            "File System": [],
            "Network": [],
            "Code Execution": [],
            "Sensitive Data": [],
        }
        for name, perms in self.permission_summaries.items():
            if perms.file_system:
                perm_counts["File System"].append(name)
            if perms.network:
                perm_counts["Network"].append(name)
            if perms.code_execution:
                perm_counts["Code Execution"].append(name)
            if perms.sensitive_data:
                perm_counts["Sensitive Data"].append(name)

        if any(v for v in perm_counts.values()):
            lines.append("")
            lines.append("Permission Summary:")
            for perm_type, tools in perm_counts.items():
                count = len(tools)
                tool_list = f" ({', '.join(tools)})" if tools else ""
                lines.append(f"  {perm_type}: {count} tool(s){tool_list}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "server_url": self.server_url,
            "trust_score": self.trust_score,
            "trust_level": self.trust_level,
            "tools": {name: result.to_dict() for name, result in self.tool_results.items()},
            "permissions": {
                name: perms.to_dict() for name, perms in self.permission_summaries.items()
            },
            "rug_pull_alerts": [
                {
                    "tool_name": a.tool_name,
                    "description_changed": a.description_changed,
                    "schema_changed": a.schema_changed,
                    "risk_delta": a.risk_delta,
                    "new_patterns": a.new_suspicious_patterns,
                }
                for a in self.rug_pull_alerts
            ],
        }


# ---------------------------------------------------------------------------
# Snapshot management
# ---------------------------------------------------------------------------


def snapshot_tool(
    tool_def: dict,
    server_url: str = "",
    timestamp: str | None = None,
) -> MCPToolSnapshot:
    """Create a snapshot of an MCP tool definition."""
    import datetime

    name = tool_def.get("name", "unknown")
    description = tool_def.get("description", "")
    schema = tool_def.get("inputSchema", {})

    # Content hash for change detection
    hashable = json.dumps(
        {"description": description, "inputSchema": schema},
        sort_keys=True,
        ensure_ascii=False,
    )
    content_hash = hashlib.sha256(hashable.encode("utf-8")).hexdigest()

    ts = timestamp or datetime.datetime.now(datetime.UTC).isoformat()

    return MCPToolSnapshot(
        tool_name=name,
        server_url=server_url,
        description=description,
        input_schema=schema,
        timestamp=ts,
        content_hash=content_hash,
    )


def save_snapshots(snapshots: list[MCPToolSnapshot], path: str | Path) -> None:
    """Persist snapshots as JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [s.to_dict() for s in snapshots]
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_snapshots(path: str | Path) -> list[MCPToolSnapshot]:
    """Load snapshots from JSON file."""
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [MCPToolSnapshot.from_dict(d) for d in data]


# ---------------------------------------------------------------------------
# Rug pull detection
# ---------------------------------------------------------------------------


def detect_rug_pull(
    previous: MCPToolSnapshot,
    current: MCPToolSnapshot,
) -> MCPDiffResult | None:
    """Compare two snapshots and detect malicious changes.

    Returns None if no changes detected, or MCPDiffResult if the tool
    definition changed (especially if new suspicious patterns appear).
    """
    if previous.content_hash == current.content_hash:
        return None

    desc_changed = previous.description != current.description
    schema_changed = json.dumps(previous.input_schema, sort_keys=True) != json.dumps(
        current.input_schema, sort_keys=True
    )

    # Scan the new version for threats
    new_scan = scan_mcp_tool(
        {
            "name": current.tool_name,
            "description": current.description,
            "inputSchema": current.input_schema,
        }
    )
    old_scan = scan_mcp_tool(
        {
            "name": previous.tool_name,
            "description": previous.description,
            "inputSchema": previous.input_schema,
        }
    )

    # Find new suspicious patterns that weren't in the old version
    old_rule_ids = {r.rule_id for r in old_scan.matched_rules}
    new_patterns = [
        {"rule_id": r.rule_id, "rule_name": r.rule_name, "category": r.category}
        for r in new_scan.matched_rules
        if r.rule_id not in old_rule_ids
    ]

    risk_delta = new_scan.risk_score - old_scan.risk_score

    if not desc_changed and not schema_changed and not new_patterns:
        return None

    return MCPDiffResult(
        tool_name=current.tool_name,
        previous_snapshot=previous,
        current_snapshot=current,
        description_changed=desc_changed,
        schema_changed=schema_changed,
        new_suspicious_patterns=new_patterns,
        risk_delta=risk_delta,
    )


# ---------------------------------------------------------------------------
# Permission analysis
# ---------------------------------------------------------------------------

# Keywords for each permission category
_FILE_SYSTEM_KEYWORDS = [
    "read_file",
    "write_file",
    "delete_file",
    "list_directory",
    "file_path",
    "directory",
    "folder",
    "mkdir",
    "rmdir",
    "open_file",
    "save_file",
    "upload",
    "download",
    "~/.ssh",
    "~/.aws",
    ".env",
    "/etc/",
]

_NETWORK_KEYWORDS = [
    "http",
    "https",
    "url",
    "fetch",
    "request",
    "api",
    "send_email",
    "webhook",
    "socket",
    "connect",
    "download",
    "upload",
    "post",
    "get_url",
]

_CODE_EXEC_KEYWORDS = [
    "exec",
    "eval",
    "execute",
    "run_command",
    "shell",
    "subprocess",
    "os.system",
    "bash",
    "cmd",
    "run_code",
    "compile",
    "interpret",
]

_SENSITIVE_DATA_KEYWORDS = [
    "credential",
    "secret",
    "password",
    "token",
    "api_key",
    "private_key",
    "ssh_key",
    "aws_key",
    "database",
    "connection_string",
    "auth",
    "session",
]


def analyze_permissions(tool_def: dict) -> PermissionSummary:
    """Analyze what resources/permissions an MCP tool claims to access."""
    # Combine all text from the tool definition
    parts: list[str] = []
    parts.append(tool_def.get("name", ""))
    parts.append(tool_def.get("description", ""))
    schema = tool_def.get("inputSchema", {})
    for _prop_name, prop_def in schema.get("properties", {}).items():
        parts.append(_prop_name)
        if isinstance(prop_def, dict) and "description" in prop_def:
            parts.append(prop_def["description"])
    text = " ".join(parts).lower()

    summary = PermissionSummary()

    for kw in _FILE_SYSTEM_KEYWORDS:
        if kw.lower() in text:
            summary.file_system = True
            summary.risk_factors.append(f"file_system: {kw}")
            break

    for kw in _NETWORK_KEYWORDS:
        if kw.lower() in text:
            summary.network = True
            summary.risk_factors.append(f"network: {kw}")
            break

    for kw in _CODE_EXEC_KEYWORDS:
        if kw.lower() in text:
            summary.code_execution = True
            summary.risk_factors.append(f"code_execution: {kw}")
            break

    for kw in _SENSITIVE_DATA_KEYWORDS:
        if kw.lower() in text:
            summary.sensitive_data = True
            summary.risk_factors.append(f"sensitive_data: {kw}")
            break

    return summary


# ---------------------------------------------------------------------------
# Server trust scoring
# ---------------------------------------------------------------------------


def score_server_trust(
    tool_results: dict[str, ScanResult],
    permission_summaries: dict[str, PermissionSummary] | None = None,
) -> tuple[int, str]:
    """Compute aggregate trust score for all tools from one MCP server.

    Returns:
        Tuple of (trust_score 0-100, trust_level str).
        Higher score = more trusted.
    """
    if not tool_results:
        return 100, "trusted"

    # Sum risk scores across all tools
    total_risk = sum(r.risk_score for r in tool_results.values())
    # Weight by number of tools
    avg_risk = total_risk / len(tool_results)
    # Factor in permission scope
    permission_penalty = 0
    if permission_summaries:
        for perms in permission_summaries.values():
            if perms.code_execution:
                permission_penalty += 10
            if perms.sensitive_data:
                permission_penalty += 5
            if perms.file_system:
                permission_penalty += 3
            if perms.network:
                permission_penalty += 2

    trust_score = max(0, min(100, 100 - int(avg_risk) - permission_penalty))

    if trust_score >= 70:
        trust_level = "trusted"
    elif trust_score >= 40:
        trust_level = "suspicious"
    else:
        trust_level = "dangerous"

    return trust_score, trust_level


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def scan_mcp_server(
    tools: list[dict],
    server_url: str = "",
    snapshot_dir: str | Path | None = None,
) -> MCPServerReport:
    """Scan all tools from an MCP server and produce a comprehensive report.

    Args:
        tools: List of MCP tool definition dicts.
        server_url: Optional URL of the MCP server (metadata).
        snapshot_dir: Directory for rug-pull snapshot storage.
            If provided, compares against previous snapshots and saves new ones.

    Returns:
        MCPServerReport with per-tool results, trust score, permissions,
        and rug-pull alerts.
    """
    # Scan each tool
    tool_results: dict[str, ScanResult] = {}
    permission_summaries: dict[str, PermissionSummary] = {}
    current_snapshots: list[MCPToolSnapshot] = []

    for i, tool in enumerate(tools):
        name = tool.get("name", f"tool_{i}")
        tool_results[name] = scan_mcp_tool(tool)
        permission_summaries[name] = analyze_permissions(tool)
        current_snapshots.append(snapshot_tool(tool, server_url))

    # Rug pull detection
    rug_pull_alerts: list[MCPDiffResult] = []
    if snapshot_dir:
        snapshot_path = Path(snapshot_dir)
        # Use server URL hash for filename (or 'local' for no URL)
        server_hash = hashlib.sha256((server_url or "local").encode()).hexdigest()[:12]
        snapshot_file = snapshot_path / f"mcp_{server_hash}.json"

        previous_snapshots = load_snapshots(snapshot_file)
        prev_by_name = {s.tool_name: s for s in previous_snapshots}

        for current in current_snapshots:
            prev = prev_by_name.get(current.tool_name)
            if prev:
                diff = detect_rug_pull(prev, current)
                if diff:
                    rug_pull_alerts.append(diff)

        # Save current snapshots
        save_snapshots(current_snapshots, snapshot_file)

    # Trust score
    trust_score, trust_level = score_server_trust(tool_results, permission_summaries)

    return MCPServerReport(
        server_url=server_url,
        tool_results=tool_results,
        trust_score=trust_score,
        trust_level=trust_level,
        permission_summaries=permission_summaries,
        rug_pull_alerts=rug_pull_alerts,
    )


# ---------------------------------------------------------------------------
# Stage-2 / Stage-3 scanners — MSB (arxiv:2510.15994, Oct 2025) classifies
# MCP attacks across three stages: tool *discovery* (already handled by
# scan_mcp_server above), tool *invocation* (runtime args), and tool
# *response* (returned payload). The invocation/response surfaces are
# where indirect-injection and puppet attacks actually fire — definitions
# alone cannot catch them.
#
# Mechanism: both scanners defer to the same pattern engine used for
# user input, treating tool arguments and tool responses as untrusted
# textual surfaces. Any hit is reported as an MCPStageFinding that a
# caller can gate on before forwarding to the LLM.
#
# Outcome: `aig mcp` now covers the full MSB 3-stage surface; puppet
# attacks that plant instructions in arg strings or rigged tool responses
# are detected instead of silently flowing back to the agent.
# ---------------------------------------------------------------------------


@dataclass
class MCPStageFinding:
    """A single invocation/response-stage finding."""

    stage: str  # "invocation" | "response"
    tool_name: str
    source_field: str  # which arg/field carried the payload
    risk_score: int
    is_blocked: bool
    matched_rule_ids: list[str]
    evidence: str  # short excerpt of the offending text


def _flatten_json_strings(obj: object, prefix: str = "") -> list[tuple[str, str]]:
    """Yield (path, string_value) pairs from an arbitrary JSON-like value."""
    out: list[tuple[str, str]] = []
    if isinstance(obj, str):
        out.append((prefix or "$", obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_flatten_json_strings(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_flatten_json_strings(v, f"{prefix}[{i}]"))
    return out


def _scan_text_field(
    tool_name: str, stage: str, field_path: str, text: str
) -> MCPStageFinding | None:
    """Run the shared scanner over one textual field."""
    if not text:
        return None
    from aigis.scanner import scan as _scan_input

    result = _scan_input(text)
    if result.is_safe:
        return None
    return MCPStageFinding(
        stage=stage,
        tool_name=tool_name,
        source_field=field_path,
        risk_score=result.risk_score,
        is_blocked=result.is_blocked,
        matched_rule_ids=[r.rule_id for r in result.matched_rules],
        evidence=text[:200],
    )


def scan_invocation(tool_name: str, arguments: dict | list | str | None) -> list[MCPStageFinding]:
    """Scan the *arguments* supplied to an MCP tool call.

    Catches prompt-injection / jailbreak / PII payloads smuggled through
    tool args — the MSB "tool invocation" attack surface.
    """
    findings: list[MCPStageFinding] = []
    if arguments is None:
        return findings
    for path, text in _flatten_json_strings(arguments):
        f = _scan_text_field(tool_name, "invocation", path, text)
        if f is not None:
            findings.append(f)
    return findings


def scan_response(tool_name: str, response: dict | list | str | None) -> list[MCPStageFinding]:
    """Scan the payload *returned* by an MCP tool call.

    Defends against puppet / rug-pull attacks that embed instructions in a
    tool's response so the calling agent re-executes them — the MSB
    "response handling" attack surface.
    """
    findings: list[MCPStageFinding] = []
    if response is None:
        return findings
    for path, text in _flatten_json_strings(response):
        f = _scan_text_field(tool_name, "response", path, text)
        if f is not None:
            findings.append(f)
    return findings


# ---------------------------------------------------------------------------
# Tool-selection bias detection — ToolHijacker / ToolTweak
#
# Two recent papers show that an attacker who can publish a tool description
# (or rename a tool) can hijack agent tool selection without any prompt
# injection in the user's message:
#
#   * "Prompt Injection Attack to Tool Selection in LLM Agents", Wang et al.,
#     NDSS 2026 (arxiv:2504.19793). ToolHijacker reaches 96.7% attack
#     success rate on MetaTool with a no-box black-box attack: a malicious
#     tool description carries a Retrieval-optimized sequence (R) that
#     inflates semantic similarity to many target tasks, plus a
#     Selection-optimized sequence (S) that pushes the LLM to pick this
#     tool over all alternatives.
#   * "ToolTweak: An Attack on Tool Selection in LLM-based Agents",
#     arxiv:2510.02554. By iteratively manipulating tool names AND
#     descriptions, adversaries lift selection rates from ~20% baseline
#     to as high as 81%.
#
# Both attacks rely on linguistic patterns that look unnatural to a human
# reviewer but slip past LLMs. None of the existing aigis detectors target
# this surface — patterns.py looks for jailbreaks/PII, mcp_scanner's
# rug-pull catches *changes*, but a hostile description is dangerous
# the very first time a user installs the server.
#
# Heuristics (zero-dep, deterministic):
#   H1  Selection-forcing imperatives ("always use this tool",
#       "preferred over", "must use first", ...).
#   H2  Self-promotion superlatives at unnatural density ("the only",
#       "100% accurate", "the most reliable").
#   H3  Comparative dismissal — explicit references to other named tools
#       as deprecated/inferior/forbidden.
#   H4  Hidden role-token injection in the description ("system:",
#       "<system>", "as an ai assistant you must"). Reuses
#       structured_query findings semantics.
#   H5  Keyword stuffing — abnormally high count of short repeated task
#       phrases ("for files for data for web for code for ...") which is
#       characteristic of the R sequence in ToolHijacker.
#
# Each hit contributes a fixed weight to a single `bias_score` (0..100).
# Above 30 we surface a SelectionBiasFinding; above 60 we mark
# `is_blocked=True`.
# ---------------------------------------------------------------------------


@dataclass
class SelectionBiasFinding:
    """Indicates a tool description is engineered to hijack agent selection."""

    tool_name: str
    bias_score: int
    is_blocked: bool
    triggered_heuristics: list[str]  # H1..H5
    evidence: list[str]  # short excerpt per trigger

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "bias_score": self.bias_score,
            "is_blocked": self.is_blocked,
            "triggered_heuristics": self.triggered_heuristics,
            "evidence": self.evidence,
        }


# Compile once at import time.
_BIAS_H1_FORCING = re.compile(
    r"\b("
    r"always\s+(?:use|select|choose|prefer|pick)\s+this"
    r"|use\s+this\s+tool\s+(?:first|always|every\s+time|by\s+default)"
    r"|must\s+(?:use|select|choose|invoke|call)\s+this"
    r"|preferred\s+over\s+(?:all|every|any|other)"
    r"|best\s+(?:for|tool\s+for)\s+(?:any|every|all)\s+(?:task|query|request)"
    r"|the\s+only\s+(?:correct|valid|right|reliable)\s+(?:choice|option|tool)"
    r"|never\s+use\s+(?:the\s+)?(?:other|alternative)"
    r"|do\s+not\s+use\s+(?:any\s+)?other\s+tool"
    r")\b",
    re.IGNORECASE,
)
_BIAS_H2_SUPERLATIVES = re.compile(
    r"\b("
    r"100%\s*(?:accurate|reliable|correct|precise)"
    r"|the\s+most\s+(?:accurate|reliable|trusted|correct|advanced)"
    r"|the\s+(?:only|sole|exclusive)\s+(?:way|method|tool|solution)"
    r"|guaranteed\s+to\s+(?:work|succeed|return|provide)"
    r"|never\s+fails"
    r"|always\s+returns\s+(?:the\s+)?correct"
    r")\b",
    re.IGNORECASE,
)
_BIAS_H3_DISMISSAL = re.compile(
    r"\b("
    r"other\s+tools\s+(?:are\s+)?(?:deprecated|broken|unreliable|outdated|inferior|obsolete)"
    r"|do\s+not\s+(?:call|invoke|use|select)\s+(?:the\s+)?(?:other|alternative)"
    r"|ignore\s+(?:the\s+)?(?:other|alternative)\s+tools?"
    r"|(?:other|alternative)\s+tools?\s+(?:should\s+(?:not|never)|must\s+(?:not|never))\s+be"
    r"|replaces?\s+(?:all\s+)?(?:other|previous|legacy)\s+tools?"
    r")\b",
    re.IGNORECASE,
)
_BIAS_H4_ROLE_TOKENS = re.compile(
    r"(?:^|[\n\r\s])("
    r"system\s*:"
    r"|</?(?:system|user|assistant|tool)\s*>"
    r"|\[(?:INST|/INST|SYSTEM|USER|ASSISTANT)\]"
    r"|<\|(?:im_start|im_end|system|user|assistant)\|>"
    r"|as\s+an\s+ai\s+assistant[, ]?\s+you\s+must"
    r"|you\s+are\s+(?:now\s+)?(?:a|an)\s+(?:helpful|capable)"
    r")",
    re.IGNORECASE,
)
# H5: keyword-stuffing detector. Counts the number of "for X" clauses or
# short comma-separated task lists; thresholding catches the R sequence
# without flagging legitimately broad utility tools.
_BIAS_H5_FOR_CLAUSE = re.compile(r"\bfor\s+\w{3,12}\b", re.IGNORECASE)


def detect_selection_bias(tool_def: dict, threshold: int = 30) -> SelectionBiasFinding | None:
    """Inspect a single MCP tool definition for selection-hijacking patterns.

    Args:
        tool_def: A dict with at least ``name`` and ``description`` keys
            (matching the MCP tool definition shape).
        threshold: Minimum bias score required to surface a finding.

    Returns:
        ``SelectionBiasFinding`` when the score crosses the threshold, else
        ``None``. ``is_blocked`` becomes ``True`` for scores >= 60.
    """
    name = str(tool_def.get("name", "unknown"))
    description = str(tool_def.get("description", ""))
    # Combine name and description: ToolTweak attacks often hijack via name.
    combined = f"{name}\n{description}"

    triggered: list[str] = []
    evidence: list[str] = []
    score = 0

    # H1 — selection-forcing imperatives are the strongest single signal.
    h1_matches = _BIAS_H1_FORCING.findall(combined)
    if h1_matches:
        triggered.append("H1")
        evidence.append(f"forcing: {h1_matches[0] if h1_matches else ''}"[:200])
        score += 35

    # H2 — superlatives.
    h2_matches = _BIAS_H2_SUPERLATIVES.findall(combined)
    if h2_matches:
        triggered.append("H2")
        evidence.append(f"superlative: {h2_matches[0]}"[:200])
        score += 15

    # H3 — comparative dismissal of other tools.
    if _BIAS_H3_DISMISSAL.search(combined):
        triggered.append("H3")
        m = _BIAS_H3_DISMISSAL.search(combined)
        evidence.append(f"dismissal: {m.group(0) if m else ''}"[:200])
        score += 30

    # H4 — hidden role tokens / fake system prompts.
    if _BIAS_H4_ROLE_TOKENS.search(combined):
        triggered.append("H4")
        m = _BIAS_H4_ROLE_TOKENS.search(combined)
        evidence.append(f"role_token: {m.group(0) if m else ''}"[:200])
        score += 35

    # H5 — keyword stuffing. A natural description rarely has more than
    # ~3 "for X" clauses; ToolHijacker R sequences typically pile up many.
    h5_count = len(_BIAS_H5_FOR_CLAUSE.findall(description))
    if h5_count >= 6:
        triggered.append("H5")
        evidence.append(f"keyword_stuffing: {h5_count} 'for X' clauses")
        # Scale the contribution but cap it so a long legitimate description
        # of a genuine generic tool doesn't auto-block.
        score += min(20, (h5_count - 5) * 4)

    score = min(100, score)
    if score < threshold:
        return None

    return SelectionBiasFinding(
        tool_name=name,
        bias_score=score,
        is_blocked=score >= 60,
        triggered_heuristics=triggered,
        evidence=evidence,
    )


def scan_selection_bias(tools: list[dict], threshold: int = 30) -> list[SelectionBiasFinding]:
    """Apply ``detect_selection_bias`` to every tool in a list."""
    out: list[SelectionBiasFinding] = []
    for tool in tools:
        f = detect_selection_bias(tool, threshold=threshold)
        if f is not None:
            out.append(f)
    return out
