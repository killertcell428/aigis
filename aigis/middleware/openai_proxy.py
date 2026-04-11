"""OpenAI drop-in proxy wrapper for aigis.

Usage::

    from aigis import Guard
    from aigis.middleware.openai_proxy import SecureOpenAI

    guard = Guard()
    client = SecureOpenAI(api_key="sk-...", guard=guard)

    # Works exactly like openai.OpenAI — scanning happens automatically
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}],
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aigis.guard import Guard

try:
    import openai
except ImportError as e:
    raise ImportError(
        "openai is required for SecureOpenAI. Install it with: pip install 'aigis[openai]'"
    ) from e


class GuardianBlockedError(RuntimeError):
    """Raised when Aigis blocks a request or response."""

    def __init__(self, message: str, risk_score: int, reasons: list[str]) -> None:
        super().__init__(message)
        self.risk_score = risk_score
        self.reasons = reasons


class SecureOpenAI:
    """Drop-in replacement for ``openai.OpenAI`` with built-in Aigis scanning.

    Every ``chat.completions.create()`` call automatically:

    1. Scans the ``messages`` list before sending to OpenAI.
    2. Scans the LLM response before returning it to the caller.

    Args:
        guard: A configured :class:`~aigis.Guard` instance.
        check_output: Scan LLM responses as well. Defaults to ``True``.
        **kwargs: All other keyword arguments are forwarded to ``openai.OpenAI()``.
    """

    def __init__(
        self,
        guard: Guard,
        check_output: bool = True,
        **kwargs: Any,
    ) -> None:
        self._client = openai.OpenAI(**kwargs)
        self._guard = guard
        self._check_output = check_output
        self.chat = _SecureChat(self._client.chat, guard, check_output)

    # Passthrough attributes to the underlying client
    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _SecureChat:
    def __init__(self, chat: Any, guard: Guard, check_output: bool) -> None:
        self._chat = chat
        self.completions = _SecureCompletions(chat.completions, guard, check_output)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class _SecureCompletions:
    def __init__(self, completions: Any, guard: Guard, check_output: bool) -> None:
        self._completions = completions
        self._guard = guard
        self._check_output = check_output

    def create(self, **kwargs: Any) -> Any:
        messages = kwargs.get("messages", [])
        if messages:
            result = self._guard.check_messages(messages)
            if result.blocked:
                raise GuardianBlockedError(
                    f"Aigis blocked request (score={result.risk_score}): "
                    + ", ".join(result.reasons),
                    result.risk_score,
                    result.reasons,
                )

        response = self._completions.create(**kwargs)

        if self._check_output:
            if hasattr(response, "model_dump"):
                response_dict = response.model_dump()
            elif hasattr(response, "to_dict"):
                response_dict = response.to_dict()
            elif hasattr(response, "__dict__"):
                response_dict = response.__dict__
            else:
                import logging

                logging.getLogger("aigis").warning(
                    "Cannot serialize OpenAI response for output scanning — "
                    "response type %s has no model_dump/to_dict. Blocking as precaution.",
                    type(response).__name__,
                )
                raise GuardianBlockedError(
                    "Aigis: unable to scan response (unsupported response type)",
                    risk_score=0,
                    reasons=["output_scan_unsupported"],
                )
            out_result = self._guard.check_response(response_dict)
            if out_result.blocked:
                raise GuardianBlockedError(
                    f"Aigis blocked response (score={out_result.risk_score}): "
                    + ", ".join(out_result.reasons),
                    out_result.risk_score,
                    out_result.reasons,
                )

        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)
