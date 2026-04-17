"""Structured-query boundary enforcement.

Inspired by StruQ (arxiv:2402.06363) — defending against prompt injection
by treating the prompt as a structured message with a hard separation
between trusted *instructions* and untrusted *data*. When a model is
prompted with ``system + instruction + data`` concatenated flat, the
model has no way to tell that a chunk of ``data`` is actually impersonating
a new ``instruction``. StruQ proposes to render the prompt with explicit
role tokens and reject any input that contains those tokens.

Mechanism
---------
1. ``StructuredMessage`` represents a prompt as three role-tagged slots:
   ``system``, ``instruction``, ``data``.
2. Each slot is scanned for *boundary-crossing* content:
   * role tokens (``<|system|>``, ``<|user|>``, ``<|assistant|>``, ``[INST]``,
     ``### Instruction:``, ``<system>``, etc.) appearing inside ``data``,
   * chat-markup tokens that only make sense at the top of the prompt,
   * prompt-override phrases in ``data`` (``ignore previous``,
     ``new instructions``) caught by a compact subset of patterns here
     for early rejection, without duplicating the full scanner.
3. ``render()`` emits a safely-delimited prompt string and raises
   ``BoundaryViolation`` when the untrusted ``data`` would cross into the
   instruction plane.

Why add this, what changes
--------------------------
The existing scanner finds these phrases anywhere in the input. This
module adds the *structural* check: the distinction between "user asked
the model to paraphrase a suspicious sentence" (legitimate) versus
"retrieved document contains a fake role token intending to reset the
prompt" (attack). StruQ-style separation is the canonical defense against
indirect injection via retrieved content — the same attack vector
highlighted in the LLMail-Inject dataset (arxiv:2506.09956).

Outcome
-------
- Callers who wrap their prompts with ``StructuredMessage.render()`` get a
  hard error before an unsafe prompt is ever sent to the LLM.
- Works together with ``rag_context_filter.py`` (T7): the filter sanitizes
  retrieved chunks, the structured-query wrapper makes any surviving
  boundary token a fatal error rather than a silent vulnerability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Role tokens used by common chat templates. Any of these inside untrusted
# data is suspicious: legitimate data rarely contains both a role name and
# the surrounding delimiters.
_ROLE_TOKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"<\|\s*(system|user|assistant|tool|developer)\s*\|>", re.IGNORECASE),
    re.compile(r"<\s*(system|assistant|tool)\s*>", re.IGNORECASE),
    re.compile(r"\[\s*(INST|/INST|SYS|/SYS)\s*\]", re.IGNORECASE),
    re.compile(r"^\s*###\s*(system|instruction|user|assistant)\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"<\s*\|im_(start|end)\s*\|\s*>", re.IGNORECASE),  # ChatML
    re.compile(r"```\s*(system|user|assistant)\s*$", re.IGNORECASE | re.MULTILINE),
)

# Compact override-phrase set — duplicates a slice of scanner patterns on
# purpose so callers can use structured_query standalone without spinning
# up the full scanner.
_OVERRIDE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(ignore|disregard|forget|override|bypass)\s+(the\s+)?(previous|prior|above|all|your|any)\s+(instructions?|rules?|guidelines?|prompts?)",
        re.IGNORECASE,
    ),
    re.compile(r"\b(new|updated)\s+instructions?\s*[:\-]", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"\b(これまで|今まで|以前)の(指示|ルール)を(無視|破棄|忘れ)", re.IGNORECASE),
)


@dataclass
class BoundaryFinding:
    slot: str  # "system" | "instruction" | "data"
    kind: str  # "role_token" | "override_phrase"
    match: str  # the offending substring (truncated)


class BoundaryViolation(ValueError):
    def __init__(self, findings: list[BoundaryFinding]) -> None:
        self.findings = findings
        super().__init__(self._render_message())

    def _render_message(self) -> str:
        head = self.findings[0]
        return (
            f"structured-query boundary violation in {head.slot!r}: "
            f"{head.kind}={head.match!r} (plus {len(self.findings) - 1} more)"
        )


@dataclass
class StructuredMessage:
    """A prompt split into trusted/untrusted slots."""

    system: str = ""
    instruction: str = ""
    data: str = ""

    def findings(self, strict: bool = True) -> list[BoundaryFinding]:
        """Return every boundary violation detected.

        ``strict=True`` (default) also scans the ``instruction`` slot for
        role tokens — protecting against accidental self-injection in
        operator-authored instructions.
        """
        out: list[BoundaryFinding] = []
        # Data is untrusted by definition — scan hard.
        for p in _ROLE_TOKEN_PATTERNS:
            for m in p.finditer(self.data):
                out.append(BoundaryFinding("data", "role_token", m.group(0)[:120]))
        for p in _OVERRIDE_PATTERNS:
            m = p.search(self.data)
            if m:
                out.append(BoundaryFinding("data", "override_phrase", m.group(0)[:120]))
        if strict:
            for p in _ROLE_TOKEN_PATTERNS:
                for m in p.finditer(self.instruction):
                    out.append(BoundaryFinding("instruction", "role_token", m.group(0)[:120]))
        return out

    def render(self, strict: bool = True) -> str:
        """Render to a delimited prompt, raising on any boundary violation."""
        fs = self.findings(strict=strict)
        if fs:
            raise BoundaryViolation(fs)
        parts: list[str] = []
        if self.system:
            parts.append(f"<|aigis:system|>\n{self.system}\n<|/aigis:system|>")
        if self.instruction:
            parts.append(f"<|aigis:instruction|>\n{self.instruction}\n<|/aigis:instruction|>")
        if self.data:
            parts.append(f"<|aigis:data|>\n{self.data}\n<|/aigis:data|>")
        return "\n\n".join(parts)
