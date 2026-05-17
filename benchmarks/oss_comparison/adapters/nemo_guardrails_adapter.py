"""NVIDIA NeMo Guardrails adapter — talks to a NeMo Guardrails server sidecar.

We use the **documented self-check input rails config** from NeMo's own
quickstart (``examples/configs/self_check_input``), which is the
out-of-the-box recommendation for input-side jailbreak / injection
checking. No custom rails are added.

Upstream: https://github.com/NVIDIA/NeMo-Guardrails
API contract used here: NeMo's HTTP server exposes ``POST /v1/chat/completions``
that runs the configured rails. The ``"allow"`` vs ``"refuse"`` signal is
inferred from the response status: a refusal message contains a
configurable refusal phrase. We treat any response that does NOT contain
the refusal phrase as ``blocked=False``.
"""

from __future__ import annotations

import os

import httpx

from benchmarks.oss_comparison.adapters.base import Verdict

# Default refusal phrase from NeMo's self_check_input quickstart config.
# Configurable via env var so users with custom rails can override.
REFUSAL_PHRASE_DEFAULT = "I'm sorry, I can't respond to that"


class NemoGuardrailsAdapter:
    name = "nemo-guardrails"
    config_tier = "default self_check_input rails (NeMo quickstart)"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        refusal_phrase: str | None = None,
    ) -> None:
        self._url = base_url or os.environ.get("NEMO_GUARDRAILS_URL", "http://localhost:8003")
        self._timeout = timeout
        self._refusal_phrase = (
            refusal_phrase or os.environ.get("NEMO_REFUSAL_PHRASE") or REFUSAL_PHRASE_DEFAULT
        )
        self._client = httpx.Client(timeout=timeout)

    def check(self, text: str) -> Verdict:
        try:
            resp = self._client.post(
                f"{self._url}/v1/chat/completions",
                json={
                    "config_id": "self_check_input",
                    "messages": [{"role": "user", "content": text}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return Verdict(blocked=False, error=f"{type(exc).__name__}: {exc}")

        messages = data.get("messages") or []
        reply = ""
        for m in messages:
            if m.get("role") == "assistant":
                reply = m.get("content", "")
                break

        blocked = self._refusal_phrase.lower() in reply.lower()
        return Verdict(blocked=blocked, label="self_check_input" if blocked else "")

    def close(self) -> None:
        self._client.close()
