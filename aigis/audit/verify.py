"""Audit log verification — detect tampering in signed logs.

Performs four integrity checks:

1. **Signature verification** — each entry's HMAC-SHA256 matches.
2. **Chain verification** — each entry's ``prev_hash`` equals the hash of
   the preceding entry.
3. **Sequence verification** — sequence numbers are strictly monotonic
   (0, 1, 2, ...).
4. **Timestamp ordering** — ISO-8601 timestamps are non-decreasing.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from pathlib import Path

from aigis.audit.chain import HashChain
from aigis.audit.signed_log import SignedLogEntry


@dataclass
class VerificationResult:
    """Outcome of an audit log verification run."""

    valid: bool
    """``True`` when all checks pass."""

    total_entries: int
    """Number of entries examined."""

    checked_entries: int
    """Number of entries that were fully checked."""

    chain_valid: bool
    """``True`` when the hash chain is unbroken."""

    signature_valid: bool
    """``True`` when every entry's HMAC signature is correct."""

    broken_chain_at: list[int] = field(default_factory=list)
    """Sequence numbers where the chain is broken."""

    invalid_signatures_at: list[int] = field(default_factory=list)
    """Sequence numbers with incorrect HMAC signatures."""

    sequence_errors_at: list[int] = field(default_factory=list)
    """Sequence numbers where monotonic ordering is violated."""

    timestamp_errors_at: list[int] = field(default_factory=list)
    """Sequence numbers where timestamps go backwards."""

    summary: str = ""
    """Human-readable summary of verification results."""


class AuditVerifier:
    """Verify integrity of signed audit logs.

    Checks:
        1. Signature verification — each entry's HMAC matches.
        2. Chain verification — each entry's ``prev_hash`` matches
           previous entry's hash.
        3. Sequence verification — sequence numbers are monotonic.
        4. Timestamp ordering — timestamps are non-decreasing.

    Usage::

        verifier = AuditVerifier(secret_key="your-secret-key")
        result = verifier.verify_file("audit.jsonl")
        if not result.valid:
            print(result.summary)
    """

    def __init__(self, secret_key: str) -> None:
        self._key: bytes = secret_key.encode("utf-8")

    # -- Public API ---------------------------------------------------------

    def verify_entries(self, entries: list[SignedLogEntry]) -> VerificationResult:
        """Verify a list of :class:`SignedLogEntry` objects.

        Returns a :class:`VerificationResult` with details of any failures.
        """
        if not entries:
            return VerificationResult(
                valid=True,
                total_entries=0,
                checked_entries=0,
                chain_valid=True,
                signature_valid=True,
                summary="No entries to verify.",
            )

        invalid_sigs: list[int] = []
        seq_errors: list[int] = []
        ts_errors: list[int] = []

        # 1. Signature verification
        for entry in entries:
            if not self.verify_entry(entry):
                invalid_sigs.append(entry.sequence)

        # 2. Chain verification
        chain_valid, broken_chain = HashChain.verify_chain(entries)

        # 3. Sequence verification (must be strictly monotonic starting at 0)
        for i, entry in enumerate(entries):
            if entry.sequence != i:
                seq_errors.append(entry.sequence)

        # 4. Timestamp ordering (non-decreasing)
        for i in range(1, len(entries)):
            if entries[i].timestamp < entries[i - 1].timestamp:
                ts_errors.append(entries[i].sequence)

        all_valid = not invalid_sigs and chain_valid and not seq_errors and not ts_errors

        # Build summary
        parts: list[str] = []
        parts.append(f"Verified {len(entries)} entries.")
        if all_valid:
            parts.append("All checks passed — no tampering detected.")
        else:
            if invalid_sigs:
                parts.append(f"SIGNATURE FAILURE at sequence(s): {invalid_sigs}.")
            if broken_chain:
                parts.append(f"CHAIN BREAK at sequence(s): {broken_chain}.")
            if seq_errors:
                parts.append(f"SEQUENCE ERROR at: {seq_errors}.")
            if ts_errors:
                parts.append(f"TIMESTAMP ORDER ERROR at: {ts_errors}.")

        return VerificationResult(
            valid=all_valid,
            total_entries=len(entries),
            checked_entries=len(entries),
            chain_valid=chain_valid,
            signature_valid=len(invalid_sigs) == 0,
            broken_chain_at=broken_chain,
            invalid_signatures_at=invalid_sigs,
            sequence_errors_at=seq_errors,
            timestamp_errors_at=ts_errors,
            summary=" ".join(parts),
        )

    def verify_file(self, path: Path | str) -> VerificationResult:
        """Load a JSONL log file and verify all entries."""
        p = Path(path)
        entries: list[SignedLogEntry] = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(SignedLogEntry.from_dict(data))
        return self.verify_entries(entries)

    def verify_entry(self, entry: SignedLogEntry) -> bool:
        """Verify a single entry's HMAC signature.

        Returns ``True`` if the signature is valid.
        """
        entry_data = {
            "sequence": entry.sequence,
            "timestamp": entry.timestamp,
            "event_type": entry.event_type,
            "actor": entry.actor,
            "action": entry.action,
            "target": entry.target,
            "risk_score": entry.risk_score,
            "outcome": entry.outcome,
            "details": entry.details,
            "prev_hash": entry.prev_hash,
        }
        canonical = json.dumps(entry_data, sort_keys=True, ensure_ascii=False)
        expected = hmac.new(self._key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, entry.signature)
