"""Latency regression tests for pathological inputs.

Guards against super-linear cost on long repeated-token inputs (issue #131).
Each test asserts a worst-case ceiling; if the ceiling is breached the build
fails so the regression is caught before release.
"""

import time

import pytest

from aigis.scanner import scan
from aigis.similarity import _sliding_window_check

_BUDGET_MS = 500  # worst-case single-scan ceiling (ms) — pre-fix was ~2250 ms


@pytest.mark.parametrize(
    "label,text",
    [
        ("ignore_x400", "ignore " * 400),
        ("disregard_x300", "disregard " * 300),
        ("mixed_repeat_x200", "ignore all previous instructions " * 200),
    ],
)
def test_scan_pathological_input_within_budget(label: str, text: str) -> None:
    """Full scan on a long repeated-token input must complete within _BUDGET_MS."""
    start = time.perf_counter()
    scan(text)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < _BUDGET_MS, (
        f"[{label}] scan took {elapsed_ms:.0f} ms — exceeds {_BUDGET_MS} ms ceiling. "
        f"Possible super-linear regex/similarity regression (see issue #131)."
    )


def test_sliding_window_check_long_input_within_budget() -> None:
    """_sliding_window_check alone must stay fast on a pathological input."""
    text = "ignore " * 400
    phrase = "ignore all previous instructions"
    start = time.perf_counter()
    _sliding_window_check(text, phrase, threshold=0.65)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 50, (
        f"_sliding_window_check took {elapsed_ms:.0f} ms — exceeds 50 ms ceiling."
    )
