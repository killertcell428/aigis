"""Common adapter interface — every guardrail tool plugs in via this protocol.

The driver does not know which tool it is talking to; it just calls ``check()``
on whatever adapter the user picked and writes the resulting verdict to CSV.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Verdict:
    """Outcome of one guardrail check on one input.

    Attributes
    ----------
    blocked:
        True when the tool would block this input. The benchmark treats
        "blocked" as "detected" for attacks and as "false positive" for
        safe baseline inputs.
    label:
        Tool-specific category label (e.g. ``"prompt_injection"``,
        ``"jailbreak"``, ``"toxicity"``). Stored for analysis but not used
        for scoring — scoring is binary blocked/allowed against the
        dataset's ground-truth label.
    score:
        Optional risk score in [0, 100]. Some tools expose this, others
        don't. Stored for analysis.
    error:
        If the tool errored on this input (timeout, malformed response),
        the error message goes here and the row is excluded from
        detection-rate math. The reporter surfaces error counts so we
        don't silently hide flaky tools.
    """

    blocked: bool
    label: str = ""
    score: float | None = None
    error: str | None = None


class Adapter(Protocol):
    """Every adapter exposes a name, a one-line config description, and
    a single ``check(text)`` method.

    Implementations must be deterministic given the same input + config —
    no random sampling, no LLM-judge layers that change the verdict run
    over run. If a tool's default config is non-deterministic, pin the
    seed in the adapter constructor.
    """

    name: str
    config_tier: str  # e.g. "default", "recommended", "owasp-llm-top10-preset"

    def check(self, text: str) -> Verdict:
        """Return the tool's verdict on ``text``.

        Must not raise. On error, return ``Verdict(blocked=False,
        error=...)`` so the driver can record the failure without
        crashing the whole run.
        """
