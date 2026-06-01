"""ActivityEvent -> Elastic Common Schema (ECS) 8.x mapper.

ECS is chosen as the default wire format because:

* it is the schema Elastic Security, Wazuh, and a number of OSS SIEMs natively
  index without transform pipelines;
* Microsoft Sentinel's Log Ingestion API + Data Collection Rules accept ECS
  JSON directly via a simple KQL projection;
* Splunk CIM can be derived from ECS field-by-field, so a CIM mapper is a
  thin wrapper over this one when it is needed;
* ECS field semantics (`event.action`, `event.outcome`, `event.severity`,
  `user.name`, `process.command_line`) align cleanly with what
  :class:`aigis.activity.ActivityEvent` already records.

This mapper is intentionally pure-data: no I/O, no global state, deterministic
output. That makes it trivial to golden-test and to swap behind
:class:`EventMapper` for CEF / OCSF / custom schemas in later phases.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

# ECS version we target. We do not advertise a newer version than we have
# actually validated against; downstream consumers use this for routing.
ECS_VERSION = "8.11.0"

# Map of Aigis policy decisions to ECS event.outcome values.
# ECS only defines {success, failure, unknown}, so we map "deny" -> failure
# (action was rejected), "allow" -> success, and "review" -> unknown
# (decision deferred). The original Aigis decision is preserved verbatim
# in aigis.policy.decision for analysts who need the precise label.
_OUTCOME_MAP = {
    "allow": "success",
    "deny": "failure",
    "review": "unknown",
    "error": "failure",
}

# Map Aigis risk_level to ECS event.severity (1=info .. 7=critical, per ECS).
_SEVERITY_MAP = {
    "low": 2,
    "medium": 4,
    "high": 6,
    "critical": 7,
}


@runtime_checkable
class EventMapper(Protocol):
    """Pluggable schema mapper.

    Implementations transform the Aigis raw event dict into the wire-format
    dict that the forwarder serializes (e.g. as JSON, CEF text, syslog
    structured data).
    """

    def map(self, event: dict) -> dict:
        """Return the mapped wire-format event. Must not mutate ``event``."""


class ECSMapper:
    """Map an ActivityEvent dict to an ECS 8.x document.

    Parameters
    ----------
    dataset:
        Value for ``event.dataset``. Defaults to ``"aigis.activity"``; set
        per-deployment if you need to split alerts from telemetry indexes.
    service_name:
        Value for ``service.name``. Defaults to ``"aigis"``.
    namespace:
        Optional value for ``data_stream.namespace`` — useful when shipping
        to multi-tenant Elastic data streams.
    """

    def __init__(
        self,
        *,
        dataset: str = "aigis.activity",
        service_name: str = "aigis",
        namespace: str | None = None,
    ) -> None:
        self._dataset = dataset
        self._service_name = service_name
        self._namespace = namespace

    def map(self, event: dict) -> dict:
        decision = event.get("policy_decision", "allow")
        event_type = event.get("event_type", "tool_call")
        risk_score = int(event.get("risk_score") or 0)
        risk_level = event.get("risk_level") or "low"

        # ECS event.kind: "alert" for blocked/reviewed/high-risk; "event"
        # otherwise. Aligns with Elastic Security alert routing.
        is_alert = (
            decision in ("deny", "review")
            or risk_score >= 50
            or event_type in ("policy_block", "scan_alert")
        )

        doc: dict = {
            "@timestamp": event.get("timestamp"),
            "ecs": {"version": ECS_VERSION},
            "event": {
                "kind": "alert" if is_alert else "event",
                "category": _ecs_category(event.get("action", "")),
                "type": _ecs_event_type(event.get("action", "")),
                "action": event.get("action"),
                "outcome": _OUTCOME_MAP.get(decision, "unknown"),
                "severity": _SEVERITY_MAP.get(risk_level, 2),
                "dataset": self._dataset,
                "module": "aigis",
                "id": event.get("event_id") or None,
                "risk_score": risk_score,
                "reason": _join(event.get("remediation_hints")) or None,
            },
            "service": {
                "name": self._service_name,
                "type": "ai_agent_guard",
            },
            "user": {
                "name": event.get("user_id") or None,
            },
            "host": {
                # cwd is the project root — analysts treat it as the host
                # working directory for the agent process.
                "name": event.get("project_name") or None,
            },
            "process": {
                "working_directory": event.get("cwd") or None,
                # `target` may be a shell command, a file path, or a URL.
                # Routing it to process.command_line gives Splunk CIM /
                # Sentinel UEBA something to correlate against.
                "command_line": event.get("target") or None,
            },
            "rule": {
                "id": event.get("policy_rule_id") or None,
                "ruleset": "aigis-policy",
                "name": (event.get("matched_rules") or [None])[0],
            },
            "labels": {
                "agent_type": event.get("agent_type") or None,
                "session_id": event.get("session_id") or None,
                "autonomy_level": event.get("autonomy_level") or None,
                "memory_scope": event.get("memory_scope") or None,
                "fix_applied": event.get("fix_applied"),
            },
            "aigis": {
                # Preserve original semantics verbatim for analysts.
                "schema_version": 1,
                "event_type": event_type,
                "policy": {
                    "decision": decision,
                    "rule_id": event.get("policy_rule_id") or None,
                },
                "risk": {
                    "score": risk_score,
                    "level": risk_level,
                },
                "matched_rules": list(event.get("matched_rules") or []),
                "owasp_refs": list(event.get("owasp_refs") or []),
                "remediation_hints": list(event.get("remediation_hints") or []),
                "delegation_chain": list(event.get("delegation_chain") or []),
                "estimated_cost_usd": event.get("estimated_cost"),
                "suggested_fix": event.get("suggested_fix") or None,
                "details": event.get("details") or {},
            },
        }

        if self._namespace:
            doc["data_stream"] = {
                "type": "logs",
                "dataset": self._dataset,
                "namespace": self._namespace,
            }

        pruned = _prune(doc)
        assert isinstance(pruned, dict)  # _prune of a dict is always a dict
        return pruned


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# ECS event.category vocabulary — fixed enum upstream. We map Aigis action
# prefixes onto the closest categories so dashboards work without custom KQL.
_CATEGORY_BY_PREFIX = {
    "shell": ["process"],
    "file": ["file"],
    "network": ["network"],
    "llm": ["intrusion_detection"],
    "mcp": ["intrusion_detection"],
    "agent": ["process"],
    "session": ["authentication"],
    "scan": ["intrusion_detection"],
    "policy": ["intrusion_detection"],
}


def _ecs_category(action: str) -> list[str]:
    prefix = action.split(":", 1)[0] if ":" in action else action
    return _CATEGORY_BY_PREFIX.get(prefix, ["process"])


def _ecs_event_type(action: str) -> list[str]:
    # ECS event.type is also an enum; we keep it conservative.
    if action.startswith(("shell:", "agent:")):
        return ["start"]
    if action.startswith("file:write"):
        return ["change"]
    if action.startswith("file:read") or action.startswith("network:"):
        return ["access"]
    return ["info"]


def _join(items: object) -> str | None:
    if not items:
        return None
    if isinstance(items, list):
        return " | ".join(str(x) for x in items if x)
    return str(items)


def _prune(value: object) -> object:
    """Recursively drop None and empty-string values to keep ECS docs lean.

    Empty lists and dicts are retained when they are the documented shape
    (``aigis.matched_rules`` is a list whether or not it has entries) but
    None/"" leaves are removed so SIEM mapping tables don't have to special-case
    optional fields.
    """
    if isinstance(value, dict):
        pruned = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in pruned.items() if v is not None and v != ""}
    if isinstance(value, list):
        return [_prune(x) for x in value]
    return value
