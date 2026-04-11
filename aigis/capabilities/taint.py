"""Taint tracking for data provenance in the CaMeL security model.

Every value flowing through the system carries a taint label indicating
whether it originated from a trusted source (system prompt, user
confirmation) or an untrusted source (tool output, external API, RAG
retrieval).  Untrusted values can never be promoted directly to trusted
without passing through a security scan first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aigis.scanner import ScanResult


class TaintLabel(StrEnum):
    """Data provenance classification."""

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    SANITIZED = "sanitized"


@dataclass
class TaintedValue:
    """A value annotated with its data-provenance taint label.

    Args:
        value: The wrapped payload (any type).
        taint: Current taint classification.
        source: Human-readable origin description (e.g. "tool:file_read", "rag:chunk_3").
        scan_result: Result from an Aigis scan, if one was performed.
        promotion_history: Audit trail of taint promotions applied to this value.
    """

    value: Any
    taint: TaintLabel
    source: str
    scan_result: ScanResult | None = None
    promotion_history: list[dict] = field(default_factory=list)

    def promote(self, new_taint: TaintLabel, reason: str) -> TaintedValue:
        """Return a new TaintedValue with an updated taint label.

        Enforces the critical invariant: UNTRUSTED cannot be promoted
        directly to TRUSTED.  The caller must scan the value first
        (producing a SANITIZED intermediate) before promoting to TRUSTED.

        Args:
            new_taint: The target taint label.
            reason: Justification for the promotion (logged for audit).

        Returns:
            A new TaintedValue with the updated taint and audit trail.

        Raises:
            ValueError: If attempting UNTRUSTED -> TRUSTED without scanning.
        """
        if self.taint == TaintLabel.UNTRUSTED and new_taint == TaintLabel.TRUSTED:
            raise ValueError(
                "Cannot promote UNTRUSTED directly to TRUSTED. "
                "Scan the value first to obtain SANITIZED status, "
                "then promote SANITIZED -> TRUSTED."
            )
        if self.taint == new_taint:
            return self

        entry = {
            "from": str(self.taint),
            "to": str(new_taint),
            "reason": reason,
        }
        new_history = [*self.promotion_history, entry]

        return TaintedValue(
            value=self.value,
            taint=new_taint,
            source=self.source,
            scan_result=self.scan_result,
            promotion_history=new_history,
        )

    @property
    def is_trusted(self) -> bool:
        return self.taint == TaintLabel.TRUSTED

    @property
    def is_untrusted(self) -> bool:
        return self.taint == TaintLabel.UNTRUSTED

    def __repr__(self) -> str:
        val_repr = repr(self.value)
        if len(val_repr) > 60:
            val_repr = val_repr[:57] + "..."
        return f"TaintedValue({val_repr}, taint={self.taint!r}, source={self.source!r})"
