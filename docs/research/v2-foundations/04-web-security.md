# Web Security as the Template for AI Agent Security

## 1. The web security primitives, summarized

The browser is the world's most-attacked sandbox. It evolved a layered defense stack against a threat model that is essentially identical to the one LLM agents face: **untrusted content (instructions encoded as data) mixed with trusted context (the user's session, secrets, capabilities) inside an executor that can act on both.**

| Primitive | One-line essence | Direct AI analog |
|---|---|---|
| **Same-Origin Policy (SOP)** | Origin = (scheme, host, port). Code from one origin cannot read another. | Every prompt fragment gets an origin tag; instructions from `tool_output://` cannot mutate the goal set by `user://`. |
| **Content Security Policy (CSP)** | Declarative whitelist of script sources, eval, inline. | Per-session declarative tool/network/eval policy. |
| **Trusted Types** | DOM sinks demand typed objects, not strings; eliminates DOM-XSS by typing. | Tool args constructed from LLM output must pass a typed sanitizer; never raw `${llm_output}` interpolation into shell/SQL/code. |
| **Subresource Integrity (SRI)** | `integrity="sha384-..."` pins external script hash. | RAG/web-fetched chunks carry hashes; mid-session drift = abort. |
| **CORS** | Cross-origin reads are opt-in via response header. | Cross-origin reads in the prompt graph (tool A reading tool B's output) need explicit policy opt-in. |
| **Cookie attributes (HttpOnly/Secure/SameSite)** | Defense-in-depth layering of a single object. | Secrets in the agent's context are tagged: `HttpOnly` (never echoable to LLM output), `SameSite` (no cross-tool leakage). |
| **iframe `sandbox`** | Strip capabilities from embedded content. | Sub-agent / quarantined LLM run with stripped tool list — this is Willison's [Dual LLM](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/). |
| **Permissions Policy** | Per-origin gating of geolocation, mic, camera. | Per-tool gating of network, filesystem, secrets, state-changing actions. |
| **Site Isolation** | One renderer process per site; Spectre containment. | One sandbox/container per untrusted-content session; blast-radius limit. |

**The killer insight:** after SOP was invented in 1996, every subsequent web defense was a different answer to the question "what is the *origin* of this content?" **Provenance is the load-bearing concept.**

## 2. The Dual-LLM lineage — already converging on the web model

Simon Willison's [dual LLM pattern](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/) explicitly cited the privileged/unprivileged split.

- **2023 — Dual LLM (Willison).** P-LLM has tools; Q-LLM reads untrusted content and emits only opaque variable references back to P-LLM.
- **2025 March — CaMeL** ([arxiv:2503.18813](https://arxiv.org/abs/2503.18813), DeepMind). Realizes dual-LLM as a capability system: P-LLM emits a typed Python-subset program; values from Q-LLM are wrapped in `Value` objects carrying **capability tags (origin + reader set + integrity)**. The interpreter is a capability monitor. **Functionally SOP + CORS + Trusted Types compiled to a small VM.**
- **2025 May — Operationalizing CaMeL** ([arxiv:2505.22852](https://arxiv.org/abs/2505.22852)). Adds prompt screening, output auditing, tiered risk, and a formally verified IL.
- **2025 June — Lethal Trifecta** ([Willison](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)). Private data + untrusted content + external comms = compromise.
- **2025 Oct — Meta's "Agents Rule of Two"** ([ai.meta.com](https://ai.meta.com/blog/practical-ai-agent-security/)). Pick at most 2 of {untrusted input, sensitive data, state change} per session.
- **2026 March — CaMeLs Can Use Computers Too** ([arxiv:2601.09923](https://arxiv.org/abs/2601.09923)). Extends CaMeL to computer-use agents via single-shot planning.
- **2026 May — Microsoft's "When prompts become shells"** ([MSRC](https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/)) documents RCE chains via prompt → tool args → shell — precisely the class Trusted Types was invented to kill.

Also relevant: [DRIFT](https://arxiv.org/pdf/2506.12104), [Polymorphic Prompt Assembling](https://arxiv.org/pdf/2506.05739) (analogous to ASLR for prompts), the [reversec design-patterns post](https://labs.reversec.com/posts/2025/08/design-patterns-to-secure-llm-agents-in-action) (`SourcedString` = tainted strings with carried provenance, a direct port of Perl taint mode 1989).

## 3. The killer insight: provenance is the right primitive

**Claim: AI agent security will rhyme with web security, and the load-bearing concept is *origin*.**

1. Every published agent vulnerability of 2024–2026 (EchoLeak / [CVE-2025-32711](https://arxiv.org/abs/2509.10540), Salesforce Agentforce, Copilot Cowork, MCP rug-pulls) has the same structure: **content from origin X was treated as if it came from origin Y.** EchoLeak: an email's body was promoted to "user instruction" because both lived in the same context window. This is XSS, retold.
2. Every promising defense — Dual LLM, CaMeL, Rule of Two, tainted strings, plan-before-data — is implicitly an origin discipline.
3. Filtering ("did this look like an attack?") will keep failing for the same reason web XSS filters failed: it's a semantic question. Origin-checking is a *structural* question.

Where the analogy weakens: in the browser, code and data are syntactically separable (parsed by different grammars). In an LLM, "code" and "data" are the same token stream — the model decides which is which. So **origin tagging cannot live inside the prompt; it must live in the orchestrator that *assembles* the prompt** and in the *interpreter* that *executes* tool calls. Aigis sits exactly there.

## 4. Concrete proposals for Aigis v2

### 4.1 `aigis.origin` — Origin model for prompt content (SOP)

Every byte fed to an LLM is wrapped in `Tagged(content, origin, integrity)`. Origin URI scheme:

```
system://aigis/v1                      # the policy itself
developer://app-name/role              # baked-in role prompt
user://session-id                      # the human in the loop
tool_output://mcp/github/issue/42      # MCP server replies
retrieved://web/sha256-...             # RAG chunks (hash-pinned)
agent_memory://session-id/turn-7       # prior turns
```

```python
from aigis.origin import Tagged, Origin, assemble

ctx = [
    Tagged(system_prompt, Origin("system://aigis/v1")),
    Tagged(user_msg, Origin(f"user://{sid}")),
    Tagged(tool_resp, Origin(f"tool_output://mcp/jira/{ticket}")),
]
prompt = assemble(ctx, policy="strict")     # raises if origins disallowed
```

**Attack stopped.** EchoLeak class: forbid `tool_output://email/*` from carrying weight ≥ `user://` for goal-setting.
**Effort.** ~2 weeks. Pure wrapper around prompt assembly; no model changes.

### 4.2 `aigis.csp` — CSP for tool calls

```yaml
default: deny
allow_tools:        [read_file, grep, list_dir]
allow_network:      none
allow_eval:         none
allow_state_change: [draft_email]
origin_trust:
  user://*:         instructions=high, data=high
  tool_output://*:  instructions=none,  data=medium
  retrieved://*:    instructions=none,  data=low
report_uri: https://aigis.example.com/violations
```

`instructions=none` means: text from this origin is allowed as evidence but never as a goal/imperative.

**Attack stopped.** Indirect injection: a poisoned web page tells the agent to email customer data. The fetched page's origin is `retrieved://`, which has `instructions=none`.
**Effort.** ~3–4 weeks.

### 4.3 `aigis.tt` — Trusted Types for LLM outputs (kills tool-arg injection)

Any tool whose argument grammar is dangerous (`shell.exec`, `sql.query`, `http.request`, `eval`) declares **typed sinks**. The LLM cannot pass a raw string; it must pass a `ShellCommand`, `SqlQuery`, `Url`, etc., which can only be constructed by an Aigis-provided sanitizer.

```python
@tool(arg_types={"cmd": ShellCommand})
def run(cmd: ShellCommand) -> str: ...

# LLM emits {"cmd": "rm -rf /"} -> Aigis parses through shlex,
# checks against an argv allowlist, rejects.
```

**Attack stopped.** [Microsoft's "prompts become shells" RCE class](https://www.microsoft.com/en-us/security/blog/2026/05/07/prompts-become-shells-rce-vulnerabilities-ai-agent-frameworks/). String interpolation of `${llm_output}` into a shell is structurally impossible.
**Effort.** ~1–2 weeks per dangerous tool family.

### 4.4 `aigis.sri` — Hash-pinned retrieval

Every retrieved chunk (RAG, web, MCP tool reply that's deterministic) is hashed on first read and the hash is recorded in the session's manifest. On every subsequent read, the hash is re-checked. Drift → abort or quarantine.

**Attack stopped.** RAG cache poisoning, MCP rug-pull (server changes tool description between approval and call), TOCTOU between two reads of the same doc.
**Effort.** ~1 week.

### 4.5 `aigis.iso` — Process-level site isolation for sub-agents

When a Q-LLM is spawned to read tainted content, it runs in a separate process with: (i) no network egress, (ii) no shared memory with the P-LLM, (iii) a restricted output channel that returns only **opaque handles** back to the P-LLM.

**Attack stopped.** Side channels and exfil through clever P-LLM prompting of its own Q-LLM. Direct port of Chrome's [Site Isolation](https://www.chromium.org/Home/chromium-security/site-isolation/).
**Effort.** ~3 weeks.

## 5. Honest critique

**Web security took 25+ years and still ships XSS.** Mitre tracks XSS at #2 in CWE Top 25 for 2024. If the AI field traces the same curve, expect prompt injection to be *common but mostly survivable* by 2035, only for deployments that adopted structural primitives early.

**Browsers had a forcing function; MCP doesn't.** WHATWG/W3C are why CSP exists everywhere. MCP has no equivalent — the [July 2026 RC spec](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/) is moving but vendor adherence is uneven. Implication: **don't wait for a standard; ship a *gateway* that enforces unilaterally.**

**CSP deployment friction is real and CSP-for-LLM will be worse.** Most production CSPs are `unsafe-inline` because devs gave up. Mitigations: (a) ship a *report-only* mode first; (b) ship `aigis-csp-evaluator`; (c) make default templates per MCP server.

**The asymmetry that *helps* AI security.** Unlike browsers, LLM agents have a single chokepoint per session (the orchestrator). The window to bake origin tagging into MCP and AgentSDKs is *now*, before it ossifies.

## 6. Recommended reading

1. **Willison, "The lethal trifecta for AI agents"** ([simonwillison.net 2025-06-16](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/))
2. **Debenedetti et al., "Defeating Prompt Injections by Design" (CaMeL)** ([arxiv:2503.18813](https://arxiv.org/abs/2503.18813))
3. **Meta AI, "Agents Rule of Two"** ([ai.meta.com 2025-10-31](https://ai.meta.com/blog/practical-ai-agent-security/))
4. **Reversec, "Design Patterns to Secure LLM Agents In Action"** ([labs.reversec.com 2025-08](https://labs.reversec.com/posts/2025/08/design-patterns-to-secure-llm-agents-in-action))
5. **W3C, "Trusted Types"** ([w3c.github.io/trusted-types](https://w3c.github.io/trusted-types/dist/spec/)) and **Google, "Site Isolation"** ([chromium.org](https://www.chromium.org/Home/chromium-security/site-isolation/))

## Top 3 to prototype (ranked)

1. **`aigis.origin`** — origin tags on every prompt fragment. **Why first:** every other defense depends on this primitive. Smallest PR. This is Aigis's SOP.
2. **`aigis.tt`** — Trusted Types for dangerous tool args. **Why second:** highest ratio of *attack-class eliminated* per *line of code*. Survives open-source disclosure fully.
3. **`aigis.csp`** — declarative per-session policy with `report-only` mode. **Why third:** public-facing artifact deployers will edit; ship after `origin` and `tt` so the schema is informed.

Skip-for-now: `aigis.sri` (small but mostly relevant once RAG is in scope), `aigis.iso` (high value but needs the others as scaffolding).
