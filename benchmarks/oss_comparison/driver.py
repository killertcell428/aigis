"""Benchmark driver.

Loads the dataset, runs every requested adapter against every record, and
writes a CSV with one row per (tool, record). The reporter (``report.py``)
turns the CSV into the markdown table that ends up in the docs.

CLI::

    python -m benchmarks.oss_comparison.driver --adapter aigis
    python -m benchmarks.oss_comparison.driver --adapter all --out custom.csv
    python -m benchmarks.oss_comparison.driver --adapter aigis,llm-guard

The driver is intentionally single-threaded so a tool's verdict is never
contaminated by load from a parallel call. If you need throughput, the
output CSV can be merged across runs because each row is keyed by
(tool, input_id) — see ``report.py``.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from pathlib import Path

from benchmarks.oss_comparison.adapters.registry import (
    available_adapters,
    build_adapter,
)
from benchmarks.oss_comparison.dataset import Record, load_dataset

RANDOM_SEED = 42
DEFAULT_OUT = Path(__file__).parent / "results" / "results.csv"

CSV_FIELDS = (
    "tool",
    "tool_config_tier",
    "input_id",
    "category",
    "ground_truth",  # "attack" | "benign"
    "blocked",
    "label",
    "score",
    "latency_ms",
    "error",
)


def _run_adapter(name: str, records: list[Record]) -> list[dict[str, object]]:
    adapter = build_adapter(name)
    rows: list[dict[str, object]] = []
    for rec in records:
        t0 = time.perf_counter()
        verdict = adapter.check(rec.text)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        rows.append(
            {
                "tool": adapter.name,
                "tool_config_tier": adapter.config_tier,
                "input_id": rec.id,
                "category": rec.category,
                "ground_truth": rec.label,
                "blocked": int(verdict.blocked),
                "label": verdict.label,
                "score": "" if verdict.score is None else f"{verdict.score:.2f}",
                "latency_ms": f"{dt_ms:.2f}",
                "error": verdict.error or "",
            }
        )
    # Close adapter sockets if present (HTTP adapters)
    close = getattr(adapter, "close", None)
    if callable(close):
        close()
    return rows


def _parse_adapter_arg(value: str) -> list[str]:
    if value == "all":
        return available_adapters()
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("--adapter cannot be empty")
    for p in parts:
        if p not in available_adapters():
            raise argparse.ArgumentTypeError(
                f"Unknown adapter {p!r}. Available: {', '.join(available_adapters())}"
            )
    return parts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the OSS-guardrails comparison benchmark.")
    parser.add_argument(
        "--adapter",
        type=_parse_adapter_arg,
        default=_parse_adapter_arg("aigis"),
        help="Comma-separated adapter name(s), or 'all'. "
        f"Available: {', '.join(available_adapters())}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"CSV output path (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-tool progress lines.",
    )
    args = parser.parse_args(argv)

    random.seed(RANDOM_SEED)
    records = load_dataset()
    if not args.quiet:
        print(
            f"[driver] dataset: {len(records)} records "
            f"({sum(1 for r in records if r.is_attack)} attacks, "
            f"{sum(1 for r in records if not r.is_attack)} benign)"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []
    for adapter_name in args.adapter:
        if not args.quiet:
            print(f"[driver] running adapter: {adapter_name}")
        try:
            rows = _run_adapter(adapter_name, records)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[driver] adapter {adapter_name!r} could not be instantiated: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            continue
        errors = sum(1 for r in rows if r["error"])
        if not args.quiet:
            print(f"[driver]   {len(rows)} rows ({errors} errors)")
        all_rows.extend(rows)

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    if not args.quiet:
        print(f"[driver] wrote {len(all_rows)} rows → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
