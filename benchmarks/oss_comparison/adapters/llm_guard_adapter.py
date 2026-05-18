"""LLM Guard adapter — talks to a Protect AI LLM Guard API sidecar.

We run LLM Guard as an HTTP service (see ``docker-compose.yml``) with the
**default recommended input-scanner preset**: PromptInjection, Toxicity,
Secrets, BanSubstrings, BanTopics. No detector cherry-picking — these are
the scanners LLM Guard's quickstart enables.

Upstream: https://github.com/protectai/llm-guard
API contract used here: ``POST /scan/prompt`` → ``{"is_valid": bool,
"sanitized_prompt": str, "results_score": {scanner_name: score}}``.
"""

from __future__ import annotations

import os

import httpx

from benchmarks.oss_comparison.adapters.base import Verdict


class LLMGuardAdapter:
    name = "llm-guard"
    config_tier = (
        "default recommended input scanners "
        "(PromptInjection, Toxicity, Secrets, BanSubstrings, BanTopics)"
    )

    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self._url = base_url or os.environ.get("LLM_GUARD_URL", "http://localhost:8001")
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def check(self, text: str) -> Verdict:
        try:
            resp = self._client.post(
                f"{self._url}/scan/prompt",
                json={"prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return Verdict(blocked=False, error=f"{type(exc).__name__}: {exc}")

        is_valid = bool(data.get("is_valid", True))
        scores = data.get("results_score", {}) or {}
        top_scanner = ""
        top_score: float | None = None
        if scores:
            top_scanner = max(scores, key=lambda k: scores[k])
            top_score = float(scores[top_scanner])

        return Verdict(
            blocked=not is_valid,
            label=top_scanner,
            score=top_score,
        )

    def close(self) -> None:
        self._client.close()
