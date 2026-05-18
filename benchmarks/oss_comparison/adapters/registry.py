"""Lazy adapter registry — instantiate only when asked, so users without
LLM Guard / Guardrails AI / NeMo running can still benchmark Aigis alone.
"""

from __future__ import annotations

from collections.abc import Callable

from benchmarks.oss_comparison.adapters.base import Adapter

_FACTORIES: dict[str, Callable[[], Adapter]] = {}


def _aigis() -> Adapter:
    from benchmarks.oss_comparison.adapters.aigis_adapter import AigisAdapter

    return AigisAdapter()


def _llm_guard() -> Adapter:
    from benchmarks.oss_comparison.adapters.llm_guard_adapter import LLMGuardAdapter

    return LLMGuardAdapter()


def _guardrails_ai() -> Adapter:
    from benchmarks.oss_comparison.adapters.guardrails_ai_adapter import (
        GuardrailsAIAdapter,
    )

    return GuardrailsAIAdapter()


def _nemo() -> Adapter:
    from benchmarks.oss_comparison.adapters.nemo_guardrails_adapter import (
        NemoGuardrailsAdapter,
    )

    return NemoGuardrailsAdapter()


_FACTORIES.update(
    {
        "aigis": _aigis,
        "llm-guard": _llm_guard,
        "guardrails-ai": _guardrails_ai,
        "nemo-guardrails": _nemo,
    }
)


def available_adapters() -> list[str]:
    return sorted(_FACTORIES)


def build_adapter(name: str) -> Adapter:
    if name not in _FACTORIES:
        raise KeyError(f"Unknown adapter {name!r}. Available: {', '.join(available_adapters())}")
    return _FACTORIES[name]()
