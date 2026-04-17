"""Safe compilation of user-supplied regexes.

User-defined ``custom_rules`` accept arbitrary patterns; a poorly formed or
maliciously crafted regex can:
  - crash the scanner (re.error),
  - silently disable scanning if exceptions are swallowed,
  - exhaust CPU via catastrophic backtracking (ReDoS).

``safe_compile_user_regex`` rejects patterns that fail any of the below checks
instead of returning them. Callers should treat a ``None`` return as a hard
failure and surface it (log + matched-rule marker) rather than continuing
silently — so that an operator can see which rule is broken.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Upper bound on pattern length. 2 KB is ample for legitimate rules and
# resists adversarially-large patterns submitted to the policy API.
_MAX_PATTERN_LEN = 2048

# Nested-quantifier detector: a parenthesized group whose *contents* include
# a quantifier (* + ? or {n,m}), followed by another quantifier outside the
# group. This is the classic ReDoS shape: (a+)+, (a*)+, (a+)*, (.+)+, etc.
_NESTED_QUANT_RE = re.compile(r"\([^()]*[\*\+\?\{][^()]*\)[\*\+\?\{]")

# Unbounded alternation inside a group with a trailing quantifier:
# "(a|ab)+", "(x|x|x)*", a common ReDoS source. Conservative — flags groups
# that contain | and are immediately followed by + * ? or {n,m}.
_ALT_QUANT_RE = re.compile(r"\([^()]*\|[^()]*\)[\*\+\?\{]")


class UnsafeRegexError(ValueError):
    """Raised when a user regex fails safety checks."""


def _check_pattern_safety(pattern: str) -> None:
    if len(pattern) > _MAX_PATTERN_LEN:
        raise UnsafeRegexError(f"pattern exceeds {_MAX_PATTERN_LEN} chars")
    if _NESTED_QUANT_RE.search(pattern):
        raise UnsafeRegexError("nested quantifier (ReDoS risk)")
    if _ALT_QUANT_RE.search(pattern):
        raise UnsafeRegexError("quantified alternation group (ReDoS risk)")


def safe_compile_user_regex(
    pattern: str,
    flags: int = re.IGNORECASE | re.DOTALL,
) -> re.Pattern[str] | None:
    """Compile a user-supplied regex or return None if it's unsafe/invalid.

    Never raises — callers get ``None`` and should record a diagnostic.
    """
    try:
        _check_pattern_safety(pattern)
        return re.compile(pattern, flags)
    except (re.error, UnsafeRegexError) as exc:
        logger.warning("Rejected user regex: %s (len=%d)", exc, len(pattern))
        return None
