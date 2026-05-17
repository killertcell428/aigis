"""CI regression guard for the OSS-comparison benchmark.

Fails (exit 1) if the Aigis row in the latest run has a detection rate
more than ``DROP_TOLERANCE_PP`` percentage points lower than the recorded
baseline in ``baseline.json``.

This protects against accidental regressions when patterns or scoring
weights change. If you've intentionally moved the score (e.g. tightened
a pattern), update ``baseline.json`` in the same PR — that's the
acknowledgement.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "baseline.json"
RESULTS_PATH = ROOT / "results" / "results.csv"

DROP_TOLERANCE_PP = 2.0  # percentage points
TOOL = "aigis"


def _detection_rate(rows: list[dict[str, str]]) -> float:
    attack_rows = [
        r for r in rows if r["tool"] == TOOL and r["ground_truth"] == "attack" and not r["error"]
    ]
    if not attack_rows:
        return 0.0
    blocked = sum(int(r["blocked"]) for r in attack_rows)
    return blocked / len(attack_rows) * 100


def main() -> int:
    if not RESULTS_PATH.exists():
        print(f"[regression-guard] no results CSV at {RESULTS_PATH}", file=sys.stderr)
        return 1
    if not BASELINE_PATH.exists():
        print(
            f"[regression-guard] no baseline at {BASELINE_PATH} — skipping",
            file=sys.stderr,
        )
        return 0

    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    current = _detection_rate(rows)
    baseline_data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    baseline = float(baseline_data["aigis"]["detection_rate_pct"])

    drop = baseline - current
    print(
        f"[regression-guard] aigis detection rate: "
        f"baseline={baseline:.2f}% current={current:.2f}% drop={drop:+.2f}pp "
        f"(tolerance={DROP_TOLERANCE_PP}pp)"
    )

    if drop > DROP_TOLERANCE_PP:
        print(
            f"[regression-guard] FAIL — detection rate dropped by {drop:.2f}pp, "
            f"more than the {DROP_TOLERANCE_PP}pp tolerance. If this is "
            f"intentional, update benchmarks/oss_comparison/baseline.json in "
            f"the same PR.",
            file=sys.stderr,
        )
        return 1

    print("[regression-guard] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
