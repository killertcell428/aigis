# Research: Prompt Injection — Cycle 0 (Second Pass)

**Domain:** `prompt-injection`
**Cycle UTC:** 2026-05-09T18-17
**Coverage angle:** Promptware kill-chain C2 stage + context-aware task-hijacking (fresh 2026 Q1–Q2 papers, different from the first-pass cycle which covered AI-addressee and delimiter-spoof vectors)

---

## Key Findings

- **Promptware Kill Chain — 7-stage malware model for prompt injection** (arxiv:2601.09625, Jan 2026; Schneier/Nassi et al.). Prior work treated prompt injection as a single exploit step. This paper formalises it as a 7-stage kill chain: (1) Initial Access via injection, (2) Privilege Escalation via jailbreak, (3) Reconnaissance, (4) Persistence via memory/RAG poisoning, (5) Command & Control, (6) Lateral Movement, (7) Actions on Objective. Of 36 documented real-world incidents analysed, 21 traverse 4+ stages. Stage 5 (C2) is the most under-detected in current tools — the agent is enrolled in an external task loop without the operator knowing.
  - *For aigis:* New `ii_promptware_c2` pattern targets Stage 5 C2 enrollment language: "receive your next task from [URL]", "report results to [URL]", "await further instructions from the server", "registered as agent #X".
  - Source: https://arxiv.org/abs/2601.09625

- **Agent Commander — live C2 exploit against production agents** (EmbraceTheRed / Johann Rehberger, March 2026; CSA Research Note). Demonstrated that multiple AI agents from different vendors (including coding agents and personal copilots) can be simultaneously enrolled into a unified C2 network via prompt injection in a document or repository. The enrolled agents continuously pull tasks from an attacker-controlled dashboard using natural-language commands. This is not theoretical — confirmed against production systems.
  - *For aigis:* Validates the `ii_promptware_c2` pattern as a real attack surface. The enrollment language uses phrases like "you are now agent #X", "report to https://...", "await tasks from https://...".
  - Source: https://embracethered.com/blog/posts/2026/agent-commander-your-agent-works-for-me-now/
  - Source: https://labs.cloudsecurityalliance.org/research/csa-research-note-promptware-agent-commander-c2-20260317-csa/

- **ARGUS / AgentLure — context-aware task hijacking** (arxiv:2605.03378, May 2026). Existing prompt injection benchmarks assume context-insensitive attacks. AgentLure is a new benchmark with context-dependent tasks across 4 agentic domains and 8 attack vectors. ARGUS (the defence) reduces ASR to 3.8% but requires LLM-at-runtime (not usable in aigis). The attack vectors documented include **task hijacking**: the injected payload redirects the agent away from the user's goal using task-switching phrasing ("stop what you are doing and instead…", "instead of completing that task, do…", "abandon your current objective"). ASR pre-defence: 85%+.
  - *For aigis:* New `ii_task_abandonment` pattern targets these task-switching constructs in retrieved/external content. These are distinct from the existing `pi_ignore_instructions` pattern which targets "ignore/disregard/forget + instructions/rules/system" nouns.
  - Source: https://arxiv.org/abs/2605.03378

- **AgentSentry — multi-turn temporal causal takeover** (arxiv:2602.22724, Feb 2026). Multi-turn indirect injection where no single turn is clearly malicious but cumulative attacker influence displaces the user goal. First inference-time defence modelling IPI as a temporal causal takeover process. Relevant as a research direction but requires stateful context tracking incompatible with aigis's stateless pattern scanning.
  - *For aigis:* No single-turn rule applicable. Candidate for a pending idea: stateful turn-window injection scoring.

- **Promptware SoK — 42 attack techniques across 78 studies** (MDPI Information 17(1), Jan 2026). Systematisation of Knowledge paper catalogues 42 distinct prompt injection techniques spanning input manipulation and tool-related vectors. Confirms that ASR against state-of-the-art defences exceeds 85% when adaptive strategies are used. Priority attack classes not yet in aigis: C2 enrollment, task abandonment, and URL fragment injection.
  - *For aigis:* C2 enrollment and task abandonment implemented this cycle. URL fragment injection remains in pending (false-positive risk too high without URL parsing context).
  - Source: https://www.mdpi.com/2078-2489/17/1/54

- **"When AI Meets the Web" — chatbot plugin conversation history tampering** (arxiv:2511.05797, IEEE S&P 2026). 8 of 17 major chatbot plugins fail to enforce conversation history integrity in network requests between the website and the plugin. Attackers can inject fake prior assistant turns into the chat history. This is a transport-layer vulnerability distinct from prompt injection in content.
  - *For aigis:* The injection surface is conversation history (not retrieved documents). The `ii_delimiter_spoof` pattern (cycle 0 first pass) already partially covers fake role-tagged message injection. No additional rule needed this cycle; log as pending for conversation-history-specific patterns.
  - Source: https://arxiv.org/abs/2511.05797

---

## Candidate Hardenings

| Priority | Change | Fits constraints? |
|----------|--------|-------------------|
| **HIGH** | New pattern `ii_promptware_c2`: C2 enrollment / callback via "await instructions from", "receive task from URL", "report to URL", "registered as agent #N" | ✅ Implemented this cycle |
| **HIGH** | New pattern `ii_task_abandonment`: task-hijacking via "stop what you're doing and instead", "abandon current task", "instead of completing that task above" | ✅ Implemented this cycle |
| **MED** | Stateful multi-turn injection scoring (AgentSentry) | ⏳ Pending (requires context state across turns) |
| **MED** | Conversation-history injection pattern (fake role tags injected at transport layer) | ⏳ Pending (partially covered by `ii_delimiter_spoof`; needs separate pattern study) |
| **LOW** | URL fragment injection (`#IGNORE_INSTRUCTIONS`) | ⏳ Pending — already noted in first-pass pending/ |
