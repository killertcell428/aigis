# Synthesis: 6-Discipline Convergence Map for Aigis v2

This document synthesizes the six discipline-specific research memos (`01-immune-system.md` through `06-safety-engineering.md`) into a unified architectural map. The original question being answered:

> 「AIセキュリティってAI側が元のコードからハッキングしてすり抜けるから意味がない、オープンソースや仕組みがAIに渡る時点で防ぎようがない」

Can we design AI security that survives full disclosure of the algorithm? Six independent research passes give a convergent answer: **yes, but only by moving beyond detection into a layered architecture where the load-bearing primitives are structural (capability, origin, plan-commit) rather than statistical (pattern matching).**

## 1. Convergence map — where the disciplines independently agreed

| # | Concept | Disciplines (Σ/6) | Common core |
|---|---|---|---|
| 1 | **Capability / Origin / Provenance** | Immune (MHC) · Mechanism · OS · Web · Safety · Crypto | **6/6.** "Structurally distinguish content by its source and the rights that source carries." Named MHC presentation / capability tokens / object capabilities / SOP / signed manifests / Clark-Wilson transactions across disciplines. |
| 2 | **Plan / commit before execution** | Mechanism · Web · OS · Safety | 4/6. Sign the plan up front; deviation is a hard fault. |
| 3 | **Graded response (not binary block)** | Immune (cytokine) · Mechanism · Web (report-only) · Safety (review queue) | 4/6. Threshold-based friction escalation. |
| 4 | **Per-session salt / randomized defender strategy** | Mechanism (Stackelberg) · Web (polymorphic) · Crypto (Kerckhoffs) | 3/6. **Publish the algorithm, keep the seed secret.** Direct answer to the open-source-detector problem. |
| 5 | **Typed sinks / Trusted Types** | Web · OS (WASI) · Safety (Clark-Wilson) | 3/6. `shell/sql/http` arguments protected at the type level. |
| 6 | **Federation / fleet-wide signal** | Mechanism · Safety (Visa) · Crypto (Sigstore) | 3/6. Exceed single-deployment visibility limits. |
| 7 | **Honeytoken / canary** | Mechanism · Immune (danger signal) | 2/6. FP=0 by construction. |

Two specific artifacts were independently recommended by multiple agents:

- **CaMeL** ([arxiv:2503.18813](https://arxiv.org/abs/2503.18813), DeepMind 2025) — capability-based dual-LLM with an IFC interpreter. Named by Mechanism, Web, OS, and Crypto memos.
- **AIP / IBCT** ([arxiv:2603.24775](https://arxiv.org/abs/2603.24775), IETF draft 2026) — Invocation-Bound Capability Tokens. Named by Mechanism and OS memos.

These should anchor v2.

## 2. The three conceptual pillars

### Pillar A — Capability + Provenance (the architectural center)

The 6/6 convergence point. Every discipline named some version of "the content carries metadata about its origin and the rights that origin confers, and the executor checks this before acting."

Concrete Aigis components that fall under this pillar:
- `aigis.origin` — origin-tagged prompt assembly (web memo)
- `aigis.cap` — AIP-compatible capability tokens (mechanism + OS memos)
- `aigis.attestation` — MHC-style step attestation (immune memo)
- Sigstore-signed tool descriptors (crypto memo)
- `aigis.transaction` — Clark-Wilson well-formed transactions (safety memo)

These are different lenses on the same primitive. Implement once, expose multiple APIs.

### Pillar B — STPA / Control-Loop Frame (the conceptual umbrella)

The safety memo's strongest argument: **Aigis v2 should be designed as a supervisory controller on the LLM control loop, not as an input filter.**

Every other discipline's contribution slots into a position on that loop:

```
                    ┌─────────────────────────────┐
                    │   LLM (controller)          │
                    │                             │
       ┌────────────►  reasoning + tool selection ├──┐
       │            │                             │  │
       │            └─────────────────────────────┘  │
       │                                             ▼
   ┌───┴─────────────────────────────────────────────────┐
   │ FEEDBACK CHANNEL                  CONTROL ACTIONS   │
   │                                                     │
   │ • origin tags on returns          • capability check│
   │ • SRI hash verification           • plan-commit chk │
   │ • staleness detection             • trusted types   │
   │ • canary scan                     • dual-control    │
   └─────────────────────────────────────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Process (world)│
                   └─────────────────┘
```

Aigis intervenes on both sides:
- Feedback channel: origin (web), SRI (web), canary (mechanism), staleness (safety).
- Control actions: capability (OS), plan (mechanism), Trusted Types (web), dual-control (safety).

Plus the surrounding governance: graded response (immune), velocity rules (safety), federation (safety).

### Pillar C — Kerckhoffs Discipline (the directly-stated answer to the question)

The crypto memo's clearest framing: **the answer to "open-source detectors are bypassable" is to publish everything except a small per-session secret.**

Candidate "keys":
- Signing key (developer/vendor)
- Per-session prompt salt
- Per-session rule-selection seed
- TEE attestation key
- C2PA manifest signing key

The two underused ones — per-session salt and rule-selection seed — cost nothing and meaningfully change the attacker's economics from "find one bypass" to "find a bypass that works across the salt distribution."

This pillar is small in code but conceptually load-bearing. It is the answer to the original question.

## 3. Unified v2 architecture

```
┌──────────────────────────────────────────────────────────┐
│ Conceptual frame: STPA (LLM = controller, Aigis = monitor)│
└──────────────────────────────────────────────────────────┘
            ↓
┌─ Layer 0: Detection (v1, retained) ─────────────────────┐
│ • pattern.py                                            │
│ • per-session salt + randomized rule selection          │ ← Kerckhoffs
├─ Layer 1: Provenance / Origin ──────────────────────────┤
│ • aigis.origin: tagged prompt fragments                 │ ← 6/6 convergence
│ • Sigstore-signed tool descriptors                      │
├─ Layer 2: Capability ───────────────────────────────────┤
│ • aigis.cap: AIP-compatible tokens                      │ ← 5/6 convergence
│ • WASI sandbox / Landlock for native tools              │
├─ Layer 3: Structural defenses ──────────────────────────┤
│ • aigis.plan: commit-reveal                             │ ← 4/6 convergence
│ • aigis.tt: Trusted Types for dangerous args            │ ← 3/6 convergence
├─ Layer 4: Behavioral / Adaptive ────────────────────────┤
│ • aigis.trace: negative selection on behavior           │
│ • aigis.cytokine: graded response score                 │ ← 4/6 convergence
├─ Layer 5: Multi-party approval ─────────────────────────┤
│ • aigis.dual_control: 2-person rule for destructive ops │
├─ Layer 6: Tripwires ────────────────────────────────────┤
│ • aigis.canary: honeytokens                             │
├─ Layer 7: Operations ───────────────────────────────────┤
│ • aigis.velocity, review_queue, observe-mode lifecycle  │
│ • aigis.recorder: tamper-evident black box              │
└─────────────────────────────────────────────────────────┘
        ↓
┌─ Future (v3): Federation + TEE ─────────────────────────┐
│ Visa-style fleet telemetry / Nitro Enclave hosting      │
└─────────────────────────────────────────────────────────┘
```

## 4. Cross-discipline prototype ranking (Top 5 across all 6 memos)

Each agent recommended a Top 3. Aggregating across agents and weighting by convergence count:

| Rank | Component | Effort | Recommended by | Why this rank |
|---|---|---|---|---|
| 1 | **`aigis.salt`** — per-session salt + randomized rule selection | 1-2 weeks | Crypto (Top 1) | Direct answer to the original question. Lowest effort. Kerckhoffs guarantee. |
| 2 | **`aigis.origin`** — provenance tagging | 2 weeks | Web (Top 1) · Crypto (Top 2) · 6/6 convergence | Foundation that every other v2 layer depends on. The SOP of LLM security. |
| 3 | **`aigis.tt`** — Trusted Types for shell/sql/http args | 1-2 weeks/family | Web (Top 2) · OS · Safety | Structurally eliminates the Microsoft "prompts become shells" RCE class with deterministic code, no patterns. |
| 4 | **`aigis.plan`** — commit-reveal plans | 1-2 weeks | Mechanism (Top 2) · Web · 4/6 convergence | Makes mid-flight prompt injection structurally impossible. |
| 5 | **`aigis.canary`** — honeytokens | 1-2 days | Mechanism (Top 1) | FP=0 by construction; fastest empirical signal. |

Layers 1-4 (#1-#4 above) should be the v2.0 core scope. `aigis.canary` (#5) is a slam-dunk side ship — small enough to bundle with any of the above.

## 5. Deferred to v3 (justified by research)

- **AIP capability tokens with slashing** — needs ecosystem buy-in (mechanism memo §4).
- **Nitro Enclave host** — real cloud lock-in; ship after the orchestrator/guardrail boundary is clean (crypto memo §B).
- **Visa-style federation** — governance and privacy commitments are the hard part, not code (safety memo §6).
- **Negative selection trace detector** — requires per-deployment tolerance training, embedding pipeline, eval harness (immune memo §3.B).
- **STPA-derived detector catalog** — high-leverage but requires sustained discipline (safety memo Top 1).

## 6. Explicit "do not prototype yet" — based on research

From the crypto memo:
1. **FHE/MPC inference at LLM scale.** Two orders of magnitude too slow.
2. **General-purpose ZK-attested tool execution.** Cost asymmetric to schema validation.
3. **Formal verification of LLM behavior.** No path to scaling.

Invest formal-methods effort in the *guardrail code* (Verus/F* for the policy engine), not in the LLM weights.

## 7. Strategic positioning

From the OS memo:

> "Aigis v1 competes in the crowded 'detect bad prompts' space. Aigis v2, if it ships the broker + sandbox combo, becomes the *only* open-source MCP layer that combines (a) deterministic pattern detection, (b) unforgeable capability dispatch, and (c) OS-level isolation under a single policy file."

Add Pillars B (STPA control-loop frame) and C (Kerckhoffs salt), plus the Visa-lesson federation hint for v3, and Aigis v2 has a defensible position that takes years to copy.

## 8. Honest critique across all six memos

Common themes from the "honest critique" sections:

1. **No single primitive defeats the open-source-detector problem alone.** The salt/seed buys economics, the capability layer bounds damage, the origin layer constrains intent inheritance. They compose multiplicatively.

2. **Every structural defense introduces friction.** Two-person rule doubles latency. Commit-reveal plans constrain agent flexibility. Trusted Types require schema engineering. The deployments that adopt them first will be the ones that can absorb the friction (regulated industries, high-stakes domains). This is fine — Aigis doesn't need 100% of the market.

3. **The frameworks help by structuring thinking, not by giving definitive enumerations.** STPA, FMEA, immune metaphors — none of them produce a closed-form rule set. Use them as conceptual scaffolding, then engineer specifics.

4. **Mechanism design needs identifiable players.** Pre-AIP, MCP has no identity layer. Aigis should hard-couple to whatever identity layer emerges (AIP is the current best candidate).

5. **Open source attackers reading the immune layers too.** Pattern + negative-selection + danger + memory raises *cost* of bypass; it doesn't eliminate bypass. The only true Kerckhoffs guarantee comes from the per-session secret (Pillar C).

## 9. Original-question check

The opening claim was: "AIセキュリティは仕組みが渡る時点で防ぎようがない." Reformulated answer based on six disciplines:

**Yes, if the security is detection-only.** No, if the security is layered with structural primitives whose strength does not depend on rule secrecy:

- **Capability** (OS, mechanism, immune): the algorithm is public; the unforgeable handles are session-scoped secrets.
- **Origin** (web, immune, crypto): the algorithm is public; the per-fragment tags are integrity-protected.
- **Plan-commit** (mechanism, web, safety): the algorithm is public; the per-session plan hash is the commitment.
- **Trusted Types** (web, OS, safety): the parser is public; the *parse* either succeeds against schema or it doesn't.
- **Per-session salt** (crypto, mechanism, web): the algorithm is public; the salt is the key. This is the textbook Kerckhoffs answer.

The Kerckhoffs move (Pillar C) is the *direct* technical answer. The other pillars (A, B) make detection-free security *feasible* at all.

## 10. Roadmap suggestion

Phase 1 (v2.0, ~6-8 weeks): Layers 0-3 with the Top 5 prototypes.
Phase 2 (v2.1, ~quarter): Layer 4 (graded response, behavioral baselining), Layer 5 (dual-control).
Phase 3 (v2.2, ~quarter): Layer 6-7 (canaries already from Phase 1; recorder, velocity, observe-mode).
Phase 4 (v3, multi-quarter): AIP integration, Nitro Enclave, federation. Each is a moat-grade investment with ecosystem dependencies.

This sequencing front-loads the Kerckhoffs guarantee (Phase 1) so the open-source-detector concern is addressed in the first release, then progressively adds the structural defenses.
