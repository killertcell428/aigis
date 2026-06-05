# Pending: OMNI-LEAK cross-agent data-boundary detection

## Title
Cross-agent data-boundary enforcement for orchestrator networks

## Motivation
OMNI-LEAK (arxiv:2602.13477, Feb 2026) demonstrates that a single indirect prompt injection
into an orchestrator multi-agent network can cause agents to leak sensitive data that they
individually should not be able to access. The attack succeeds because agents do not verify
that the data they are about to relay was within their access scope to begin with. A data-
boundary scanner would check whether an agent message references data from a domain that the
sending agent did not legitimately have access to.

## Research finding that led to this idea
OMNI-LEAK finding in `research/2026-06-05T03-03_6-multi-agent.md`:
> "Demonstrates that a single indirect prompt injection can be amplified across a
> multi-agent network to leak data from agents that individually have restricted data access."

## Proposed change
Add a `data_boundary_check(message, sender_scope)` method to `AgentMessageScanner` that:
1. Takes a set of data labels (e.g., `{"user_pii", "financial_records"}`) representing
   what data the sending agent is authorized to reference.
2. Scans the message content for references to data labels outside that scope.
3. Raises a `data_exfil` risk if cross-boundary data references are found.

This would complement the existing exfiltration URL patterns with a content-level check.

## Why it was held back
This feature requires callers to provide per-agent data-access scopes, which is a new
required parameter concept. It changes the public API surface of `AgentMessageScanner`
(either a new required method argument or a new configuration object). This is a
**breaking public API change** (or at minimum a significant new concept that needs design).

## Constraint that blocked it
"Any breaking public API change in `aigis/`, including signature changes, removals, or
semantic changes."

## Suggested next step for the human reviewer
Design an opt-in `DataBoundaryPolicy` object that can be passed to `AgentMessageScanner`
at construction time (default `None` = disabled). When set, the `scan_message` method
uses it to validate that message content only references data within the sender's declared
scope. Keep the existing API fully backward-compatible. The boundary policy could be backed
by a simple YAML file or Python dict mapping agent IDs to allowed data labels.
