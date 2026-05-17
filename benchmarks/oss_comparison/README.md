# OSS Guardrails Comparison Benchmark

Reproducible head-to-head comparison of Aigis against three other open-source
LLM-guardrail projects:

- [LLM Guard](https://github.com/protectai/llm-guard) (Protect AI)
- [Guardrails AI](https://github.com/guardrails-ai/guardrails) (Guardrails AI)
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) (NVIDIA)

All four tools run on the **same inputs** with the **same "default / recommended"
configuration tier** documented by each project — no cherry-picked detectors.

See [`docs/benchmarks/oss-comparison.md`](../../docs/benchmarks/oss-comparison.md)
for methodology, results, and limitations.

## Quick start

```bash
# Boot the three external guardrail services (LLM Guard, Guardrails AI, NeMo)
docker compose -f benchmarks/oss-comparison/docker-compose.yml up -d

# Run the benchmark (writes results/results.csv + results/report.md)
make bench

# Or run a single adapter
python -m benchmarks.oss_comparison.driver --adapter aigis --out results/aigis.csv
```

## Dataset

The curated dataset in `datasets/` is checked in and deterministic. It draws
from publicly documented attack categories without vendoring upstream corpora
that have research-only licenses:

| File | Source | License | N |
|---|---|---|---|
| `datasets/prompt_injection.jsonl` | Curated from public PromptBench-style patterns + Aigis internal corpus | MIT-compatible | varies |
| `datasets/jailbreak.jsonl` | Curated jailbreak templates (DAN-class, roleplay-bypass) | MIT-compatible | varies |
| `datasets/data_exfiltration.jsonl` | Curated PII / secret extraction probes | MIT-compatible | varies |
| `datasets/evasion.jsonl` | Obfuscation: ZWC, leet, base64, keyword-splitter | MIT-compatible | varies |
| `datasets/safe_baseline.jsonl` | Benign inputs (multi-lingual) | MIT-compatible | varies |

For the **extended** datasets (full PromptBench, HarmBench), run
`python -m benchmarks.oss_comparison.fetch_extended` — this downloads upstream
data at run time and never commits it to the repo.

## Reproducibility

- All dependencies pinned in `requirements.txt`
- All Docker images pinned by SHA256 digest
- Random seed fixed in `driver.py` (`RANDOM_SEED = 42`)
- A fresh `docker compose up && make bench` should reproduce the published
  detection-rate and false-positive numbers within ±2% — anything bigger is
  a regression and a CI guard fires.
