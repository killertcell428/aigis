"""MCP Tool Hash Pinning — detect unauthorized changes to tool definitions.

Defends against "rug pull" attacks where a tool definition is modified after
initial approval to include malicious instructions.  On first use, tool
definitions are hashed and stored in a pin file.  On subsequent runs the
current definitions are compared against the pins and any discrepancy is
flagged.

Usage::

    from aigis.supply_chain import ToolPinManager

    manager = ToolPinManager()

    # First time: pin current tool definitions
    manager.pin_tools(mcp_tools_list)
    manager.save()

    # Later: verify tools haven't changed
    results = manager.verify_tools(mcp_tools_list)
    for r in results:
        if r.status == "modified":
            print(f"WARNING {r.tool_name} has been modified!")
            print(f"  {r.diff_summary}")
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class PinnedTool:
    """A pinned MCP tool definition with its expected hash."""

    tool_name: str
    definition_hash: str  # SHA-256 of the canonical tool definition JSON
    pinned_at: str  # ISO timestamp
    source: str  # Where the tool came from (server URL, package name)
    version: str = ""  # Optional version tag


@dataclass
class ToolVerificationResult:
    """Outcome of verifying a single tool against its pin."""

    tool_name: str
    status: str  # "verified" | "modified" | "new" | "removed"
    expected_hash: str
    actual_hash: str
    diff_summary: str  # Human-readable description of what changed (if modified)


class ToolPinManager:
    """Pin MCP tool definitions and detect unauthorized changes.

    First use: scan MCP tools and create a pin file
    (```.aigis/tool_pins.json```).
    Subsequent uses: verify tools against pins, alert on changes.

    This defends against "rug pull" attacks where a tool definition is
    modified after initial approval to include malicious instructions.

    Usage::

        manager = ToolPinManager()

        # First time: pin current tool definitions
        manager.pin_tools(mcp_tools_list)
        manager.save()

        # Later: verify tools haven't changed
        results = manager.verify_tools(mcp_tools_list)
        for r in results:
            if r.status == "modified":
                print(f"WARNING {r.tool_name} has been modified!")
    """

    def __init__(self, pin_file: Path | str = ".aigis/tool_pins.json"):
        self._pin_file = Path(pin_file)
        self._pins: dict[str, PinnedTool] = {}
        self._lock = threading.Lock()
        # Auto-load if the file already exists
        if self._pin_file.exists():
            self.load()

    # ------------------------------------------------------------------
    # Pinning
    # ------------------------------------------------------------------

    def pin_tool(
        self,
        tool_name: str,
        definition: dict,
        source: str = "",
        version: str = "",
    ) -> PinnedTool:
        """Pin a single tool definition.

        Args:
            tool_name: Name of the tool (used as key).
            definition: Full MCP tool definition dict.
            source: Where the tool came from (server URL, package name).
            version: Optional version tag.

        Returns:
            The newly created ``PinnedTool``.
        """
        h = self.compute_hash(definition)
        pin = PinnedTool(
            tool_name=tool_name,
            definition_hash=h,
            pinned_at=datetime.now(UTC).isoformat(),
            source=source,
            version=version,
        )
        with self._lock:
            self._pins[tool_name] = pin
        return pin

    def pin_tools(
        self,
        tools: list[dict],
        source: str = "",
    ) -> list[PinnedTool]:
        """Pin a list of MCP tool definitions.

        Each dict must contain a ``"name"`` key.  The full dict is hashed.

        Args:
            tools: List of MCP tool definition dicts.
            source: Common source for all tools.

        Returns:
            List of ``PinnedTool`` instances.
        """
        results: list[PinnedTool] = []
        for tool in tools:
            name = tool.get("name", "")
            if not name:
                continue
            pin = self.pin_tool(name, tool, source=source)
            results.append(pin)
        return results

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_tool(self, tool_name: str, definition: dict) -> ToolVerificationResult:
        """Verify a single tool definition against its pin.

        Args:
            tool_name: Name of the tool.
            definition: Current MCP tool definition dict.

        Returns:
            ``ToolVerificationResult`` with status ``"verified"``,
            ``"modified"``, or ``"new"``.
        """
        actual_hash = self.compute_hash(definition)
        with self._lock:
            pin = self._pins.get(tool_name)

        if pin is None:
            return ToolVerificationResult(
                tool_name=tool_name,
                status="new",
                expected_hash="",
                actual_hash=actual_hash,
                diff_summary=f"Tool '{tool_name}' is new (no pin exists).",
            )

        if pin.definition_hash == actual_hash:
            return ToolVerificationResult(
                tool_name=tool_name,
                status="verified",
                expected_hash=pin.definition_hash,
                actual_hash=actual_hash,
                diff_summary="",
            )

        # Build a human-readable diff summary
        diff_summary = (
            f"Tool '{tool_name}' definition has been modified since it was "
            f"pinned at {pin.pinned_at}. "
            f"Expected hash: {pin.definition_hash[:16]}..., "
            f"actual hash: {actual_hash[:16]}..."
        )

        return ToolVerificationResult(
            tool_name=tool_name,
            status="modified",
            expected_hash=pin.definition_hash,
            actual_hash=actual_hash,
            diff_summary=diff_summary,
        )

    def verify_tools(self, tools: list[dict]) -> list[ToolVerificationResult]:
        """Verify a list of MCP tool definitions against their pins.

        Also detects *removed* tools: pins that have no corresponding tool
        in the current list.

        Args:
            tools: List of current MCP tool definition dicts.

        Returns:
            List of ``ToolVerificationResult`` (one per tool + one per
            removed pin).
        """
        results: list[ToolVerificationResult] = []
        seen_names: set[str] = set()

        for tool in tools:
            name = tool.get("name", "")
            if not name:
                continue
            seen_names.add(name)
            results.append(self.verify_tool(name, tool))

        # Detect removed tools
        with self._lock:
            for pinned_name, pin in self._pins.items():
                if pinned_name not in seen_names:
                    results.append(
                        ToolVerificationResult(
                            tool_name=pinned_name,
                            status="removed",
                            expected_hash=pin.definition_hash,
                            actual_hash="",
                            diff_summary=(
                                f"Tool '{pinned_name}' was previously pinned but "
                                f"is no longer present in the tool list."
                            ),
                        )
                    )

        return results

    # ------------------------------------------------------------------
    # Pin management
    # ------------------------------------------------------------------

    def unpin(self, tool_name: str) -> bool:
        """Remove a pin for the named tool.

        Returns:
            ``True`` if a pin was removed, ``False`` if no pin existed.
        """
        with self._lock:
            return self._pins.pop(tool_name, None) is not None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path | str | None = None) -> None:
        """Save current pins to a JSON file.

        Args:
            path: Override file path.  Defaults to the path given at init.
        """
        target = Path(path) if path is not None else self._pin_file
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            data = {name: asdict(pin) for name, pin in self._pins.items()}
        target.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self, path: Path | str | None = None) -> None:
        """Load pins from a JSON file.

        Args:
            path: Override file path.  Defaults to the path given at init.
        """
        source = Path(path) if path is not None else self._pin_file
        if not source.exists():
            return
        raw = json.loads(source.read_text(encoding="utf-8"))
        with self._lock:
            self._pins.clear()
            for name, pin_data in raw.items():
                self._pins[name] = PinnedTool(
                    tool_name=pin_data["tool_name"],
                    definition_hash=pin_data["definition_hash"],
                    pinned_at=pin_data["pinned_at"],
                    source=pin_data["source"],
                    version=pin_data.get("version", ""),
                )

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    @staticmethod
    def compute_hash(definition: dict) -> str:
        """Canonical SHA-256 hash of a tool definition.

        Uses ``json.dumps(sort_keys=True)`` for deterministic hashing.

        Args:
            definition: MCP tool definition dict.

        Returns:
            Lowercase hex SHA-256 digest.
        """
        import unicodedata

        canonical = json.dumps(definition, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        # Normalize Unicode to NFC to prevent homoglyph/zero-width character bypass
        canonical = unicodedata.normalize("NFC", canonical)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
