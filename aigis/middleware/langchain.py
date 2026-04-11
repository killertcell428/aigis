"""LangChain callback handler for aigis.

Usage::

    from langchain_openai import ChatOpenAI
    from aigis import Guard
    from aigis.middleware.langchain import AIGuardianCallback

    guard = Guard()
    callback = AIGuardianCallback(guard=guard)

    llm = ChatOpenAI(callbacks=[callback])
    llm.invoke("Hello!")  # automatically scanned
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aigis.guard import Guard

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.outputs import LLMResult
except ImportError as e:
    raise ImportError(
        "langchain-core is required for AIGuardianCallback. "
        "Install it with: pip install 'aigis[langchain]'"
    ) from e


class GuardianBlockedError(RuntimeError):
    """Raised when Aigis blocks an LLM input or output."""

    def __init__(self, message: str, risk_score: int, reasons: list[str]) -> None:
        super().__init__(message)
        self.risk_score = risk_score
        self.reasons = reasons


class AIGuardianCallback(BaseCallbackHandler):  # type: ignore[misc]
    """LangChain callback that scans prompts and responses with aigis.

    Args:
        guard: A configured :class:`~aigis.Guard` instance.
        block_on_output: Also scan LLM outputs. Defaults to ``True``.
        raise_on_block: Raise :class:`GuardianBlockedError` when blocked.
                        If ``False``, logs a warning instead. Defaults to ``True``.
    """

    def __init__(
        self,
        guard: Guard,
        block_on_output: bool = True,
        raise_on_block: bool = True,
    ) -> None:
        self.guard = guard
        self.block_on_output = block_on_output
        self.raise_on_block = raise_on_block

    # ------------------------------------------------------------------
    # Input scanning
    # ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        for prompt in prompts:
            result = self.guard.check_input(prompt)
            if result.blocked:
                self._handle_block(
                    f"Aigis blocked LLM input (score={result.risk_score})",
                    result.risk_score,
                    result.reasons,
                )

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        **kwargs: Any,
    ) -> None:
        for message_group in messages:
            openai_msgs = []
            for msg in message_group:
                role = getattr(msg, "type", "user")
                content = getattr(msg, "content", str(msg))
                openai_msgs.append({"role": role, "content": content})
            result = self.guard.check_messages(openai_msgs)
            if result.blocked:
                self._handle_block(
                    f"Aigis blocked chat input (score={result.risk_score})",
                    result.risk_score,
                    result.reasons,
                )

    # ------------------------------------------------------------------
    # Output scanning
    # ------------------------------------------------------------------

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        if not self.block_on_output:
            return
        for generations in response.generations:
            for gen in generations:
                text = getattr(gen, "text", "") or ""
                result = self.guard.check_output(text)
                if result.blocked:
                    self._handle_block(
                        f"Aigis blocked LLM output (score={result.risk_score})",
                        result.risk_score,
                        result.reasons,
                    )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_block(self, message: str, score: int, reasons: list[str]) -> None:
        if self.raise_on_block:
            raise GuardianBlockedError(message, score, reasons)
        import warnings

        warnings.warn(message, stacklevel=3)
