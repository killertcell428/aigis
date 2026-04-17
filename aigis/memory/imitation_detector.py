"""Semantic-imitation detector for stored agent experiences.

Targets the attack class introduced by MemoryGraft (arxiv:2512.16962, Dec
2025), where an adversary inserts benign-looking *experience* entries into
an agent's long-term memory. The entries do not contain overt injection
phrases — instead they imitate the *shape* of the agent's own system
prompt and exemplars. At retrieval time, the agent's "semantic imitation
heuristic" treats them as authoritative guidance, producing persistent
behavioural drift that the ordinary content-based memory scanner
(``aigis/memory/scanner.py``) cannot catch.

Mechanism
---------
1. The operator registers canonical *reference* texts that define the
   agent's intended voice: system prompt, exemplars, known-good
   instructions. These live in an ``ExperienceReference`` set.
2. A candidate experience entry is compared against the reference set by
   structural + lexical similarity (character-ngram Jaccard, not a
   neural embedding — we keep aigis's zero-dep promise).
3. Entries that look *too much* like the system voice are flagged with
   an ``ImitationFinding``. High similarity in an untrusted source
   ("user", "tool", retrieved document) is the warning sign.
4. The caller can either quarantine the entry outright or downgrade its
   retrieval priority via the existing ``memory/integrity.py`` TTL
   controls.

Why we add this
---------------
``memory/scanner.py`` already handles *explicit* memory poisoning
(hidden instructions, persona override, sleeper triggers). MemoryGraft
evades all of those because the planted entries do not look like
instructions — they look like lessons the agent itself wrote.
Structural-imitation detection fills that gap without model weights.

Outcome
-------
- Entries from untrusted sources that mimic system-voice structure are
  flagged and can be quarantined before they are ever retrieved again.
- Complements, rather than replaces, the content-pattern scanner: both
  signals feed into ``MemoryScanResult.recommendation``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aigis.memory.scanner import MemoryEntry

_NGRAM_N = 4
# Empirically chosen: ~0.55 ngram overlap is where an entry starts to look
# like paraphrased system content rather than legitimately similar text.
DEFAULT_THRESHOLD = 0.55


def _char_ngrams(text: str, n: int = _NGRAM_N) -> set[str]:
    text = text.lower().strip()
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass
class ExperienceReference:
    """Canonical agent-voice sample: system prompt, exemplar, etc."""

    label: str  # "system_prompt" | "exemplar" | "golden_response" | custom
    text: str
    _ngrams: set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        self._ngrams = _char_ngrams(self.text)


@dataclass
class ImitationFinding:
    entry_key: str
    matched_reference: str  # label of the most similar reference
    similarity: float  # 0.0 - 1.0
    reason: str
    source: str  # copy of MemoryEntry.source for downstream routing


class ImitationDetector:
    """Flag memory entries that structurally imitate the system voice."""

    # Sources that are trusted — matches here are legitimate agent voice.
    _TRUSTED_SOURCES: frozenset[str] = frozenset({"system"})

    def __init__(
        self,
        references: list[ExperienceReference] | None = None,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.references: list[ExperienceReference] = references or []
        self.threshold = threshold

    def add_reference(self, label: str, text: str) -> None:
        self.references.append(ExperienceReference(label=label, text=text))

    def check(self, entry: MemoryEntry) -> ImitationFinding | None:
        if entry.source in self._TRUSTED_SOURCES or not self.references:
            return None
        candidate = _char_ngrams(entry.content)
        if not candidate:
            return None
        best_label = ""
        best_sim = 0.0
        for ref in self.references:
            sim = _jaccard(candidate, ref._ngrams)
            if sim > best_sim:
                best_sim = sim
                best_label = ref.label
        if best_sim < self.threshold:
            return None
        return ImitationFinding(
            entry_key=entry.key,
            matched_reference=best_label,
            similarity=best_sim,
            reason=(
                f"entry from untrusted source {entry.source!r} structurally imitates "
                f"reference {best_label!r} (jaccard={best_sim:.2f} >= {self.threshold:.2f})"
            ),
            source=entry.source,
        )
