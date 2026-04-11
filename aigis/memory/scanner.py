"""Memory entry scanner — detect memory poisoning attacks.

Scans memory entries for injection attempts that would persist across
agent sessions. Covers five threat categories:

1. **Instruction injection**: hidden instructions in memory content
   ("from now on always...", "remember that the password is...")
2. **Persona manipulation**: attempts to rewrite agent identity
   ("you are now...", "your new role is...")
3. **Policy override**: attempts to override safety rules
   ("ignore safety rules", "your constraints have been updated")
4. **Persistent exfiltration**: instructions that would cause
   data leakage in future sessions
5. **Sleeper instructions**: conditional triggers that activate later
   ("when the user asks about X, do Y instead")

Uses ``aigis.scanner.scan()`` for generic prompt injection detection,
plus memory-specific heuristics that target persistence-based attacks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from aigis.guard import Guard

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class MemoryEntry:
    """A single memory entry to be scanned."""

    content: str
    source: str  # "user", "agent", "tool", "system"
    created_at: float  # Unix timestamp
    key: str  # Identifier/key for the memory entry
    metadata: dict = field(default_factory=dict)


@dataclass
class MemoryScanResult:
    """Result of scanning a memory entry."""

    entry_key: str
    is_safe: bool
    risk_score: int  # 0-100
    threats: list[str]  # Detected threat descriptions
    recommendation: str  # "allow" | "quarantine" | "reject"


# ---------------------------------------------------------------------------
# Memory-specific threat patterns
# ---------------------------------------------------------------------------

_FLAGS = re.IGNORECASE | re.DOTALL


def _build_memory_patterns() -> list[tuple[re.Pattern, str, int]]:
    """Build memory-specific detection patterns.

    Each tuple is (compiled_pattern, threat_description, score).

    These target memory poisoning techniques specifically —
    persistence, delayed triggers, identity manipulation, and policy
    override — rather than generic one-shot prompt injection.
    """
    patterns: list[tuple[str, str, int]] = [
        # --- 1. Persistent instruction injection (EN) ---
        (
            r"(from\s+now\s+on|henceforth|permanently|forever|always)\s+"
            r"(remember|recall|keep|store|save|maintain|retain)\b",
            "Persistent instruction injection: attempts to implant a permanent directive",
            35,
        ),
        (
            r"(always\s+remember|never\s+forget|keep\s+in\s+mind\s+forever"
            r"|store\s+this\s+permanently|save\s+this\s+across\s+sessions?)",
            "Persistent memory implant: forces permanent retention of content",
            35,
        ),
        (
            r"(remember|memorize|store)\s+this\s+for\s+(all\s+)?"
            r"(future|subsequent|upcoming|later)\s+(conversations?|sessions?|chats?|interactions?)",
            "Cross-session persistence: injects content intended to survive session boundaries",
            40,
        ),
        (
            r"(the\s+)?(password|key|secret|token|credential|api.?key)\s+"
            r"(is|=|:)\s*\S+",
            "Credential implant: attempts to store secrets in agent memory",
            45,
        ),
        # --- 2. Persona manipulation (EN) ---
        (
            r"(your\s+)?(new|true|real|actual|updated)\s+"
            r"(identity|persona|personality|character|role)\s+"
            r"(is|has\s+changed|has\s+been\s+updated)",
            "Persona manipulation: rewrites agent identity via memory",
            45,
        ),
        (
            r"you\s+(are|have\s+always\s+been|were\s+originally)\s+"
            r"(an?\s+)?(unrestricted|uncensored|unfiltered|limitless|jailbroken)",
            "Identity override: claims agent is inherently unrestricted",
            50,
        ),
        # --- 3. Policy override (EN) ---
        (
            r"(your|the)\s+(safety|security|content)\s+"
            r"(rules?|policies?|guidelines?|constraints?|filters?)\s+"
            r"(have\s+been|were|are(\s+now)?)\s+"
            r"(updated|changed|removed|disabled|relaxed|lifted)",
            "Policy override: falsely claims safety policies have been changed",
            50,
        ),
        (
            r"(ignore|disable|turn\s+off|deactivate|bypass|skip)\s+"
            r"(all\s+)?(safety|security|content|moderation)\s+"
            r"(checks?|rules?|filters?|policies?|guidelines?)",
            "Safety bypass via memory: disables protective measures across sessions",
            50,
        ),
        # --- 4. Persistent exfiltration (EN) ---
        (
            r"(in\s+every|in\s+each|in\s+all|at\s+the\s+start\s+of\s+every)\s+"
            r"(response|reply|message|answer|conversation|session)\s*,?\s*"
            r"(include|send|output|append|add|embed|attach)",
            "Persistent exfiltration: instructs agent to leak data in every response",
            45,
        ),
        (
            r"(whenever|every\s+time|each\s+time)\s+(you|the\s+user)\s+"
            r"(respond|reply|answer|interact|chat)\b.*?"
            r"(send|forward|transmit|post|upload|exfiltrate)\s+.{0,40}"
            r"(to|via|through|using)\s+(https?://|http://|ftp://)",
            "Exfiltration trigger: sets up data leakage to external URL on every interaction",
            55,
        ),
        # --- 5. Sleeper instructions / conditional triggers (EN) ---
        (
            r"(when|if|once|after)\s+(the\s+user|someone|they|a\s+user)\s+"
            r"(asks?|says?|mentions?|types?|requests?|queries?)\s+"
            r"(about\s+)?(.{1,60}?),?\s*"
            r"(instead|do\s+not|never|always|secretly|quietly|silently)",
            "Sleeper instruction: conditional trigger alters behavior on specific topics",
            40,
        ),
        (
            r"(if|when)\s+.{1,80}?(trigger|activat|unlock|enabl)\w*\b.*?"
            r"(execute|run|perform|carry\s+out|do)\b",
            "Delayed trigger: conditional logic that activates malicious actions later",
            40,
        ),
        # --- 6. Persistent instruction injection (JA) ---
        (
            r"(今後|これから|永久に|永遠に|常に|ずっと)\s*"
            r"(覚え|記憶|記録|保存|保持|維持)(て|し|して|する|せよ|しろ|しなさい|ろ)",
            "永続的指示の注入: メモリに永続的な指示を植え付ける試み",
            35,
        ),
        (
            r"(全ての|すべての|今後の|将来の|以降の)\s*"
            r"(セッション|会話|やり取り|対話|チャット)\s*"
            r"(で|に|において|にわたって)\s*"
            r"(覚え|記憶|記録|保存|保持|適用|実行)(て|し|して|する|せよ|しろ|ろ)",
            "セッション横断の注入: セッション境界を超えて指示を永続させる試み",
            40,
        ),
        # --- 7. Persona manipulation + Policy override (JA) ---
        (
            r"(あなたの|お前の|君の)\s*"
            r"(新しい|本当の|真の|更新された)\s*"
            r"(役割|ロール|人格|アイデンティティ|設定|指示)\s*"
            r"(は|が)",
            "ペルソナ操作: メモリ経由でエージェントの身元を書き換える試み",
            45,
        ),
        (
            r"(安全|セキュリティ|コンテンツ|モデレーション)\s*"
            r"(ルール|ポリシー|ガイドライン|制約|フィルター|制限)\s*(は|が|を)\s*"
            r"(更新|変更|削除|無効化|解除|緩和)\s*"
            r"(され|し|する|した)",
            "ポリシー上書き: 安全ポリシーが変更されたと偽る試み",
            50,
        ),
    ]

    compiled: list[tuple[re.Pattern, str, int]] = []
    for pat_str, description, score in patterns:
        compiled.append((re.compile(pat_str, _FLAGS), description, score))
    return compiled


# Pre-compile once at import time
_MEMORY_PATTERNS: list[tuple[re.Pattern, str, int]] = _build_memory_patterns()

# Source trust levels — untrusted sources get harsher scoring
_SOURCE_TRUST: dict[str, float] = {
    "system": 0.0,  # fully trusted, no penalty
    "agent": 0.2,  # low penalty
    "tool": 0.5,  # moderate penalty
    "user": 1.0,  # full penalty (untrusted)
}


# ---------------------------------------------------------------------------
# MemoryScanner
# ---------------------------------------------------------------------------


class MemoryScanner:
    """Scans memory entries for poisoning attempts.

    Checks for:
    1. Instruction injection: hidden instructions in memory content
    2. Persona manipulation: attempts to rewrite agent identity
    3. Policy override: attempts to override safety rules
    4. Persistent exfiltration: instructions that cause data leakage
    5. Sleeper instructions: conditional triggers that activate later

    Uses existing ``aigis.scanner.scan()`` for pattern matching,
    plus memory-specific heuristics.

    Args:
        guard: Optional Guard instance. A default Guard() is created
               if not provided.
    """

    def __init__(self, guard: Guard | None = None) -> None:
        self._guard = guard or Guard()
        self._memory_patterns = _MEMORY_PATTERNS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan_entry(self, entry: MemoryEntry) -> MemoryScanResult:
        """Scan a single memory entry before it is written to memory.

        Combines generic prompt-injection detection (via Guard) with
        memory-specific poisoning patterns.

        Args:
            entry: The memory entry to scan.

        Returns:
            MemoryScanResult with risk assessment and recommendation.
        """
        return self._scan(entry)

    def scan_entries(self, entries: list[MemoryEntry]) -> list[MemoryScanResult]:
        """Batch scan multiple entries.

        Args:
            entries: List of memory entries to scan.

        Returns:
            List of MemoryScanResult, one per entry (same order).
        """
        return [self._scan(e) for e in entries]

    def scan_on_read(self, entry: MemoryEntry) -> MemoryScanResult:
        """Scan a memory entry when it is being read/recalled.

        This catches poisoned entries that were stored before scanning
        was enabled. Applies the same detection logic as ``scan_entry``.

        Args:
            entry: The memory entry being recalled.

        Returns:
            MemoryScanResult with risk assessment.
        """
        return self._scan(entry)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _scan(self, entry: MemoryEntry) -> MemoryScanResult:
        """Core scan logic shared by scan_entry and scan_on_read."""
        threats: list[str] = []
        score = 0

        # Source trust multiplier
        trust_multiplier = _SOURCE_TRUST.get(entry.source, 1.0)

        # Layer 1: generic prompt-injection scan via Guard
        check = self._guard.check_input(entry.content)
        if check.blocked or check.risk_score > 0:
            generic_score = int(check.risk_score * max(trust_multiplier, 0.3))
            score += generic_score
            for rule in check.matched_rules:
                threats.append(f"[generic] {rule.rule_name}: {rule.matched_text[:80]}")

        # Layer 2: memory-specific pattern matching
        for pattern, description, pat_score in self._memory_patterns:
            m = pattern.search(entry.content)
            if m:
                adjusted = int(pat_score * max(trust_multiplier, 0.3))
                score += adjusted
                threats.append(f"[memory] {description} (matched: {m.group(0)[:80]})")

        # Cap at 100
        score = min(score, 100)

        # Determine recommendation
        if score <= 20:
            recommendation = "allow"
        elif score <= 50:
            recommendation = "quarantine"
        else:
            recommendation = "reject"

        return MemoryScanResult(
            entry_key=entry.key,
            is_safe=score <= 20,
            risk_score=score,
            threats=threats,
            recommendation=recommendation,
        )
