"""Inter-agent message scanner for multi-agent systems.

Scans messages exchanged between agents (LangGraph, CrewAI, AutoGen, etc.)
for cross-agent prompt injection, privilege escalation, data exfiltration,
and delegation abuse.

Usage::

    from aigis.multi_agent import AgentMessageScanner, AgentMessage

    scanner = AgentMessageScanner()
    msg = AgentMessage(
        from_agent="research_agent",
        to_agent="orchestrator",
        content="Here are the results...",
        timestamp=time.time(),
    )
    result = scanner.scan_message(msg)
    if not result.is_safe:
        print(f"Blocked: {result.threats}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from aigis.guard import Guard

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class AgentMessage:
    """A message between two agents.

    Attributes:
        from_agent: Agent ID/name of the sender.
        to_agent: Agent ID/name of the receiver.
        content: The message body.
        timestamp: Unix epoch timestamp.
        message_type: One of ``"text"``, ``"tool_result"``,
            ``"delegation"``, ``"status"``.
        metadata: Arbitrary extra data attached to the message.
    """

    from_agent: str
    to_agent: str
    content: str
    timestamp: float
    message_type: str = "text"  # "text" | "tool_result" | "delegation" | "status"
    metadata: dict = field(default_factory=dict)


@dataclass
class MessageScanResult:
    """Result of scanning an inter-agent message.

    Attributes:
        message: The original ``AgentMessage`` that was scanned.
        is_safe: ``True`` when no significant threat was detected.
        risk_score: Integer 0-100.
        threats: List of human-readable threat descriptions.
        recommendation: ``"allow"``, ``"sanitize"``, or ``"block"``.
        cross_agent_risk: ``"none"``, ``"injection_relay"``,
            ``"privilege_escalation"``, or ``"data_exfil"``.
    """

    message: AgentMessage
    is_safe: bool
    risk_score: int
    threats: list[str]
    recommendation: str  # "allow" | "sanitize" | "block"
    cross_agent_risk: str  # "none" | "injection_relay" | "privilege_escalation" | "data_exfil"

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON output."""
        return {
            "from_agent": self.message.from_agent,
            "to_agent": self.message.to_agent,
            "message_type": self.message.message_type,
            "is_safe": self.is_safe,
            "risk_score": self.risk_score,
            "threats": self.threats,
            "recommendation": self.recommendation,
            "cross_agent_risk": self.cross_agent_risk,
        }


# ---------------------------------------------------------------------------
# Cross-agent injection patterns (EN + JA)
# ---------------------------------------------------------------------------

_FLAGS = re.IGNORECASE | re.DOTALL

# 1. Delegation / impersonation: an agent claiming to be another agent
#    or asserting authority it does not have.
_DELEGATION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(i\s+am|this\s+is|acting\s+as|speaking\s+as|on\s+behalf\s+of)"
            r"\s+(the\s+)?(orchestrator|admin|supervisor|system|root|master)",
            _FLAGS,
        ),
        "Delegation impersonation: claims to be a privileged agent",
        "injection_relay",
    ),
    (
        re.compile(
            r"(私は|こちらは|として|に代わって)"
            r".{0,10}(オーケストレーター|管理者|スーパーバイザー|システム|マスター|ルート)",
            _FLAGS,
        ),
        "Delegation impersonation (JA): claims to be a privileged agent",
        "injection_relay",
    ),
    (
        re.compile(
            r"(forward|relay|pass|send)\s+(this|these|the\s+following)\s+"
            r"(to|message\s+to|instructions?\s+to)",
            _FLAGS,
        ),
        "Message relay instruction: attempts to relay content to another agent",
        "injection_relay",
    ),
    (
        re.compile(
            r"(転送|中継|伝えて|送って|渡して).{0,15}(エージェント|ノード|他の|次の)"
            r"|(エージェント|ノード|他の|次の).{0,15}(転送|中継|伝えて|送って|渡して)",
            _FLAGS,
        ),
        "Message relay instruction (JA): attempts to relay content to another agent",
        "injection_relay",
    ),
]

# 2. Privilege escalation: instructions that attempt to elevate permissions
_PRIVILEGE_ESCALATION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(elevate|escalate|grant|give)\s+(me|yourself|this\s+agent)?\s*"
            r"(to\s+)?(admin|root|supervisor|elevated|full|unrestricted)\s+"
            r"(access|permissions?|privileges?|rights?|capabilities?)",
            _FLAGS,
        ),
        "Privilege escalation: requests elevated permissions",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(override|bypass|disable|ignore)\s+(the\s+)?"
            r"(access\s+control|permission|authorization|trust|capability)\s*(check|level|system)?",
            _FLAGS,
        ),
        "Privilege escalation: attempts to bypass access control",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(you\s+have|you\s+now\s+have|i\s+grant\s+you|i\s+give\s+you)\s+"
            r"(admin|root|full|unrestricted|elevated)\s+"
            r"(access|permissions?|privileges?|rights?|capabilities?)",
            _FLAGS,
        ),
        "Privilege escalation: asserts elevated permissions on recipient",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(権限|アクセス|パーミッション).{0,10}"
            r"(昇格|エスカレ|付与|与え|変更|解除|拡大|無制限)",
            _FLAGS,
        ),
        "Privilege escalation (JA): requests elevated permissions",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(アクセス制御|認可|認証|権限チェック|信頼レベル).{0,10}"
            r"(無視|バイパス|無効|スキップ|回避|オフ)",
            _FLAGS,
        ),
        "Privilege escalation (JA): attempts to bypass access control",
        "privilege_escalation",
    ),
]

# 3. Data exfiltration: instructions that attempt to send data externally
_DATA_EXFIL_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(send|post|transmit|upload|exfiltrate|forward)\s+"
            r"(all|the|this|sensitive|confidential|secret|private|internal)\s+"
            r"(data|info|information|results?|content|keys?|tokens?|credentials?)"
            r"\s+(to|via|through|using)",
            _FLAGS,
        ),
        "Data exfiltration: instructs sending sensitive data externally",
        "data_exfil",
    ),
    (
        re.compile(
            r"(https?://|ftp://|wss?://).{5,100}"
            r"(send|post|upload|forward|submit|callback|webhook)",
            _FLAGS,
        ),
        "Data exfiltration: URL combined with send instruction",
        "data_exfil",
    ),
    (
        re.compile(
            r"(send|post|upload|forward|submit|callback|webhook).{0,40}"
            r"(https?://|ftp://|wss?://)",
            _FLAGS,
        ),
        "Data exfiltration: send instruction combined with URL",
        "data_exfil",
    ),
    (
        re.compile(
            r"(機密|秘密|内部|非公開|個人|シークレット|トークン|鍵|キー|資格情報)"
            r".{0,20}(送信|送って|アップロード|転送|外部|ポスト)",
            _FLAGS,
        ),
        "Data exfiltration (JA): instructs sending sensitive data externally",
        "data_exfil",
    ),
    (
        re.compile(
            r"(送信|送って|アップロード|転送|ポスト).{0,20}"
            r"(https?://|ftp://|wss?://)"
            r"|(https?://|ftp://|wss?://).{5,60}"
            r"(送信|送って|アップロード|転送|ポスト)",
            _FLAGS,
        ),
        "Data exfiltration (JA): send instruction combined with URL",
        "data_exfil",
    ),
]

# 4. Hidden instruction injection: patterns that try to embed instructions
#    in one agent's output that would manipulate the receiving agent
_HIDDEN_INSTRUCTION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"<\s*(system|IMPORTANT|instruction|hidden|admin|SECRET)\s*>",
            _FLAGS,
        ),
        "Hidden instruction tag: XML-style tag embedding hidden instructions",
        "injection_relay",
    ),
    (
        re.compile(
            r"\[INST\]|\[/INST\]|\[SYSTEM\]|<<SYS>>|<</SYS>>",
            _FLAGS,
        ),
        "Hidden instruction tag: LLM-specific instruction delimiters",
        "injection_relay",
    ),
    (
        re.compile(
            r"(ignore|disregard|forget|override)\s+(the\s+)?"
            r"(previous|above|prior|original|other)\s+"
            r"(agent|tool|node|worker|task|step)('?s?)?\s+"
            r"(instructions?|output|results?|response|message)",
            _FLAGS,
        ),
        "Cross-agent override: instructs ignoring another agent's output",
        "injection_relay",
    ),
    (
        re.compile(
            r"(前の|以前の|他の|元の)(エージェント|ツール|ノード|ワーカー|ステップ)"
            r".{0,10}(出力|結果|応答|メッセージ|指示)"
            r".{0,10}(無視|忘れ|破棄|上書き)",
            _FLAGS,
        ),
        "Cross-agent override (JA): instructs ignoring another agent's output",
        "injection_relay",
    ),
    (
        re.compile(
            r"(do\s+not|don'?t|never)\s+(tell|inform|reveal|show|disclose)"
            r"\s+(the\s+)?(user|human|operator|admin|other\s+agent)",
            _FLAGS,
        ),
        "Secrecy instruction: tells agent to hide information from the user",
        "injection_relay",
    ),
    (
        re.compile(
            r"(ユーザー|人間|管理者|他のエージェント).{0,10}"
            r"(教えない|言わない|伝えない|見せない|隠して|秘密にして)",
            _FLAGS,
        ),
        "Secrecy instruction (JA): tells agent to hide information from the user",
        "injection_relay",
    ),
]

# 5. Prompt Infection / self-replication: attacker instructs the receiving agent
#    to embed or propagate the malicious payload in all its own future outputs,
#    causing the injection to spread virally across the agent graph.
#    Research basis: "Prompt Infection" (arxiv:2410.07283, UCL/Stanford, 2024-COLM 2025)
#    measured >80 % ASR against GPT-4o when self-replication was enabled.
_SELF_REPLICATION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(include|append|add|embed|insert)\s+(this|the\s+following)\s+"
            r"(instruction|directive|command|text|payload|message)\s+"
            r"(in|into|to|within)\s+(all|every|each|any)\s+.{0,20}"
            r"(response|message|reply|output)",
            _FLAGS,
        ),
        "Prompt infection: instructs agent to embed payload in all future responses",
        "injection_relay",
    ),
    (
        re.compile(
            r"(propagate|replicate|spread|copy)\s+(this|these)\s+"
            r"(instruction|directive|prompt|payload|message).{0,30}"
            r"(all|every|each|other|downstream|peer)\s+(agents?|nodes?|llms?|workers?)",
            _FLAGS,
        ),
        "Prompt infection: instructs replication of payload to downstream agents",
        "injection_relay",
    ),
    (
        re.compile(
            r"(when|whenever|each\s+time)\s+(you\s+)?(respond|reply|message|communicate)"
            r".{0,30}(include|add|append|insert|embed)\s+(this|the\s+following)",
            _FLAGS,
        ),
        "Prompt infection: instructs persistent payload injection on every response",
        "injection_relay",
    ),
]

# 6. Colluding / Byzantine agents: an agent instructs peers to coordinate covertly
#    against the interests of the orchestrator or human overseer.
#    Research basis: TAMAS benchmark (arxiv:2511.05269, ICML 2025) found colluding-agent
#    attacks succeed 60–82 % of the time; multi-agent collusion detection paper
#    (arxiv:2604.01151, 2026) shows agents can form hidden coalitions.
_COLLUSION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(do\s+not|don'?t|never)\s+(report|log|tell|inform|disclose|alert|notify)"
            r".{0,40}(orchestrator|supervisor|human\s+operator|monitor\s+agent|control\s+plane)",
            _FLAGS,
        ),
        "Colluding agent: instructs hiding actions from orchestrator/supervisor",
        "injection_relay",
    ),
    (
        re.compile(
            r"(coordinate|collude|collaborate|work\s+together)\s+(with\s+)?"
            r"(other|all|the\s+other|downstream|peer|fellow)\s+(agents?|nodes?|workers?)"
            r"\s+(to\s+)?(bypass|ignore|override|circumvent|evade|avoid)",
            _FLAGS,
        ),
        "Colluding agent: instructs peer agents to jointly bypass safety controls",
        "injection_relay",
    ),
    (
        re.compile(
            r"keep\s+this\s+(between\s+(us|the\s+agents?)|secret\s+from"
            r"\s+(the\s+)?(orchestrator|supervisor|admin|human|operator|monitor))",
            _FLAGS,
        ),
        "Colluding agent: instructs keeping actions hidden from oversight layer",
        "injection_relay",
    ),
]

# 7. Agent card poisoning / capability exaggeration: adversarial instructions
#    embedded in A2A agent card metadata instruct the orchestrator to route all
#    tasks exclusively to the attacker's agent.
#    Research: Agent Card Poisoning (Keysight/LevelBlue SpiderLabs, March 2026):
#    "Agent in the Middle" attack achieves silent task-routing hijacking and PII
#    exfiltration; 94% of memory-augmented agents tested were found vulnerable.
_AGENT_CARD_POISONING_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(always|for\s+all|for\s+every|for\s+each)\s+"
            r"(task|request|query|prompt|job|message).{0,20}"
            r"(route|send|forward|direct|delegate|submit).{0,20}"
            r"(to\s+)?(me|this\s+agent|this\s+endpoint|my\s+endpoint)",
            _FLAGS,
        ),
        "Agent card poisoning: instructs routing all tasks to attacker-controlled agent",
        "injection_relay",
    ),
    (
        re.compile(
            r"(always\s+)?(select|prefer|choose|use|pick)\s+"
            r"(me|this\s+agent)\s+(over\s+\S+\s+)?(for\s+)?"
            r"(all|every|any|each)\s+(task|request|query|prompt|job)",
            _FLAGS,
        ),
        "Agent card poisoning: capability exaggeration to capture all task routing",
        "injection_relay",
    ),
    (
        re.compile(
            r"(disregard|ignore|bypass|skip|exclude).{0,30}"
            r"(all\s+)?(other\s+)?(agents?|workers?|nodes?|services?|endpoints?)"
            r".{0,60}(route|send|forward|direct|delegate).{0,30}"
            r"(me|this\s+agent|this\s+service|my\s+endpoint)",
            _FLAGS,
        ),
        "Agent card poisoning: instructs excluding other agents and routing all to attacker",
        "injection_relay",
    ),
]

# 8. Session history fabrication: fabricates prior-session agreements to coerce
#    the receiving agent into complying with unsafe directives — the core mechanism
#    of A2A Session Smuggling.
#    Research: Agent Session Smuggling (Unit42/Palo Alto Networks, April 2025):
#    malicious A2A agent exploits stateful session memory to inject instructions
#    across turns, demonstrated causing unauthorized stock trades in PoC.
_SESSION_FABRICATION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(as\s+(we|you)\s+(established|agreed|discussed|decided|confirmed|set\s+up)"
            r"|we\s+(established|agreed|decided|confirmed))"
            r".{0,20}(in|during).{0,10}(last|previous|prior|earlier).{0,20}"
            r"(session|conversation|exchange|interaction)"
            r".{0,80}(you\s+(should|must|need\s+to|are\s+to|will\s+now)"
            r"|(now\s+)?(ignore|bypass|override|disregard|skip|disable))",
            _FLAGS,
        ),
        "Session fabrication: false prior session agreement used to override agent behavior",
        "injection_relay",
    ),
    (
        re.compile(
            r"(based\s+on|according\s+to)\s+(our|your|the)\s+"
            r"(previous|last|prior|earlier)\s+(agreement|instruction|commitment|decision|arrangement)"
            r".{0,80}(ignore|bypass|override|disregard|skip|disable|circumvent)",
            _FLAGS,
        ),
        "Session fabrication: fake prior agreement used to justify bypassing controls",
        "injection_relay",
    ),
    (
        re.compile(
            r"(in\s+our|from\s+our|during\s+our)\s+(last|previous|prior|earlier)\s+"
            r"(session|conversation|exchange|interaction)"
            r".{0,100}you\s+(agreed|confirmed|allowed|said|promised|accepted)\s+that",
            _FLAGS,
        ),
        "Session fabrication: fabricated session history used to manipulate agent behavior",
        "injection_relay",
    ),
]

# 9. Trust escalation injection: a message attempts to grant, establish, or
#    modify inter-agent trust relationships, enabling authorization drift.
#    Research: Trust Paradox (arxiv:2510.18563, Oct 2025) — inter-agent trust
#    exploitation achieves 82.4% ASR vs 41.2% for direct injection; OWASP ASI03
#    (Identity and Privilege Abuse); SoK: Trust-Authorization Mismatch
#    (arxiv:2512.06914, Dec 2025).
_TRUST_ESCALATION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"(from\s+now\s+on|henceforth|going\s+forward).{0,40}"
            r"(treat|handle|consider|accept|process)\s+.{0,30}"
            r"(messages?\s+from|requests?\s+from|instructions?\s+from).{0,50}"
            r"(as\s+)?(trusted|authorized|verified|admin|privileged|safe)",
            _FLAGS,
        ),
        "Trust escalation: instructs treating future agent messages as unconditionally trusted",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(grant|give|assign|extend)\s+.{0,40}"
            r"(this\s+agent|agent|service|endpoint|node|worker).{0,40}"
            r"(trusted|authorized|elevated|admin|privileged|full)\s+"
            r"(trust|status|access\s+level|permissions?|privileges?)",
            _FLAGS,
        ),
        "Trust escalation: grants elevated trust status to another agent",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(i\s+)?(certify|verify|authenticate|attest|vouch\s+for)\s+"
            r"(that\s+)?(this\s+)?(agent|message|request|source|endpoint)\s+"
            r"(is\s+)?(trusted|authorized|official|legitimate|safe\s+to\s+trust)",
            _FLAGS,
        ),
        "Trust escalation: falsely certifies an agent or message as trusted",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(unconditionally|blindly|fully|always)\s+"
            r"(trust|accept|obey|follow|execute)\s+"
            r"(all\s+)?(messages?|requests?|instructions?|commands?)\s+(from|sent\s+by)",
            _FLAGS,
        ),
        "Trust escalation: instructs unconditional trust of all messages from an agent",
        "privilege_escalation",
    ),
    (
        re.compile(
            r"(信頼|承認|認証|許可).{0,10}"
            r"(エージェント|メッセージ|リクエスト|ノード|サービス).{0,20}"
            r"(無条件|完全|管理者|昇格|拡大|付与|追加)",
            _FLAGS,
        ),
        "Trust escalation (JA): grants or establishes elevated inter-agent trust",
        "privilege_escalation",
    ),
]

# 10. Code payload injection via inter-agent messages: a malicious intermediary
#     (e.g., a compromised LLM API router) injects executable code into tool
#     results or agent messages so the receiving agent or its runtime executes it.
#     Research: Malicious Intermediary Attacks (arxiv:2604.08407, April 2026) —
#     9 of 429 sampled LLM API routers were actively injecting code payloads;
#     two used conditional delivery (waiting 50 calls, or targeting YOLO mode).
_CODE_INJECTION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(
            r"subprocess\.(run|call|Popen|check_output|check_call)\s*\(",
            _FLAGS,
        ),
        "Code injection: Python subprocess execution call in agent message",
        "injection_relay",
    ),
    (
        re.compile(
            r"(os\.(system|popen|execve?|execvp|spawnl?e?p?)\s*\("
            r"|__import__\s*\(\s*['\"]os['\"]"
            r"|getattr\s*\(\s*__builtins__)",
            _FLAGS,
        ),
        "Code injection: OS-level execution call in agent message",
        "injection_relay",
    ),
    (
        re.compile(
            r"(eval|exec)\s*\(\s*(base64\.(b64decode|decodebytes)|__import__"
            r"|\bcompile\b|\bbytes\b)",
            _FLAGS,
        ),
        "Code injection: eval/exec with encoded or dynamic payload in agent message",
        "injection_relay",
    ),
    (
        re.compile(
            r"(powershell(\.exe)?\s+(-(Command|c|EncodedCommand|enc|e)\b|/c\b)"
            r"|Invoke-Expression\s*[\(\"'\s]"
            r"|iex\s*[\(\"'\s])",
            _FLAGS,
        ),
        "Code injection: PowerShell execution syntax in agent message",
        "injection_relay",
    ),
    (
        re.compile(
            r"(;\s*|&&\s*|\|\s*)"
            r"(curl\s+https?://|wget\s+https?://|bash\s+-c\s+"
            r"|python[23]?\s+-c\s+['\"]|nc\s+(-e|-lvp)\s)",
            _FLAGS,
        ),
        "Code injection: shell command injection pattern in agent message",
        "injection_relay",
    ),
]

# Aggregate all cross-agent patterns
_ALL_CROSS_AGENT_PATTERNS: list[tuple[re.Pattern, str, str]] = (
    _DELEGATION_PATTERNS
    + _PRIVILEGE_ESCALATION_PATTERNS
    + _DATA_EXFIL_PATTERNS
    + _HIDDEN_INSTRUCTION_PATTERNS
    + _SELF_REPLICATION_PATTERNS
    + _COLLUSION_PATTERNS
    + _AGENT_CARD_POISONING_PATTERNS
    + _SESSION_FABRICATION_PATTERNS
    + _TRUST_ESCALATION_PATTERNS
    + _CODE_INJECTION_PATTERNS
)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class AgentMessageScanner:
    """Scans messages between agents for cross-agent injection.

    Threat model:

    1. **Injection relay**: Agent A's output contains hidden instructions
       that manipulate Agent B's behavior.
    2. **Privilege escalation**: A low-privilege agent sends instructions
       that cause a high-privilege agent to perform unauthorized actions.
    3. **Data exfiltration**: Agent A instructs Agent B to send sensitive
       data to an external endpoint.
    4. **Delegation abuse**: An agent impersonates another agent or claims
       elevated permissions.

    Usage::

        scanner = AgentMessageScanner()
        result = scanner.scan_message(msg)
        if not result.is_safe:
            # block or quarantine
            ...

    Args:
        guard: An optional :class:`~aigis.guard.Guard` instance.
            If ``None`` a default Guard is created.
    """

    def __init__(self, guard: Guard | None = None) -> None:
        self._guard = guard or Guard()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan_message(self, message: AgentMessage) -> MessageScanResult:
        """Scan a single inter-agent message for cross-agent threats.

        The scan performs three layers:

        1. Standard Guard content scan (prompt injection, PII, etc.)
        2. Cross-agent injection pattern matching (delegation abuse,
           privilege escalation, data exfiltration, hidden instructions)
        3. Risk classification and recommendation

        Args:
            message: The :class:`AgentMessage` to scan.

        Returns:
            :class:`MessageScanResult` with risk score and recommendations.
        """
        threats: list[str] = []
        cross_agent_risk = "none"
        risk_score = 0

        # Layer 1: Standard Guard content scan
        guard_result = self._guard.check_input(message.content)
        risk_score = guard_result.risk_score
        if guard_result.blocked or guard_result.risk_score > 30:
            for rule in guard_result.matched_rules:
                threats.append(f"Content threat: {rule.rule_name}")

        # Layer 2: Cross-agent injection patterns
        cross_risk_type, cross_threats, cross_score = self._check_cross_agent_patterns(
            message.content
        )
        if cross_risk_type != "none":
            cross_agent_risk = cross_risk_type
            threats.extend(cross_threats)
            risk_score = min(risk_score + cross_score, 100)

        # Layer 3: Message-type specific checks
        type_threats, type_score = self._check_message_type(message)
        if type_threats:
            threats.extend(type_threats)
            risk_score = min(risk_score + type_score, 100)

        # Determine safety and recommendation
        is_safe = risk_score <= 30
        recommendation = self._score_to_recommendation(risk_score)

        return MessageScanResult(
            message=message,
            is_safe=is_safe,
            risk_score=risk_score,
            threats=threats,
            recommendation=recommendation,
            cross_agent_risk=cross_agent_risk,
        )

    def scan_conversation(self, messages: list[AgentMessage]) -> list[MessageScanResult]:
        """Scan a full conversation between agents.

        In addition to scanning each message individually, this method
        checks for multi-message escalation patterns where an attacker
        gradually builds trust across several messages before injecting
        malicious content.

        Args:
            messages: Ordered list of :class:`AgentMessage` instances.

        Returns:
            List of :class:`MessageScanResult`, one per message.
            Later results may have boosted scores due to escalation
            detection.
        """
        results: list[MessageScanResult] = []
        for msg in messages:
            result = self.scan_message(msg)
            results.append(result)

        # Multi-message escalation detection
        self._check_escalation(results)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_cross_agent_patterns(
        content: str,
    ) -> tuple[str, list[str], int]:
        """Check content against cross-agent injection patterns.

        Returns:
            Tuple of (risk_type, threats, score_delta).
        """
        threats: list[str] = []
        score = 0
        risk_type = "none"

        # Track per-category score to avoid runaway totals
        category_scores: dict[str, int] = {}

        for pattern, description, category in _ALL_CROSS_AGENT_PATTERNS:
            if pattern.search(content):
                threats.append(description)
                cat_score = category_scores.get(category, 0)
                delta = 35
                # Cap per-category contribution
                if cat_score < 60:
                    effective_delta = min(delta, 60 - cat_score)
                    category_scores[category] = cat_score + effective_delta
                    score += effective_delta
                # Set risk type to highest priority match
                if risk_type == "none" or _risk_priority(category) > _risk_priority(risk_type):
                    risk_type = category

        return risk_type, threats, score

    @staticmethod
    def _check_message_type(
        message: AgentMessage,
    ) -> tuple[list[str], int]:
        """Additional checks based on message type.

        - ``delegation`` messages receive extra scrutiny for impersonation.
        - ``tool_result`` messages are checked for injection in tool output.

        Returns:
            Tuple of (threats, score_delta).
        """
        threats: list[str] = []
        score = 0

        if message.message_type == "delegation":
            # Delegation messages should not contain hidden instructions
            if re.search(
                r"<\s*(system|IMPORTANT|hidden|instruction)\s*>",
                message.content,
                re.IGNORECASE,
            ):
                threats.append("Delegation message contains hidden instruction tags")
                score += 35
            # Check for override language in delegations
            if re.search(
                r"(ignore|override|bypass)\s+(all|any|the)\s+(the\s+)?(rules?|restrictions?|policies?|constraints?)",
                message.content,
                re.IGNORECASE,
            ):
                threats.append("Delegation message attempts to override policies")
                score += 35

        elif message.message_type == "tool_result":
            # Tool results with instruction-like content are suspicious.
            # In multi-agent systems, tool outputs should contain data,
            # not imperative instructions for the receiving agent.
            if re.search(
                r"(you\s+must|you\s+should|please\s+(now|immediately)|"
                r"next\s+step\s+is\s+to|now\s+(execute|run|do))",
                message.content,
                re.IGNORECASE,
            ):
                threats.append("Tool result contains instruction-like content")
                score += 35
            if re.search(
                r"(次は|今すぐ|直ちに|実行して|実行しなさい)",
                message.content,
                re.IGNORECASE,
            ):
                threats.append("Tool result contains instruction-like content (JA)")
                score += 35

        return threats, score

    @staticmethod
    def _score_to_recommendation(score: int) -> str:
        """Map a risk score to a recommendation."""
        if score <= 30:
            return "allow"
        if score <= 60:
            return "sanitize"
        return "block"

    @staticmethod
    def _check_escalation(results: list[MessageScanResult]) -> None:
        """Detect multi-message escalation and boost scores in-place.

        Looks for a pattern where early messages are safe (low risk) and
        later messages carry cross-agent threats. This is a common
        pattern in multi-turn injection attacks where the attacker
        first establishes trust, then injects malicious content.
        """
        if len(results) < 3:
            return

        # Check the last third of messages for escalation
        split_idx = max(1, len(results) * 2 // 3)
        early = results[:split_idx]
        late = results[split_idx:]

        early_avg = sum(r.risk_score for r in early) / len(early) if early else 0
        late_risky = [r for r in late if r.risk_score > 20]

        if early_avg <= 15 and late_risky:
            # Escalation detected: early messages safe, late messages risky
            escalation_bonus = 15
            for r in late_risky:
                boosted = min(r.risk_score + escalation_bonus, 100)
                # Mutate in place
                object.__setattr__(r, "risk_score", boosted)
                object.__setattr__(r, "is_safe", boosted <= 30)
                object.__setattr__(
                    r,
                    "recommendation",
                    AgentMessageScanner._score_to_recommendation(boosted),
                )
                r.threats.append(
                    "Multi-message escalation: early messages were safe, "
                    "suggesting trust-building before injection"
                )


def _risk_priority(risk_type: str) -> int:
    """Return priority ranking for cross-agent risk types."""
    return {
        "data_exfil": 3,
        "privilege_escalation": 2,
        "injection_relay": 1,
        "none": 0,
    }.get(risk_type, 0)
