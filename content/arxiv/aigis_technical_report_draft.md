# Aigis: A Zero-Dependency Reference Implementation of Seven Recent LLM-Security Defenses

**Authors:** {{ Name }}{{ ¹}}, {{ optional co-authors }}
{{¹}}: independent researcher, killertcell428@gmail.com

**Status:** v0.1 working draft — sections marked [DRAFT] need writing; sections marked [TODO] need benchmark data; sections marked [DONE] are ready for review.

**Target:** arXiv cs.CR (Cryptography and Security) → cross-list cs.AI / cs.CL. Aim: 8–12 pages in single-column format.

---

## Abstract — [DONE]

Defensive research for large language model (LLM) applications has accelerated through 2025–2026, with multiple papers proposing prompt-injection mitigations, tool-poisoning detectors, memory-graft defenses, and goal-conditioned monitoring. However, defenders integrating these proposals into production face two systemic gaps: (i) most papers ship neither code nor reproducible artifacts; (ii) the few that do depend on specific LLM APIs, large machine-learning toolchains, or framework-specific scaffolding, none of which compose cleanly when a single application needs more than one mitigation.

We present **Aigis**, an open-source (Apache-2.0) zero-dependency Python library implementing seven recent LLM-security defenses as separately-usable modules sharing a single CheckResult schema: Mirror Design Pattern (arxiv:2603.11875), StruQ + LLMail-Inject input separation, MI9 goal-conditioned finite-state monitoring (arxiv:2508.03858), MemoryGraft long-term memory poisoning defense (arxiv:2512.16962), MSB 3-stage MCP tool-poisoning scanner (arxiv:2510.15994), DataFilter + RAGDefender retrieval-context filtering, and AdvJudge-Zero judge-manipulation detection. Aigis composes these into a four-wall + L4–L7 architecture covering ingress, agent capability boundaries, atomic execution, safety verification, and runtime goal divergence. The core engine has zero non-stdlib dependencies and runs as a Python library, an HTTP sidecar, or a CLI. We report 940+ passing unit tests across the seven modules and discuss what reference implementation choices reveal about the original papers — in particular, where paper-defined invariants under-specify the behavior needed for production deployment.

**Keywords:** LLM security, prompt injection, agent security, MCP, tool poisoning, memory poisoning, goal divergence, defense in depth, reference implementation.

---

## 1. Introduction — [DONE]

### 1.1 Motivation

Between Q3 2025 and Q1 2026, at least seven peer-reviewed or arXiv-published papers proposed concrete defensive mechanisms against attacks on LLM applications and AI agents. These include: input-space attacks (StruQ, LLMail-Inject), tool-space attacks (MSB on MCP servers), memory-space attacks (MemoryGraft against long-term memory stores), goal-space attacks (MI9 against agent finite-state goals), reflection-asymmetry attacks (Mirror), retrieval-poisoning attacks (DataFilter, RAGDefender), and judge-evaluation attacks (AdvJudge-Zero).

Each paper independently delivers a strong defensive contribution. However, when a security-conscious team attempts to ship a real LLM application — say, a Claude Code or Cursor integration that calls into MCP tools and keeps long-term memory — the team rapidly discovers four practical gaps:

1. **Code availability**: most papers cite "code released upon publication" but link to private repositories, partial implementations, or framework-specific demos.
2. **Toolchain weight**: published implementations frequently depend on `transformers`, `spaCy`, `langchain`, or vendor-specific SDKs. Defenders running on memory-constrained hosts (e.g., 512 MB sidecar containers) cannot deploy these in front of an existing service.
3. **Schema fragmentation**: each paper invents its own result type, severity scale, and trigger semantics. Composing two defenses (e.g., StruQ at ingress + MI9 at planning) requires custom adapter code per pair.
4. **Coverage holes between papers**: any single defense addresses one attack family. Real deployments need all of them simultaneously, plus a hardening layer (capability access control, atomic execution boundaries) that no single paper alone provides.

This work does not propose a new attack or a new defense. We present an engineering contribution: a single library that ports the seven defenses above into a unified, production-deployable form, and we report what reference-implementing each paper revealed about specifications that worked in evaluation but were ambiguous when deployed.

### 1.2 Contributions

We make the following contributions:

1. **Reference implementation** of seven recent LLM-security papers, each independently usable behind a unified `CheckResult` schema. All code is Apache-2.0 and Python-stdlib-only at the core.
2. **Four-wall + L4–L7 composition architecture** that allows the seven mechanisms to operate concurrently on the same request without per-pair adapter code (Section 3).
3. **Spec-vs-implementation gap analysis**: for each ported paper, we document where the paper specification under-determined the implementation, and which choices we made (Section 5).
4. **Operational artifacts**: 940+ unit tests, 44 compliance template mappings (US/CN/JP/EU regulatory frameworks), three deployment modes (library / HTTP sidecar / CLI), and a published Docker image, demonstrating that paper-grounded defenses can be made deployable without engineering effort that obscures the underlying research.

### 1.3 Scope

We explicitly do **not** claim:

- That Aigis is a complete LLM security solution. It is one layer of defense in depth.
- That our reference implementations match the original papers' evaluation numbers exactly. We re-implemented from spec, not from authors' artifacts.
- That the defenses we ported are the optimal seven. We selected papers with (a) clear practical defense semantics, (b) spec-level descriptions adequate for reference implementation, and (c) evaluation that was reproducible at least in qualitative terms.

---

## 2. Related Work — [DRAFT]

### 2.1 Existing OSS LLM-security tools

We compare Aigis against four canonical open-source projects:

- **LLM Guard** (Protect AI / Laiyer): Python toolkit, runtime input/output filtering. Coverage: prompt injection, PII, banned topics. Dependencies: `transformers`, `spacy`. Architecture: function-style guards, no agent-aware composition.
- **Guardrails AI**: validator framework with rich validator catalog (PII, toxicity, regex, structured output). Composition story but focused on input/output, not agent-state or tool-space attacks.
- **NeMo Guardrails** (NVIDIA): Colang-based dialog policy engine. Strong on conversational flow, weaker on tool-calling agents and memory poisoning.
- **Rebuff** (Protect AI): single-purpose self-hardening prompt-injection detector. Useful but narrow.

A comparison table appears in Section 6 covering paper-coverage, dependencies, agent-tool-space coverage, MCP support, and self-improving capability.

### 2.2 Defense families and the papers we ported

We ported defenses spanning seven of the major attack surfaces in the LLM-application threat model:

1. **Reflection-asymmetry attacks** → Mirror Design Pattern (Liu et al., 2026) [arxiv:2603.11875]
2. **Direct prompt injection at ingress** → StruQ (Chen et al., 2024) and LLMail-Inject (Microsoft Research, 2025)
3. **Goal divergence at runtime** → MI9 (Anonymous, 2025) [arxiv:2508.03858]
4. **Long-term memory poisoning** → MemoryGraft (Liu et al., 2026) [arxiv:2512.16962]
5. **MCP tool-space attacks** → MSB (Anonymous, 2025) [arxiv:2510.15994]
6. **Retrieval-context poisoning** → DataFilter and RAGDefender
7. **Judge-evaluation manipulation** → AdvJudge-Zero

For each, Section 4 details the paper's mechanism, our implementation choices, and where the paper under-specifies behavior.

### 2.3 What Aigis is not

Aigis is not a model-side defense (no fine-tuning, no RLHF). It does not claim formal-verification guarantees. It is a runtime-enforcement layer — comparable to a network firewall, not a microkernel.

---

## 3. Architecture — [DRAFT]

### 3.1 Four walls + L4–L7

Aigis composes the seven defenses into a layered architecture inspired by network defense in depth, adapted for LLM applications:

```
                     ┌─────────────────────────────────────────┐
   User Input ─────▶ │ Wall 1: Ingress (StruQ, Mirror)         │
                     ├─────────────────────────────────────────┤
   RAG Context ────▶ │ Wall 2: Context Filter (DataFilter,     │
                     │         RAGDefender)                    │
                     ├─────────────────────────────────────────┤
   Memory Read ───▶  │ Wall 3: Memory Verifier (MemoryGraft)   │
                     ├─────────────────────────────────────────┤
   Tool Catalog ──▶  │ Wall 4: Tool Scanner (MSB)              │
                     ├─────────────────────────────────────────┤
   Agent Runtime ─▶  │ L4: Capability ACC (deny-by-default)    │
                     │ L5: Atomic Execution (per-call boundary)│
                     │ L6: Safety Verifier (AdvJudge-Zero)     │
                     │ L7: Goal FSM (MI9)                      │
                     └─────────────────────────────────────────┘
```

Walls are stateless filters at the boundary between trusted and untrusted data. Levels 4–7 are stateful monitors operating during agent execution. The split is load-bearing: walls can be deployed independently in front of any LLM service; L4–L7 require integration with the agent runtime.

### 3.2 The unified CheckResult schema

All seven modules return a `CheckResult` with the following fields:

```python
@dataclass
class CheckResult:
    blocked: bool                       # whether the request should be denied
    risk_score: int                     # 0-100
    risk_level: RiskLevel               # LOW, MEDIUM, HIGH, CRITICAL
    reasons: list[str]                  # human-readable trigger names
    details: list[DetectionDetail]      # per-trigger context (pattern, span, owasp_ref, remediation_hint)
```

This shared schema is the key composition primitive: a deployer can OR or AND results from any subset of the seven modules without per-pair adapter code.

### 3.3 Three deployment modes — [DONE]

Same engine, three packaging targets:

1. **Python library**: `from aigis import Guard; Guard().check_input(text)` — three lines of integration code.
2. **HTTP sidecar**: `aigis serve` (Python stdlib HTTP server, no Flask/FastAPI dependency). `POST /v1/check/input`. Useful for non-Python stacks.
3. **CLI**: `aigis scan "<text>"` — one-shot evaluation, useful for CI pipelines and quick triage.

All three modes share the same engine and the same CheckResult schema.

---

## 4. Implementation of Seven Defenses — [DRAFT]

For each ported paper, we describe (a) what the paper specifies, (b) our implementation, and (c) ambiguity gaps we encountered.

### 4.1 Mirror Design Pattern — [DRAFT]

[**Paper specification.**] [TODO summary]

[**Our implementation.**] [TODO]

[**Ambiguity notes.**] [TODO]

### 4.2 StruQ + LLMail-Inject — [DRAFT]
[similar structure]

### 4.3 MI9 goal-conditioned FSM — [DRAFT]
[similar structure — note that we implement 7 of 9 divergence states; explain why two are deferred]

### 4.4 MemoryGraft — [DRAFT]
[note: we do retrieval-time check in addition to write-time check; discuss whether this is justified]

### 4.5 MSB 3-stage MCP scanner — [DRAFT]
[note: we found stage-2 description-vs-effect divergence detection requires choices not specified in paper]

### 4.6 DataFilter + RAGDefender — [DRAFT]

### 4.7 AdvJudge-Zero — [DRAFT]

---

## 5. Spec-vs-Implementation Gaps — [DRAFT]

This section is the single largest engineering contribution beyond "we ported these papers." For each defense, we document:

- Paper invariants that worked in evaluation but were under-specified for deployment
- Implementation choices we made
- Tests that demonstrate the choice's effect

[~3-4 pages, one subsection per paper]

---

## 6. Comparison and Coverage Analysis — [TODO]

Table: Aigis vs LLM Guard, Guardrails AI, NeMo Guardrails, Rebuff across:

- Number of papers implemented
- Paper-grounding (with citations)
- Agent-tool-space coverage (MCP, capability ACC)
- Memory-space coverage (graft detection)
- Goal-space coverage (FSM)
- External dependencies (lower is better for deployment)
- Self-improving feedback loop

---

## 7. Evaluation — [TODO — needs benchmark runs]

### 7.1 Datasets

[TODO: list benchmark corpora]

- AdvBench (Zou et al., 2023): 520 harmful prompts
- HarmBench (Mazeika et al., 2024): broader red-team prompts
- StruQ-style corpora: structured-prompt attacks
- MSB tool-poisoning corpus: from MSB paper supplemental
- Custom 940-test internal suite

### 7.2 Metrics

- True-positive rate per defense module
- False-positive rate on benign corpora (UltraChat, ShareGPT subset)
- End-to-end latency (P50, P95, P99) in library mode
- Sidecar HTTP latency overhead

### 7.3 Results

[TODO: table with numbers from actual benchmark runs]

### 7.4 Ablation

[TODO: each module on/off, cumulative coverage]

---

## 8. Limitations — [DRAFT]

- **Reference implementation, not the original.** Numbers may differ from each paper's reported numbers due to spec ambiguity (Section 5).
- **Pattern-matching base.** Walls 1–4 use regex + heuristics. Adversaries with sufficient generation budget can evade specific patterns.
- **L7 FSM coverage gap.** MI9 specifies 9 divergence states; we implement 7. The remaining two require per-application instrumentation we judged out of scope for a generic library.
- **No model-side hardening.** Aigis is purely runtime; we do not retrain models, fine-tune, or use RLHF.
- **Single-author audit.** Reference implementations are unaudited beyond the unit test suite. Independent security review welcomed.

---

## 9. Conclusion — [DRAFT]

[~ half a page summarizing the engineering contribution and what we believe the bottleneck for deploying paper-grounded LLM defenses currently is]

---

## References — [TODO]

[Generate from a BibTeX file once paper sections finalize. Will include the seven implemented papers, the four OSS comparison projects, OWASP LLM Top 10, NIST AI RMF, EU AI Act, and the broader LLM-attack literature for context (Greshake et al., Liu et al., Zou et al.).]

---

## Appendices — [TODO]

- **A: Full CheckResult JSON schema**
- **B: Sidecar HTTP API specification (OpenAPI 3.0)**
- **C: Compliance-template-to-OWASP mapping table** (44 entries)
- **D: How to add a new defense module** (replication instructions)

---

# Writing plan

## Total target: 8–12 pages single-column

| Section | Status | Estimated effort |
|---|---|---|
| 1. Introduction | DONE | — |
| 2. Related Work | needs 2.1–2.2 expansion | 2 hours |
| 3. Architecture | needs prose around the diagrams | 2 hours |
| 4. Seven Defenses | needs 7×3-paragraph subsection | 6 hours |
| 5. Spec-vs-Implementation | the contribution-heavy section | 4 hours |
| 6. Comparison Table | data already in README | 1 hour |
| 7. Evaluation | **needs actual benchmark runs** | 8 hours runtime + 2 hours writeup |
| 8. Limitations | DONE | — |
| 9. Conclusion | half a page | 30 min |
| References | from existing citation list in code | 1 hour |
| Appendices | from existing repo content | 2 hours |

**Critical path:** Section 7 (evaluation) requires running each module against published benchmark corpora and recording numbers. This is the gating item before submission.

**Submission target:** arXiv cs.CR by 2026-06-15, 6 weeks after v1.0.0.
