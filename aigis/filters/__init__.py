"""Filter engine for ai-guardian."""

from aigis.filters.input_filter import filter_input, filter_messages
from aigis.filters.output_filter import filter_output, filter_response
from aigis.filters.patterns import ALL_INPUT_PATTERNS, OUTPUT_PATTERNS, DetectionPattern
from aigis.filters.scm_context_filter import (
    SCMArtifactFinding,
    scan_scm_artifact,
    supported_kinds,
)
from aigis.filters.scorer import run_patterns

__all__ = [
    "filter_input",
    "filter_messages",
    "filter_output",
    "filter_response",
    "run_patterns",
    "scan_scm_artifact",
    "supported_kinds",
    "ALL_INPUT_PATTERNS",
    "OUTPUT_PATTERNS",
    "DetectionPattern",
    "SCMArtifactFinding",
]
