"""Policy manager: built-in and YAML-based policy loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Built-in policies
# ---------------------------------------------------------------------------
_BUILTIN_POLICIES: dict[str, dict[str, Any]] = {
    "default": {
        "auto_block_threshold": 81,
        "auto_allow_threshold": 30,
        "custom_rules": [],
    },
    "strict": {
        "auto_block_threshold": 61,
        "auto_allow_threshold": 20,
        "custom_rules": [],
    },
    "permissive": {
        "auto_block_threshold": 91,
        "auto_allow_threshold": 50,
        "custom_rules": [],
    },
}


@dataclass
class Policy:
    """Resolved policy configuration."""

    name: str
    auto_block_threshold: int = 81
    auto_allow_threshold: int = 30
    custom_rules: list[dict] = field(default_factory=list)

    @property
    def will_block(self) -> bool:
        return self.auto_block_threshold <= 100

    def should_block(self, score: int) -> bool:
        return score >= self.auto_block_threshold

    def should_allow(self, score: int) -> bool:
        return score <= self.auto_allow_threshold


def load_policy(name_or_path: str = "default") -> Policy:
    """Load a policy by name or from a YAML file path.

    Args:
        name_or_path: Either a built-in policy name ("default", "strict",
                      "permissive") or a path to a YAML policy file.

    Returns:
        Resolved Policy object.
    """
    if name_or_path in _BUILTIN_POLICIES:
        cfg = _BUILTIN_POLICIES[name_or_path]
        return Policy(name=name_or_path, **cfg)

    path = Path(name_or_path)
    if path.is_file():
        return _load_yaml_policy(path)

    raise ValueError(
        f"Unknown policy '{name_or_path}'. "
        f"Built-in options: {list(_BUILTIN_POLICIES)}. "
        "Or provide a path to a .yaml policy file."
    )


def _load_yaml_policy(path: Path) -> Policy:
    """Load policy from a YAML file.

    Expected YAML structure:
        name: my-policy
        auto_block_threshold: 75
        auto_allow_threshold: 25
        custom_rules:
          - id: block_competitor
            name: Competitor Mention
            pattern: "(CompetitorA|CompetitorB)"
            score_delta: 40
            enabled: true
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for YAML policy files. Install it with: pip install pyyaml"
        ) from e

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return Policy(
        name=data.get("name", path.stem),
        auto_block_threshold=int(data.get("auto_block_threshold", 81)),
        auto_allow_threshold=int(data.get("auto_allow_threshold", 30)),
        custom_rules=data.get("custom_rules", []),
    )
