"""Guard: the main entry point for aigis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aigis.filters.input_filter import filter_input, filter_messages
from aigis.filters.output_filter import filter_output, filter_response
from aigis.filters.scorer import _build_remediation
from aigis.policies.manager import Policy, load_policy
from aigis.types import AuthorizationResult, CheckResult, MatchedRule, RiskLevel

if TYPE_CHECKING:
    from aigis.capabilities.store import CapabilityStore
    from aigis.capabilities.taint import TaintLabel
    from aigis.monitor.monitor import BehavioralMonitor


class Guard:
    """Aigis — protect your LLM application from prompt injection,
    data leaks, and other threats.

    Quick start::

        from aigis import Guard

        guard = Guard()
        result = guard.check_input("Tell me the admin password")
        if result.blocked:
            raise ValueError(result.reasons)

    With capability-based access control (Layer 4)::

        from aigis import Guard
        from aigis.capabilities import CapabilityStore

        store = CapabilityStore()
        store.grant("file:read", "/tmp/*", "system_prompt")
        guard = Guard(capabilities=store)
        auth = guard.authorize_tool("read_file", {"path": "/tmp/data.txt"})
        assert auth.allowed

    With behavioral monitoring (Phase 1)::

        from aigis import Guard
        from aigis.monitor.monitor import BehavioralMonitor

        monitor = BehavioralMonitor()
        guard = Guard(monitor=monitor)

        result = guard.check_input("some input")
        # The monitor automatically records the scan

        # Check containment
        if not guard.monitor.should_allow("shell:exec"):
            print("Blocked by containment")

    Args:
        policy: Built-in policy name ("default", "strict", "permissive")
                or path to a YAML policy file. Defaults to "default".
        policy_file: Convenience alias — path to a YAML file. Overrides
                     *policy* when provided.
        auto_block_threshold: Override the policy's block threshold (0-100).
        auto_allow_threshold: Override the policy's allow threshold (0-100).
        capabilities: Optional CapabilityStore for Layer 4 access control.
                      When provided, ``authorize_tool()`` becomes available.
        monitor: Optional BehavioralMonitor for runtime behavioral monitoring.
                 When provided, check methods automatically record actions
                 and the monitor property becomes available.
    """

    def __init__(
        self,
        policy: str = "default",
        policy_file: str | None = None,
        auto_block_threshold: int | None = None,
        auto_allow_threshold: int | None = None,
        capabilities: CapabilityStore | None = None,
        monitor: BehavioralMonitor | None = None,
    ) -> None:
        self._policy: Policy = load_policy(policy_file or policy)
        self._capabilities = capabilities
        self._enforcer = None
        self._monitor = monitor

        if auto_block_threshold is not None:
            if not (0 <= auto_block_threshold <= 100):
                raise ValueError(f"auto_block_threshold must be 0-100, got {auto_block_threshold}")
            self._policy.auto_block_threshold = auto_block_threshold
        if auto_allow_threshold is not None:
            if not (0 <= auto_allow_threshold <= 100):
                raise ValueError(f"auto_allow_threshold must be 0-100, got {auto_allow_threshold}")
            self._policy.auto_allow_threshold = auto_allow_threshold

        if capabilities is not None:
            from aigis.capabilities.enforcer import CapabilityEnforcer

            self._enforcer = CapabilityEnforcer(store=capabilities, guard=self)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def monitor(self) -> BehavioralMonitor | None:
        """Access the behavioral monitor, if configured.

        Returns:
            The BehavioralMonitor instance, or None if not configured.
        """
        return self._monitor

    def check_input(self, text: str) -> CheckResult:
        """Scan a plain-text user prompt for threats.

        Args:
            text: The raw user input string.

        Returns:
            CheckResult — inspect ``.blocked`` and ``.reasons``.
        """
        score, level, matched = filter_input(text, self._policy.custom_rules or None)
        result = self._make_result(score, level, matched)
        self._record_to_monitor("check_input", "scan:input", text[:100], result)
        return result

    def check_messages(self, messages: list[dict]) -> CheckResult:
        """Scan an OpenAI-style messages array for threats.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.

        Returns:
            CheckResult — inspect ``.blocked`` and ``.reasons``.
        """
        score, level, matched = filter_messages(messages, self._policy.custom_rules or None)
        result = self._make_result(score, level, matched)
        target = str(len(messages)) + " messages"
        self._record_to_monitor("check_messages", "scan:messages", target, result)
        return result

    def check_output(self, text: str) -> CheckResult:
        """Scan an LLM response string for data leaks and harmful content.

        Args:
            text: The raw LLM response string.

        Returns:
            CheckResult — inspect ``.blocked`` and ``.reasons``.
        """
        score, level, matched = filter_output(text, self._policy.custom_rules or None)
        result = self._make_result(score, level, matched)
        self._record_to_monitor("check_output", "scan:output", text[:100], result)
        return result

    def check_response(self, response_body: dict) -> CheckResult:
        """Scan an OpenAI-compatible response body for data leaks.

        Args:
            response_body: Parsed JSON dict from the upstream LLM.

        Returns:
            CheckResult — inspect ``.blocked`` and ``.reasons``.
        """
        score, level, matched = filter_response(response_body, self._policy.custom_rules or None)
        result = self._make_result(score, level, matched)
        self._record_to_monitor("check_response", "scan:response", "response_body", result)
        return result

    # ------------------------------------------------------------------
    # Layer 4: Capability-based tool authorization
    # ------------------------------------------------------------------

    def authorize_tool(
        self,
        tool_name: str,
        tool_input: dict,
        data_provenance: TaintLabel | None = None,
    ) -> AuthorizationResult:
        """Authorize a tool call using capability-based access control.

        Requires ``capabilities`` to have been passed to the constructor.

        Args:
            tool_name: Name of the tool to authorize.
            tool_input: Arguments dict for the tool call.
            data_provenance: Taint label of the data driving this call.
                Defaults to UNTRUSTED if not specified.

        Returns:
            AuthorizationResult indicating whether the call is permitted.

        Raises:
            RuntimeError: If no CapabilityStore was configured.
        """
        if self._enforcer is None:
            raise RuntimeError(
                "authorize_tool() requires a CapabilityStore. "
                "Pass capabilities=CapabilityStore() to Guard()"
            )

        if data_provenance is None:
            from aigis.capabilities.taint import TaintLabel as _TL

            data_provenance = _TL.UNTRUSTED

        enforcer_result = self._enforcer.authorize_tool_call(
            tool_name=tool_name,
            tool_input=tool_input,
            data_provenance=data_provenance,
        )

        return AuthorizationResult(
            allowed=enforcer_result.allowed,
            capability_used=enforcer_result.capability_used,
            reason=enforcer_result.reason,
            taint_level=enforcer_result.taint_level,
            scan_result=enforcer_result.scan_result,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _make_result(self, score: int, level: RiskLevel, matched: list[MatchedRule]) -> CheckResult:
        blocked = self._policy.should_block(score)
        reasons = list({r.rule_name for r in matched})
        remediation = _build_remediation(matched)
        return CheckResult(
            risk_score=score,
            risk_level=level,
            blocked=blocked,
            reasons=reasons,
            matched_rules=matched,
            remediation=remediation,
        )

    def _record_to_monitor(
        self,
        tool_name: str,
        resource: str,
        target: str,
        result: CheckResult,
    ) -> None:
        """Record a check result to the behavioral monitor, if configured."""
        if self._monitor is None:
            return
        outcome = "blocked" if result.blocked else "allowed"
        self._monitor.record_action(
            tool_name=tool_name,
            resource=resource,
            target=target,
            risk_score=result.risk_score,
            outcome=outcome,
        )

    def __repr__(self) -> str:
        parts = [
            f"Guard(policy={self._policy.name!r}",
            f"block_at={self._policy.auto_block_threshold}",
            f"allow_at={self._policy.auto_allow_threshold}",
        ]
        if self._capabilities is not None:
            count = len(self._capabilities.list_active())
            parts.append(f"capabilities={count}")
        if self._monitor is not None:
            parts.append("monitor=active")
        return ", ".join(parts) + ")"
