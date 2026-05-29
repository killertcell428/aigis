# The Immune System as a Security Paradigm for Aigis

## 1. Core immune system concepts and their AI-security mapping

| Biology | Mechanism | AI-security analog |
|---|---|---|
| **Innate immunity** (PRRs detect PAMPs — e.g., TLR4 binding LPS) | Hard-coded receptors for conserved molecular signatures shared by broad pathogen classes. Fast, no learning. | Exactly what Aigis does today — regex/`DetectionPattern` matches on "ignore previous instructions", base64-wrapped payloads, MCP rug-pull descriptor diffs. PAMP = pattern. |
| **Adaptive immunity** (B/T cell receptor diversity via V(D)J recombination, clonal selection, affinity maturation) | Random combinatorial receptor library → antigen binders are *selected and amplified*; somatic hypermutation produces higher-affinity variants. | A learning loop that generates detector "antibodies" against novel attacks and refines them over exposures. Aigis's `adversarial_loop.py` is a primitive of this. |
| **Memory B/T cells** | Long-lived clones from past responses produce a faster, stronger secondary response. | A "memory pool" of past-attack embeddings/patterns, queried before invoking expensive checks. |
| **Negative selection in thymus** (central tolerance) | T cells that bind *self* antigens too strongly are deleted during maturation. The mature repertoire by construction does not attack self. | Train detectors only on **known-good** agent traces, delete any detector that fires on them, keep the rest. Whatever survives flags non-self. |
| **Peripheral tolerance / Treg cells** | Self-reactive cells that escape the thymus are suppressed in tissue. | Per-deployment whitelist / suppression layer that learns the *local* definition of normal for a given customer. |
| **Danger model (Polly Matzinger, 1994)** | Immune system attacks things that emit *danger signals* (necrosis, HMGB1, ATP in wrong compartment), not things that are merely non-self. Explains why we tolerate gut flora and a fetus. | Don't flag based on "foreign-looking text" — flag based on *consequences*: tool calls that touch new capabilities, sudden privilege widening, exfiltration-shaped traffic, unexpected state writes. |
| **MHC class I / II antigen presentation** | Every cell continuously displays fragments of its internal proteins on the surface; if the fragment is wrong (viral) or absent, the cell is killed. | Force every agent step to "present" its proof-of-state: structured trace of (prompt-hash, tool-args, memory-read-keys). A monitor inspects what was presented, not just inputs/outputs. |
| **Cytokine cascade / inflammation** | Graded chemical response: local → systemic, with positive and negative regulators. | Replace binary allow/block with a *threat score* that decays over time, raises sensitivity of neighbors, and triggers escalation only past thresholds. |
| **Autoimmune disease** (T1D, MS, lupus) | Tolerance breaks; immune system attacks self. | False positives — Aigis blocking a legitimate refactor request because it contains "delete file". The cost is loss of user trust, not just an annoyance. |
| **Allergy / hypersensitivity (IgE, anaphylaxis)** | Overreaction to harmless antigens; the response itself is the damage. | Over-aggressive filtering that destroys task completion (e.g., a coding agent that refuses to read any `.env.example`). |

## 2. Existing academic work — what was tried and why most of it stalled

**Stephanie Forrest & Steven Hofmeyr — Computer immunology (UNM, 1996–2007).** Foundational work. `Intrusion detection using sequences of system calls` (J. Computer Security, 1998) showed short n-grams of syscalls from privileged UNIX processes give a clean self/non-self boundary. Worked well *on the narrow problem* — UNIX daemons in 1998 had very stable syscall distributions. **Why it didn't scale:** modern software is too dynamic; the "self" set is unbounded. ([Forrest's review, ACSAC 2008](https://www.cs.unm.edu/~forrest/publications/acsac08.pdf))

**Negative Selection Algorithm (Forrest et al., 1994).** Generate random detectors, discard any that match self, keep the rest. **Critique:** Stibor, Timmis, and Eckert (2005–2006) showed the detector space grows exponentially in input dimensionality; on real network data NSA was *worse* than a one-class SVM. The 2023 ScienceDirect survey ([negative selection in anomaly detection — A survey](https://www.sciencedirect.com/science/article/abs/pii/S1574013723000242)) confirms the field has largely been outclassed by deep one-class methods, with niche revivals using r-chunk detectors.

**Dasgupta's AIS textbook line (1999–2011).** Broadest framing of AIS as a soft-computing paradigm. Many algorithms (CLONALG, AIRS, aiNet) but mostly evaluated on UCI toy datasets. Field consensus by ~2015: most AIS algorithms are "GAs / k-NN / one-class SVMs with immunological vocabulary."

**Dendritic Cell Algorithm — Greensmith, Aickelin, Cayzer (Nottingham, 2005–2010).** Real implementation of danger theory: combines "danger", "safe", and "PAMP" input signals into a context score. Strong on port-scan detection. **Limitations** (per Greensmith 2010 and the [2022 cursory-DCA review](https://www.mdpi.com/1999-4893/15/1/1)): signal categories must be *hand-engineered per domain*, online segmentation is awkward, and benchmarks rarely beat tuned ensemble baselines.

**Danger theory in computer security — Aickelin & Cayzer (2002), Aickelin et al. (2003).** The most *philosophically* useful AIS contribution: stop trying to enumerate non-self; instead detect damage signals. Influenced modern XDR/EDR designs more than it's credited.

**Recent (2024–2026) LLM/agent work that uses the immune analogy explicitly or implicitly:**

- **[TraceAegis (arXiv:2510.11203, Oct 2025)](https://arxiv.org/abs/2510.11203)** — hierarchical behavioral anomaly detection on agent execution traces; F1 0.93–0.96 on healthcare/procurement benchmarks. This is essentially negative selection over agent trace n-grams.
- **[Trajectory Guard (arXiv:2601.00516)](https://arxiv.org/pdf/2601.00516)** — lightweight sequence anomaly model for agentic AI, 17–27× faster than LLM-judge. Direct descendant of Hofmeyr/Forrest syscall-sequence IDS.
- **[Open Challenges in Multi-Agent Security (arXiv:2505.02077)](https://arxiv.org/html/2505.02077v2)** — frames the threat surface (steganographic collusion, coordinated attacks). Useful adversary model.
- **[Multi-Agent LLM Defense Pipeline (arXiv:2509.14285)](https://arxiv.org/html/2509.14285v4)** — Multiple cooperating LLM defenders; close to the "innate + adaptive" two-tier idea.
- **[Hosseini et al., AIS for Industrial IDS, Wiley 2025](https://onlinelibrary.wiley.com/doi/full/10.1155/je/8408209)** — PRISMA review confirming AIS is still active in OT/ICS but trailing on LLM-era threats.

**Net assessment of the field:** AIS contributed two enduring ideas — (a) *danger > non-self*, and (b) *populations of cheap heterogeneous detectors beat one monolithic classifier* — and a lot of overfit benchmarks. Modern deep one-class models eat its lunch on pure accuracy; its remaining value is *architectural inspiration* and *interpretability* (each detector has a meaning).

## 3. Concrete architectural proposals for Aigis v2

### A. Innate layer (keep what works — clarify the framing)
**Component:** Today's `aigis/patterns.py` (~803 lines, 100+ `DetectionPattern`s). Relabel internally as the *innate* layer; expose a `pattern.pamp_class` field (e.g., `instruction_override`, `exfil_shape`, `capability_widening`). This is purely conceptual but enables every other layer to reason about *what kind of danger* fired.
**Detects:** Conserved attack signatures — public jailbreaks, known MCP rug-pull diffs, well-known data-exfil URLs.
**Attack model:** Unsophisticated / copy-pasted attacks.
**FP risk:** Already measured at 0/26 in v1.1.0 benchmark.

### B. Negative-selection trace detector (NEW — highest priority)
**Component:** `aigis/immune/negative_selection.py`. Embed agent execution traces (sequences of `tool_name + arg_schema_hash + memory_keys_touched`) using a small sentence-embedding model. During a "tolerance phase" per deployment, learn the convex hull of normal traces. At runtime, flag traces whose nearest-neighbor cosine distance > τ.
**Detects:** Semantic bypasses of the pattern layer — attacks worded in novel ways but producing *behaviorally* anomalous tool-call sequences (e.g., `read_file → http_post` where normal traces always have `read_file → summarize`).
**Attack model:** Attacker reads `patterns.py` on GitHub and rewrites the payload until no regex fires. Negative selection doesn't care about wording, only about behavior.
**FP risk:** Medium-high. Mitigations: (i) per-customer tolerance training, (ii) require trace anomaly *plus* a danger signal from layer C before blocking, (iii) ship in "shadow / log-only" mode for N runs before enforcement.
**Prior art:** TraceAegis is essentially this; replicate it as an offline-trainable component shipped with Aigis.

### C. Danger-signal layer (Matzinger-style) (NEW)
**Component:** `aigis/immune/danger.py`. A short list of *consequence* detectors that fire regardless of input wording:
- Capability widening: tool A called with arg set never seen before for this session.
- Memory delta: write to a memory key that's read by a future session of a *different* user.
- Egress shape: outbound payload contains > N bytes of base64 / high-entropy strings.
- Authority escalation: a sub-agent obtains a token the parent didn't have.
**Detects:** Indirect prompt injection where the *prompt* looks innocuous (page summary) but the resulting actions are damaging.
**Attack model:** Indirect injection via retrieved content / poisoned tools.
**FP risk:** Lower than B because danger signals are tied to side-effects, which are inherently rare.
**Wiring:** Danger signal scores feed into a graded threat score (layer F).

### D. Adaptive memory ("B-cell pool") (NEW — formalize what `adversarial_loop.py` already drafts)
**Component:** `aigis/immune/memory_pool.py`. When *any* layer (B/C/E) flags a novel attack with high confidence:
1. Hash + embed the offending input + the tool-call trace.
2. Generate K mutated variants (LLM-driven paraphrase, encoding swaps, splitting, language flip).
3. Add (original + variants) to a persistent memory index.
4. On future requests, do a sub-millisecond ANN lookup against the memory pool before invoking heavier checks. A hit = immediate block with the original rule_id as evidence.

### E. MHC-style trace attestation (NEW — structural, not statistical)
**Component:** `aigis/immune/attestation.py`. Wrap each agent step so it must emit a signed structured `Presentation`:
```
{step_id, prompt_hash, system_prompt_hash, tools_offered_hash,
 chosen_tool, args_schema_hash, memory_read_keys, parent_step_id}
```
A monitor (running out-of-band) verifies invariants: tools_offered_hash matches the registered MCP servers; memory_read_keys are within the agent's declared capability; parent_step_id forms a valid DAG. Anything that fails attestation is killed *before* execution.
**Detects:** MCP rug-pull at runtime (server changes tool schema mid-session → `tools_offered_hash` changes → kill), capability escalation, prompt-template tampering.
**Attack model:** Supply-chain attacks against MCP servers.
**FP risk:** Near zero — these are structural checks, not statistical.

### F. Cytokine layer / graded response (NEW)
**Component:** `aigis/immune/cytokines.py`. Replace boolean `block_or_allow` with a continuous `inflammation_score ∈ [0, 1]` per session that:
- Increments on any layer firing (weighted by danger class).
- Decays exponentially with time and successful clean steps.
- Above threshold T1: require user confirmation on next tool call.
- Above T2: switch the agent's model to a stricter system prompt ("immune-activated mode").
- Above T3: terminate session, emit audit event.

### G. Peripheral tolerance / per-customer whitelist (NEW)
**Component:** A first-class `tolerance_profile.yaml` loaded per deployment. Negative selection (layer B) trains against it; danger thresholds (layer C) read it. Without this, B will produce unacceptable FP rates on diverse customer workloads — the same reason the thymus alone is insufficient and you need Tregs.

## 4. Honest critique — where the metaphor breaks

1. **Biology has co-evolution over 500M years; AIS designers don't.**
2. **"Self" is well-defined in a body, undefined in software.** A cell's "self" is its MHC-presented peptides — physically grounded. An LLM agent's "self" is whatever you decide normal looks like.
3. **AIS overfit on toy benchmarks.** When evaluated on modern data, AIS rarely beats a tuned isolation forest. Don't assume immune framing gives you accuracy gains; it gives you *architecture* gains.
4. **Autoimmunity is a real, expensive failure mode.** FPs in immunology look like lupus or T1D. Negative selection without strong tolerance training is *guaranteed* to produce this.
5. **Inflammation has off-switches that we have to design.** Biology has IL-10, Tregs, glucocorticoids. The "cytokine score" idea above needs explicit dampeners.
6. **The danger model is not actually a clean theory in immunology either.** Matzinger's danger model is still debated.
7. **You cannot ship sterile.** Aigis is open-source; attackers will read the immune layers too. Pattern + negative-selection + danger + memory raises *cost* of bypass, it doesn't eliminate it.

## 5. Recommended reading (3–5, highest signal first)

1. **Forrest, S. & Beauchemin, C. (2007). *Computer Immunology*.** Immunological Reviews 216:176–197. ([PDF](https://www.cs.unm.edu/~forrest/publications/computer-immunology))
2. **Hofmeyr, S., Forrest, S., & Somayaji, A. (1998). *Intrusion detection using sequences of system calls*.** J. Computer Security 6(3). ([SAGE](https://journals.sagepub.com/doi/10.3233/JCS-980109))
3. **Aickelin, U. & Cayzer, S. (2002). *The Danger Theory and Its Application to Artificial Immune Systems*.** ICARIS.
4. **Liu, J. et al. (2025). *TraceAegis*.** [arXiv:2510.11203](https://arxiv.org/abs/2510.11203)
5. **Greensmith, J., Aickelin, U., & Cayzer, S. (2010). *Detecting Danger: The Dendritic Cell Algorithm*.** [arXiv:1006.5008](https://arxiv.org/pdf/1006.5008)

Optional 6th: **Stibor, T., Timmis, J., & Eckert, C. (2005).** Strongest critique of NSA.

## Top 3 to prototype (ranked effort/impact)

| Rank | Prototype | Effort | Impact |
|---|---|---|---|
| 1 | **MHC-style trace attestation (layer E)** in `aigis/immune/attestation.py`. Pure structural checks, near-zero FP. | ~1 week | High |
| 2 | **Cytokine / graded response (layer F)** in `aigis/immune/cytokines.py`. Refactor binary block path into a score with decay and three thresholds. | ~1 week | High |
| 3 | **Negative-selection trace detector (layer B) + B-cell memory pool (layer D)** — ship together. Train tolerance per customer; require a danger signal to *block* (otherwise log-only). | 3–4 weeks | Highest ceiling |
