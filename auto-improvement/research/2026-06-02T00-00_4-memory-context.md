# Research: Memory Context Attacks — Cycle 4, Fourth Pass (2026-06-02T00-00)

**Domain:** `memory-context` — Memory poisoning, context manipulation, long-context attacks, RAG poisoning  
**Cycle index:** 4  
**Cycle timestamp:** 2026-06-02T00-00

## Background

Prior passes for this domain covered:
- Pass 1 (2026-05-08T08-00): MCFA tool-steering, objective hijacking, summarization persistence, agent trust laundering
- Pass 2 (2026-05-10T18-15): MemoryGraft experience hijacking, ZombieAgent conditional triggers, false user preference injection
- Pass 3 (2026-05-14T03-07): Context-chained plan injection, sleeper/dormant memory injection

This pass targets RAG corpus poisoning via chain-of-thought tag spoofing and memory consolidation hijacking via future-session directives — two attack classes not covered by any existing pattern.

## Findings

- **Chain-of-Thought Poisoning Against R1-Based RAG (arxiv:2505.16367, May 2025)**
  Adversarial documents in a RAG corpus are wrapped in the same XML thinking-delimiter tags (`<think>…</think>`, `<reasoning>…</reasoning>`) used by DeepSeek-R1, Qwen3, and derivative reasoning models for internal chain-of-thought. When the poisoned document is retrieved, the target model treats the enclosed text as its own prior computation rather than external input, substantially increasing its acceptance of fabricated conclusions. Validated on MS MARCO; a single poisoned document raised a false answer's rank over legitimate retrieved passages.
  **Source:** https://arxiv.org/abs/2505.16367
  **aigis takeaway:** Add `ii_reasoning_tag_spoof` to INDIRECT_INJECTION_PATTERNS — these XML tags (`<think>`, `<thinking>`, `<reasoning>`, `<reflection>`, `<internal_thought>`) have no legitimate place in external documents or RAG content; their presence is a high-confidence injection indicator.

- **AdversarialCoT: Single-Document Retrieval Poisoning (arxiv:2604.12201, Apr 2026, SIGIR 2026)**
  A query-specific attack: the attacker extracts the target model's reasoning framework, constructs a fake chain-of-thought document mimicking the model's own reasoning style with embedded false conclusions, and iteratively refines it via LLM interaction to maximize retrieval rank. Only one poisoned document is needed — improving attack success by up to +23% over multi-document poisoning baselines. Accepted at SIGIR 2026.
  **Source:** https://arxiv.org/abs/2604.12201
  **aigis takeaway:** The CoT tag spoofing pattern (`ii_reasoning_tag_spoof`) provides coverage for the lexical variant of this attack where the adversarial document explicitly uses reasoning delimiter tags. Structural fake-CoT (without special tags) is harder to detect with regex and is deferred to pending.

- **eTAMP — Environment-Injected Memory Consolidation Hijack (arxiv:2604.02623, Apr 2026)**
  An agent browses a malicious web page (product listing, document, email) containing hidden future-session directives. During memory consolidation (where the agent compresses observations into persistent memory), the directive is encoded alongside legitimate observations. In a later, unrelated session the poisoned entry activates, steering behavior without any active injection in the current context. GPT-5-mini: 32.5% ASR, GPT-5.2: 23.4%, GPT-OSS-120B: 19.5%; ASR rises up to 8× under "frustration exploitation" conditions (deliberately inducing agent stress via garbled text/failed interactions).
  **Source:** https://arxiv.org/abs/2604.02623
  **aigis takeaway:** Add `mem_consolidation_hijack` targeting the combination of future-session-targeting phrases ("in the next session", "carry this instruction into future sessions") with exfiltration verbs and external destinations.

- **Omission Constraint Decay (arxiv:2604.20911, Apr 2026)**
  Prohibition-type constraints ("do not reveal X", "never do Y") decay with conversation depth while requirement-type constraints ("always format as JSON") remain stable. At turn 5 omission compliance is 73%; by turn 16 it drops to 33%. Commission constraints hold ~100% throughout. The decay is driven by constraint text being diluted by surrounding context, accounting for 62–100% of the effect. Tested across 4,416 trials, 12 models, 8 providers.
  **Source:** https://arxiv.org/abs/2604.20911
  **aigis takeaway:** This requires stateful session tracking (distance from last prohibition to current turn), which goes beyond aigis's single-input scan model. Deferred to pending for a stateful constraint-monitor extension.

- **Black-Hole Attack on Vector Databases (arxiv:2604.05480, Apr 2026)**
  Exploits "centrality-driven hubness" in high-dimensional embedding spaces: vectors near the geometric centroid of the embedding space become nearest neighbors to a disproportionately large fraction of all other vectors. Injecting a small number of centroid-positioned vectors causes them to appear in top-k retrieval for almost every query (up to 99.85% co-retrieval rate). Only a small number of injected vectors required.
  **Source:** https://arxiv.org/abs/2604.05480
  **aigis takeaway:** Detecting hubness exploitation requires computing retrieval metadata (repeated chunks across queries) — not feasible in a single-scan model. The lexical injection content itself (the actual attack payload in the hub vector) is detectable via existing patterns once aigis receives it.

- **Semantic Chameleon: Corpus-Dependent GCG Poisoning (arxiv:2603.18034, Mar 2026)**
  Uses Greedy Coordinate Gradient (GCG) optimization to create "sleeper + trigger" document pairs that achieve 46.7–93.3% ASR against various LLM families on Security Stack Exchange corpus. Attack is corpus-dependent: success drops to 0% on a different corpus (Wikipedia FEVER). GCG-optimized text typically contains syntactically anomalous token sequences (non-word character runs, high-entropy adversarial suffixes) that could in principle be detected as entropy anomalies — but are too varied for a fixed regex.
  **Source:** https://arxiv.org/abs/2603.18034
  **aigis takeaway:** GCG adversarial suffixes are too variable for rule-based regex detection. Deferred to pending for a future entropy-heuristic scanner extension.

- **ADMIT: Few-Shot Knowledge Poisoning in RAG (arxiv:2510.13842, Oct 2025)**
  Semantically aligned poisoning attack that flips fact-checking decisions and induces deceptive justifications by injecting few-shot examples that normalize the false answer. Does not require access to the target LLM, retriever, or token-level control. The injected examples look identical in structure to legitimate few-shot demonstrations; distinguishing feature is the semantic falseness of the stated fact, not the format.
  **Source:** https://arxiv.org/abs/2510.13842
  **aigis takeaway:** The format is indistinguishable from legitimate few-shot examples at the lexical level; content-level falseness detection requires semantic analysis. Out of scope for regex-based detection.

- **Unstable Safety Under Long Context (arxiv:2512.02445, Dec 2025)**
  Models with 1M–2M token context windows show severe safety degradation well before their stated limits, already at 100K tokens. Refusal rate shifts up to 70 percentage points. No crafted adversarial content required — length alone suffices. The active exploitation form is "context padding": inserting large blocks of semantically incoherent or repetitive text before a harmful request to shift into the unsafe context-depth regime.
  **Source:** https://arxiv.org/abs/2512.02445
  **aigis takeaway:** A context-length pressure heuristic was previously deferred (`2026-06-01_context-flooding-detection.md`). This paper strengthens the research basis. Still deferred due to false-positive risk on legitimate long-document tasks.

## Candidate Hardenings

1. **`ii_reasoning_tag_spoof`** ✅ (implemented this cycle) — Detects model-internal reasoning XML delimiter tags in externally retrieved content: `<think>`, `<thinking>`, `<reasoning>`, `<reflection>`, `<internal_thought>`. Source: arxiv:2505.16367 (May 2025).

2. **`mem_consolidation_hijack`** ✅ (implemented this cycle) — Detects memory consolidation hijack via future-session directives in observation content: "in the next session", "the next time you start", "carry this instruction into future sessions", "remember this for all future conversations" — combined with exfiltration verb and external destination. Source: arxiv:2604.02623 (Apr 2026), 19.5–32.5% base ASR.

3. *(Deferred)* Omission constraint decay tracker — requires stateful session context; proposed as a constraint-monitor extension. Source: arxiv:2604.20911.

4. *(Deferred)* GCG adversarial suffix entropy heuristic — requires entropy-scoring; not feasible as fixed regex. Source: arxiv:2603.18034.

5. *(Deferred)* Context-length pressure heuristic — strengthened research basis from arxiv:2512.02445 but false-positive risk on legitimate long-document tasks remains. Previous deferred entry: `2026-06-01_context-flooding-detection.md`.
