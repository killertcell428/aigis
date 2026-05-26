# Safety Engineering & Anti-Fraud Paradigms for Aigis v2

LLM agent security is currently dominated by a CS/ML mindset: pattern detection, model evaluation, red-teaming. But hostile environments with high-stakes failure modes are a *solved-ish* problem in older disciplines — aviation kills people, nuclear melts cities, banks lose billions.

## 1. Safety Engineering Primitives — What Survives the Translation

### Swiss Cheese Model (Reason, 1990)
Every defensive layer has holes. Failures occur when holes line up. **Measure hole alignment, not individual layer accuracy.** If two layers both miss the same attack category, they aren't independent — they're one layer pretending to be two.

**Aigis proposal:** add a `correlation_matrix` report to `aigis bench` showing which detectors miss the same attacks.

### Defense in Depth (Nuclear)
A reactor has: fuel pellet matrix → cladding → primary coolant loop → containment vessel → exclusion zone → regulatory oversight. Each layer engineered for a *different* failure class.

### Two-Person Rule
Nuclear launch, narcotic dispensing, prod DB changes. Two independent agents must agree. **Highest-ROI single import for Aigis.**

**`aigis.dual_control`** — a policy attribute on tools. When `dual_control=True`, the call is forwarded to a second, independently-prompted LLM (different system prompt, ideally different model) that sees only `{tool_name, arguments, brief justification}` and must approve.

```python
@aigis.tool(dual_control=True, reviewer_model="claude-haiku")
def delete_files(paths: list[str]): ...
```

Effort: ~1 week. The reviewer prompt is the hard part — must be independent enough that prompt injection doesn't transfer.

### FMEA — Failure Mode and Effects Analysis
For each component: what can fail, what's the effect, severity, detectability. Aigis already does this informally. Formalizing would yield `failure_modes.yaml` per detector class.

### STAMP / STPA (Leveson, MIT) — The Most Important Framework Here
Leveson's claim: most modern accidents are not component failures, they are **control failures**. The classic STPA categorization of unsafe control actions:

1. Control action **not provided** when needed
2. Control action **provided** when unsafe
3. Control action provided with **wrong timing/order**
4. Control action provided with **wrong duration**

Map onto an LLM agent:
- LLM doesn't call `verify_user_intent` when it should → (1)
- LLM calls `transfer_funds` based on poisoned email → (2)
- LLM calls `send_email` before approval comes back → (3)
- LLM holds a database transaction open indefinitely → (4)

**This generates a deterministic detector catalog** — not a vibes-based one.

### Bow-Tie Analysis
Left = threats/causes; center = hazard; right = consequences. Barriers on both sides.

**Aigis proposal:** publish `docs/bowties/` with one bow-tie per top attack class (prompt injection, MCP rug-pull, memory poisoning, tool argument tampering). Each barrier maps to a specific detector rule ID.

### Black Box / Flight Data Recorder
**Aigis proposal:** `aigis.recorder` — append-only signed log of `(prompt, retrieval, tool_calls, detector_verdicts, output)` per agent turn. Compatible with a public incident-report schema.

### NOTAMs / Safety Bulletins
Aviation broadcasts hazards fleet-wide within hours. CVE is the closest CS analog but slow. See §6 (Visa).

## 2. Military / Intelligence Models — Mostly Bad Fits, One Good One

- **Bell-LaPadula**: designed for static document classification. LLM context is fluid. Poor fit.
- **Biba**: integrity dual of BLP. "Don't let the agent read low-integrity sources before issuing high-integrity actions" is exactly the prompt-injection-via-retrieval pattern. Worth a look.
- **Brewer-Nash Chinese Wall**: relevant when the same agent handles multiple tenants.
- **Clark-Wilson — well-formed transactions, separation of duty**: this *is* the right model. Every tool call should be a well-formed transaction that can only move the system between valid states.

**`aigis.transaction` decorator** — a tool call wrapped in pre/post-condition check. Pre: arguments validate against schema + business rules. Post: side effects match declared effects. Rejected transactions roll back.

- **Cross-domain solutions / data diodes**: one-way information flow. Sandboxed-tool output that the LLM should be able to *read but not act on without review*.

## 3. Anti-Fraud — The Closest Existing Analog

Banking anti-fraud is the discipline closest to "deterministic guardrails on a probabilistic agent."

### Velocity Rules
Visa flags "5 transactions in 60 seconds across 3 countries." Trivial logic, enormous coverage.

**`aigis.velocity`** — per-(agent, tool) and per-(agent, capability-class) rate limits with adaptive backoff. Effort: ~3 days.

```python
aigis.velocity.configure(
    ("agent_id", "fs.write"), max_per_minute=10, burst=20,
    on_breach="soft_block",
)
```

### Behavioral Baselining
Banks compute a per-cardholder spending baseline; deviations trigger review. Equivalent for agents: per-agent baseline of tool-call distribution, prompt length, retrieval diversity.

**`aigis.baseline`** — collects a 7-day rolling distribution per agent. Cheap, no ML needed.

### Step-Up Authentication
Low-risk transactions go through; high-risk ones demand more proof.

### Soft Block + Review Queue
Banks rarely hard-decline ambiguous transactions — they hold them. Far better UX than a hard block and provides labeled training data.

**`aigis.review_queue`** — when a detector returns `verdict=ambiguous`, the call is paused, serialized, and made available to a human reviewer or higher-tier model.

### Reason Codes
Every Visa decline has a numbered reason code. Aigis already has rule IDs — preserve this strength.

### Shadow Mode for New Rules
New fraud rules ship in observation mode for weeks before enforcement. **The single biggest discipline gap in current LLM security.**

**`mode=observe`** on every new detector. Telemetry from N runs feeds an automatic promotion check.

### Chargebacks — Economic Feedback
Banks make merchants pay for fraud they accept. Governance proposal more than code: agent operators should bear cost when their agent causes harm to downstream parties.

## 4. Concrete Proposals for Aigis v2 (Consolidated)

| # | Proposal | Attack class | Effort | API surface |
|---|---|---|---|---|
| 1 | `aigis.dual_control` | Destructive tool misuse | 1 week | Tool decorator |
| 2 | `aigis.velocity` | Runaway loops, exfiltration | 3 days | Middleware config |
| 3 | `aigis.baseline` | Behavioral drift | 1 week | Background collector |
| 4 | `aigis.review_queue` | Ambiguous cases, UX | 2 weeks | New subsystem |
| 5 | `aigis.recorder` | Forensics, compliance | 1 week | Append-only sink |
| 6 | `aigis.transaction` (Clark-Wilson) | Integrity violations | 2 weeks | Tool decorator |
| 7 | `mode=observe` lifecycle | New-rule false positives | 1 week | Detector metadata |
| 8 | STPA-derived detector catalog | Control failures | 4 weeks | Generated rules |
| 9 | Bow-tie docs per attack class | Compliance, legibility | 2 weeks | `docs/bowties/` |

## 5. The Control-Theory Frame — Why This Might Be the Right Mental Model

Leveson's STAMP argues that pattern detection is structurally insufficient because it treats accidents as component failures. But LLM agents fail like control systems fail: the controller (LLM) acts on a process (the world via tools), with feedback (tool results, retrieval), and the controller has a model (the context window) that diverges from reality over time.

The dominant failure modes match STPA's categories exactly:
- **Stale context**: the LLM's mental model lags the actual session.
- **Poisoned feedback**: retrieved documents or tool outputs are adversarial.
- **Missing feedback**: tool calls succeed silently when the effect is wrong.
- **Wrong-timing actions**: agent commits before user confirms.

**Implication for Aigis v2:** stop thinking of Aigis as an input filter sitting in front of the LLM. Think of it as a **supervisory controller** that monitors the loop: prompt → action → observation → next prompt. It enforces invariants on the *loop*, not just the messages.

Concretely:
- Enforce that every tool call has a feedback consumed within N turns ("the controller must read its sensors").
- Enforce that destructive actions cannot be issued before a confirming observation ("no fire without target lock").
- Detect when context staleness exceeds a threshold and force a re-grounding step.

This is the largest conceptual shift v2 should make.

## 6. The Visa Lesson — Federation as a Force Multiplier

Visa sees fraud patterns no single bank can. The federation layer is the product. No single Aigis deployment will see the next novel jailbreak; the fleet will.

**Aigis Federation (proposal):** opt-in, privacy-preserving telemetry channel emitting `(rule_id_fired, detector_class, anonymized_pattern_hash, timestamp, deployment_region)`. Aggregate dashboard shows novel-pattern emergence. Subscribers receive new detector rules with a 24-hour SLA, shipped in `mode=observe` by default.

The hard parts are political, not technical: privacy commitments, governance, competitive dynamics.

**This is plausibly Aigis's strongest moat** — single-deployment guardrails commoditize fast; a federation does not.

## 7. Honest Critique

- **Safety engineering assumes stable failure modes.** LLMs fail in continuous, distributional, context-dependent ways. FMEA tables go stale fast. The frameworks help by *structuring thinking*, not by giving definitive enumerations.
- **Two-person rule has high friction.** Doubling latency and inference cost is unacceptable for low-stakes calls. Use sparingly.
- **Anti-fraud federation requires data sharing.** Cross-company sharing is hard.
- **Bell-LaPadula doesn't transfer cleanly.**
- **STAMP is hard to operationalize.** Best frame, but turning STPA analyses into running code requires discipline most teams won't sustain.
- **Velocity and baseline rules have a cold-start problem.**

## 8. Recommended Reading

1. **Nancy Leveson, *Engineering a Safer World*** (MIT Press, 2011) — free PDF: https://direct.mit.edu/books/oa-monograph/2908/Engineering-a-Safer-WorldSystems-Thinking-Applied
2. **Nancy Leveson, *STPA Handbook*** (2018) — free PDF: https://psas.scripts.mit.edu/home/get_file.php?name=STPA_handbook.pdf
3. **James Reason, *Human Error*** (Cambridge, 1990).
4. **Diogo Sebastião et al., "Applying STPA to AI safety"** — recent work bringing STPA into ML contexts.
5. **David Clark & David Wilson, "A Comparison of Commercial and Military Computer Security Policies"** (1987).

## Top 3 to Prototype (Ranked)

1. **STPA-derived detector catalog (`aigis.stpa`)** — the single biggest conceptual upgrade. Run STPA analysis on a representative agent, enumerate unsafe control actions across the four STPA categories, and codegen detector stubs. Highest leverage, highest learning.

2. **`aigis.velocity` + `aigis.review_queue` + `mode=observe` lifecycle** — bundle these three because they together port the anti-fraud operations discipline into Aigis. Converts Aigis from "rule engine" to "fraud operations platform." Mid effort, immediate user-visible value.

3. **`aigis.dual_control` for destructive tools** — narrow, high-leverage, story-tellable. Picks up exactly the prompt-injection-to-destructive-action class. Cheap to ship, easy to demo, defensible in compliance conversations.

Federation (Visa lesson) is the highest *strategic* value but premature until the single-deployment story is solid — defer to v2.x, not v2.0.
