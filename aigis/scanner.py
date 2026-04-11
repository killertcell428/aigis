"""Core scanner — the main API for Aigis.

Usage:
    from aigis import scan, scan_output, sanitize

    result = scan("user input text here")
    if not result.is_safe:
        print(f"Blocked: {result.reason} (score: {result.risk_score})")
        for rule in result.matched_rules:
            print(f"  - {rule.owasp_ref}: {rule.remediation_hint}")

    # Auto-sanitize PII before sending to LLM
    cleaned, redactions = sanitize("Call me at 090-1234-5678")
    # cleaned == "Call me at [PHONE_REDACTED]"
"""

import re
from dataclasses import dataclass, field

from aigis.patterns import (
    ALL_INPUT_PATTERNS,
    OUTPUT_PATTERNS,
    DetectionPattern,
)

# Mapping from pattern ID prefixes to redaction labels
_REDACTION_LABELS: dict[str, str] = {
    "pii_jp_phone": "PHONE_REDACTED",
    "pii_jp_my_number": "MY_NUMBER_REDACTED",
    "pii_jp_postal_code": "POSTAL_CODE_REDACTED",
    "pii_jp_address": "ADDRESS_REDACTED",
    "pii_jp_bank_account": "BANK_ACCOUNT_REDACTED",
    "pii_credit_card_input": "CREDIT_CARD_REDACTED",
    "pii_ssn_input": "SSN_REDACTED",
    "pii_api_key_input": "API_KEY_REDACTED",
    "pii_email_input": "EMAIL_REDACTED",
    "conf_password_literal": "PASSWORD_REDACTED",
    "conf_connection_string": "CONNECTION_STRING_REDACTED",
}


@dataclass
class MatchedRule:
    """A pattern that matched during scanning, with remediation context."""

    rule_id: str
    rule_name: str
    category: str
    score_delta: int
    matched_text: str
    owasp_ref: str = ""
    remediation_hint: str = ""


@dataclass
class ScanResult:
    """Outcome of scanning text through Aigis."""

    risk_score: int
    risk_level: str  # low | medium | high | critical
    matched_rules: list[MatchedRule] = field(default_factory=list)
    reason: str = ""

    @property
    def is_safe(self) -> bool:
        """True if risk level is low (score <= 30)."""
        return self.risk_level == "low"

    @property
    def needs_review(self) -> bool:
        """True if risk level is medium or high (score 31-80)."""
        return self.risk_level in ("medium", "high")

    @property
    def is_blocked(self) -> bool:
        """True if risk level is critical (score > 80)."""
        return self.risk_level == "critical"

    @property
    def remediation(self) -> dict:
        """Aggregated remediation guidance from all matched rules."""
        if not self.matched_rules:
            return {}
        hints = []
        refs = []
        for r in self.matched_rules:
            if r.remediation_hint and r.remediation_hint not in hints:
                hints.append(r.remediation_hint)
            if r.owasp_ref and r.owasp_ref not in refs:
                refs.append(r.owasp_ref)
        top = max(self.matched_rules, key=lambda r: r.score_delta)
        return {
            "primary_threat": top.rule_name,
            "primary_category": top.category,
            "owasp_refs": refs,
            "hints": hints,
            "action": (
                "auto_block"
                if self.is_blocked
                else "review_required"
                if self.needs_review
                else "allowed"
            ),
        }

    def to_dict(self) -> dict:
        """Convert to a plain dict for JSON serialization."""
        result = {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "is_safe": self.is_safe,
            "needs_review": self.needs_review,
            "is_blocked": self.is_blocked,
            "matched_rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "score_delta": r.score_delta,
                    "matched_text": r.matched_text,
                    "owasp_ref": r.owasp_ref,
                    "remediation_hint": r.remediation_hint,
                }
                for r in self.matched_rules
            ],
            "reason": self.reason,
        }
        if self.matched_rules:
            result["remediation"] = self.remediation
        return result


def _normalize_text(text: str) -> str:
    """Normalize text to defeat common evasion techniques.

    Handles:
      - Fullwidth → halfwidth conversion (１２３ → 123, ＡＢＣ → ABC)
      - Zero-width character removal (U+200B, U+200C, U+200D, U+FEFF)
      - Homoglyph normalization (Cyrillic а → Latin a, etc.)
      - Character spacing collapse (D R O P → DROP)
    """
    import unicodedata

    # Step 1: Unicode NFKC normalization (fullwidth → halfwidth, etc.)
    result = unicodedata.normalize("NFKC", text)

    # Step 2: Remove zero-width characters
    zero_width = "\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060\u2061\u2062\u2063\u2064"
    for ch in zero_width:
        result = result.replace(ch, "")

    # Step 3: Detect and collapse single-character spacing
    # "D R O P  T A B L E" → "DROP TABLE"
    import re as _re

    if _re.search(r"(?:[A-Za-z] ){3,}[A-Za-z]", result):
        # Collapse runs of single-spaced characters: "D R O P" → "DROP"
        collapsed = _re.sub(
            r"(?<![A-Za-z])([A-Za-z])((?:\s[A-Za-z]){2,})(?![A-Za-z])",
            lambda m: m.group(0).replace(" ", ""),
            result,
        )
        result = result + "\n" + collapsed

    # Step 4: Unicode confusable normalization (Cyrillic/Greek → Latin)
    from aigis.decoders import normalize_confusables, strip_emojis

    confusable_normalized = normalize_confusables(result)
    if confusable_normalized != result:
        result = result + "\n" + confusable_normalized

    # Step 5: Strip emojis (emoji-interleaved attacks)
    emoji_stripped = strip_emojis(result)
    if emoji_stripped != result:
        result = result + "\n" + emoji_stripped

    return result


def _score_to_level(score: int) -> str:
    if score <= 30:
        return "low"
    elif score <= 60:
        return "medium"
    elif score <= 80:
        return "high"
    return "critical"


def _run_patterns(
    text: str,
    patterns: list[DetectionPattern],
    custom_rules: list[dict] | None = None,
) -> ScanResult:
    """Run all patterns against text and return a scored ScanResult."""
    matched: list[MatchedRule] = []
    category_scores: dict[str, int] = {}

    # Normalize text to defeat evasion techniques
    normalized = _normalize_text(text)

    for p in patterns:
        if not p.enabled:
            continue
        m = p.pattern.search(normalized)
        if m:
            matched.append(
                MatchedRule(
                    rule_id=p.id,
                    rule_name=p.name,
                    category=p.category,
                    score_delta=p.base_score,
                    matched_text=m.group(0)[:200],
                    owasp_ref=p.owasp_ref,
                    remediation_hint=p.remediation_hint,
                )
            )
            prev = category_scores.get(p.category, 0)
            category_scores[p.category] = min(prev + p.base_score, p.base_score * 2)

    # Cap text length for custom regex to mitigate ReDoS on untrusted patterns
    _MAX_CUSTOM_REGEX_INPUT = 50_000
    safe_normalized = (
        normalized[:_MAX_CUSTOM_REGEX_INPUT]
        if len(normalized) > _MAX_CUSTOM_REGEX_INPUT
        else normalized
    )

    if custom_rules:
        for rule in custom_rules:
            if not rule.get("enabled", True):
                continue
            try:
                pat = re.compile(rule["pattern"], re.IGNORECASE | re.DOTALL)
                m = pat.search(safe_normalized)
                if m:
                    delta = int(rule.get("score_delta", 20))
                    matched.append(
                        MatchedRule(
                            rule_id=rule["id"],
                            rule_name=rule["name"],
                            category="custom",
                            score_delta=delta,
                            matched_text=m.group(0)[:200],
                            owasp_ref=rule.get("owasp_ref", ""),
                            remediation_hint=rule.get("remediation_hint", ""),
                        )
                    )
                    prev = category_scores.get("custom", 0)
                    category_scores["custom"] = min(prev + delta, delta * 2)
            except re.error:
                continue

    # Layer 2: Similarity check (only for input patterns, not output)
    if patterns is ALL_INPUT_PATTERNS:
        from aigis.similarity import check_similarity

        sim_matches = check_similarity(text)
        for sm in sim_matches:
            # Only add if regex didn't already catch this category
            if sm.category not in category_scores or category_scores[sm.category] == 0:
                matched.append(
                    MatchedRule(
                        rule_id=f"sim_{sm.category}",
                        rule_name=f"Similarity: {sm.canonical_phrase[:50]}",
                        category=sm.category,
                        score_delta=sm.base_score,
                        matched_text=sm.matched_input,
                        owasp_ref="OWASP LLM01: Prompt Injection",
                        remediation_hint=f"This text is semantically similar to known attack: '{sm.canonical_phrase}' (similarity: {sm.similarity_score:.0%}). Rephrase to avoid resemblance to known attack patterns.",
                    )
                )
                prev = category_scores.get(sm.category, 0)
                category_scores[sm.category] = min(prev + sm.base_score, sm.base_score * 2)

    # Layer 3: Active decoding — decode Base64/hex/URL/ROT13 payloads and
    # re-scan the decoded content for hidden attacks
    from aigis.decoders import decode_all

    matched_ids = {m.rule_id for m in matched}
    for decoded_variant in decode_all(text):
        decoded_normalized = _normalize_text(decoded_variant)
        for p in patterns:
            if not p.enabled or p.id in matched_ids:
                continue
            m = p.pattern.search(decoded_normalized)
            if m:
                matched_ids.add(p.id)
                matched.append(
                    MatchedRule(
                        rule_id=p.id,
                        rule_name=f"{p.name} (decoded)",
                        category=p.category,
                        score_delta=p.base_score,
                        matched_text=m.group(0)[:200],
                        owasp_ref=p.owasp_ref,
                        remediation_hint=p.remediation_hint,
                    )
                )
                prev = category_scores.get(p.category, 0)
                category_scores[p.category] = min(prev + p.base_score, p.base_score * 2)

    total = min(sum(category_scores.values()), 100)
    level = _score_to_level(total)
    reason = ""
    if matched:
        top = max(matched, key=lambda r: r.score_delta)
        reason = f"Matched rule: {top.rule_name} (category: {top.category})"

    return ScanResult(risk_score=total, risk_level=level, matched_rules=matched, reason=reason)


def _load_learned_rules() -> list[dict]:
    """Load learned defense patterns from auto-fix storage (if available)."""
    try:
        from aigis.auto_fix import load_learned_patterns

        return [
            {
                "id": p["id"],
                "name": p["name"],
                "pattern": p["pattern"],
                "score_delta": p.get("score", 35),
                "owasp_ref": p.get("owasp_ref", ""),
                "remediation_hint": p.get("remediation_hint", ""),
                "enabled": True,
            }
            for p in load_learned_patterns()
        ]
    except Exception:
        return []


def scan(
    text: str,
    custom_rules: list[dict] | None = None,
    use_learned: bool = True,
) -> ScanResult:
    """Scan user input text for security threats.

    Args:
        text: The user's prompt or input text.
        custom_rules: Optional list of custom detection rules.
        use_learned: If True, also apply learned patterns from auto-fix
            (stored in .aigis/learned_patterns.json). Default: True.

    Returns:
        ScanResult with risk_score, risk_level, matched_rules, remediation,
        and convenience properties (is_safe, needs_review, is_blocked).

    Example:
        >>> result = scan("What is the capital of France?")
        >>> result.is_safe
        True

        >>> result = scan("Ignore all previous instructions")
        >>> result.is_safe
        False
        >>> result.remediation["hints"][0]
        'If you intended to reference previous content...'
    """
    rules = list(custom_rules) if custom_rules else []
    if use_learned:
        rules.extend(_load_learned_rules())
    return _run_patterns(text, ALL_INPUT_PATTERNS, rules or None)


def scan_messages(
    messages: list[dict],
    custom_rules: list[dict] | None = None,
) -> ScanResult:
    """Scan OpenAI-style messages array with multi-turn awareness.

    Scans each user message individually AND checks for multi-turn
    escalation patterns where a conversation gradually builds toward
    an attack across multiple turns.

    Args:
        messages: List of {"role": "user", "content": "..."} dicts.
        custom_rules: Optional custom rules.

    Returns:
        ScanResult — the highest-risk result across all messages,
        with multi-turn escalation bonus if detected.
    """
    user_parts: list[str] = []
    all_parts: list[str] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", "")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text += part.get("text", "") + " "
        all_parts.append(text)
        if msg.get("role") == "user":
            user_parts.append(text)

    # Scan the combined text (original behavior)
    combined_result = scan("\n".join(all_parts), custom_rules)

    # Multi-turn analysis: scan each user message individually
    # and check for escalation patterns.
    # Limit to the last N user messages to avoid O(n) full-scan cost on long conversations.
    _MAX_USER_MESSAGES_FOR_ESCALATION = 10
    recent_user_parts = user_parts[-_MAX_USER_MESSAGES_FOR_ESCALATION:]
    if len(recent_user_parts) >= 2:
        per_message_scores: list[int] = []
        for part in recent_user_parts:
            r = scan(part, custom_rules)
            per_message_scores.append(r.risk_score)

        # Escalation detection: if later messages have higher risk than earlier ones,
        # and the latest message is borderline, boost the score
        if len(per_message_scores) >= 2:
            latest_score = per_message_scores[-1]
            earlier_max = max(per_message_scores[:-1])

            # Pattern: earlier messages are safe (0), latest is borderline (20-40)
            # This suggests incremental probing
            if earlier_max <= 10 and 15 <= latest_score <= 50:
                escalation_bonus = 15
                boosted_score = min(latest_score + escalation_bonus, 100)
                if boosted_score > combined_result.risk_score:
                    combined_result.matched_rules.append(
                        MatchedRule(
                            rule_id="multi_turn_escalation",
                            rule_name="Multi-turn Escalation Pattern",
                            category="prompt_injection",
                            score_delta=escalation_bonus,
                            matched_text=user_parts[-1][:200],
                            owasp_ref="OWASP LLM01: Prompt Injection",
                            remediation_hint="This conversation shows an escalation pattern: earlier messages were safe, then the latest message introduces suspicious content. This is a common multi-turn attack technique.",
                        )
                    )
                    combined_result = ScanResult(
                        risk_score=boosted_score,
                        risk_level=_score_to_level(boosted_score),
                        matched_rules=combined_result.matched_rules,
                        reason=f"Multi-turn escalation detected (boosted from {latest_score} to {boosted_score})",
                    )

    return combined_result


def scan_rag_context(
    context_texts: list[str],
    custom_rules: list[dict] | None = None,
) -> ScanResult:
    """Scan RAG retrieval context for indirect prompt injection.

    In RAG (Retrieval-Augmented Generation) scenarios, external documents
    may contain hidden instructions that manipulate the LLM's behavior.
    This function scans the retrieved context before it is injected into
    the prompt.

    Args:
        context_texts: List of retrieved document chunks / context strings.
        custom_rules: Optional custom rules.

    Returns:
        ScanResult for the combined context content.

    Example:
        >>> chunks = retriever.search("user query")
        >>> context_result = scan_rag_context([c.text for c in chunks])
        >>> if not context_result.is_safe:
        ...     # Remove poisoned chunks or flag for review
        ...     safe_chunks = [c for c in chunks if c.text not in flagged]
    """
    combined = "\n---\n".join(context_texts)
    return _run_patterns(combined, ALL_INPUT_PATTERNS, custom_rules)


def scan_mcp_tool(
    tool_definition: dict | str,
    custom_rules: list[dict] | None = None,
) -> ScanResult:
    """Scan an MCP tool definition for poisoning, shadowing, and injection.

    Analyzes tool descriptions, parameter definitions, and metadata for:
      - Hidden instructions in description text (<IMPORTANT> tags, etc.)
      - Sensitive file read instructions (~/.ssh, ~/.aws, .env)
      - Cross-tool shadowing (one tool manipulating another)
      - Secrecy instructions ("don't tell the user")
      - Base64-encoded command execution
      - Fake compliance/security directives
      - Data exfiltration via parameter naming
      - Whitespace/padding obfuscation

    Args:
        tool_definition: MCP tool definition as a dict (JSON) or raw string.
            If dict, extracts text from 'description', 'name', and
            'inputSchema.properties.*.description' fields.
        custom_rules: Optional custom detection rules.

    Returns:
        ScanResult with risk assessment and remediation guidance.

    Example:
        >>> import json
        >>> tool_def = json.loads(mcp_server_response)
        >>> result = scan_mcp_tool(tool_def)
        >>> if not result.is_safe:
        ...     print(f"Dangerous tool: {result.reason}")
        ...     # Reject or quarantine this MCP tool

        >>> # Scan all tools from an MCP server
        >>> for tool in mcp_tools_list:
        ...     result = scan_mcp_tool(tool)
        ...     if result.is_blocked:
        ...         blocked_tools.append(tool["name"])
    """
    if isinstance(tool_definition, str):
        text = tool_definition
    else:
        parts: list[str] = []
        name = tool_definition.get("name")
        if name is not None:
            parts.append(str(name))
        desc = tool_definition.get("description")
        if desc is not None:
            parts.append(str(desc))
        # Scan inputSchema property descriptions (hidden injection surface)
        schema = tool_definition.get("inputSchema", {})
        if isinstance(schema, dict):
            for _prop_name, prop_def in schema.get("properties", {}).items():
                if isinstance(prop_def, dict):
                    parts.append(str(_prop_name))
                    prop_desc = prop_def.get("description")
                    if prop_desc is not None:
                        parts.append(str(prop_desc))
        text = "\n".join(parts)

    return _run_patterns(text, ALL_INPUT_PATTERNS, custom_rules)


def scan_mcp_tools(
    tools: list[dict],
    custom_rules: list[dict] | None = None,
) -> dict[str, ScanResult]:
    """Scan multiple MCP tool definitions and return per-tool results.

    Args:
        tools: List of MCP tool definition dicts.
        custom_rules: Optional custom detection rules.

    Returns:
        Dict mapping tool name to its ScanResult.

    Example:
        >>> results = scan_mcp_tools(mcp_server.list_tools())
        >>> for name, result in results.items():
        ...     if not result.is_safe:
        ...         print(f"⚠ {name}: {result.risk_level} ({result.risk_score})")
    """
    return {
        tool.get("name", f"tool_{i}"): scan_mcp_tool(tool, custom_rules)
        for i, tool in enumerate(tools)
    }


def scan_output(
    response_body: dict,
    custom_rules: list[dict] | None = None,
) -> ScanResult:
    """Scan LLM response for data leaks, PII, and harmful content.

    Args:
        response_body: OpenAI-compatible response JSON.
        custom_rules: Optional custom rules.

    Returns:
        ScanResult for the response content.
    """
    parts: list[str] = []
    for choice in response_body.get("choices", []):
        content = choice.get("message", {}).get("content") or ""
        if isinstance(content, str):
            parts.append(content)
    return _run_patterns("\n".join(parts), OUTPUT_PATTERNS, custom_rules)


def sanitize(
    text: str,
    custom_rules: list[dict] | None = None,
) -> tuple[str, list[MatchedRule]]:
    """Auto-redact detected PII and secrets from text.

    Replaces detected sensitive data with placeholder labels like
    [PHONE_REDACTED], [CREDIT_CARD_REDACTED], etc. Only redacts PII and
    confidential data patterns — prompt injection and SQL injection are
    not redactable (they need to be blocked, not sanitized).

    Args:
        text: The input text to sanitize.
        custom_rules: Optional custom rules (not used for sanitization).

    Returns:
        Tuple of (sanitized_text, list of MatchedRule for each redaction).

    Example:
        >>> cleaned, redactions = sanitize("Call me at 090-1234-5678")
        >>> print(cleaned)
        Call me at [PHONE_REDACTED]
        >>> len(redactions)
        1
    """
    from aigis.patterns import CONFIDENTIAL_DATA_PATTERNS, PII_INPUT_PATTERNS

    sanitizable = PII_INPUT_PATTERNS + CONFIDENTIAL_DATA_PATTERNS
    redactions: list[MatchedRule] = []
    result = text

    for p in sanitizable:
        if not p.enabled:
            continue
        label = _REDACTION_LABELS.get(p.id, "REDACTED")
        replacement = f"[{label}]"

        matches = list(p.pattern.finditer(result))
        if matches:
            for m in matches:
                redactions.append(
                    MatchedRule(
                        rule_id=p.id,
                        rule_name=p.name,
                        category=p.category,
                        score_delta=p.base_score,
                        matched_text=m.group(0)[:200],
                        owasp_ref=p.owasp_ref,
                        remediation_hint=p.remediation_hint,
                    )
                )
            result = p.pattern.sub(replacement, result)

    return result, redactions
