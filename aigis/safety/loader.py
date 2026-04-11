"""Load safety specifications from JSON or YAML files.

Supports both JSON (stdlib) and YAML (PyYAML when available, otherwise
a minimal built-in parser compatible with the policy.py parser).

Usage::

    from aigis.safety.loader import load_safety_spec, load_safety_specs_dir

    spec = load_safety_spec("safety.yaml")
    specs = load_safety_specs_dir("safety_specs/")
"""

from __future__ import annotations

import json
from pathlib import Path

from aigis.safety.spec import EffectSpec, Invariant, SafetySpec


def load_safety_spec(path: str) -> SafetySpec:
    """Load a safety spec from a JSON or YAML file.

    JSON files are parsed with the stdlib :mod:`json` module.
    YAML files are parsed with PyYAML if available, falling back to a
    minimal built-in parser.

    Args:
        path: Filesystem path to the spec file (``.json``, ``.yaml``,
            or ``.yml``).

    Returns:
        A :class:`SafetySpec` constructed from the file contents.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Safety spec not found: {path}")

    text = file_path.read_text(encoding="utf-8")

    if file_path.suffix == ".json":
        data = json.loads(text)
    else:
        data = _parse_yaml(text)

    return _dict_to_spec(data)


def load_safety_specs_dir(dir_path: str) -> list[SafetySpec]:
    """Load all safety specs from a directory.

    Scans for ``.json``, ``.yaml``, and ``.yml`` files in *dir_path*
    (non-recursive) and loads each one.

    Args:
        dir_path: Path to the directory containing spec files.

    Returns:
        A list of :class:`SafetySpec` objects (may be empty if no
        matching files are found).

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    directory = Path(dir_path)
    if not directory.is_dir():
        raise FileNotFoundError(f"Specs directory not found: {dir_path}")

    specs: list[SafetySpec] = []
    for ext in ("*.json", "*.yaml", "*.yml"):
        for file_path in sorted(directory.glob(ext)):
            specs.append(load_safety_spec(str(file_path)))
    return specs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_yaml(text: str) -> dict:
    """Parse YAML text, preferring PyYAML when available.

    Falls back to a minimal parser that handles the safety-spec
    schema (flat keys, lists of dicts).
    """
    try:
        import yaml  # type: ignore[import-untyped]

        return yaml.safe_load(text) or {}
    except ImportError:
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser (stdlib only).

    Handles the safety-spec schema: top-level scalars, lists of dicts
    (allowed_effects, forbidden_effects, invariants), and nested
    ``conditions`` dicts.  Does NOT support anchors, multiline strings,
    or flow sequences.
    """
    result: dict = {}
    current_list_key: str | None = None
    current_item: dict | None = None
    current_conditions: dict | None = None
    in_conditions = False

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if indent == 0 and ":" in stripped:
            # Top-level key
            if current_item and current_list_key:
                if current_conditions:
                    current_item["conditions"] = current_conditions
                result.setdefault(current_list_key, []).append(current_item)
                current_item = None
                current_conditions = None
                in_conditions = False

            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                result[key] = val
            current_list_key = key if not val else None

        elif stripped.startswith("- ") and current_list_key:
            # List item
            if current_item:
                if current_conditions:
                    current_item["conditions"] = current_conditions
                result.setdefault(current_list_key, []).append(current_item)
                current_conditions = None
                in_conditions = False
            current_item = {}
            rest = stripped[2:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                current_item[k.strip()] = v.strip().strip('"').strip("'")

        elif current_item is not None and ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            if key == "conditions" and not val:
                in_conditions = True
                current_conditions = {}
            elif in_conditions and indent >= 6:
                if current_conditions is not None:
                    current_conditions[key] = val
            else:
                in_conditions = False
                current_item[key] = val

    # Flush last item
    if current_item and current_list_key:
        if current_conditions:
            current_item["conditions"] = current_conditions
        result.setdefault(current_list_key, []).append(current_item)

    return result


def _dict_to_spec(data: dict) -> SafetySpec:
    """Convert a parsed dict to a :class:`SafetySpec`."""
    allowed = [
        EffectSpec(
            effect_type=e.get("effect_type", "*"),
            scope=e.get("scope", "*"),
            conditions=e.get("conditions", {}),
        )
        for e in data.get("allowed_effects", [])
    ]
    forbidden = [
        EffectSpec(
            effect_type=e.get("effect_type", "*"),
            scope=e.get("scope", "*"),
            conditions=e.get("conditions", {}),
        )
        for e in data.get("forbidden_effects", [])
    ]
    invariants = [
        Invariant(
            name=inv.get("name", ""),
            check=inv.get("check", ""),
            description=inv.get("description", ""),
        )
        for inv in data.get("invariants", [])
    ]

    return SafetySpec(
        name=data.get("name", "unnamed"),
        version=data.get("version", "1.0"),
        allowed_effects=allowed,
        forbidden_effects=forbidden,
        invariants=invariants,
    )
