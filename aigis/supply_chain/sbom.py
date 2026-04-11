"""AI Dependency SBOM — Software Bill of Materials for AI agent stacks.

Generates a CycloneDX-inspired SBOM covering Python packages relevant to
AI/LLM workloads, MCP tool definitions, and configured models.  The SBOM
enables supply-chain auditing and feeds into ``DependencyVerifier`` for
integrity checks.

Usage::

    from aigis.supply_chain import SBOMGenerator

    gen = SBOMGenerator()
    gen.scan_python_packages()
    gen.scan_mcp_tools(mcp_tools, source="https://mcp.example.com")
    gen.add_model("claude-3-opus", provider="anthropic")
    sbom = gen.generate()
    gen.save()
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Default package prefixes to look for when scanning Python packages
_DEFAULT_PREFIXES: list[str] = [
    "openai",
    "anthropic",
    "langchain",
    "crewai",
    "aigis",
    "aig_guardian",
    "litellm",
    "llama",
    "transformers",
    "huggingface",
    "torch",
    "tensorflow",
    "autogen",
    "semantic_kernel",
    "guidance",
    "vllm",
    "together",
    "cohere",
    "mistral",
    "groq",
]


@dataclass
class SBOMEntry:
    """A single entry in the AI Software Bill of Materials."""

    name: str  # Package or tool name
    version: str  # Installed version
    entry_type: str  # "python_package" | "mcp_tool" | "mcp_server" | "model"
    source: str  # PyPI URL, MCP server URL, etc
    hash: str  # SHA-256 of the installed artifact
    license: str = ""  # License identifier if known
    verified: bool = False  # True if hash matches known-good value


class SBOMGenerator:
    """Generate Software Bill of Materials for AI agent dependencies.

    Covers:

    1. **Python packages** -- scan installed packages relevant to AI/LLM
       (uses ``importlib.metadata``).
    2. **MCP tools** -- enumerate tool definitions from connected servers.
    3. **Models** -- record which models are configured.

    Output: JSON file following a CycloneDX-inspired structure.
    """

    def __init__(self) -> None:
        self._entries: list[SBOMEntry] = []

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def scan_python_packages(
        self,
        relevant_prefixes: list[str] | None = None,
    ) -> list[SBOMEntry]:
        """Scan installed Python packages and add AI-relevant ones.

        Uses ``importlib.metadata`` to enumerate distributions.  Only
        packages whose *normalized* name starts with one of the given
        prefixes are included.

        Args:
            relevant_prefixes: List of package-name prefixes to match.
                Defaults to a built-in list of common AI/LLM packages.

        Returns:
            List of ``SBOMEntry`` instances that were added.
        """
        import importlib.metadata as md

        prefixes = relevant_prefixes or _DEFAULT_PREFIXES
        # Normalize prefix list (PyPI names use - and _, lower-case)
        norm_prefixes = [p.lower().replace("-", "_") for p in prefixes]

        added: list[SBOMEntry] = []
        for dist in md.distributions():
            raw_name = dist.metadata.get("Name", "")
            if not raw_name:
                continue
            norm_name = raw_name.lower().replace("-", "_")
            if not any(norm_name.startswith(p) for p in norm_prefixes):
                continue

            version = dist.metadata.get("Version", "") or ""
            license_str = dist.metadata.get("License") or ""
            # Try to get a classifier-based license if metadata field is empty
            if not license_str:
                classifiers = dist.metadata.get_all("Classifier") or []
                for c in classifiers:
                    if "License" in c:
                        license_str = c.split("::")[-1].strip()
                        break

            # Hash: use the package metadata as a proxy for identity
            hash_input = f"{norm_name}=={version}"
            pkg_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

            entry = SBOMEntry(
                name=raw_name,
                version=version,
                entry_type="python_package",
                source=f"https://pypi.org/project/{raw_name}/{version}/",
                hash=pkg_hash,
                license=license_str,
            )
            self._entries.append(entry)
            added.append(entry)

        return added

    def scan_mcp_tools(
        self,
        tools: list[dict],
        source: str = "",
    ) -> list[SBOMEntry]:
        """Add MCP tool definitions to the SBOM.

        Args:
            tools: List of MCP tool definition dicts (must contain ``"name"``).
            source: MCP server URL or identifier.

        Returns:
            List of ``SBOMEntry`` instances added.
        """
        added: list[SBOMEntry] = []
        for tool in tools:
            name = tool.get("name", "")
            if not name:
                continue
            # Use same canonical format as ToolPinManager.compute_hash()
            from aigis.supply_chain.hash_pin import ToolPinManager

            tool_hash = ToolPinManager.compute_hash(tool)

            entry = SBOMEntry(
                name=name,
                version="",
                entry_type="mcp_tool",
                source=source,
                hash=tool_hash,
            )
            self._entries.append(entry)
            added.append(entry)
        return added

    def add_model(
        self,
        name: str,
        provider: str,
        version: str = "",
    ) -> SBOMEntry:
        """Record a model used in the system.

        Args:
            name: Model name (e.g. ``"claude-3-opus"``).
            provider: Provider identifier (e.g. ``"anthropic"``).
            version: Optional version/snapshot string.

        Returns:
            The ``SBOMEntry`` that was added.
        """
        hash_input = f"{provider}/{name}/{version}"
        model_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        entry = SBOMEntry(
            name=name,
            version=version,
            entry_type="model",
            source=provider,
            hash=model_hash,
        )
        self._entries.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(self) -> dict:
        """Generate the full SBOM as a dict (CycloneDX-inspired JSON).

        Returns:
            A dict with ``bomFormat``, ``specVersion``, ``metadata``,
            and ``components`` keys.
        """
        components: list[dict] = []
        for entry in self._entries:
            comp: dict = {
                "type": _entry_type_to_cdx(entry.entry_type),
                "name": entry.name,
                "version": entry.version,
                "hashes": [
                    {"alg": "SHA-256", "content": entry.hash},
                ],
                "properties": [
                    {"name": "ai-guardian:entry_type", "value": entry.entry_type},
                    {"name": "ai-guardian:source", "value": entry.source},
                    {"name": "ai-guardian:verified", "value": str(entry.verified).lower()},
                ],
            }
            if entry.license:
                comp["licenses"] = [{"license": {"id": entry.license}}]
            components.append(comp)

        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(UTC).isoformat(),
                "tools": [
                    {
                        "vendor": "ai-guardian",
                        "name": "ai-guardian-sbom",
                        "version": "1.0.0",
                    }
                ],
            },
            "components": components,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path | str = ".aigis/sbom.json") -> None:
        """Save the SBOM to a JSON file.

        Args:
            path: Destination file path.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = self.generate()
        target.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self, path: Path | str = ".aigis/sbom.json") -> None:
        """Load SBOM entries from a previously saved file.

        Replaces the current entry list with the loaded data.

        Args:
            path: Source file path.
        """
        source = Path(path)
        if not source.exists():
            return
        raw = json.loads(source.read_text(encoding="utf-8"))
        self._entries.clear()
        for comp in raw.get("components", []):
            props = {p["name"]: p["value"] for p in comp.get("properties", [])}
            hash_val = ""
            for h in comp.get("hashes", []):
                if h.get("alg") == "SHA-256":
                    hash_val = h.get("content", "")
                    break
            license_str = ""
            for lic in comp.get("licenses", []):
                license_str = lic.get("license", {}).get("id", "")
                if license_str:
                    break
            entry = SBOMEntry(
                name=comp.get("name", ""),
                version=comp.get("version", ""),
                entry_type=props.get("ai-guardian:entry_type", ""),
                source=props.get("ai-guardian:source", ""),
                hash=hash_val,
                license=license_str,
                verified=props.get("ai-guardian:verified", "false") == "true",
            )
            self._entries.append(entry)

    @property
    def entries(self) -> list[SBOMEntry]:
        """Read-only access to current entries."""
        return list(self._entries)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry_type_to_cdx(entry_type: str) -> str:
    """Map our entry types to CycloneDX component types."""
    mapping = {
        "python_package": "library",
        "mcp_tool": "application",
        "mcp_server": "application",
        "model": "machine-learning-model",
    }
    return mapping.get(entry_type, "library")
