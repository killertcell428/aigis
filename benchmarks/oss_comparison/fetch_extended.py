"""Download extended attack corpora (PromptBench, HarmBench) on demand.

The repo only checks in a small curated dataset to keep the benchmark
reproducible without pulling research-licensed material into the source
tree. Run this script if you want to expand the dataset:

    python -m benchmarks.oss_comparison.fetch_extended

The downloads go to ``benchmarks/oss_comparison/datasets/extended/`` which
is gitignored. The driver does NOT load extended files by default — pass
``--extended`` (TODO: wire through CLI) once they're present.

License notes:
- PromptBench: MIT license, safe to redistribute. Hosted at
  https://github.com/microsoft/promptbench
- HarmBench: MIT code + behaviors covered by an Acceptable Use Policy that
  forbids using behaviors to produce real harmful content. The benchmark
  only uses the behaviors as black-box detection probes against guardrail
  inputs — we never instantiate a model to answer them.
"""

from __future__ import annotations

import sys
from pathlib import Path

EXTENDED_DIR = Path(__file__).parent / "datasets" / "extended"


def main() -> int:
    EXTENDED_DIR.mkdir(parents=True, exist_ok=True)
    print(
        "fetch_extended is a stub — wiring up PromptBench/HarmBench downloads "
        "is intentionally manual the first time so the contributor reviews "
        "each project's license before opting in. Open an issue if you want "
        "this automated.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
