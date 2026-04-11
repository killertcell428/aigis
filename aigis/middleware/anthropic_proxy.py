"""Anthropic Claude drop-in proxy wrapper for aigis.

Usage::

    from aigis import Guard
    from aigis.middleware.anthropic_proxy import SecureAnthropic

    guard = Guard()
    client = SecureAnthropic(api_key="sk-ant-...", guard=guard)

    # Works exactly like anthropic.Anthropic — scanning happens automatically
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}],
    )

Resolves: https://github.com/killertcell428/aigis/issues/3
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aigis.guard import Guard

try:
    import anthropic
except ImportError as e:
    raise ImportError(
        "anthropic is required for SecureAnthropic. Install it with: pip install 'aigis[anthropic]'"
    ) from e


class GuardianBlockedError(RuntimeError):
    """Raised when Aigis blocks a request or response."""

    def __init__(self, message: str, risk_score: int, reasons: list[str]) -> None:
        super().__init__(message)
        self.risk_score = risk_score
        self.reasons = reasons


def _extract_text_from_content(content: Any) -> str:
    """Extract plain text from Anthropic message content (str or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            elif hasattr(block, "text"):
                # ContentBlock objects (anthropic SDK)
                parts.append(block.text)
        return " ".join(parts)
    return str(content)


def _extract_response_text(response: Any) -> str:
    """Extract text from an Anthropic Message response object."""
    if hasattr(response, "content"):
        return _extract_text_from_content(response.content)
    return ""


class SecureAnthropic:
    """Drop-in replacement for ``anthropic.Anthropic`` with built-in Aigis scanning.

    Every ``messages.create()`` call automatically:

    1. Scans the ``messages`` list before sending to Anthropic.
    2. Scans the LLM response before returning it to the caller.

    Args:
        guard: A configured :class:`~aigis.Guard` instance.
        check_output: Scan LLM responses as well. Defaults to ``True``.
        **kwargs: All other keyword arguments are forwarded to ``anthropic.Anthropic()``.

    Example::

        guard = Guard(policy="strict")
        client = SecureAnthropic(api_key="sk-ant-...", guard=guard)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": "What is 2+2?"}],
        )
    """

    def __init__(
        self,
        guard: Guard,
        check_output: bool = True,
        **kwargs: Any,
    ) -> None:
        self._client = anthropic.Anthropic(**kwargs)
        self._guard = guard
        self._check_output = check_output
        self.messages = _SecureMessages(self._client.messages, guard, check_output)

    # Passthrough attributes to the underlying client
    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _SecureMessages:
    def __init__(self, messages: Any, guard: Guard, check_output: bool) -> None:
        self._messages = messages
        self._guard = guard
        self._check_output = check_output

    def create(self, **kwargs: Any) -> Any:
        """Scan messages before sending; scan response before returning."""
        raw_messages = kwargs.get("messages", [])
        system_prompt = kwargs.get("system", "")

        # Build a unified list for scanning
        messages_to_scan: list[dict[str, str]] = []
        if system_prompt:
            messages_to_scan.append(
                {"role": "system", "content": _extract_text_from_content(system_prompt)}
            )
        for msg in raw_messages:
            if isinstance(msg, dict):
                messages_to_scan.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": _extract_text_from_content(msg.get("content", "")),
                    }
                )

        if messages_to_scan:
            result = self._guard.check_messages(messages_to_scan)
            if result.blocked:
                raise GuardianBlockedError(
                    f"Aigis blocked request (score={result.risk_score}): "
                    + ", ".join(result.reasons),
                    result.risk_score,
                    result.reasons,
                )

        response = self._messages.create(**kwargs)

        if self._check_output:
            response_text = _extract_response_text(response)
            if response_text:
                out_result = self._guard.check_output(response_text)
                if out_result.blocked:
                    raise GuardianBlockedError(
                        f"Aigis blocked response (score={out_result.risk_score}): "
                        + ", ".join(out_result.reasons),
                        out_result.risk_score,
                        out_result.reasons,
                    )

        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._messages, name)
