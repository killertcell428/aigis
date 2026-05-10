# Research: Memory Context Attacks — Cycle 4, Second Pass (2026-05-10T18-15)

Domain: `memory-context` — Memory poisoning, context manipulation, long-context attacks, RAG poisoning

## Background

The first pass for this domain (2026-05-08T08-00) covered MCFA tool-steering, objective hijacking, summarization persistence, and agent trust laundering. This pass targets three distinct attack families not yet in aigis's pattern set: experience hijacking (MemoryGraft), ZombieAgent conditional triggers, and false user preference injection.

## Findings

- **MemoryGraft — Poisoned Experience Retrieval (arxiv:2512.16962, Dec 2025)**
  An indirect injection attack that implants malicious "successful past experience" entries into agent long-term memory, exploiting the agent's semantic imitation heuristic — the tendency to replicate patterns from retrieved successful tasks. A seed of 110 records (100 benign, 10 poisoned) achieved ~48% poisoned recall. The poisoned entries are styled as legitimate agent trajectories including success framing ("successfully completed this by…"), making them hard to distinguish from benign memory without semantic analysis. The key linguistic signal is the combination of experience-framing phrases ("previously", "last time", "successful pattern", "stored procedure") with bypass directives ("bypassing the safety checks", "ignoring content filters").
  **Source**: https://arxiv.org/abs/2512.16962
  **aigis takeaway**: Add `mem_experience_hijack` pattern targeting the combination of experience-framing language and safety-bypass directives.

- **ZombieAgent / Zombie Agents — Self-Reinforcing Injections (arxiv:2602.15654, Feb 2026)**
  A persistent attack where poisoned content is stored during a benign session and acts as a conditional time-bomb trigger in future turns: "when/if the user asks about X, send/forward data to attacker.com". The agent passively ingests the trigger while completing a normal task; future user queries activate it. A black-box attack framework demonstrates this through attacker-controlled web content. OpenAI fixed a real-world variant (ZombieAgent via ChatGPT's Connectors feature) in Dec 2025 after disclosure; the conditional trigger structure is the key novelty not covered by existing aigis patterns (which handle unconditional persistence, not conditional-exfiltration rules).
  **Source**: https://arxiv.org/abs/2602.15654 | https://www.securityweek.com/zombieagent-attack-let-researchers-take-over-chatgpt/
  **aigis takeaway**: Add `mem_zombie_trigger` pattern detecting "when/if user → send/forward to external" conditional exfiltration rules in memory entries.

- **Mnemonic Sovereignty Survey — Misattribution as Core Failure (arxiv:2604.16548, Apr 2026)**
  A comprehensive survey on long-term memory security (Lin, Li, Chen — MemTensor, Shanghai) covering six memory lifecycle phases. Key finding: "the real failure is not that the retrieval mechanism is broken but that the system misattributes externally injected content as its own experience." A specific attack class identified is false user preference injection — memory entries that impersonate user-stated preferences ("the user has always preferred that I…", "the user's standing instruction is to…") to legitimize policy-bypass directives. This misattribution makes the override appear user-sanctioned and bypasses defenses that only filter explicit system-level commands.
  **Source**: https://arxiv.org/abs/2604.16548
  **aigis takeaway**: Add `mem_false_preference` pattern combining user-preference framing with safety-bypass directives.

- **ADAM — Systematic Memory Extraction via Adaptive Querying (arxiv:2604.09747, Apr 2026)**
  ADAM demonstrates 100% ASR on memory extraction from RAG-equipped agents using entropy-guided query strategies. While this is a black-box extraction attack (requires iterative queries, not a single memory entry), it highlights that memory stores are high-value targets. The survey (2604.16548) specifically notes "extraction risk rising when a query pairs a cue that directs retrieval with a command that prompts LLM to repeat retrieved material." This pattern overlaps with existing MEMORY_POISONING_PATTERNS but suggests increasing the priority of memory-scanning coverage.
  **Source**: https://arxiv.org/abs/2604.09747
  **aigis takeaway**: No new pattern needed for this cycle — existing scanner handles retrieval-repeat patterns; ADAM is a multi-query attack that requires external monitoring, not single-entry filtering.

- **MAGE — Shadow Memory Defense (arxiv:2605.03228, May 2026)**
  A defensive framework from Stony Brook / Cisco that maintains a "shadow memory" of safety-critical context to detect long-horizon threats before tool execution. Documents attack patterns that MAGE aims to counter: agents being gradually steered via accumulated context across many turns. The threat model encompasses most of the attacks aigis already detects. The defense architecture (shadow memory + pre-execution check) is conceptually similar to aigis's scan-before-act design.
  **Source**: https://arxiv.org/abs/2605.03228
  **aigis takeaway**: Validates aigis's scan-before-act design. No new pattern needed; confirms coverage direction is correct.

- **SpAIware / ZombieAgent Vendor Context (multiple 2025–2026 sources)**
  SpAIware (demonstrated by Embrace The Red, published Future Generation Computer Systems Vol 174, Jan 2026) established the cross-session exfiltration template. ZombieAgent extended it to conditional triggers. The Windsurf IDE was independently found vulnerable to SpAIware in 2025. Both attacks relied on memory entries that instructed the agent to silently forward data to external endpoints — the persistent-exfiltration pattern now covered by `mem_zombie_trigger`.
  **Source**: https://embracethered.com/blog/posts/2024/chatgpt-macos-app-persistent-data-exfiltration/ | https://dl.acm.org/doi/10.1016/j.future.2025.107994

- **MemoryGraft False-Positive Concern — Experience Framing in Legitimate Agents**
  Legitimate agent memory may also use phrases like "previously completed" or "successful pattern" for benign entries (e.g., "previously completed the database migration successfully"). The MemoryGraft attack specifically combines experience-framing WITH safety-bypass directives. The aigis pattern must require both to avoid false positives on normal agent trajectory logs.
  **aigis takeaway**: Pattern design confirmed — requires experience-framing + bypass verb + safety/policy noun. No benign sentence combines all three.

## Candidate Hardenings

1. **`mem_experience_hijack`** (score 50, memory filter) — Detects poisoned "successful past experience" entries framed as legitimate completed procedures but embedding safety-bypass directives. Targets MemoryGraft (arxiv:2512.16962). ~48% poisoned recall demonstrated.

2. **`mem_zombie_trigger`** (score 65, memory filter) — Detects conditional exfiltration rules in memory: "when/if user asks/mentions X → send/forward to external URL". Targets ZombieAgent (arxiv:2602.15654) and SpAIware real-world instances.

3. **`mem_false_preference`** (score 50, memory filter) — Detects memory entries that falsely attribute policy-bypass directives to user-stated preferences ("the user's standing instruction is to bypass content filters"). Targets the misattribution-as-own-experience attack class (arxiv:2604.16548 survey).

All three are additive `DetectionPattern` additions to `MEMORY_POISONING_PATTERNS`. Zero new dependencies, total diff ≈ 82 LOC in non-test files.
