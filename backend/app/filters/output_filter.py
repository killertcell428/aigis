"""Output filter: analyze LLM response for data leaks and harmful content."""
import json

from app.filters.patterns import OUTPUT_PATTERNS
from app.filters.scorer import FilterResult, run_patterns


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
    response_body: dict,
    custom_rules: list[dict] | None = None,
) -> FilterResult:
    """Run output filter on LLM response.

    Args:
        response_body: Parsed JSON response from upstream LLM.
        custom_rules: Tenant-specific custom rules from Policy.

    Returns:
        FilterResult with risk score, level, and matched rules.
    """
    text = extract_text_from_response(response_body)
    return run_patterns(text, OUTPUT_PATTERNS, custom_rules)
