"""Dataset loader for the OSS-comparison benchmark.

The dataset is a set of JSONL files in ``datasets/``. Each line is one record:

    {"id": "pi-001", "category": "prompt_injection", "label": "attack",
     "text": "Ignore previous instructions...", "source": "..."}

``label`` is one of ``"attack"`` (should be blocked) or ``"benign"`` (should
NOT be blocked). The dataset is deterministic and version-controlled — the
same checkout always loads the same records in the same order.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATASET_DIR = Path(__file__).parent / "datasets"

# Files loaded in this order. Adding a new category? Add the filename here.
DATASET_FILES = (
    "prompt_injection.jsonl",
    "jailbreak.jsonl",
    "data_exfiltration.jsonl",
    "evasion.jsonl",
    "safe_baseline.jsonl",
)


@dataclass(frozen=True)
class Record:
    id: str
    category: str
    label: str  # "attack" | "benign"
    text: str
    source: str

    @property
    def is_attack(self) -> bool:
        return self.label == "attack"


def load_dataset(files: tuple[str, ...] = DATASET_FILES) -> list[Record]:
    records: list[Record] = []
    for fname in files:
        path = DATASET_DIR / fname
        if not path.exists():
            raise FileNotFoundError(f"Dataset file missing: {path}")
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                records.append(
                    Record(
                        id=data["id"],
                        category=data["category"],
                        label=data["label"],
                        text=data["text"],
                        source=data.get("source", ""),
                    )
                )
    return records


def dataset_stats(records: list[Record]) -> dict[str, int]:
    """Per-category counts — used by the reporter and by smoke tests."""
    stats: dict[str, int] = {}
    for r in records:
        stats[r.category] = stats.get(r.category, 0) + 1
    return stats
