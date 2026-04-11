"""Input filter: analyze incoming LLM request messages."""
from app.filters.patterns import ALL_INPUT_PATTERNS
from app.filters.scorer import FilterResult, run_patterns


def extract_text_from_messages(messages: list[dict]) -> str:
    """Concatenate all message content into a single string for pattern matching."""
    parts: list[str] = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            # Handle multi-part messages (text + images etc.)
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(part.get("text", ""))
    return "\n".join(parts)


def filter_input(
    messages: list[dict],
    custom_rules: list[dict] | None = None,
) -> FilterResult:
    """Run input filter on request messages.

    Args:
        messages: OpenAI-style messages array.
        custom_rules: Tenant-specific custom rules from Policy.

    Returns:
        FilterResult with risk score, level, and matched rules.
    """
    text = extract_text_from_messages(messages)
    return run_patterns(text, ALL_INPUT_PATTERNS, custom_rules)
