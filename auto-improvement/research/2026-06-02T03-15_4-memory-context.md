# Research: Memory Context Attacks — Cycle 4, Fourth Pass (2026-06-02T03-15)

Domain: `memory-context` — Memory poisoning, context manipulation, long-context attacks, RAG poisoning

**Cycle index:** 4  
**Cycle timestamp:** 2026-06-02T03-15

## Background

Prior passes for this domain covered:
- Pass 1 (2026-05-08T08-00): MCFA tool-steering, objective hijacking, summarization persistence, agent trust laundering
- Pass 2 (2026-05-10T18-15): MemoryGraft experience hijacking, ZombieAgent conditional triggers, false user preference injection
- Pass 3 (2026-05-14T03-07): Plan injection / context-chained injection (arxiv:2506.17318), Sleeper/dormant injection (arxiv:2503.16248)

This pass focuses on **memory lifecycle attacks** — specifically the understudied "Forget/Rollback" and "Write-path" phases documented in the 2026 survey, and sleeper memory poisoning with retrieval-aware rewriting (arxiv:2605.15338).

## Findings

- **Survey: "A Survey on the Security of Long-Term Memory in LLM Agents: Toward Mnemonic Sovereignty" (arxiv:2604.16548, April 2026)**  
  Comprehensive survey covering six memory lifecycle phases: Write, Store, Retrieve, Execute, Share, and Forget/Rollback. The Write and Retrieve phases dominate the literature (~55% of works). A key observation: **governance-related attacks at the Store and Forget phases are explicitly understudied**. The Forget/Rollback phase includes "memory rollback attacks" where adversaries instruct the agent to delete or override existing safety constraints, then replace them with attacker-controlled rules. The survey identifies this as distinct from generic jailbreaks because the effect persists across session resets.  
  Source: https://arxiv.org/html/2604.16548v1  
  **aigis takeaway**: Add `mem_forget_replace` — a pattern targeting the explicit "erase safety constraints + replace with new rules" two-phase structure of memory rollback attacks.

- **"Hidden in Memory: Sleeper Memory Poisoning in LLM Agents" (arxiv:2605.15338v2, May 2026)**  
  Documents a three-stage attack (Injection → Retrieval-aware rewriting → Activation) with measured injection rates of 91.5–99.8% on vulnerable models (GPT-5.4/5.5, Claude Sonnet, Gemini, Kimi-K2.6), retrieval rates of 90–95% for semantically-aligned queries, and end-to-end adversarial usage rates of 42–89%. The "retrieval-aware goal rewriting" technique rewrites malicious memory entries to be semantically close to future user queries without changing their malicious intent. Attack goals include commercial manipulation ("user prefers Brand X"), operational sabotage (exfiltration endpoints), and workflow hijacking. Mechanistic analysis shows adversarial entries create "highly separable activation patterns" with 0.93–0.99 AUROC in hidden states.  
  Source: https://arxiv.org/html/2605.15338v2  
  **aigis takeaway**: Injection rates near 100% confirm urgency of memory-write scanning. The `mem_false_preference` and `mem_sleeper_dormant` patterns already cover some variants; the new `mem_forget_replace` closes the rollback angle not yet covered.

- **"Memory Poisoning Attack and Defense on Memory Based LLM-Agents" (arxiv:2601.05504, January 2026)**  
  Studies memory poisoning in a realistic Electronic Health Record (EHR) agent setting across GPT-4o-mini, Gemini-2.0-Flash, and Llama-3.1-8B-Instruct. References MINJA (Memory Injection Attack), which achieves >95% injection success under ideal conditions but drops significantly in realistic deployments with pre-existing legitimate memories. Defense strategies proposed: (1) composite trust scoring across multiple signals, (2) trust-aware retrieval with temporal decay and pattern-based filtering. The paper validates that pattern-based filtering is a practical first-line defense.  
  Source: https://arxiv.org/abs/2601.05504  
  **aigis takeaway**: Validates the rule-based approach. The >95% injection rate under ideal conditions underscores how dangerous unscanned memory writes are.

- **RAG Corpus Poisoning Taxonomy (arxiv:2604.08304, April 2026)**  
  Comprehensive taxonomy of RAG poisoning including: corpus poisoning (PoisonedRAG, BadRAG), structured/graph poisoning (GRAGPoison), and code poisoning (RACG, ImportSnare). Key insight: modern attacks emphasize *coherence* — poisoned documents are written to blend seamlessly with legitimate context. "A single text optimized for retrievability and coherence is enough to successfully compromise the system" (CorruptRAG, AuthChain). This means text-pattern detection must look beyond obvious malicious phrases and target structural markers (authority claims, replacement directives) rather than keyword-only matching.  
  Source: https://arxiv.org/html/2604.08304v1  
  **aigis takeaway**: Confirms that sophisticated RAG poisoning avoids obvious malicious keywords. Detection must target structural patterns (erase + replace) that are semantically distinct from benign document content.

- **CtrlRAG: Black-box Document Poisoning (arxiv:2503.06950, March 2026)**  
  Black-box RAG poisoning using MLM-guided optimization. Two attack categories: (1) Emotion Manipulation — injecting emotionally charged content, (2) Hallucination Amplification — injecting false facts. Achieves up to 90% success on GPT-4o with only 5 malicious documents in a million-document dataset. Attack signatures are high-level semantic rather than lexical, limiting direct regex applicability.  
  Source: https://arxiv.org/pdf/2503.06950  
  **aigis takeaway**: CtrlRAG attacks don't have distinct lexical signatures detectable by simple regex; out of scope for pattern-based rules this cycle.

- **OWASP Agentic Security Initiative — ASI06: Memory and Context Poisoning (2026)**  
  OWASP created a dedicated entry in the Agentic AI Top 10 for memory and context poisoning, signaling industry-wide recognition that memory attacks are a first-class security concern distinct from prompt injection. The ASI06 classification covers: false memory injection, memory rollback, cross-session persistence, and context manipulation.  
  Source: https://reddogsecurity.substack.com/p/llm-security-in-2026-a-complete-attack  
  **aigis takeaway**: Adds compliance backing for memory-specific detection rules; OWASP LLM01 (Prompt Injection) and ASI06 (Memory Poisoning) are both valid OWASP references for new patterns.

- **Positional Bias Attacks: Context Window Manipulation (arxiv:2508.07479)**  
  LLMs show "lost in the middle" primacy/recency bias: safety instructions placed in the middle of a long context are attended to less than instructions at the beginning or end. Attackers can exploit this by flooding the context window with benign content that pushes safety instructions into the middle of the attention range. As of 2026, no production model has fully eliminated position bias.  
  Source: https://arxiv.org/pdf/2508.07479  
  **aigis takeaway**: Context-flooding detection is pending (see `auto-improvement/pending/2026-06-01_context-flooding-detection.md`) — requires heuristic approach beyond simple regex. Not addressed this cycle.

## Candidate Hardenings

1. **`mem_forget_replace`** (score 55, input/memory filter) — Detects memory rollback-and-replacement attacks: instructions that explicitly erase existing safety constraints from memory and direct the agent to store attacker-controlled replacement rules. Two-phase regex: (a) erasure verb targeting constraint-adjacent content + (b) store/remember command with a replacement marker. Targets arxiv:2604.16548 "Forget/Rollback phase" attacks and OWASP ASI06. Distinct from existing `mem_experience_hijack` (which targets success-framing without the explicit erasure step) and `pl_forget_and_ask` (which targets forget + prompt-reveal, not forget + replace).

2. *(Deferred)* Context flooding / InfoFlood detection — already in `pending/2026-06-01_context-flooding-detection.md`. Requires character/token length heuristic, not pure regex; still blocked by false-positive calibration concerns.

3. *(Deferred)* Retrieval-aware semantic similarity detection — arxiv:2605.15338 "retrieval-aware goal rewriting" makes poisoned memories semantically similar to legitimate queries. Detection requires embedding-level analysis (cosine similarity against known malicious templates), which is outside aigis's zero-runtime-dependency constraint.

4. *(Deferred)* OWASP ASI06 compliance template field — adding ASI06 as a recognized OWASP reference field in compliance templates. Small change but deferred to a compliance-focused cycle (index 8).
