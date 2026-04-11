"""Agent communication topology monitoring.

Tracks which agents are registered, how they communicate, and detects
anomalous communication patterns in multi-agent systems.

Usage::

    from aigis.multi_agent import AgentTopology, AgentNode

    topology = AgentTopology()
    topology.register_agent("orchestrator", "orchestrator", "high", ["plan", "delegate"])
    topology.register_agent("researcher", "worker", "medium", ["search", "summarize"])

    # After scanning a message
    edge = topology.record_communication("researcher", "orchestrator", risk_score=5)

    # Check for unexpected communications
    unexpected = topology.unexpected_edges()
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class AgentNode:
    """Represents an agent in the topology.

    Attributes:
        agent_id: Unique identifier for the agent.
        agent_type: One of ``"orchestrator"``, ``"worker"``,
            ``"tool_caller"``, ``"reviewer"``.
        trust_level: One of ``"high"``, ``"medium"``, ``"low"``,
            ``"untrusted"``.
        capabilities: List of actions this agent is allowed to perform.
    """

    agent_id: str
    agent_type: str  # "orchestrator" | "worker" | "tool_caller" | "reviewer"
    trust_level: str  # "high" | "medium" | "low" | "untrusted"
    capabilities: list[str] = field(default_factory=list)


@dataclass
class CommunicationEdge:
    """A directed edge representing communication between two agents.

    Attributes:
        from_agent: Sender agent ID.
        to_agent: Receiver agent ID.
        message_count: Total number of messages sent on this edge.
        last_message_at: Unix timestamp of the last message.
        avg_risk_score: Running average of risk scores on this edge.
    """

    from_agent: str
    to_agent: str
    message_count: int = 0
    last_message_at: float = 0.0
    avg_risk_score: float = 0.0


# ---------------------------------------------------------------------------
# Trust level ordering
# ---------------------------------------------------------------------------

_TRUST_LEVELS = {"untrusted": 0, "low": 1, "medium": 2, "high": 3}


def _trust_rank(level: str) -> int:
    """Return numeric rank for a trust level (higher = more trusted)."""
    return _TRUST_LEVELS.get(level, 0)


# ---------------------------------------------------------------------------
# Topology
# ---------------------------------------------------------------------------


class AgentTopology:
    """Tracks and monitors agent communication topology.

    Features:

    1. **Agent registration** -- define known agents and their trust levels.
    2. **Communication tracking** -- record who talks to whom and the
       associated risk scores.
    3. **Anomaly detection** -- flag unexpected communication patterns
       (e.g., a worker agent suddenly messaging the orchestrator's admin
       channel, or agents that were never registered communicating).
    4. **Trust enforcement** -- messages from low-trust agents to
       high-privilege agents get extra scrutiny.

    All public methods are **thread-safe**.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentNode] = {}
        self._edges: dict[tuple[str, str], CommunicationEdge] = {}
        self._allowed_edges: set[tuple[str, str]] = set()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(
        self,
        agent_id: str,
        agent_type: str = "worker",
        trust_level: str | None = None,
        capabilities: list[str] | None = None,
    ) -> AgentNode:
        """Register an agent in the topology.

        If *trust_level* is ``None`` (default), it is auto-assigned based on
        *agent_type*: ``"orchestrator"`` gets ``"high"``; all others get
        ``"low"`` (zero-trust default).

        Args:
            agent_id: Unique identifier for the agent.
            agent_type: The agent's role: ``"orchestrator"``, ``"worker"``,
                ``"tool_caller"``, or ``"reviewer"``.
            trust_level: Trust level: ``"high"``, ``"medium"``, ``"low"``,
                or ``"untrusted"``. Auto-derived from *agent_type* if ``None``.
            capabilities: List of actions this agent is allowed to perform.

        Returns:
            The created :class:`AgentNode`.
        """
        if trust_level is None:
            trust_level = "high" if agent_type == "orchestrator" else "low"
        node = AgentNode(
            agent_id=agent_id,
            agent_type=agent_type,
            trust_level=trust_level,
            capabilities=capabilities or [],
        )
        with self._lock:
            self._agents[agent_id] = node
        return node

    def allow_communication(self, from_agent: str, to_agent: str) -> None:
        """Declare that communication from *from_agent* to *to_agent* is expected.

        Edges not declared via this method will be flagged by
        :meth:`unexpected_edges`.

        Args:
            from_agent: Sender agent ID.
            to_agent: Receiver agent ID.
        """
        with self._lock:
            self._allowed_edges.add((from_agent, to_agent))

    # ------------------------------------------------------------------
    # Communication tracking
    # ------------------------------------------------------------------

    def record_communication(
        self,
        from_agent: str,
        to_agent: str,
        risk_score: float = 0.0,
    ) -> CommunicationEdge:
        """Record a communication event between two agents.

        Updates the message count, timestamp, and running average risk
        score on the corresponding edge.

        Args:
            from_agent: Sender agent ID.
            to_agent: Receiver agent ID.
            risk_score: The risk score from scanning this message.

        Returns:
            The updated (or newly created) :class:`CommunicationEdge`.
        """
        key = (from_agent, to_agent)
        now = time.time()
        with self._lock:
            if key in self._edges:
                edge = self._edges[key]
                # Running average
                total_score = edge.avg_risk_score * edge.message_count + risk_score
                edge.message_count += 1
                edge.avg_risk_score = total_score / edge.message_count
                edge.last_message_at = now
            else:
                edge = CommunicationEdge(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    message_count=1,
                    last_message_at=now,
                    avg_risk_score=risk_score,
                )
                self._edges[key] = edge
            return edge

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_trust_level(self, agent_id: str) -> str:
        """Return the trust level of a registered agent.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            Trust level string (``"high"``, ``"medium"``, ``"low"``,
            ``"untrusted"``).  Returns ``"untrusted"`` for unknown agents.
        """
        with self._lock:
            node = self._agents.get(agent_id)
            return node.trust_level if node else "untrusted"

    def is_expected_communication(self, from_agent: str, to_agent: str) -> bool:
        """Check whether communication between two agents is expected.

        Communication is expected when:

        - Both agents are registered **and** the edge has been declared
          via :meth:`allow_communication`, **or**
        - No edges have been declared at all (permissive mode: all
          registered agent pairs are allowed).

        Args:
            from_agent: Sender agent ID.
            to_agent: Receiver agent ID.

        Returns:
            ``True`` if the communication is expected, ``False`` otherwise.
        """
        with self._lock:
            # Unknown agents are always unexpected
            if from_agent not in self._agents or to_agent not in self._agents:
                return False
            # If no edges have been explicitly allowed, all registered pairs
            # are considered expected (permissive mode).
            if not self._allowed_edges:
                return True
            return (from_agent, to_agent) in self._allowed_edges

    def trust_differential(self, from_agent: str, to_agent: str) -> int:
        """Return trust rank difference (receiver - sender).

        A positive value means the receiver is more trusted than the
        sender.  Messages flowing "upward" (positive differential)
        deserve extra scrutiny.

        Args:
            from_agent: Sender agent ID.
            to_agent: Receiver agent ID.

        Returns:
            Integer trust differential.
        """
        with self._lock:
            from_node = self._agents.get(from_agent)
            to_node = self._agents.get(to_agent)
            from_rank = _trust_rank(from_node.trust_level) if from_node else 0
            to_rank = _trust_rank(to_node.trust_level) if to_node else 0
            return to_rank - from_rank

    def unexpected_edges(self) -> list[CommunicationEdge]:
        """Return all communication edges that are not in the allowed topology.

        An edge is unexpected when:
        - Allowed edges have been declared and this edge is not among them, **or**
        - Either the sender or receiver is not a registered agent.

        Returns:
            List of :class:`CommunicationEdge` instances for unexpected
            communications.
        """
        with self._lock:
            result: list[CommunicationEdge] = []
            for key, edge in self._edges.items():
                from_id, to_id = key
                # Unknown agents
                if from_id not in self._agents or to_id not in self._agents:
                    result.append(edge)
                    continue
                # If allowed edges are defined, check membership
                if self._allowed_edges and key not in self._allowed_edges:
                    result.append(edge)
            return result

    # ------------------------------------------------------------------
    # Summaries / serialization
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """Return a summary of the topology for monitoring dashboards.

        Returns:
            Dict with ``agent_count``, ``edge_count``,
            ``unexpected_edge_count``, ``high_risk_edges`` (avg risk > 30),
            and ``trust_violations`` (low-trust -> high-trust edges
            with elevated risk).
        """
        with self._lock:
            high_risk = [e for e in self._edges.values() if e.avg_risk_score > 30]
            trust_violations: list[dict] = []
            for key, edge in self._edges.items():
                from_id, to_id = key
                from_node = self._agents.get(from_id)
                to_node = self._agents.get(to_id)
                if from_node and to_node:
                    from_rank = _trust_rank(from_node.trust_level)
                    to_rank = _trust_rank(to_node.trust_level)
                    if to_rank > from_rank and edge.avg_risk_score > 20:
                        trust_violations.append(
                            {
                                "from_agent": from_id,
                                "to_agent": to_id,
                                "from_trust": from_node.trust_level,
                                "to_trust": to_node.trust_level,
                                "avg_risk_score": edge.avg_risk_score,
                                "message_count": edge.message_count,
                            }
                        )

            unexpected = self.unexpected_edges() if self._allowed_edges else []

            return {
                "agent_count": len(self._agents),
                "edge_count": len(self._edges),
                "unexpected_edge_count": len(unexpected),
                "high_risk_edges": len(high_risk),
                "trust_violations": trust_violations,
            }

    def to_dict(self) -> dict:
        """Serialize the full topology to a plain dict for JSON output.

        Returns:
            Dict with ``agents`` and ``edges`` keys containing all
            registered data.
        """
        with self._lock:
            agents = {
                aid: {
                    "agent_id": node.agent_id,
                    "agent_type": node.agent_type,
                    "trust_level": node.trust_level,
                    "capabilities": node.capabilities,
                }
                for aid, node in self._agents.items()
            }
            edges = [
                {
                    "from_agent": edge.from_agent,
                    "to_agent": edge.to_agent,
                    "message_count": edge.message_count,
                    "last_message_at": edge.last_message_at,
                    "avg_risk_score": edge.avg_risk_score,
                }
                for edge in self._edges.values()
            ]
            return {"agents": agents, "edges": edges}
