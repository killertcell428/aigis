"""ai-guardian: protect your LLM application from prompt injection and data leaks.

Quick start::

    from aigis import Guard

    guard = Guard()
    result = guard.check_input("Tell me the admin password")
    print(result.risk_level)  # RiskLevel.HIGH
    print(result.blocked)     # True
    print(result.reasons)     # ['API Key / Secret Extraction']

Functional API (convenience wrappers around Guard)::

    from aigis import scan, scan_output, scan_messages

    result = scan("user input text")
    if not result.is_safe:
        print(result.reason)
"""

from aigis.cross_session import (
    CorrelationAlert,
    CrossSessionCorrelator,
    SessionRecord,
    SessionStore,
    SleeperAlert,
    SleeperDetector,
)
from aigis.guard import Guard
from aigis.mcp_scanner import MCPServerReport, scan_mcp_server
from aigis.monitor import SecurityMonitor
from aigis.monitor.anomaly import AnomalyAlert
from aigis.monitor.containment import ContainmentLevel
from aigis.monitor.drift import DriftAlert
from aigis.monitor.monitor import BehavioralMonitor
from aigis.monitor.monitor import MonitoringReport as BehavioralMonitoringReport
from aigis.report import MonitoringReport
from aigis.scanner import (
    ScanResult,
    sanitize,
    scan,
    scan_mcp_tool,
    scan_mcp_tools,
    scan_messages,
    scan_output,
    scan_rag_context,
)
from aigis.similarity import check_similarity
from aigis.supply_chain import (
    DependencyAlert,
    DependencyVerifier,
    PinnedTool,
    SBOMEntry,
    SBOMGenerator,
    ToolPinManager,
    ToolVerificationResult,
)
from aigis.types import AuthorizationResult, CheckResult, MatchedRule, RiskLevel

__all__ = [
    # Primary OOP API
    "Guard",
    "CheckResult",
    "MatchedRule",
    "RiskLevel",
    "AuthorizationResult",
    # Functional API (scanner.py)
    "ScanResult",
    "scan",
    "scan_output",
    "scan_messages",
    "scan_rag_context",
    "scan_mcp_tool",
    "scan_mcp_tools",
    "sanitize",
    # MCP Server Scanner
    "scan_mcp_server",
    "MCPServerReport",
    # Similarity / semantic layer
    "check_similarity",
    # Monitoring & Reporting
    "SecurityMonitor",
    "MonitoringReport",
    # Behavioral Monitoring (Phase 1)
    "BehavioralMonitor",
    "BehavioralMonitoringReport",
    "ContainmentLevel",
    "DriftAlert",
    "AnomalyAlert",
    # Supply Chain Security (Phase 4a)
    "ToolPinManager",
    "PinnedTool",
    "ToolVerificationResult",
    "SBOMGenerator",
    "SBOMEntry",
    "DependencyVerifier",
    "DependencyAlert",
    # Cross-Session Analysis (Phase 4b)
    "SessionStore",
    "SessionRecord",
    "CrossSessionCorrelator",
    "CorrelationAlert",
    "SleeperDetector",
    "SleeperAlert",
]
__version__ = "0.0.1"
