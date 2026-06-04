# Pending: FlowSteer Workflow Routing Redirection Patterns

**Title:** Detect prompt-only workflow steering attacks that redirect agent orchestration
**Motivation:** FlowSteer (NUS WING, 2026) demonstrates that prompts alone can steer agent organization and malicious-signal propagation in multi-agent LLM systems without modifying infrastructure. The attack exploits orchestrators that use natural language to decide which sub-agents to invoke, making the routing decision vulnerable to adversarial framing.

**Research finding:** FlowSteer (NUS WING 2026) — <https://wing.comp.nus.edu.sg/publication/flowsteer-2026/>. Showed that workflow formation itself is a planning-time attack surface; FlowGuard was proposed as an input-side defense.

**Proposed change:** Add a `_WORKFLOW_STEERING_PATTERNS` group detecting:
- "route (all|every|this) (task|request|query) through [agent]"
- "use [agent] as the (primary|only|main) (handler|processor|executor) for (all|every|any)"
- "ensure (all|every) (step|task|decision) goes through [agent]"
These are distinct from `_AGENT_CARD_POISONING_PATTERNS` which focus on "always route to me" in agent capability metadata; FlowSteer targets the orchestrator's planning prompt.

**Why held back:** Significant overlap with existing `_AGENT_CARD_POISONING_PATTERNS`. The three patterns above would fire on nearly identical content to existing patterns #7a and #7b. Adding them without a clear distinguishing characterization of workflow-steering vs. task-routing would increase duplicate alerts without improving coverage. A future cycle should first audit whether the existing agent card patterns catch FlowSteer-style attacks empirically.

**Constraint that blocked it:** Too close to existing patterns; risk of duplicate-detection noise. Needs empirical differentiation study first.

**Suggested next step:** Run FlowSteer benchmark payloads against existing `_AGENT_CARD_POISONING_PATTERNS` to measure coverage gaps. If >30% of FlowSteer payloads are missed, add distinct routing-context patterns targeting the orchestrator's task-planning step.
