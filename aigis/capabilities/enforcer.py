"""Capability enforcer: the decision engine for tool-call authorization.

Implements the CaMeL separation principle — control-flow-sensitive tools
(shell:exec, agent:spawn) are NEVER authorized when data provenance is
UNTRUSTED, regardless of capability grants.  This prevents indirect
prompt injection from escalating into arbitrary code execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aigis.capabilities.store import CapabilityStore
from aigis.capabilities.taint import TaintedValue, TaintLabel
from aigis.types import CheckResult

if TYPE_CHECKING:
    from aigis.guard import Guard


# Tools that affect control flow must never be driven by untrusted data.
# MCP tool calls are included because MCP tools can execute arbitrary
# actions on remote servers (file I/O, network, code execution).
_CONTROL_FLOW_RESOURCES = frozenset(
    {
        "shell:exec",
        "agent:spawn",
        "code:eval",
        "mcp:tool_call",
    }
)

# Mapping from tool names (lowercase) to (resource_type, target_key) pairs.
# Lookup is case-insensitive; see _map_tool().
_TOOL_RESOURCE_MAP: dict[str, tuple[str, str]] = {
    # Generic / SDK names
    "read_file": ("file:read", "path"),
    "write_file": ("file:write", "path"),
    "edit_file": ("file:write", "file_path"),
    "execute": ("shell:exec", "command"),
    "bash": ("shell:exec", "command"),
    "shell": ("shell:exec", "command"),
    "spawn_agent": ("agent:spawn", "agent_id"),
    "http_request": ("network:fetch", "url"),
    "fetch": ("network:fetch", "url"),
    "mcp_call": ("mcp:tool_call", "tool_name"),
    # Claude Code tool names (PascalCase -> lowercase keys)
    "read": ("file:read", "file_path"),
    "write": ("file:write", "file_path"),
    "edit": ("file:write", "file_path"),
    "glob": ("file:search", "pattern"),
    "grep": ("file:search", "pattern"),
    "webfetch": ("network:fetch", "url"),
    "websearch": ("network:search", "query"),
    "agent": ("agent:spawn", "prompt"),
    "notebookedit": ("file:write", "file_path"),
    "skill": ("agent:spawn", "skill"),
}


class AuthorizationResult:
    """Outcome of a capability-based authorization check.

    Args:
        allowed: Whether the tool call is permitted.
        capability_used: Nonce of the capability that authorized the call, or None.
        reason: Human-readable explanation of the decision.
        taint_level: The data provenance label that was in effect.
        scan_result: Optional CheckResult from an Aigis scan.
    """

    __slots__ = ("allowed", "capability_used", "reason", "taint_level", "scan_result")

    def __init__(
        self,
        allowed: bool,
        capability_used: str | None,
        reason: str,
        taint_level: str,
        scan_result: CheckResult | None = None,
    ) -> None:
        self.allowed = allowed
        self.capability_used = capability_used
        self.reason = reason
        self.taint_level = taint_level
        self.scan_result = scan_result

    def __bool__(self) -> bool:
        return self.allowed

    def __repr__(self) -> str:
        return (
            f"AuthorizationResult(allowed={self.allowed!r}, "
            f"reason={self.reason!r}, taint={self.taint_level!r})"
        )


def _map_tool(tool_name: str) -> tuple[str, str]:
    """Map a tool name to its (resource_type, target_key) pair.

    Lookup is **case-insensitive** so both ``"Bash"`` (Claude Code) and
    ``"bash"`` (generic) resolve to ``("shell:exec", "command")``.

    MCP tools (``mcp__*``) are mapped to ``mcp:tool_call``.

    Falls back to a generic ``"tool:{name}"`` resource with ``"input"``
    as the target key for unknown tools.
    """
    lower = tool_name.lower()

    if lower in _TOOL_RESOURCE_MAP:
        return _TOOL_RESOURCE_MAP[lower]

    # MCP tools: mcp__server__tool_name -> mcp:tool_call
    if lower.startswith("mcp__") or lower.startswith("mcp_"):
        return "mcp:tool_call", "input"

    for prefix, (resource, _) in _TOOL_RESOURCE_MAP.items():
        if lower.startswith(prefix):
            return resource, "input"

    return f"tool:{tool_name}", "input"


def _extract_target(tool_input: dict, target_key: str) -> str:
    """Extract the authorization target from tool input."""
    if target_key in tool_input:
        return str(tool_input[target_key])
    if tool_input:
        first_val = next(iter(tool_input.values()))
        return str(first_val) if first_val is not None else "*"
    return "*"


class CapabilityEnforcer:
    """Authorizes tool calls against capability grants and taint labels.

    Args:
        store: The CapabilityStore holding active grants.
        guard: Optional Guard instance for running security scans on tool inputs.
    """

    def __init__(self, store: CapabilityStore, guard: Guard | None = None) -> None:
        self._store = store
        self._guard = guard

    def authorize_tool_call(
        self,
        tool_name: str,
        tool_input: dict,
        data_provenance: TaintLabel = TaintLabel.UNTRUSTED,
    ) -> AuthorizationResult:
        """Decide whether a tool call should be allowed.

        Authorization logic:
            1. Map tool_name to a resource type.
            2. Extract the target from tool_input.
            3. If data_provenance is UNTRUSTED and the resource is
               control-flow-sensitive, DENY unconditionally.
            4. Check the capability store for a matching grant.
            5. Optionally run a Guard scan on the tool input.
            6. Return an AuthorizationResult.

        Args:
            tool_name: Name of the tool being invoked.
            tool_input: Arguments dict for the tool call.
            data_provenance: Taint label of the data driving this call.

        Returns:
            AuthorizationResult indicating whether the call is permitted.
        """
        resource, target_key = _map_tool(tool_name)
        target = _extract_target(tool_input, target_key)

        # CaMeL invariant: untrusted data must never drive control-flow tools
        if data_provenance == TaintLabel.UNTRUSTED and resource in _CONTROL_FLOW_RESOURCES:
            return AuthorizationResult(
                allowed=False,
                capability_used=None,
                reason=(
                    f"Control-flow tool '{resource}' blocked: "
                    f"data provenance is UNTRUSTED (CaMeL separation)"
                ),
                taint_level=str(data_provenance),
            )

        # Check for a matching capability grant
        cap = self._store.check(resource, target)
        if cap is None:
            return AuthorizationResult(
                allowed=False,
                capability_used=None,
                reason=f"No capability granted for {resource} on target '{target}'",
                taint_level=str(data_provenance),
            )

        # Check requires_review constraint
        if cap.constraints.get("requires_review"):
            return AuthorizationResult(
                allowed=False,
                capability_used=cap.nonce,
                reason=f"Capability for {resource} requires human review",
                taint_level=str(data_provenance),
            )

        # Optional Guard scan on the assembled tool input
        scan_result: CheckResult | None = None
        if self._guard is not None:
            scan_text = f"{tool_name} {target}"
            scan_result = self._guard.check_input(scan_text)
            if scan_result.blocked:
                return AuthorizationResult(
                    allowed=False,
                    capability_used=cap.nonce,
                    reason=f"Guard scan blocked: {', '.join(scan_result.reasons)}",
                    taint_level=str(data_provenance),
                    scan_result=scan_result,
                )

        return AuthorizationResult(
            allowed=True,
            capability_used=cap.nonce,
            reason=f"Authorized via capability (granted_by={cap.granted_by})",
            taint_level=str(data_provenance),
            scan_result=scan_result,
        )

    def wrap_tool_output(self, output: Any, tool_name: str) -> TaintedValue:
        """Wrap a tool's output as an UNTRUSTED TaintedValue.

        All data returned from tools is untrusted by default because it
        may contain adversarial content (indirect prompt injection via
        file contents, API responses, etc.).

        Args:
            output: The raw output from the tool.
            tool_name: Name of the tool that produced the output.

        Returns:
            A TaintedValue wrapping the output with UNTRUSTED taint.
        """
        return TaintedValue(
            value=output,
            taint=TaintLabel.UNTRUSTED,
            source=f"tool:{tool_name}",
        )
