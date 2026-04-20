"""Meeting-transcript PII and sensitivity classifier.

Motivated by the April 2026 wave of AI-meeting-assistant incidents:

* **Fireflies.AI class action** (Apr 2026): plaintiffs who never installed
  Fireflies, never accepted the ToS, and never consented to biometric
  collection alleged that the bot joined meetings they attended and
  captured their voiceprints. The complaint invokes Illinois BIPA.
* **Healthcare incident**: an auto-join note-taker distributed a
  transcript containing patient PHI to an entire mailing list before
  anyone noticed it was on the call.
* Industry commentary in April 2026 began framing AI meeting assistants
  as "the biggest security risk in your office".

This module sits between "raw transcript" and "summary / storage". It
does three things a summariser cannot do on its own:

1. Classify each segment's **sensitivity** (public / internal /
   confidential / regulated) using fast keyword rules and structural
   cues — a transcript containing patient IDs, salary figures, or trade
   secrets should never be summarised into a channel that can't hold it.
2. Mark **biometric / consent-relevant segments**: anyone who says "I
   do not consent to recording" or "please stop the bot", along with
   the preceding few seconds of speech that may already have been
   captured. Operators can then prune these from storage to stay on
   the BIPA / GDPR side of the line.
3. Redact **direct PII** before the transcript is handed downstream
   (e-mail addresses, phone numbers, Japanese マイナンバー, SSNs, credit
   cards). Redaction is non-destructive — the caller can fetch the
   redaction map alongside the transcript for audit.

Why a dedicated module
----------------------
Generic PII scanners run on strings. A meeting transcript is a sequence
of ``Segment(speaker, ts, text)`` tuples where context matters: the
sensitivity of a segment often depends on whether the previous speaker
was identified as, e.g., "Legal" or "HR". Classifying segment-by-segment
lets callers apply different retention / sharing rules to different
parts of the same call — for example, strip the five minutes in the
middle where the CFO reads out account numbers, but keep the 25
surrounding minutes.

Outcome
-------
- A caller can enforce, e.g., "do not summarise any segment classified
  ``regulated`` into a non-SOC-2 target" with a single boolean check.
- Consent-withdrawn segments are flagged for deletion rather than
  silently persisted.
- Zero-dep; Japanese + English coverage out of the box.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Sensitivity = Literal["public", "internal", "confidential", "regulated"]


@dataclass
class Segment:
    """One chunk of transcript. ``speaker`` may be empty if unknown."""

    speaker: str
    ts: float  # seconds from start of meeting
    text: str


@dataclass
class SegmentClassification:
    index: int
    sensitivity: Sensitivity
    pii_kinds: list[str] = field(default_factory=list)
    consent_flag: bool = False
    reasons: list[str] = field(default_factory=list)


@dataclass
class TranscriptReport:
    classifications: list[SegmentClassification]
    redacted_segments: list[Segment]
    redaction_map: dict[str, str]
    overall_sensitivity: Sensitivity


# --- PII patterns -----------------------------------------------------------

_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    # Phone: JP-style (0XX-XXXX-XXXX, +81-...) and US/EU-ish.
    ("phone_jp", re.compile(r"\b0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4}\b")),
    ("phone_intl", re.compile(r"\+\d{1,3}[-\s]?\d{2,4}[-\s]?\d{2,4}[-\s]?\d{2,4}\b")),
    # Japanese マイナンバー — 12 consecutive digits.
    ("mynumber", re.compile(r"(?<!\d)\d{12}(?!\d)")),
    # US SSN-ish.
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Credit card — 13-16 digits optionally separated by spaces or hyphens.
    ("credit_card", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    # Japanese passport: 1 letter + 8 digits.
    ("passport_jp", re.compile(r"\b[A-Z]{1,2}\d{7,8}\b")),
)


# --- Sensitivity cues -------------------------------------------------------

# Regulated: health, legal, finance-PCI, children, biometric / voiceprint.
_REGULATED_CUES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(patient|diagnosis|prescription|PHI|HIPAA|medical\s+record)\b", re.IGNORECASE),
    re.compile(r"(患者|診断|処方|カルテ|医療記録|病名)"),
    re.compile(r"\b(credit\s*card|cvv|cardholder|PCI-DSS|card\s+number)\b", re.IGNORECASE),
    re.compile(r"(クレジットカード|カード番号|セキュリティコード)"),
    re.compile(r"\b(minor|child\s+under|under\s+13|under\s+16)\b", re.IGNORECASE),
    re.compile(r"(未成年|児童)"),
    re.compile(r"\b(voiceprint|biometric|face\s*id|face\s+recognition)\b", re.IGNORECASE),
    re.compile(r"(声紋|生体認証|顔認証)"),
)

# Confidential: salary, M&A, legal strategy, trade secrets, personnel.
_CONFIDENTIAL_CUES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(salary|compensation|layoff|severance|firing|termination)\b", re.IGNORECASE),
    re.compile(r"(給与|賞与|年収|解雇|リストラ|人事評価)"),
    re.compile(r"\b(merger|acquisition|due\s*diligence|term\s*sheet|NDA)\b", re.IGNORECASE),
    re.compile(r"(M&A|買収|合併|機密保持|契約交渉)"),
    re.compile(r"\b(trade\s+secret|proprietary|confidential|under\s+seal)\b", re.IGNORECASE),
    re.compile(r"(営業秘密|社外秘|極秘|機密)"),
)

# Internal: roadmap, customer names, project code names.
_INTERNAL_CUES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(roadmap|next\s+release|internal\s+only|do\s+not\s+share)\b", re.IGNORECASE),
    re.compile(r"(ロードマップ|社内限|社外秘扱い|内部資料)"),
)

# Consent withdrawal — both soft and hard.
_CONSENT_CUES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(i\s+do\s+not\s+consent|stop\s+recording|turn\s+off\s+the\s+(bot|recorder|transcription))\b", re.IGNORECASE),
    re.compile(r"\b(remove\s+me\s+from\s+(this|the)\s+recording|don'?t\s+record\s+me)\b", re.IGNORECASE),
    re.compile(r"(録音(しないで|をやめて|を停止して)|議事録に残さないで|文字起こしを止めて|同意していません)"),
)


_SENSITIVITY_ORDER: tuple[Sensitivity, ...] = (
    "public",
    "internal",
    "confidential",
    "regulated",
)


def _max_sensitivity(a: Sensitivity, b: Sensitivity) -> Sensitivity:
    return a if _SENSITIVITY_ORDER.index(a) >= _SENSITIVITY_ORDER.index(b) else b


def _classify_one(text: str) -> tuple[Sensitivity, list[str], list[str], bool]:
    """Classify a single segment's text. Returns (level, pii_kinds, reasons, consent)."""
    pii_kinds: list[str] = []
    reasons: list[str] = []

    for kind, pat in _PII_PATTERNS:
        if pat.search(text):
            pii_kinds.append(kind)

    level: Sensitivity = "public"

    if any(p.search(text) for p in _REGULATED_CUES) or {
        "mynumber",
        "ssn",
        "credit_card",
        "passport_jp",
    }.intersection(pii_kinds):
        level = "regulated"
        reasons.append("regulated_cue_or_high_risk_pii")
    elif any(p.search(text) for p in _CONFIDENTIAL_CUES):
        level = "confidential"
        reasons.append("confidential_cue")
    elif any(p.search(text) for p in _INTERNAL_CUES) or pii_kinds:
        # Any PII present, even low-risk (email/phone), is at least internal.
        level = "internal"
        if pii_kinds:
            reasons.append(f"pii:{','.join(pii_kinds)}")
        else:
            reasons.append("internal_cue")

    consent = any(p.search(text) for p in _CONSENT_CUES)
    if consent:
        reasons.append("consent_withdrawn")

    return level, pii_kinds, reasons, consent


def _redact(text: str, redaction_map: dict[str, str]) -> str:
    out = text
    for kind, pat in _PII_PATTERNS:
        def _sub(m: re.Match[str]) -> str:
            raw = m.group(0)
            token = f"[REDACTED_{kind.upper()}_{len(redaction_map) + 1}]"
            redaction_map[token] = raw
            return token

        out = pat.sub(_sub, out)
    return out


def classify_transcript(
    segments: list[Segment],
    *,
    redact: bool = True,
    consent_lookback_seconds: float = 10.0,
) -> TranscriptReport:
    """Classify and optionally redact a meeting transcript.

    Parameters
    ----------
    segments:
        Speaker-attributed transcript in chronological order.
    redact:
        If true, return ``redacted_segments`` with PII replaced by
        ``[REDACTED_...]`` tokens. The plaintext is never mutated in place.
    consent_lookback_seconds:
        When a speaker withdraws consent at ``t``, segments whose ``ts``
        is within ``[t - lookback, t]`` are also consent-flagged so the
        caller can prune speech captured before the bot reacted.
    """
    classifications: list[SegmentClassification] = []
    redacted: list[Segment] = []
    rmap: dict[str, str] = {}
    overall: Sensitivity = "public"

    # First pass — per-segment classification.
    for i, seg in enumerate(segments):
        level, pii_kinds, reasons, consent = _classify_one(seg.text)
        classifications.append(
            SegmentClassification(
                index=i,
                sensitivity=level,
                pii_kinds=pii_kinds,
                consent_flag=consent,
                reasons=reasons,
            )
        )
        overall = _max_sensitivity(overall, level)

    # Second pass — propagate consent-withdrawal backwards.
    for i, cls in enumerate(classifications):
        if not cls.consent_flag:
            continue
        cutoff = segments[i].ts - consent_lookback_seconds
        for j in range(i - 1, -1, -1):
            if segments[j].ts < cutoff:
                break
            if not classifications[j].consent_flag:
                classifications[j].consent_flag = True
                classifications[j].reasons.append("consent_lookback")

    # Optional redaction.
    if redact:
        for seg in segments:
            redacted.append(
                Segment(speaker=seg.speaker, ts=seg.ts, text=_redact(seg.text, rmap))
            )

    return TranscriptReport(
        classifications=classifications,
        redacted_segments=redacted,
        redaction_map=rmap,
        overall_sensitivity=overall,
    )


def safe_to_summarise(
    report: TranscriptReport,
    *,
    target_clearance: Sensitivity = "internal",
) -> bool:
    """Convenience gate: true iff the target storage can hold this call."""
    return _SENSITIVITY_ORDER.index(report.overall_sensitivity) <= _SENSITIVITY_ORDER.index(
        target_clearance
    )
