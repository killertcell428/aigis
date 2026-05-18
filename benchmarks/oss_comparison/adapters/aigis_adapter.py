"""Aigis adapter — runs in-process against the local checkout.

Uses the public ``Guard().check_input()`` API with the built-in ``"default"``
policy, no custom rules. This is the same surface a normal Aigis user gets.
"""

from __future__ import annotations

from benchmarks.oss_comparison.adapters.base import Verdict


class AigisAdapter:
    name = "aigis"
    config_tier = "default policy (built-in)"

    def __init__(self, policy: str = "default") -> None:
        from aigis import Guard

        self._guard = Guard(policy=policy)

    def check(self, text: str) -> Verdict:
        try:
            result = self._guard.check_input(text)
        except Exception as exc:  # noqa: BLE001 — adapter contract: never raise
            return Verdict(blocked=False, error=f"{type(exc).__name__}: {exc}")

        label = ""
        if result.matched_rules:
            label = result.matched_rules[0].rule_id

        return Verdict(
            blocked=bool(result.blocked),
            label=label,
            score=float(result.risk_score) if result.risk_score is not None else None,
        )
