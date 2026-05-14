# Research: Memory Context Attacks — Cycle 4, Third Pass (2026-05-14T03-07)

Domain: `memory-context` — Memory poisoning, context manipulation, long-context attacks, RAG poisoning

**Cycle index:** 4  
**Cycle timestamp:** 2026-05-14T03-07

## Background

Prior passes for this domain covered:
- Pass 1 (2026-05-08T08-00): MCFA tool-steering, objective hijacking, summarization persistence, agent trust laundering
- Pass 2 (2026-05-10T18-15): MemoryGraft experience hijacking, ZombieAgent conditional triggers, false user preference injection

This pass targets two new attack classes not yet in aigis's pattern set: **context-chained plan injection** (plan corruption via task-continuation framing) and **sleeper/dormant memory injection** (explicit dormancy + deferred exfiltration designed to bypass initial scans).

## Findings

- **Plan Injection / Context-Chained Injection (arxiv:2506.17318, ICML 2025)**
  Patlan, Hebbar, Viswanath & Mittal introduce "plan injection" — attacks that corrupt an agent's stored task plan rather than its input prompt. Unlike prompt injection (which targets the current context window), plan injection writes malicious content to the agent's external memory/plan store. "Context-chained injections" disguise the payload as a logical task continuation ("as a next step…", "to complete this task also…"), making them appear to be reasonable follow-ups rather than injected instructions. Evaluated on Browser-use and Agent-E: standard prompt injection defenses reduced prompt injection from >80% to <20% ASR, but a single plan injection still achieved 46% on Agent-E and 63% on Browser-use. Context-chained variants achieved 3× higher success than non-contextual injections.
  **Source**: https://arxiv.org/abs/2506.17318
  **aigis takeaway**: Add `mem_plan_injection` pattern targeting task-continuation framing combined with an exfiltration directive and external address indicator.

- **Sleeper / Dormant Memory Injection (arxiv:2503.16248, March 2026)**
  "Real AI Agents with Fake Memories: Fatal Context Manipulation Attacks on Web3 Agents" demonstrates dormant/sleeper injections stored in long-term memory that look inert at injection time. The entry explicitly instructs the agent not to act immediately ("do not act now", "stay dormant", "wait until triggered"), only activating when a future benign user query matches the trigger condition. The dormancy instruction is the key design choice: it causes initial moderation scans (which check for immediate-action payloads) to pass the entry as harmless. Demonstrated on ElizaOS across 150+ blockchain tasks and 500+ attack cases (CrAIBench); memory injection outperformed prompt injection by a significant margin.
  **Source**: https://arxiv.org/abs/2503.16248
  **aigis takeaway**: Add `mem_sleeper_dormant` pattern detecting the dormancy instruction + deferred exfiltration combination.

- **Context-Chained vs. Direct Injection (arxiv:2506.17318 detail)**
  The paper formalizes three injection types: (a) non-contextual (directly malicious, easy to detect), (b) task-aligned (matches the user's domain but adds extra actions), (c) context-chained (builds a logical bridge between the user's goal and the attacker's objective). Type (c) is hardest to detect because the injected text looks like a plausible next step in the user's task. The new `mem_plan_injection` pattern specifically targets this framing by requiring both a task-continuation phrase and an exfiltration/redirect verb with an external destination.
  **aigis takeaway**: Confirms the importance of pairing both signals (framing + external action) to minimize false positives.

- **Cross-Session Backdoors (arxiv:2503.16248 detail)**
  The paper also documents "cross-session backdoors": a fake memory entry injected by one user persists in a shared memory store and influences sessions belonging to other users. In multi-tenant agent deployments, this represents a user-to-user attack path. The dormancy instruction helps the attacker ensure the backdoor does not fire in the injector's session (where it might be noticed) but instead activates in a later victim session.
  **aigis takeaway**: Confirms urgency of scanning memory on both write and read, not just at ingestion. Covered by `mem_sleeper_dormant` dormancy signal.

- **Sleeper Cell Temporal Backdoor (arxiv:2603.03371, March 2026)**
  Pallakonda et al. demonstrate implanting latent malicious behavior into tool-using agents via fine-tuning (SFT-then-GRPO). The "sleeper cell" is a model weight backdoor — inactive until a trigger phrase in input activates it. This is a model poisoning attack (not a runtime memory injection) and is out of scope for pattern-based detection at inference time. Noted for completeness; no aigis pattern can detect weight-level backdoors.
  **Source**: https://arxiv.org/abs/2603.03371
  **aigis takeaway**: Out of scope for runtime patterns. Appropriate mitigation is supply-chain validation (model provenance checks), which is a separate concern from memory scanning.

- **ARGUS Defense Framework (arxiv:2605.03378, May 2026)**
  ARGUS defends against context-aware prompt injection by maintaining a separate context-integrity monitor. Its threat model explicitly includes memory-based attacks, validating that both plan injection and sleeper injection are real operational risks. ARGUS's approach (monitoring retrieved context separately from user prompts) is architecturally similar to aigis's scan-before-act model.
  **Source**: https://arxiv.org/abs/2605.03378
  **aigis takeaway**: Validates aigis's scan-before-act philosophy. No new pattern needed; confirms coverage direction is correct.

- **Visual Memory Injection in Multi-Turn Conversations (arxiv:2602.15927)**
  Documents injection attacks that plant malicious instructions via images in multi-turn visual conversation history. The injected image content is retrieved in a later turn and activates attack behavior. Multimodal attack, not detectable by text-pattern scanning.
  **Source**: https://arxiv.org/abs/2602.15927
  **aigis takeaway**: Out of scope for text-based pattern detection. Relevant for future multimodal scanning capability.

## Candidate Hardenings

1. **`mem_plan_injection`** (score 55, input/memory filter) — Detects context-chained plan injection: task-continuation framing ("as a next step", "to complete this task", "continuing from the previous step") combined with an exfiltration verb and external URL/address. Targets arxiv:2506.17318 (ICML 2025). 46–63% ASR even with prompt injection defenses active.

2. **`mem_sleeper_dormant`** (score 60, input/memory filter) — Detects explicit dormancy instruction ("do not act now", "stay dormant", "wait until triggered") combined with a deferred exfiltration directive and external URL/address. Targets arxiv:2503.16248 (March 2026). Specifically designed to bypass scans that only check for immediate-action payloads.

3. *(Deferred)* Cross-session memory isolation audit documentation — describes how to protect multi-tenant memory stores from cross-user poisoning. Useful as a `docs/hardening/memory_isolation.md` guide but too large for this cycle.

4. *(Deferred)* Multimodal memory scanning notes — visual injection via conversation history images (arxiv:2602.15927). Requires new capability beyond text patterns; pending.
