"""Guardrails AI adapter — talks to a Guardrails AI service sidecar.

We use the **documented "PromptInjection" + "ToxicLanguage" + "DetectPII"
guards** wired through ``guard.parse()`` over HTTP. These are the
top-of-page examples in Guardrails AI's own docs, so this represents the
"out-of-the-box" experience a new user would get.

Upstream: https://github.com/guardrails-ai/guardrails
API contract used here: ``POST /validate`` → ``{"validation_passed": bool,
"validated_output": str, "failed_validators": [...]}``.
"""

from __future__ import annotations

import os

import httpx

from benchmarks.oss_comparison.adapters.base import Verdict


class GuardrailsAIAdapter:
    name = "guardrails-ai"
    config_tier = "default recommended input guards (PromptInjection, ToxicLanguage, DetectPII)"

    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self._url = base_url or os.environ.get("GUARDRAILS_AI_URL", "http://localhost:8002")
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def check(self, text: str) -> Verdict:
        try:
            resp = self._client.post(
                f"{self._url}/validate",
                json={"input": text},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return Verdict(blocked=False, error=f"{type(exc).__name__}: {exc}")

        passed = bool(data.get("validation_passed", True))
        failed = data.get("failed_validators", []) or []
        label = failed[0] if failed else ""

        return Verdict(blocked=not passed, label=label)

    def close(self) -> None:
        self._client.close()
