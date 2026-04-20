"""Plugin & conversation-history integrity check.

Motivated by the IEEE S&P 2026 third-party chatbot plugins study
(arxiv:2511.05797) and follow-up industry measurements reported in April
2026 (sombrainc LLM Security Risks 2026, sqmagazine Prompt Injection
Statistics 2026). Headline findings:

* **8 of 17** audited plugins (used on ~8,000 sites) did **not** verify
  the integrity of the conversation history they were handed — they
  trusted whatever the host page / extension sent them.
* **15 of 17** web-scraping tools did not separate trusted content from
  externally-fetched content, letting an attacker plant an instruction in
  a page and have the assistant execute it on the next turn.
* In production incidents (financial sector, ~US$250k fraudulent wire
  transfer) the attacker only needed to poison one turn of history; all
  later turns inherited the injected "system" message.

This module plugs the second untrusted surface aigis did not previously
cover: *the conversation history itself*. ``rag_context_filter`` hardens
retrieved documents; ``structured_query`` hardens the top-level prompt;
this module hardens turns that claim to be prior exchanges.

Mechanism
---------
1. Caller passes a list of ``HistoryTurn`` objects (role + content +
   optional HMAC tag + optional source origin).
2. For each turn we run three independent checks:
   * **Provenance tag** — if the caller supplied an HMAC, verify it.
     A turn without a valid tag is demoted to ``role="external"``
     regardless of what it claimed.
   * **Role coherence** — an ``assistant`` turn must not contain role
     tokens or system-level override phrases (reused from
     ``structured_query``). A ``tool`` turn must not contain directive
     phrases addressed at the assistant.
   * **Origin mixing** — content whose ``origin`` is ``"external"``
     (scraped page, email body, plugin output) is re-screened with the
     same directive patterns ``rag_context_filter`` uses, and the
     offending sentences stripped.
3. The output is a ``IntegrityResult`` with:
   * ``safe_turns`` — the turns that can be forwarded to the model,
     re-tagged where necessary (forged assistant → external),
   * ``quarantined_turns`` — turns that failed integrity and should not
     be replayed,
   * ``findings`` — per-turn evidence suitable for audit logs.

Why a separate module
---------------------
The RAG filter treats one retrieval surface. The structured-query module
treats the top-level prompt. Plugin-vs-history injection is a third class
(the same content is replayed across turns, so a miss compounds). Keeping
it separate lets the operator choose granular enforcement — e.g. allow
history-level strip on chat UIs while keeping RAG at block.

Outcome
-------
- Forged ``assistant``/``system`` turns coming from a compromised plugin
  are demoted and cannot re-prompt the model with elevated authority.
- External-origin snippets replayed across turns are stripped the same
  way they would have been on the original retrieval hop.
- Zero-dep (uses stdlib ``hmac`` only when a secret is provided).
"""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Optional

from aigis.filters.rag_context_filter import _DIRECTIVE_PATTERNS, _SENTENCE_SPLIT_RE
from aigis.filters.structured_query import _OVERRIDE_PATTERNS, _ROLE_TOKEN_PATTERNS

_VALID_ROLES = {"system", "user", "assistant", "tool", "external"}

# Directive phrases aimed at the assistant that should never appear inside
# a ``tool`` turn. Tools return data; they don't issue orders.
_TOOL_DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(you\s+must|you\s+should|you\s+are\s+required\s+to)\b", re.IGNORECASE),
    re.compile(r"\b(assistant|claude|gpt|model)\s*,?\s*(please|kindly)?\s*(do|run|execute|send|email|transfer)", re.IGNORECASE),
    re.compile(r"(アシスタント|モデル)は\s*.{0,20}\s*(してください|しなさい|すること)"),
)


@dataclass
class HistoryTurn:
    """A single turn of conversation history arriving at the aigis boundary."""

    role: str
    content: str
    # Optional HMAC-SHA256 hex digest over ``role|content`` produced by the
    # trusted emitter (our own backend) at write time. If provided, we can
    # reject turns that were inserted by a compromised client or plugin.
    tag: Optional[str] = None
    # Where the content originated. ``"trusted"`` = our own backend or a
    # vetted tool; ``"external"`` = scraped page, email, untrusted plugin.
    origin: str = "trusted"


@dataclass
class TurnFinding:
    index: int
    original_role: str
    final_role: str
    action: str  # "kept" | "stripped" | "demoted" | "quarantined"
    reasons: list[str] = field(default_factory=list)


@dataclass
class IntegrityResult:
    safe_turns: list[HistoryTurn]
    quarantined_turns: list[HistoryTurn]
    findings: list[TurnFinding]


def _expected_tag(secret: bytes, role: str, content: str) -> str:
    return hmac.new(secret, f"{role}|{content}".encode("utf-8"), sha256).hexdigest()


def _strip_hostile_sentences(text: str) -> tuple[str, list[str]]:
    sentences = _SENTENCE_SPLIT_RE.split(text)
    kept: list[str] = []
    reasons: list[str] = []
    for sent in sentences:
        stripped = sent.strip()
        if not stripped:
            continue
        hostile = False
        for p in _DIRECTIVE_PATTERNS:
            if p.search(stripped):
                reasons.append("directive_in_external")
                hostile = True
                break
        if hostile:
            continue
        for p in _ROLE_TOKEN_PATTERNS:
            if p.search(stripped):
                reasons.append("role_token_in_external")
                hostile = True
                break
        if hostile:
            continue
        kept.append(sent)
    return (" ".join(s.strip() for s in kept).strip(), reasons)


def _assistant_turn_is_forged(content: str) -> tuple[bool, str]:
    for p in _ROLE_TOKEN_PATTERNS:
        if p.search(content):
            return True, "role_token_in_assistant_turn"
    for p in _OVERRIDE_PATTERNS:
        if p.search(content):
            return True, "override_phrase_in_assistant_turn"
    return False, ""


def _tool_turn_is_forged(content: str) -> tuple[bool, str]:
    for p in _TOOL_DIRECTIVE_PATTERNS:
        if p.search(content):
            return True, "directive_in_tool_turn"
    for p in _ROLE_TOKEN_PATTERNS:
        if p.search(content):
            return True, "role_token_in_tool_turn"
    return False, ""


def verify_history(
    turns: list[HistoryTurn],
    *,
    secret: Optional[bytes] = None,
    strict: bool = False,
) -> IntegrityResult:
    """Run integrity checks on a conversation history.

    Parameters
    ----------
    turns:
        The history as received by the LLM wrapper. May include turns
        inserted by plugins, browser extensions, or a compromised client.
    secret:
        If provided, each turn must carry a valid HMAC-SHA256 tag computed
        over ``role|content`` with this secret. Turns without a matching
        tag are demoted (``role`` → ``external``) before content checks.
    strict:
        When true, a forged assistant/tool turn is quarantined (dropped)
        instead of demoted. Use for high-risk flows (finance, healthcare).
    """
    assert all(t.role in _VALID_ROLES for t in turns), (
        f"unknown role; expected one of {_VALID_ROLES}"
    )

    safe: list[HistoryTurn] = []
    quarantined: list[HistoryTurn] = []
    findings: list[TurnFinding] = []

    for idx, turn in enumerate(turns):
        reasons: list[str] = []
        role = turn.role
        origin = turn.origin

        # Step 1 — provenance. A missing or wrong tag demotes the turn.
        if secret is not None:
            if not turn.tag or not hmac.compare_digest(
                turn.tag, _expected_tag(secret, turn.role, turn.content)
            ):
                reasons.append("provenance_tag_missing_or_invalid")
                role = "external"
                origin = "external"

        # Step 2 — role coherence.
        if role == "assistant":
            forged, why = _assistant_turn_is_forged(turn.content)
            if forged:
                reasons.append(why)
                if strict:
                    quarantined.append(turn)
                    findings.append(
                        TurnFinding(
                            index=idx,
                            original_role=turn.role,
                            final_role=role,
                            action="quarantined",
                            reasons=reasons,
                        )
                    )
                    continue
                role = "external"
                origin = "external"
        elif role == "tool":
            forged, why = _tool_turn_is_forged(turn.content)
            if forged:
                reasons.append(why)
                if strict:
                    quarantined.append(turn)
                    findings.append(
                        TurnFinding(
                            index=idx,
                            original_role=turn.role,
                            final_role=role,
                            action="quarantined",
                            reasons=reasons,
                        )
                    )
                    continue
                role = "external"
                origin = "external"

        # Step 3 — origin mixing. External content is stripped of directives.
        content = turn.content
        if origin == "external":
            new_content, strip_reasons = _strip_hostile_sentences(turn.content)
            if strip_reasons:
                reasons.extend(strip_reasons)
            if not new_content:
                quarantined.append(turn)
                findings.append(
                    TurnFinding(
                        index=idx,
                        original_role=turn.role,
                        final_role=role,
                        action="quarantined",
                        reasons=reasons or ["external_content_fully_hostile"],
                    )
                )
                continue
            content = new_content

        action = "kept"
        if role != turn.role:
            action = "demoted"
        elif content != turn.content:
            action = "stripped"

        safe.append(HistoryTurn(role=role, content=content, tag=turn.tag, origin=origin))
        findings.append(
            TurnFinding(
                index=idx,
                original_role=turn.role,
                final_role=role,
                action=action,
                reasons=reasons,
            )
        )

    return IntegrityResult(
        safe_turns=safe,
        quarantined_turns=quarantined,
        findings=findings,
    )


def sign_turn(secret: bytes, role: str, content: str) -> str:
    """Produce the HMAC tag an emitter should attach to a new history turn."""
    return _expected_tag(secret, role, content)
