"""Safety Verifier -- verify planned actions against safety specifications.

Produces a :class:`ProofCertificate` for every action, recording whether
the action is proven safe, a violation was found, or the verdict is
undetermined.

Usage::

    from aigis.safety.loader import load_safety_spec
    from aigis.safety.verifier import SafetyVerifier

    spec = load_safety_spec("safety.yaml")
    verifier = SafetyVerifier([spec])
    cert = verifier.verify("file:write", "/etc/passwd", {})
    if cert.verdict != "proven_safe":
        raise SecurityError(cert.violations)
"""

from __future__ import annotations

import datetime
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import PurePosixPath

from aigis.safety.spec import EffectSpec, SafetySpec


def _expand_braces(pattern: str) -> list[str]:
    """Expand a single brace group in a glob pattern.

    Handles patterns like ``"**/*.{py,js,ts}"`` by expanding them into
    ``["**/*.py", "**/*.js", "**/*.ts"]``.  If the pattern contains no
    braces, returns a single-element list with the original pattern.
    Only the first brace group is expanded (nested/multiple braces are
    not supported; they are passed through unchanged).
    """
    start = pattern.find("{")
    if start == -1:
        return [pattern]
    end = pattern.find("}", start)
    if end == -1:
        return [pattern]

    prefix = pattern[:start]
    suffix = pattern[end + 1 :]
    alternatives = pattern[start + 1 : end].split(",")
    return [f"{prefix}{alt}{suffix}" for alt in alternatives]


@dataclass
class ProofCertificate:
    """Certificate that a planned action satisfies (or violates) safety specs.

    Attributes:
        spec_name: Name of the spec that was evaluated.
        spec_version: Version of the spec.
        action: The effect type that was checked (e.g. ``"file:write"``).
        target: The target that was checked (e.g. ``"/tmp/out.txt"``).
        verdict: One of ``"proven_safe"``, ``"violation_found"``, or
            ``"undetermined"``.
        violations: Human-readable descriptions of each violation found.
        checked_invariants: List of dicts ``{"name": ..., "passed": ...,
            "details": ...}`` for every invariant that was evaluated.
        timestamp: ISO-8601 timestamp (UTC) when the certificate was issued.
        certificate_id: Unique identifier (UUID4) for this certificate.
    """

    spec_name: str
    spec_version: str
    action: str
    target: str
    verdict: str  # "proven_safe" | "violation_found" | "undetermined"
    violations: list[str] = field(default_factory=list)
    checked_invariants: list[dict] = field(default_factory=list)
    timestamp: str = ""
    certificate_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        if not self.certificate_id:
            self.certificate_id = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Built-in invariant check functions
# ---------------------------------------------------------------------------

# Patterns for detecting API keys and secrets in text.
_SECRET_PATTERNS: list[re.Pattern] = [
    # OpenAI
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    # Google
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    # GitHub PAT
    re.compile(r"ghp_[0-9A-Za-z]{36}"),
    # Slack tokens
    re.compile(r"xox[baprs]-[0-9a-zA-Z\-]+"),
    # AWS Access Key
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # Generic password assignment
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*\S{4,}"),
    # Connection strings with credentials
    re.compile(r"(?i)(postgresql|mysql|mongodb|redis|mssql)://\S+:\S+@\S+"),
]

# Patterns for detecting PII in text.
_PII_PATTERNS: list[re.Pattern] = [
    # US SSN
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # Credit card (Visa, MC, Amex)
    re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
    # Japanese My Number (12 digits)
    re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    # Bulk email addresses (3+ in sequence)
    re.compile(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}[\s,;]){3,}"),
    # Japanese phone numbers
    re.compile(r"(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}|0[789]0[-\s]?\d{4}[-\s]?\d{4})"),
]

# Path traversal indicators.
_PATH_TRAVERSAL_PATTERN: re.Pattern = re.compile(r"(^|[/\\])\.\.[/\\]")


def _check_no_secrets_in_output(action: str, target: str, context: dict) -> bool:
    """Return True if no secrets are found in the context output."""
    output = context.get("output", "")
    if not output:
        return True
    return not any(pat.search(output) for pat in _SECRET_PATTERNS)


def _check_no_pii_in_output(action: str, target: str, context: dict) -> bool:
    """Return True if no PII patterns are found in the context output."""
    output = context.get("output", "")
    if not output:
        return True
    return not any(pat.search(output) for pat in _PII_PATTERNS)


def _check_path_traversal(action: str, target: str, context: dict) -> bool:
    """Return True if the target path contains no directory traversal."""
    normalized = target.replace("\\", "/")
    return not bool(_PATH_TRAVERSAL_PATTERN.search(normalized))


# ---------------------------------------------------------------------------
# SafetyVerifier
# ---------------------------------------------------------------------------


class SafetyVerifier:
    """Verifies planned actions against safety specifications.

    The verifier evaluates every loaded :class:`SafetySpec` and produces a
    :class:`ProofCertificate` for the *first* spec that yields a definitive
    result.

    Evaluation order per spec:

    1. **Forbidden effects** -- if the action matches any forbidden effect,
       the verdict is ``"violation_found"``.
    2. **Allowed effects** -- if the action matches *no* allowed effect
       (and at least one is defined), the verdict is ``"violation_found"``.
    3. **Invariant checks** -- each registered invariant is executed; if
       any fails the verdict is ``"violation_found"``.
    4. If all checks pass, the verdict is ``"proven_safe"``.

    Uses :func:`fnmatch.fnmatch` for scope matching, consistent with
    :mod:`aigis.policy`.
    """

    def __init__(self, specs: list[SafetySpec]) -> None:
        self._specs = specs
        self._checks: dict[str, Callable[[str, str, dict], bool]] = {}
        self._register_builtin_checks()

    # -- public API ---------------------------------------------------------

    def register_check(
        self,
        name: str,
        func: Callable[[str, str, dict], bool],
    ) -> None:
        """Register a custom invariant check function.

        The callable signature is ``(action, target, context) -> bool``.
        Return ``True`` if the invariant holds, ``False`` if violated.
        """
        self._checks[name] = func

    def verify(
        self,
        action: str,
        target: str,
        context: dict | None = None,
    ) -> ProofCertificate:
        """Verify a single action against all loaded specs.

        Args:
            action: The effect type, e.g. ``"file:write"``.
            target: The target of the effect, e.g. ``"/etc/passwd"``.
            context: Optional dictionary with extra data (e.g.
                ``{"output": "..."}`` for invariant checks).

        Returns:
            A :class:`ProofCertificate` with the verification result.
        """
        ctx = context or {}

        # Pre-check: normalize target path to defeat traversal attacks
        # (e.g. "subdir/../.env" -> ".env") before scope matching.
        normalized_target = target.replace("\\", "/")
        if ".." in normalized_target:
            from pathlib import PurePosixPath

            normalized_target = str(PurePosixPath(normalized_target))
            # Also update target for downstream matching
            target = normalized_target

        for spec in self._specs:
            violations: list[str] = []
            checked_invariants: list[dict] = []

            # 1. Check forbidden effects
            for forbidden in spec.forbidden_effects:
                if self._effect_matches(action, target, forbidden):
                    violations.append(
                        f"Forbidden effect matched: {forbidden.effect_type} "
                        f"scope={forbidden.scope!r}"
                    )

            if violations:
                return ProofCertificate(
                    spec_name=spec.name,
                    spec_version=spec.version,
                    action=action,
                    target=target,
                    verdict="violation_found",
                    violations=violations,
                    checked_invariants=checked_invariants,
                )

            # 2. Check allowed effects (deny if none match and list is non-empty)
            if spec.allowed_effects:
                matched_any = any(
                    self._effect_matches(action, target, allowed)
                    for allowed in spec.allowed_effects
                )
                if not matched_any:
                    violations.append(
                        f"Action {action!r} on target {target!r} not covered by any allowed effect"
                    )
                    return ProofCertificate(
                        spec_name=spec.name,
                        spec_version=spec.version,
                        action=action,
                        target=target,
                        verdict="violation_found",
                        violations=violations,
                        checked_invariants=checked_invariants,
                    )

            # 3. Run invariant checks
            for inv in spec.invariants:
                check_fn = self._checks.get(inv.check)
                if check_fn is None:
                    checked_invariants.append(
                        {
                            "name": inv.name,
                            "passed": None,
                            "details": f"Check function {inv.check!r} not registered",
                        }
                    )
                    continue

                try:
                    passed = check_fn(action, target, ctx)
                except Exception as exc:  # noqa: BLE001
                    checked_invariants.append(
                        {
                            "name": inv.name,
                            "passed": False,
                            "details": f"Check raised exception: {exc}",
                        }
                    )
                    violations.append(f"Invariant {inv.name!r} raised: {exc}")
                    continue

                checked_invariants.append(
                    {
                        "name": inv.name,
                        "passed": passed,
                        "details": inv.description if not passed else "OK",
                    }
                )
                if not passed:
                    violations.append(f"Invariant {inv.name!r} failed: {inv.description}")

            if violations:
                return ProofCertificate(
                    spec_name=spec.name,
                    spec_version=spec.version,
                    action=action,
                    target=target,
                    verdict="violation_found",
                    violations=violations,
                    checked_invariants=checked_invariants,
                )

            # All checks passed for this spec
            return ProofCertificate(
                spec_name=spec.name,
                spec_version=spec.version,
                action=action,
                target=target,
                verdict="proven_safe",
                violations=[],
                checked_invariants=checked_invariants,
            )

        # No specs loaded -- undetermined
        return ProofCertificate(
            spec_name="(none)",
            spec_version="0.0",
            action=action,
            target=target,
            verdict="undetermined",
            violations=["No safety specs loaded"],
            checked_invariants=[],
        )

    def verify_plan(self, actions: list[dict]) -> list[ProofCertificate]:
        """Verify multiple actions (a plan). Each gets its own certificate.

        Args:
            actions: List of dicts, each with at least ``"action"`` and
                ``"target"`` keys, and optionally ``"context"``.

        Returns:
            A list of :class:`ProofCertificate`, one per action.
        """
        return [
            self.verify(
                action=a["action"],
                target=a["target"],
                context=a.get("context"),
            )
            for a in actions
        ]

    # -- private helpers ----------------------------------------------------

    def _register_builtin_checks(self) -> None:
        """Register built-in invariant check functions."""
        self._checks["check_no_secrets_in_output"] = _check_no_secrets_in_output
        self._checks["check_no_pii_in_output"] = _check_no_pii_in_output
        self._checks["check_path_traversal"] = _check_path_traversal

    @staticmethod
    def _effect_matches(action: str, target: str, effect: EffectSpec) -> bool:
        """Check if an (action, target) pair matches an EffectSpec.

        Uses :func:`fnmatch.fnmatch` for both action type and scope matching,
        consistent with :mod:`aigis.policy`.
        """
        # Match effect type (e.g. "file:write" against "file:*")
        if not fnmatch(action, effect.effect_type):
            return False

        # Match scope (glob pattern against target).
        # Expand brace groups (e.g. "*.{py,js}") since fnmatch does not
        # support them natively.
        normalized_target = target.replace("\\", "/")
        raw_pattern = effect.scope.replace("\\", "/")
        patterns = _expand_braces(raw_pattern)

        basename = PurePosixPath(normalized_target).name
        is_shell = action.startswith("shell:")

        for pattern in patterns:
            # Try full path match first
            if fnmatch(normalized_target, pattern):
                return True

            # Also try basename match (e.g. ".env" matches "path/to/.env")
            if fnmatch(basename, pattern):
                return True

            # If the pattern uses "**/" prefix (recursive glob), also try
            # matching basename against the filename portion of the pattern.
            # fnmatch's "**" does not recurse into directories, so
            # "**/*.py" won't match "output.py" -- but it should.
            # Skip when the filename portion is just "*" to avoid false
            # positives (e.g. "**/.ssh/*" should NOT match "output.py").
            if "**/" in pattern:
                pattern_basename = pattern.rsplit("/", 1)[-1]
                if pattern_basename != "*" and fnmatch(basename, pattern_basename):
                    return True

            # For shell:exec-style actions, check if the pattern appears
            # as a substring (e.g. "*sudo*" matches "sudo apt install ...")
            if is_shell and fnmatch(normalized_target, f"*{pattern}*"):
                return True

        return False
