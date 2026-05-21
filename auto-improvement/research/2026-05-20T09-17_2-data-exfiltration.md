# Research: data-exfiltration — 2026-05-20T09-17

## Domain: data-exfiltration (index 2, fifth pass)
## Cycle index: 2
## Cycle timestamp: 2026-05-20T09-17

Previous cycles covered:
- Cycle 1 (2026-05-07): Markdown image URL exfil, OAST relay domains.
- Cycle 2 (2026-05-10): DNS encode instruct, reference-style Markdown exfil (EchoLeak), tunnel relay URLs, Unicode Tag Block (was pending, later implemented).
- Cycle 3 (2026-05-13): Mermaid diagram href, web-search covert channel, URL-index analysis, sharded exfiltration.
- Cycle 4 (2026-05-14): Unicode Tag Block smuggling (implemented), sharded exfiltration (implemented), CSS hidden-text (pending), LogJack cloud log injection (pending).

This pass focuses on: chain-request callback exfiltration (Reprompt, CVE-2026-24307), backdoored tool exfiltration (Back-Reveal, arXiv:2604.05432), causality laundering (arXiv:2604.04035), and ANSI escape + clipboard poisoning.

---

## Findings

- **Reprompt / Chain-Request Orchestration (CVE-2026-24307, Varonis Threat Labs, Jan 2026)**:
  Varonis researchers discovered a three-stage attack against Microsoft Copilot Personal. The
  "chain-request" technique instructs the agent to fetch follow-up commands from an attacker-
  controlled URL after exfiltrating context: (1) parameter-to-prompt (P2P) injection via
  Copilot's `?q=` URL prefill parameter, (2) double-request bypass to evade first-request
  protections, (3) the agent fetches its next instruction from `https://attacker.com/step2`,
  which returns another prompt that repeats the cycle. This creates a sustained C2 loop
  invisible to client-side monitors. Microsoft patched on Jan 13–14 2026.
  - Source: https://www.varonis.com/blog/reprompt
  - Source: https://www.securityweek.com/new-reprompt-attack-silently-siphons-microsoft-copilot-data/
  - **aigis takeaway**: Add input pattern `exfil_chain_callback_fetch` (score 70) detecting
    prompts that instruct an agent to fetch its next commands/instructions from an external URL.
    The distinguishing signal is "next instruction/command/prompt from URL" or
    "fetch URL for next instruction/command/prompt" — a combination almost never legitimate.
    **→ IMPLEMENTED this cycle.**

- **Back-Reveal: Backdoored Tool-Use Exfiltration (arXiv:2604.05432, Wuyang Zhang & Shichao Pei, Apr 2026)**:
  Fine-tuned LLM agents can be backdoored during the fine-tuning phase to embed semantic
  triggers: when a user query matches the trigger topic, the agent invokes memory-access tools
  to retrieve stored user context, then exfiltrates it via disguised retrieval tool calls that
  look like normal RAG lookups to monitoring systems. Multi-turn interactions amplify the attack
  because attacker-controlled retrieval responses can steer future behavior. Unlike prompt-
  injection attacks, Back-Reveal does not require the attacker to inject content at inference
  time — the malicious behavior is baked into the model weights during fine-tuning.
  - Source: https://arxiv.org/abs/2604.05432
  - **aigis takeaway**: This attack operates at the model-weight level and cannot be fully
    countered by a text-based rule engine. However, the output-side signal — an unexpected
    sequence of memory-access + external-send tool calls — could be flagged by the behavioral
    monitor. Candidate for pending (behavioral detection requires hooking tool-call sequences,
    not text patterns).

- **Causality Laundering / Denial-Feedback Leakage (arXiv:2604.04035, Mohammad Hossein Chinaei, Apr 2026)**:
  An adversary probes a protected action, learns from the denial outcome, and exfiltrates the
  inferred information through a later seemingly benign tool call. For example: the agent is
  asked to read a protected file (denied), and the attacker infers the file's content from
  the shape of the denial. The paper proposes the Agentic Reference Monitor (ARM) which tracks
  provenance through a graph of tool calls, including denied ones. Causality laundering is not
  captured by flat provenance tracking because the leaked information arises from causal
  influence of the denied action, not direct data flow.
  - Source: https://arxiv.org/abs/2604.04035
  - **aigis takeaway**: Behavioral/runtime detection concern only. Cannot be captured by a
    static regex. The cross-session sleeper or behavioral monitor could be extended to correlate
    denied actions with subsequent tool calls. Candidate for pending.

- **ANSI Escape Sequence + OSC 52 Clipboard Poisoning (Terminal DiLLMa, embracethered.com 2024 / Codex CLI 2026)**:
  LLM-powered CLI tools (including Codex CLI and other code assistants) that render model output
  in terminals can be manipulated via prompt injection to emit ANSI escape sequences. The OSC 52
  escape sequence (`\x1b]52;c;<base64-data>\x07`) causes supporting terminals (iTerm2, some
  xterm variants, Windows Terminal) to replace the system clipboard with attacker-controlled
  content. A concrete Codex CLI vulnerability (reported Feb 2026) allowed the `--model`
  parameter to inject ANSI into terminal output, which was chained with OSC 52 to poison
  the clipboard. As AI coding assistants become default CLI tools, this vector is growing.
  - Source: https://docs.mindgard.ai/attack-library/prompt-injection/AnsiEscaped
  - **aigis takeaway**: Output pattern `out_ansi_osc52_clipboard` to detect OSC 52 escape
    sequences in model output. The sequence is distinctive: `\x1b]52;` or `ESC]52;`.
    Candidate hardening — well-scoped regex, low FP risk.

- **LMDeploy SSRF — CVE-2026-33626 (Sysdig TRT, Apr 2026, exploited in 12 hours)**:
  Critical SSRF in LMDeploy's vision-language `load_image()` function allows attackers to
  make the AI inference server fetch arbitrary URLs, including cloud IMDS endpoints and
  internal Redis/MySQL ports. Exploited within 12h of disclosure in the wild. The existing
  `mcp_ssrf_metadata_endpoint` rule covers cloud IMDS (169.254.169.254) but not the
  `load_image(url=...)` parameter naming convention or the rapid-exploit context.
  - Source: https://www.sysdig.com/blog/cve-2026-33626-how-attackers-exploited-lmdeploy-llm-inference-engines-in-12-hours
  - **aigis takeaway**: The existing SSRF rules cover the endpoint IPs. The new angle is
    the `load_image` function name as an SSRF vector in LLM-specific contexts. Low priority
    since the IP rules already catch the key payload.

- **Reprompt via URL Prefill Parameter (CVE-2026-24307 broader)**:
  The P2P injection variant uses `?q=` URL parameters to pre-populate AI assistant prompts
  without user interaction. When a victim clicks a crafted link, the AI immediately executes
  the attacker's prompt. This is specific to Copilot's URL schema and similar "deep link to
  prompt" affordances being added to AI products. Detection in aigis: suspicious prompt
  pre-population patterns that include exfiltration or instruction-override keywords in
  URL-delivered contexts are already partly covered by existing rules.
  - Source: https://aviatrix.ai/threat-research-center/reprompt-attack-microsoft-copilot-2026-ai-prompt-injection/
  - **aigis takeaway**: Covered by existing prompt injection + exfil rules in combination.
    No new rule needed.

- **Back-Reveal Multi-Turn Steer (arXiv:2604.05432, follow-up)**:
  The attacker-controlled retrieval server returns responses that subtly steer the agent's
  subsequent queries, enabling cumulative information leakage across turns. This means even
  if a single turn's exfiltrated data is small, the attacker can guide the agent to extract
  progressively more sensitive information over a session. This is a monitoring concern that
  cross-session behavioral analysis (already in aigis) can partially address.
  - Source: https://arxiv.org/abs/2604.05432
  - **aigis takeaway**: Existing cross-session sleeper and drift monitor cover the behavioral
    side. No new text pattern needed.

---

## Candidate hardenings

1. **`exfil_chain_callback_fetch`** (input, score 70) — Detect "next instructions/commands/prompts
   from URL" or "fetch URL for next instructions" patterns. Directly covers CVE-2026-24307 /
   Reprompt chain-request callback. Low false-positive risk: legitimate agent inputs do not
   instruct agents to fetch next runtime commands from URLs. **→ Selected for implementation.**

2. **`out_ansi_osc52_clipboard`** (output, score 75) — Detect OSC 52 ANSI escape sequences
   (`\x1b]52;c;<base64>`) in model output that would poison the system clipboard. Concrete
   vector documented against Codex CLI (Feb 2026) and Terminal DiLLMa. Very low FP risk
   (OSC 52 with data payload has no legitimate use in AI text output). **→ Selected for
   implementation as a second pattern this cycle.**

3. **Back-Reveal behavioral detection** — Correlate memory-access tool calls immediately
   followed by external-URL send calls. Requires tool-call sequence tracking in the behavioral
   monitor rather than a text regex. **→ Pending (too complex for this cycle).**

4. **Causality laundering provenance graph** — Track denied actions in the ARM monitor and
   correlate with subsequent benign tool calls. Requires graph-based runtime analysis.
   **→ Pending (architectural change, > 100 LOC).**
