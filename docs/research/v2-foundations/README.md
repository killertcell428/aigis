# Aigis v2 Foundations — Cross-Discipline Research

This directory contains research informing the Aigis v2 architecture. The original question:

> 「AIセキュリティってAI側が元のコードからハッキングしてすり抜けるから意味がない、オープンソースや仕組みがAIに渡る時点で防ぎようがない」という議論をクリアする仕組みは作れるか？

That is: **can we design AI security that survives full disclosure of the algorithm?** The cryptographic answer (Kerckhoffs) is yes — but only if the design moves beyond detection. This research surveys six adjacent disciplines for transferable architectural primitives.

## Contents

| File | Discipline | Core insight |
|---|---|---|
| `01-immune-system.md` | Biological immunology | Innate + adaptive layers, danger theory (consequences > non-self), graded response (cytokines) |
| `02-mechanism-design.md` | Game theory / mechanism design | Slashable capability tokens, commit-reveal plans, honeytokens. AIP (arxiv:2603.24775) |
| `03-os-systems-security.md` | OS / capability systems | Object capabilities, WASI sandbox, Landlock+seccomp, privsep. Wassette / AIP convergence |
| `04-web-security.md` | Web security model | SOP/CSP/Trusted Types/SRI. Provenance is the load-bearing primitive. CaMeL lineage |
| `05-cryptography-tee.md` | Cryptography / TEE / ZKP | Per-session salt (Kerckhoffs), Sigstore provenance, Nitro Enclaves. ZK/HE deferred |
| `06-safety-engineering.md` | Safety engineering / anti-fraud | STAMP/STPA control-loop frame, two-person rule, Visa-style federation, Clark-Wilson |
| `synthesis.md` | All six | Convergence map, unified v2 architecture, prioritized roadmap |

## TL;DR (read this first)

Six independent research passes converged on the same architectural center:

1. **Capability / Origin / Provenance** — load-bearing primitive named by all 6 disciplines under different names (MHC presentation, capability tokens, object capabilities, SOP, signed manifests, Clark-Wilson transactions).
2. **Plan / commit before execution** — named by 4 disciplines (commit-reveal, CaMeL static plan, capability grants, STPA "no fire without target lock").
3. **Graded response, not binary block** — 4 disciplines (cytokine, cost-asymmetric, report-only, review queue).
4. **Per-session salt / randomized defender strategy** — 3 disciplines (Stackelberg, polymorphic prompt, Kerckhoffs). The direct answer to the open-source-detector problem.

Two specific artifacts were independently recommended by multiple agents:

- **CaMeL** (arxiv:2503.18813, DeepMind 2025) — capability-based dual-LLM with IFC interpreter.
- **AIP / IBCT** (arxiv:2603.24775, IETF draft 2026) — Invocation-Bound Capability Tokens for MCP.

These should anchor v2.

## Recommended v2 prototype order

| # | Component | Effort | Why |
|---|---|---|---|
| 1 | `aigis.salt` — per-session salt + randomized rule selection | 1-2 weeks | Directly answers the open-source-detector problem with the cheapest Kerckhoffs move |
| 2 | `aigis.origin` — provenance-tagged prompt assembly | 2 weeks | Foundation every other v2 layer depends on (the SOP of LLM security) |
| 3 | `aigis.tt` — Trusted Types for shell/sql/http tool args | 1-2 weeks/family | Structurally eliminates the "prompts become shells" RCE class |
| 4 | `aigis.plan` — commit-reveal plan enforcement | 1-2 weeks | Makes mid-flight prompt injection structurally impossible |
| 5 | `aigis.canary` — honeytoken module | 1-2 days | FP=0 by construction; fastest empirical signal |

Defer to v3: AIP capability tokens (needs ecosystem buy-in), Nitro Enclaves (cloud lock-in), Visa-style federation (governance), ZK/MPC/HE inference (still 10-1000× overhead).

## Conceptual frame

The strongest umbrella framing came from safety engineering: **Aigis v2 should be designed as a supervisory controller on the LLM control loop (Leveson's STAMP), not as an input filter.** Every other discipline's contribution slots into a position on that loop:

- Origin/provenance — controls what information the controller sees
- Capability — controls what control actions the controller can issue
- Plan/commit — controls when control actions can be reordered
- Graded response — controls system response to anomalies
- Salt/randomization — controls the controller's attack-time predictability
- Federation — provides fleet-level feedback the controller can't generate alone

## Original research date

Researched 2026-05-26. Sources are dated through 2026-Q2.
