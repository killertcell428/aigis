"""Output filter: analyze LLM response for data leaks and harmful content."""

from __future__ import annotations

from aigis.filters.patterns import OUTPUT_PATTERNS
from aigis.filters.scorer import run_patterns
from aigis.types import MatchedRule, RiskLevel


def extract_text_from_response(response_body: dict) -> str:
    """Extract text content from an OpenAI-compatible response body."""
    parts: list[str] = []
    choices = response_body.get("choices", [])
    for choice in choices:
        message = choice.get("message", {})
        content = message.get("content") or ""
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def filter_output(
    text: str,
    custom_rules: list[dict] | None = None,
) -> tuple[int, RiskLevel, list[MatchedRule]]:
    """Run output filter on a plain text string."""
    return run_patterns(text, OUTPUT_PATTERNS, custom_rules)


def filter_response(
    response_body: dict,
    custom_rules: list[dict] | None = None,
) -> tuple[int, RiskLevel, list[MatchedRule]]:
    """Run output filter on an OpenAI-compatible response body."""
    text = extract_text_from_response(response_body)
    return run_patterns(text, OUTPUT_PATTERNS, custom_rules)
