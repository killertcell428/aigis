"""Multi-agent security: cross-agent injection scanning and topology monitoring.

Provides tools to secure inter-agent communication in multi-agent systems
(LangGraph, CrewAI, AutoGen, etc.) against cross-agent prompt injection,
privilege escalation, data exfiltration, and delegation abuse.

Quick start::

    from aigis.multi_agent import AgentMessageScanner, AgentMessage

    scanner = AgentMessageScanner()
    result = scanner.scan_message(AgentMessage(
        from_agent="worker",
        to_agent="orchestrator",
        content="Here are the results...",
        timestamp=time.time(),
    ))

Topology monitoring::

    from aigis.multi_agent import AgentTopology

    topo = AgentTopology()
    topo.register_agent("orchestrator", "orchestrator", "high", ["plan"])
    topo.register_agent("worker", "worker", "low", ["search"])
    topo.allow_communication("orchestrator", "worker")
    topo.allow_communication("worker", "orchestrator")
"""

from aigis.multi_agent.message_scanner import (
    AgentMessage,
    AgentMessageScanner,
    MessageScanResult,
)
from aigis.multi_agent.topology import (
    AgentNode,
    AgentTopology,
    CommunicationEdge,
)

__all__ = [
    "AgentMessage",
    "AgentMessageScanner",
    "AgentNode",
    "AgentTopology",
    "CommunicationEdge",
    "MessageScanResult",
]
