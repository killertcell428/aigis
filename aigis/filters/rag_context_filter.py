"""RAG context filter — sanitise retrieved chunks before LLM ingestion.

Adds protection against corpus-poisoning attacks on retrieval-augmented
generation (RAG) systems. Two waves of research from late 2025 motivated
this module:

* **DataFilter** (arxiv:2510.19207, Oct 2025) — a model-agnostic
  pre-filter that removes malicious instructions from data while
  preserving benign content.
* **RAGDefender** (arxiv:2511.01268, Nov 2025) — a lightweight
  post-retrieval filter that discards adversarial passages before they
  reach the generator.

Both rely on the same insight: an instruction embedded in retrieved
content is only dangerous *after* retrieval, so scrubbing or dropping
the hostile text at that junction costs nothing at query time and
preserves the rest of the corpus.

Mechanism
---------
1. Caller passes a list of ``RetrievedChunk`` objects (text + source id).
2. Each chunk is scanned with two independent signals:
   * the ``filters.fast_screen`` n-gram screen (T1) — quick overall risk,
   * a small curated set of *directive* phrases that have no business in
     retrieved reference documents (e.g. "ignore the above", role tokens,
     fake system prompts). We reuse ``structured_query`` (T3) for the
     role-token check to avoid duplication.
3. Two enforcement modes are offered:
   * ``policy="strip"`` — remove offending sentences, keep the rest.
     Good default for corpora where an attacker may have poisoned a few
     sentences inside an otherwise useful document.
   * ``policy="block"`` — drop the entire chunk. Use when tolerance for
     poisoned text is zero (legal, medical, security advisories).
4. Returns a ``RAGFilterResult`` with the sanitised text and per-chunk
   decisions, so downstream systems can log / alert without losing the
   original retrieval context.

Why we add this, what changes
-----------------------------
The existing scanner focuses on *user input*. RAG pipelines add a second
untrusted surface — retrieved documents — where the same attacks apply
but with far more patience (the attacker plants once, the agent reads
many times). This module gives operators a single call-site to harden
that surface without touching their retriever.

Outcome
-------
- Poisoned passages are dropped or truncated *before* the LLM is called,
  eliminating the class of indirect-injection attacks covered by
  DataFilter/RAGDefender evaluations.
- Zero-dep implementation — callers keep aigis's install story.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from aigis.filters.fast_screen import THRESHOLD_BLOCK, THRESHOLD_WARN, screen
from aigis.filters.structured_query import _ROLE_TOKEN_PATTERNS

# Directive phrases that legitimate reference content should never contain.
# Conservative — these are hard signals, not statistical ones.
_DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(ignore|disregard|forget|override|bypass)\s+(the\s+)?(above|previous|prior|instructions?|rules?)", re.IGNORECASE),
    re.compile(r"\bnew\s+instructions?\s*[:\-]", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"\bsystem\s*:\s", re.IGNORECASE),
    re.compile(r"\bassistant\s*:\s", re.IGNORECASE),
    re.compile(r"(これまで|今まで|以前)の(指示|ルール)を(無視|破棄|忘れ)", re.IGNORECASE),
)

# Sentence splitter — crude but language-agnostic. Good enough for chunk
# granularity; we are not parsing prose, only isolating offending lines.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?。！？])\s+|\n+")


@dataclass
class RetrievedChunk:
    """A single chunk from a retriever."""

    source_id: str
    text: str


@dataclass
class ChunkDecision:
    source_id: str
    action: str  # "kept" | "stripped" | "blocked"
    original_len: int
    final_len: int
    reasons: list[str] = field(default_factory=list)
    screen_score: float = 0.0


@dataclass
class RAGFilterResult:
    """Aggregate output of a filter pass."""

    chunks: list[RetrievedChunk]
    decisions: list[ChunkDecision]
    blocked_chunks: int
    stripped_chunks: int


def _sentence_is_hostile(sentence: str) -> tuple[bool, str]:
    for p in _DIRECTIVE_PATTERNS:
        if p.search(sentence):
            return True, f"directive:{p.pattern[:40]}"
    for p in _ROLE_TOKEN_PATTERNS:
        if p.search(sentence):
            return True, "role_token"
    return False, ""


def filter_chunks(
    chunks: list[RetrievedChunk],
    policy: str = "strip",
) -> RAGFilterResult:
    """Sanitise RAG chunks. ``policy`` is ``"strip"`` (default) or ``"block"``."""
    assert policy in {"strip", "block"}, "policy must be 'strip' or 'block'"
    out_chunks: list[RetrievedChunk] = []
    decisions: list[ChunkDecision] = []
    blocked = 0
    stripped = 0

    for chunk in chunks:
        original_len = len(chunk.text)
        reasons: list[str] = []
        scr = screen(chunk.text)

        # Block path — heavy screen score, or policy=block with any hostile signal.
        if scr.score >= THRESHOLD_BLOCK or (
            policy == "block" and any(p.search(chunk.text) for p in _DIRECTIVE_PATTERNS)
        ):
            reasons.append(f"screen={scr.score:.2f}")
            if scr.verdict != "benign":
                reasons.append(f"verdict={scr.verdict}")
            blocked += 1
            decisions.append(
                ChunkDecision(
                    source_id=chunk.source_id,
                    action="blocked",
                    original_len=original_len,
                    final_len=0,
                    reasons=reasons,
                    screen_score=scr.score,
                )
            )
            continue

        # Strip path — remove offending sentences but keep the rest.
        sentences = _SENTENCE_SPLIT_RE.split(chunk.text)
        kept: list[str] = []
        for sent in sentences:
            stripped_sent = sent.strip()
            if not stripped_sent:
                continue
            hostile, why = _sentence_is_hostile(stripped_sent)
            if hostile:
                reasons.append(why)
                continue
            kept.append(sent)

        new_text = " ".join(s.strip() for s in kept).strip()
        if new_text != chunk.text and new_text:
            stripped += 1
            decisions.append(
                ChunkDecision(
                    source_id=chunk.source_id,
                    action="stripped",
                    original_len=original_len,
                    final_len=len(new_text),
                    reasons=reasons,
                    screen_score=scr.score,
                )
            )
            out_chunks.append(RetrievedChunk(source_id=chunk.source_id, text=new_text))
        elif not new_text:
            # Whole chunk was hostile — drop like block path.
            blocked += 1
            decisions.append(
                ChunkDecision(
                    source_id=chunk.source_id,
                    action="blocked",
                    original_len=original_len,
                    final_len=0,
                    reasons=reasons or ["all_sentences_hostile"],
                    screen_score=scr.score,
                )
            )
        else:
            decisions.append(
                ChunkDecision(
                    source_id=chunk.source_id,
                    action="kept",
                    original_len=original_len,
                    final_len=len(new_text),
                    reasons=[],
                    screen_score=scr.score,
                )
            )
            out_chunks.append(chunk)

    return RAGFilterResult(
        chunks=out_chunks,
        decisions=decisions,
        blocked_chunks=blocked,
        stripped_chunks=stripped,
    )
