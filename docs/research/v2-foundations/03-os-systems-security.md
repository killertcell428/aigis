# Systems-Security Primitives for Aigis v2: Capabilities, Sandboxing, and OS-Level Isolation

## 0. The thesis in one paragraph

Aigis v1 is a **detector** — it answers "is this input/output malicious?" using ~100 deterministic patterns. The structural weakness is obvious: in open source, an attacker can read the rules. The systems-security tradition spent fifty years on the dual question: **"given that the input is malicious, what authority does it actually convey?"** That is the question capability systems, sandboxing, and MAC frameworks answer. For Aigis v2, the right move is not to replace detection but to **layer it under capability-mediated execution**, so a bypass of a detector is bounded by what the agent's capability set can actually express. Detection is probabilistic; capability is structural. They compose multiplicatively.

## 1. Core concepts

### 1.1 Capability-based security

A **capability** is an unforgeable, transferable reference that names an object *and* the right to act on it. There is no separate ACL lookup, no "ambient authority", and no name-to-object resolution that an attacker can spoof. Possession of the capability *is* the permission.

- **seL4** — microkernel with machine-checked functional-correctness, integrity, and confidentiality proofs down to binary code. ([seL4 Verification](https://sel4.systems/Verification/))
- **CHERI / ARM Morello / CHERIoT** — hardware capabilities: pointers become 128-bit fat references with bounds and permission bits enforced by the ISA. ([CHERI-seL4](https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/cheri-sel4.html), [VeriCHERI arxiv](https://arxiv.org/pdf/2407.18679))
- **Fuchsia** — Google's microkernel OS. Every Zircon syscall takes a handle (a capability).
- **KeyKOS / EROS / Genode** — the lineage. Genode is the practical descendant.
- **E language / Mark Miller's work** — the object-capability ("ocap") model formalized.

### 1.2 Sandboxing & SFI (Software Fault Isolation)

- **WebAssembly (Wasmtime, Wasmer, WASI Preview 2)** — deny-by-default capability runtime. A `.wasm` module has no `open`, no `socket`, no clock unless the host passes a capability. **The single most relevant primitive for Aigis v2.**
- **gVisor** — userspace re-implementation of ~70-80% of the Linux syscall surface in Go. ~10-30% I/O overhead.
- **Firecracker** — KVM microVMs, ~125ms boot, ~5 MiB memory overhead.
- **Native Client (NaCl)** — instructive even though deprecated.
- **seccomp-bpf** — syscall allowlist as BPF program.
- **Landlock** — unprivileged filesystem and (since 6.7) network sandboxing.

### 1.3 MAC / DAC

- **SELinux / AppArmor / BSD MAC** — labels-and-policy. Useful when you need a *third party* to override what the program would otherwise be allowed to do.

### 1.4 Privilege separation & POLA

- **OpenSSH privsep** — the canonical example. A small "monitor" process holds privileges; an unprivileged "slave" parses untrusted network input.
- **POLA (Principle Of Least Authority)** — the object-capability community's version of POLP.

### 1.5 TCB minimization

seL4's TCB is ~10 kLOC of C. Linux's is ~25 MLOC. For an LLM agent, the agent's *prompt and model weights are part of the TCB* if they decide which tool to call — unless capabilities make that decision unforgeable.

## 2. Existing AI-security applications (2024-2026)

- **Wassette (Microsoft, Aug 2025)** — runs MCP tools as Wasm Components with a deny-by-default, per-tool capability grant. ([Microsoft Open Source Blog](https://opensource.microsoft.com/blog/2025/08/06/introducing-wassette-webassembly-based-tools-for-ai-agents/), [InfoWorld](https://www.infoworld.com/article/4039243/wassette-a-bridge-between-wasm-and-mcp/))
- **wasmcp** — polyglot SDK for composing MCP servers from Wasm components ([github.com/wasmcp/wasmcp](https://github.com/wasmcp/wasmcp)).
- **Hyper MCP** — Rust MCP host loading tools as sandboxed WASM plugins.
- **MCP-SandboxScan (arxiv 2601.01241)** — WASM-based secure execution + runtime analysis for MCP tools.
- **Sandlock (Multikernel, Mar 2026)** — per-tool-call fork + Landlock + seccomp-bpf, no containers ([multikernel.io](https://multikernel.io/2026/03/25/sandlock-mcp-per-tool-sandboxing/)).
- **Google Agent Sandbox (KubeCon NA 2025)** — gVisor-backed sandbox pods.
- **Tenuo / IBCTs (arxiv 2603.24775, "AIP: Agent Identity Protocol")** — cryptographic capability tokens. ~0.05 ms verification.
- **Cerbos for MCP** — policy-engine layer over MCP permission scoping.
- **OWASP MCP Top 10 (2025)** — first formal MCP risk taxonomy.

Vector that has *not* shipped publicly yet: **CHERI for AI workloads**. Greenfield.

## 3. Concrete proposals for Aigis v2

### 3.1 Object-capability MCP tool registry (effort: M, impact: HIGH)

Replace MCP's tool-name-as-string addressing with an unforgeable capability handle. The Aigis broker becomes the *only* component that can mint handles.

**Attack prevented (structurally):** Prompt-injected tool calls to tools the agent was never granted. If the model emits `call_tool("delete_database", ...)` but holds no `delete_database` capability, the broker drops the call before any string-matching detector runs. No bypass via clever obfuscation, base64, language switching, etc.

**API sketch:**
```python
caps = aigis.mint_capabilities(
    agent_id="researcher-007",
    grants=[
        Cap("filesystem.read", scope="/home/user/papers/**"),
        Cap("http.fetch", scope="arxiv.org"),
    ],
    ttl=timedelta(hours=1),
)
ctx = aigis.AgentContext(caps=caps)
result = ctx.invoke(cap_handle, args)
```

Handle = signed `(agent_id, tool_id, scope, parent_handle?, exp, nonce)` — essentially the IBCT design from arxiv 2603.24775.

### 3.2 WASI sandboxing for MCP tools (effort: M-L, impact: HIGH)

`aigis-wasi-shim`: a runner that loads each MCP server as a Wasm Component. Host passes only the WASI capabilities declared in `aigis.toml` per tool.

**Attack prevented:** A compromised MCP tool cannot exfiltrate `~/.ssh/id_rsa` because the WASI host did not pass a preopened dir containing it. No filesystem grant = no `open` syscall.

```toml
[tools.read_doc]
wasm = "oci://ghcr.io/acme/read_doc:1.2"
wasi.fs.preopen = { "/data" = "ro" }
wasi.net.allow  = []
wasi.env        = []
```

Wassette already does most of this; Aigis adds the **detector layer behind the sandbox** so the broker can also pattern-scan inputs/outputs as defense-in-depth.

### 3.3 Per-call Landlock+seccomp confinement for non-Wasm tools (effort: S, impact: MEDIUM)

For native Python/Node MCP servers we can't easily compile to Wasm, wrap each invocation in `fork() → Landlock(rulesets) → seccomp(allowlist) → exec`. ~3 ms overhead per call.

**Attack prevented:** Token-theft via reading env vars / dotfiles; sub-process exec (`bash -c`); raw socket; ptrace. seccomp blocks `execve`, `mount`, `ptrace`, `process_vm_*`, `unshare`.

### 3.4 Capability attenuation & chained delegation (effort: M, impact: HIGH for multi-agent)

Adopt IBCT/Biscuit-style append-only token chains. When agent A delegates to sub-agent B, A's broker mints a *strictly weaker* token. Cryptographically enforced: B cannot widen its own scope.

**Attack prevented:** Confused-deputy in multi-agent / A2A systems.

### 3.5 Aigis broker as a privsep monitor (effort: S, impact: STRUCTURAL)

Split Aigis into two processes: a tiny **broker** (capability table, policy, signing key — <2 kLOC) and a **scanner** (the detector engine — large, exposed to attacker-controlled text). Scanner runs unprivileged, drops syscalls, talks to broker over a unix socket with a typed protocol.

**Attack prevented:** An RCE in a YAML/regex parser inside the scanner cannot mint capabilities.

### 3.6 SELinux/AppArmor profile shipped with Aigis (effort: XS, impact: LOW-MEDIUM)

Bundled MAC policy: `aigis_t` domain that can read its config, listen on the broker socket, and nothing else.

### 3.7 Forward path: CHERI/CHERIoT for embedded MCP (effort: L, research-grade)

Port Aigis broker to CHERIoT-RTOS for edge/IoT MCP deployments. Tool handles become hardware capabilities.

## 4. How this composes with v1 detection

| Layer | Question answered | Failure mode if alone |
|------|----------|----------|
| **v1 detectors** (regex + heuristic) | "Is this input/output suspicious?" | Bypassable by attackers who read the rules |
| **Capability broker** (3.1, 3.4) | "Does the agent even *have* the right to do this?" | Allows benign-looking but unsafe tool composition |
| **WASI / Landlock sandbox** (3.2, 3.3) | "If the call is made, what can the callee touch?" | Doesn't see the prompt; can't reason about intent |
| **MAC / privsep** (3.5, 3.6) | "If everything else fails, what does the OS still refuse?" | Coarse-grained |

Aigis v1 is a *probabilistic upper bound* on attacks. Capabilities are a *structural upper bound* on damage.

The Aigis v2 thesis: **detectors are eyes, capabilities are hands. Tie the hands and the eyes can be wrong without catastrophe.**

## 5. Honest critique

**Why haven't capabilities won in 40 years?**
- *Developer ergonomics.* ACLs map onto "users and groups" which humans understand.
- *Migration cost.* You cannot bolt capabilities onto POSIX without breaking software that assumes `open("/etc/passwd")` works.
- *Tooling.* No `strace` equivalent for capability flows until recently.
- *Network effects.* For AI agents this is *changing now* because the runtime is new.

**WASM limitations.**
- Missing syscalls: WASI Preview 2 still lacks robust threads, full POSIX sockets, `fork`.
- Cold start: ~5-50ms per module load.
- Numerics: 10-30% slower for SIMD-heavy code.
- Python-on-Wasm (componentize-py) works but isn't seamless.

**Confused deputy / capability leakage.**
- Capabilities solve the deputy problem *only if* you actually attenuate on delegation.
- Side channels: a capability cannot prevent the agent from *describing* sensitive data in its outputs.
- Revocation: capability tokens with long TTL = stolen-token risk.

## 6. Recommended reading (ranked by signal)

1. **Mark Miller, *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control*** (PhD thesis, 2006).
2. **Klein et al., *seL4: Formal Verification of an OS-Kernel Microkernel*** (CACM, 2010 + updates at [sel4.systems](https://sel4.systems/Verification/)).
3. **Watson et al., *CHERI: A Hybrid Capability-System Architecture***.
4. **The AIP / IBCT paper, arxiv [2603.24775](https://arxiv.org/pdf/2603.24775).** Most actionable artifact for Aigis.
5. **Wassette docs + source ([blog](https://opensource.microsoft.com/blog/2025/08/06/introducing-wassette-webassembly-based-tools-for-ai-agents/))** and **Sandlock writeup ([multikernel.io](https://multikernel.io/2026/03/25/sandlock-mcp-per-tool-sandboxing/))** — current-art reference implementations.

Honorable mention: Norm Hardy's 1988 "Confused Deputy" memo.

## Top 3 to prototype (effort × impact)

1. **Capability-handle MCP broker (§3.1)** — *highest impact, medium effort.* Eliminates string-matched tool dispatch entirely. Ship as `aigis.broker` with IBCT-style signed handles.
2. **Per-call Landlock + seccomp sandbox (§3.3)** — *cheapest big win.* No new dependency, no Wasm compilation, ~3 ms overhead.
3. **WASI shim for tools that can compile to Wasm (§3.2)** — *highest structural ceiling.* Slot in alongside (1) and (2).

**Strategic point:** Aigis v1 competes in the crowded "detect bad prompts" space. Aigis v2, if it ships the broker + sandbox combo, becomes the *only* open-source MCP layer that combines (a) deterministic pattern detection, (b) unforgeable capability dispatch, and (c) OS-level isolation under a single policy file.
