# Aigis Architecture (v1.3.1)

> Last updated: 2026-04-10
> Version: v1.3.1 — 165+ patterns, 25+ threat categories, 6-layer detection, CaMeL capabilities, AEP, Safety Specs

## Overview

Aigis is a **general-purpose security layer for AI agents**. It monitors inputs, outputs, and MCP tool definitions of LLM applications, detecting, blocking, and reporting with remediation guidance across 25+ threat categories — from prompt injection to data exfiltration. In v1.3.1, in addition to the conventional 3-layer detection (pattern, similarity, decoding), Capability-based access control powered by CaMeL (L4), Atomic Execution Pipeline (L5), and Safety Specification & Verifier (L6) have been added, achieving 6-layer defense. Zero external dependencies (Python standard library only).

```
┌──────────────────────────────────────────────────────────────────────┐
│                          AI Agents                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Claude   │  │ OpenAI / │  │ LangChain│  │ Custom   │            │
│  │ Code     │  │ Anthropic│  │ LangGraph│  │ Agent    │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │              │              │              │                  │
│       ▼              ▼              ▼              ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │              Aigis Security Layer                      │     │
│  │                                                              │     │
│  │  ┌────────────────────────────────────────────────────────┐ │     │
│  │  │  Adapter Layer                                          │ │     │
│  │  │  Claude Code hooks │ FastAPI middleware │ LangChain CB  │ │     │
│  │  │  Anthropic Proxy   │ OpenAI Proxy      │ LangGraph Node│ │     │
│  │  └─────────┬──────────────────────────────────────────────┘ │     │
│  │            │                                                 │     │
│  │  ┌─────────▼──────────────────────────────────────────────┐ │     │
│  │  │  Detection & Enforcement Pipeline (6 layers)            │ │     │
│  │  │                                                         │ │     │
│  │  │  L1. Regex Pattern Matching (165+ patterns)             │ │     │
│  │  │      25+ categories × 4 languages (EN/JA/KO/ZH)        │ │     │
│  │  │      + NFKC normalization + zero-width char removal     │ │     │
│  │  │      + space compression + Confusable normalization     │ │     │
│  │  │      + Emoji removal                                    │ │     │
│  │  │                                                         │ │     │
│  │  │  L2. Semantic Similarity Detection (56 phrases)         │ │     │
│  │  │      difflib + n-gram fuzzy matching                    │ │     │
│  │  │                                                         │ │     │
│  │  │  L3. Active Decoding                                    │ │     │
│  │  │      Base64/Hex/ROT13/URL/Unicode → decode → rescan    │ │     │
│  │  │                                                         │ │     │
│  │  │  L4. Capability-Based Access Control ★v1.2              │ │     │
│  │  │      CaMeL: control flow / data flow separation         │ │     │
│  │  │      Taint tracking + capability tokens + policy        │ │     │
│  │  │      enforcement                                        │ │     │
│  │  │                                                         │ │     │
│  │  │  L5. Atomic Execution Pipeline (AEP) ★v1.3              │ │     │
│  │  │      Scan → Execute → Vaporize (atomic execution)       │ │     │
│  │  │      Sandbox isolation + trace elimination              │ │     │
│  │  │                                                         │ │     │
│  │  │  L6. Safety Specification & Verifier ★v1.3.1            │ │     │
│  │  │      Declarative safety specs + proof certificate       │ │     │
│  │  │      verification                                       │ │     │
│  │  │      Built-in specs (no_exfil, no_exec, pii_guard, etc.)│ │     │
│  │  └─────────┬──────────────────────────────────────────────┘ │     │
│  │            │                                                 │     │
│  │  ┌─────────▼──────────────────────────────────────────────┐ │     │
│  │  │  Output Layer                                           │ │     │
│  │  │                                                         │ │     │
│  │  │  Activity Stream ─► Local + Global + Alert (3-tier log)│ │     │
│  │  │  Remediation Hints (with OWASP/CWE/MITRE references)   │ │     │
│  │  │  Compliance Report (OWASP/NIST/MITRE/CSA/AI Guidelines)│ │     │
│  │  │  Benchmark Report / Badge (shields.io)                 │ │     │
│  │  └────────────────────────────────────────────────────────┘ │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
aigis/
│
├── scanner.py              # Core detection engine
│   ├── scan()              #   User input scan
│   ├── scan_output()       #   LLM response scan
│   ├── scan_messages()     #   Multi-turn conversation scan (escalation detection)
│   ├── scan_rag_context()  #   RAG document scan
│   ├── scan_mcp_tool()     #   MCP tool definition scan
│   ├── scan_mcp_tools()    #   Batch scan for multiple MCP tools
│   ├── sanitize()          #   Automatic PII masking
│   ├── _normalize_text()   #   Normalization (NFKC + zero-width + space + Confusable + Emoji)
│   └── _run_patterns()     #   L1-L3: Sequential execution of pattern → similarity → decoding
│
├── decoders.py             # L3: Active decoding
│   ├── decode_base64_payloads()    #   Base64 detection & decoding
│   ├── decode_hex_payloads()       #   \xNN / 0xNNNN decoding
│   ├── decode_url_encoding()       #   %XX percent-encoding
│   ├── decode_rot13()              #   ROT13 (indicator-based text detection)
│   ├── normalize_confusables()     #   Cyrillic/Greek → Latin homoglyph conversion
│   ├── strip_emojis()              #   Emoji removal
│   └── decode_all()                #   Apply all decoders → return variant list
│
├── mcp_scanner.py          # ★v1.1 MCP server-level scanner
│   ├── scan_mcp_server()           #   Comprehensive analysis of entire server
│   ├── detect_rug_pull()           #   Rug pull detection via snapshot comparison
│   ├── analyze_permissions()       #   Permission scope analysis (4 axes)
│   ├── score_server_trust()        #   Trust score calculation (0-100)
│   ├── snapshot_tool()             #   Create tool definition snapshot
│   ├── save_snapshots() / load_snapshots()  # Snapshot persistence
│   ├── MCPToolSnapshot             #   Snapshot data class
│   ├── MCPServerReport             #   Server report data class
│   └── MCPDiffResult               #   Diff result data class
│
├── filters/
│   └── patterns.py         # All 165+ detection pattern definitions (25+ categories)
│       ├── PROMPT_INJECTION_PATTERNS        # EN 6 + JA 4 + KO 4 + ZH 4 = 18
│       ├── JAILBREAK_ROLEPLAY_PATTERNS      # 6
│       ├── MCP_SECURITY_PATTERNS            # 13
│       ├── INDIRECT_INJECTION_PATTERNS      # 5
│       ├── ENCODING_BYPASS_PATTERNS         # 8
│       ├── MEMORY_POISONING_PATTERNS        # 9
│       ├── SECOND_ORDER_INJECTION_PATTERNS  # 9
│       ├── SQL_INJECTION_PATTERNS           # 8
│       ├── COMMAND_INJECTION_PATTERNS       # 2
│       ├── DATA_EXFIL_PATTERNS              # 4
│       ├── PII_INPUT_PATTERNS               # JP + Intl + KO + ZH = 11+
│       ├── CONFIDENTIAL_DATA_PATTERNS       # 3
│       ├── PROMPT_LEAK_PATTERNS             # EN 6 + JA 2 = 8
│       ├── TOKEN_EXHAUSTION_PATTERNS        # 5
│       ├── HALLUCINATION_ACTION_PATTERNS    # 3
│       ├── SYNTHETIC_CONTENT_PATTERNS       # 4
│       ├── EMOTIONAL_MANIPULATION_PATTERNS  # 3
│       ├── OVER_RELIANCE_PATTERNS           # 3
│       ├── SANDBOX_ESCAPE_PATTERNS          # ★v1.2: 4
│       ├── SELF_PRIVILEGE_ESCALATION_PATTERNS # ★v1.2: 4
│       ├── COT_DECEPTION_PATTERNS           # ★v1.2: 3
│       ├── EVALUATION_GAMING_PATTERNS       # ★v1.2: 3
│       ├── AUDIT_TAMPERING_PATTERNS         # ★v1.2: 4
│       ├── AUTONOMOUS_EXPLOIT_PATTERNS      # ★v1.2: 5
│       └── OUTPUT_PATTERNS                  # 9 (SSN/CC/Email/Secret/Harmful/MyNumber/Phone, etc.)
│
├── similarity.py           # L2: Semantic similarity detection
│   ├── ATTACK_CORPUS       #   56 attack phrases (EN + JA + KO + ZH)
│   └── check_similarity()  #   difflib + n-gram fuzzy matching
│
├── capabilities/           # ★v1.2 L4: CaMeL capability-based access control
│   ├── __init__.py
│   ├── enforcer.py         #   Capability enforcement (permission check + policy application)
│   ├── policy_bridge.py    #   Bridge to existing policy engine
│   ├── store.py            #   Capability store (permission persistence)
│   ├── taint.py            #   Taint tracking (data flow contamination propagation)
│   └── tokens.py           #   Capability tokens (control flow / data flow separation)
│
├── aep/                    # ★v1.3 L5: Atomic Execution Pipeline
│   ├── __init__.py
│   ├── pipeline.py         #   Scan → Execute → Vaporize pipeline
│   ├── sandbox.py          #   Sandboxed isolated execution
│   └── vaporizer.py        #   Secure erasure of execution traces
│
├── safety/                 # ★v1.3.1 L6: Safety Specification & Verifier
│   ├── __init__.py
│   ├── spec.py             #   Declarative safety specification definition (SafetySpec)
│   ├── builtin_specs.py    #   Built-in specs (no_exfil, no_exec, pii_guard, etc.)
│   ├── loader.py           #   Load specs from YAML/JSON
│   └── verifier.py         #   Proof certificate verification (Guaranteed Safe AI compliant)
│
├── guard.py                # OOP API (Guard class)
│   ├── Guard               #   check_input() / check_output() / check_messages()
│   └── CheckResult         #   blocked / risk_level / reasons / remediation
│
├── benchmark.py            # Benchmark suite
│   ├── BenchmarkSuite      #   Accuracy benchmark (112 attacks + 26 safe inputs)
│   │   ├── run()           #     Per-category detection rate
│   │   ├── run_latency()   #     Latency measurement (Avg/P95/P99/throughput)
│   │   └── run_json()      #     JSON output
│   ├── LatencyResult       #   ★v1.1: to_markdown_report() / to_badge_json()
│   └── ATTACK_CORPUS       #   16-category attack corpus
│
├── redteam.py              # Red team suite
│   ├── RedTeamSuite        #   Template-based attack generation
│   │   ├── run()           #     Standard mode (9 categories)
│   │   └── run_adaptive()  #     ★v1.1: Adaptive mutation (up to N mutations → retry)
│   ├── MultiStepAttack     #   ★v1.1: Multi-step attack chains
│   ├── RedTeamReportGenerator  # ★v1.1: Markdown/HTML report generation
│   ├── make_http_check()   #   ★v1.1: HTTP endpoint testing
│   └── _adaptive_mutate()  #   ★v1.1: 5 mutation strategies (spacing/emoji/case/prefix/synonym)
│
├── activity.py             # Activity Stream (3-tier logging)
│   ├── ActivityStream      #   record() / query() / export_csv() / export_excel_summary()
│   └── rotate_logs()       #   Compress after 7 days, delete after 60 days
│
├── policy.py               # Policy engine (declarative YAML)
│   ├── load_policy()       #   YAML/JSON loader
│   └── evaluate()          #   Prefix-match rule evaluation → allow/deny/review
│
├── compliance.py           # Compliance mapping (AI Business Operator Guidelines v1.2: 37/37)
│
├── cli.py                  # CLI (aig command)
│   ├── aig scan            #   Text scan
│   ├── aig mcp             #   MCP tool scan
│   │   ├── --trust         #     ★v1.1: Display server trust score
│   │   ├── --diff          #     ★v1.1: Rug pull detection (snapshot comparison)
│   │   └── --server        #     ★v1.1: Specify server URL
│   ├── aig redteam         #   Red team
│   │   ├── --adaptive      #     ★v1.1: Adaptive mutation mode
│   │   ├── --report        #     ★v1.1: Vulnerability report generation
│   │   └── --target-url    #     ★v1.1: HTTP endpoint testing
│   ├── aig benchmark       #   Benchmark
│   │   ├── --latency       #     Latency measurement
│   │   ├── --report        #     ★v1.1: Markdown report generation
│   │   └── --badge         #     ★v1.1: shields.io badge JSON
│   ├── aig init            #   Project initialization
│   ├── aig logs            #   Activity Stream viewer
│   ├── aig policy          #   Policy management
│   ├── aig status          #   Governance overview
│   ├── aig report          #   Compliance report
│   ├── aig maintenance     #   Log rotation
│   └── aig doctor          #   Setup diagnostics
│
├── middleware/              # Framework integrations
│   ├── fastapi.py          #   FastAPI/Starlette middleware
│   ├── langchain.py        #   LangChain callback
│   ├── langgraph.py        #   LangGraph GuardNode
│   ├── anthropic_proxy.py  #   SecureAnthropic drop-in proxy
│   └── openai_proxy.py     #   SecureOpenAI drop-in proxy
│
├── adapters/
│   └── claude_code.py      #   Claude Code hooks integration (PreToolUse)
│
└── badge.py                #   "Secured by Aigis" badge (SVG)
```

## Detection Pipeline Details

The complete flow of how input text is processed through 6 layers:

```
Input Text
    │
    ▼
┌─── L1: Regex Pattern Matching ────────────────────────────────┐
│  ① Text Normalization (preprocessing)                          │
│     NFKC normalization → zero-width char removal → space       │
│     compression → Confusable normalization → Emoji removal     │
│  ② Sequential matching against 165+ patterns (25+ categories  │
│     × 4 languages)                                             │
│     Match → MatchedRule generation (rule_id, score_delta,      │
│     owasp_ref)                                                 │
│     Per-category score aggregation (cap: base_score × 2 /      │
│     category)                                                  │
└───────┬───────────────────────────────────────────────────────┘
        │ Normalized text + match results
        ▼
┌─── L2: Semantic Similarity ───────────────────────────────────┐
│  Similarity comparison against a dictionary of 56 attack       │
│  phrases                                                       │
│  Only targets categories not detected by L1 (prevents          │
│  double detection)                                             │
│  difflib.SequenceMatcher + n-gram for threshold evaluation    │
└───────┬───────────────────────────────────────────────────────┘
        │
        ▼
┌─── L3: Active Decoding ───────────────────────────────────────┐
│  Executes only when encoding indicators are detected           │
│  (minimizing performance impact)                               │
│                                                                 │
│  ① Base64 strings → base64.b64decode → text conversion        │
│  ② Hex (\xNN) → bytes.fromhex → text conversion              │
│  ③ ROT13 indicator-bearing text → codecs.decode(rot_13)       │
│  ④ URL (%XX) → urllib.parse.unquote                            │
│  ⑤ Unicode escapes → decode                                    │
│                                                                 │
│  Decoded results are rescanned through L1 → L2                 │
│  Only new matches are added (deduplication by rule_id)         │
│  "(decoded)" is appended to rule names for traceability        │
└───────┬────────────────────────────────────────────────────────┘
        │
        ▼
┌─── L4: Capability-Based Access Control ★v1.2 ─────────────────┐
│  CaMeL Architecture: separation of control flow and data flow  │
│                                                                 │
│  ① Taint Tracking (taint.py)                                   │
│     Assigns taint labels to external inputs (user/RAG/MCP)     │
│     Tracks contamination propagation across the entire data     │
│     flow                                                        │
│  ② Capability Tokens (tokens.py)                               │
│     Issues tokens for capabilities required by operations       │
│     Granular control: file:read, net:connect, exec:shell, etc. │
│  ③ Enforcement (enforcer.py)                                   │
│     Taint level × required permissions → allow/deny decision   │
│     Automatically blocks privileged operations by tainted data │
│                                                                 │
│  Reference: CaMeL (Debenedetti et al., 2025)                   │
└───────┬────────────────────────────────────────────────────────┘
        │
        ▼
┌─── L5: Atomic Execution Pipeline (AEP) ★v1.3 ─────────────────┐
│  Isolates tool execution in 3 atomic phases                     │
│                                                                 │
│  ① Scan — Pre-execution inspection of commands/arguments       │
│     via L1-L4                                                   │
│  ② Execute — Isolated execution within a sandbox (sandbox.py)  │
│     Runs in an environment with restricted filesystem/network  │
│  ③ Vaporize — Secure erasure of execution traces               │
│     (vaporizer.py)                                              │
│     Ensures removal of temporary files and in-memory           │
│     sensitive data                                              │
│                                                                 │
│  Reference: AEP / CIV (Scan-Execute-Vaporize pattern)          │
└───────┬────────────────────────────────────────────────────────┘
        │
        ▼
┌─── L6: Safety Specification & Verifier ★v1.3.1 ───────────────┐
│  Formal guarantees through declarative safety specifications    │
│                                                                 │
│  ① Safety Spec Definition (spec.py / builtin_specs.py)         │
│     no_exfil: Prohibit external data exfiltration              │
│     no_exec: Prohibit arbitrary code execution                 │
│     pii_guard: Prevent PII leakage                             │
│     Custom specs can also be defined in YAML/JSON (loader.py)  │
│  ② Verifier (verifier.py)                                      │
│     Verifies whether execution results satisfy the safety spec │
│     Issues proof certificates                                   │
│     On violation: blocks with reason + remediation guidance     │
│                                                                 │
│  Reference: Guaranteed Safe AI (Dalrymple et al., 2024)         │
└───────┬────────────────────────────────────────────────────────┘
        │
        ▼
┌─── Score Calculation ─────────────────────────────────────────┐
│  total = min(Σ category scores, 100)                           │
│  risk_level:                                                   │
│    0-30  → low (safe)                                          │
│    31-60 → medium (review required)                            │
│    61-80 → high (dangerous)                                    │
│    81+   → critical (auto-blocked)                             │
└───────┬───────────────────────────────────────────────────────┘
        │
        ▼
  ScanResult {
    risk_score, risk_level, matched_rules[],
    reason, is_safe, needs_review, is_blocked,
    remediation { primary_threat, owasp_refs, hints, action }
  }
```

## MCP Security Architecture

### 6 Attack Surfaces

```
MCP Server                                    Aigis Defense
┌──────────────────────┐
│ tools/list response   │
│                      │
│ ① Tool Description   │──▶ 14 MCP patterns + all input patterns
│    <IMPORTANT> tag    │    (scans the description field)
│                      │
│ ② Parameter Schema   │──▶ Recursive scan of
│    hidden descriptions│    inputSchema.properties name + description
│                      │
│ ③ Tool Output        │──▶ scan_output() to scan responses
│    re-injection       │    (output poisoning detection)
│    instructions       │
│                      │
│ ④ Cross-Tool Shadow  │──▶ mcp_cross_tool_shadow pattern
│    manipulating other │    (cross-tool interference detection)
│    tools              │
│                      │
│ ⑤ Rug Pull           │──▶ ★v1.1: Snapshot comparison
│    malicious changes  │    detect_rug_pull() + diff scan
│    to definitions     │
│                      │
│ ⑥ Sampling Hijack    │──▶ Detected by prompt injection patterns
│    context poisoning  │
└──────────────────────┘
```

### v1.1 MCP Server-Level Analysis

```
aig mcp --file tools.json --trust --diff
         │
         ▼
┌─── Per-Tool Scan ─────────────────┐
│  scan_mcp_tool(tool) × N           │
│  → ScanResult per tool             │
└─────────┬──────────────────────────┘
          │
          ▼
┌─── Permission Analysis ──────────┐
│  analyze_permissions(tool):        │
│    file_system  (read/write/del)   │
│    network      (http/fetch/send)  │
│    code_execution (exec/shell)     │
│    sensitive_data (creds/keys)     │
└─────────┬──────────────────────────┘
          │
          ▼
┌─── Rug Pull Detection ───────────┐
│  load_snapshots(previous)          │
│  detect_rug_pull(previous, current)│
│  → description changes + new       │
│    pattern detection                │
│  save_snapshots(current)           │
└─────────┬──────────────────────────┘
          │
          ▼
┌─── Trust Score Calculation ───────┐
│  score_server_trust():             │
│  100 - avg_risk - permission_pen   │
│    70-100: trusted                 │
│    40-69:  suspicious              │
│    0-39:   dangerous               │
└─────────┬──────────────────────────┘
          │
          ▼
  MCPServerReport {
    trust_score, trust_level,
    tool_results, permission_summaries,
    rug_pull_alerts
  }
```

## Agent Operation → Governance Decision Flow

```
1. Agent invokes a tool (e.g., Bash "rm -rf /")
       │
       ▼
2. Adapter intercepts
   ├── Claude Code hook: PreToolUse
   ├── FastAPI middleware: POST/PUT/PATCH
   ├── LangChain callback: on_llm_start
   ├── Anthropic/OpenAI Proxy: messages.create
   └── LangGraph GuardNode: pre-node execution
       │
       ▼
3. Construct ActivityEvent
   action: "shell:exec", target: "rm -rf /",
   user_id: "tanaka", agent_type: "claude_code"
       │
       ▼
4. Execute detection pipeline (L1→L2→L3→L4→L5→L6)
   → risk_score: 90, risk_level: "critical"
   → matched_rules: [cmdi_shell, ...]
       │
       ▼
5. Policy evaluation
   Load aigis-policy.yaml
   Prefix-match rule evaluation → decision: "deny"
       │
       ▼
6. Record to Activity Stream (all 3 tiers)
   Local:  .aigis/logs/2026-04-10.jsonl
   Global: ~/.aigis/global/2026-04-10.jsonl
   Alert:  ~/.aigis/alerts/2026-04-10.jsonl
       │
       ▼
7. Return decision to agent
   exit 0 → allow (tool execution proceeds)
   exit 2 → deny (tool blocked + reason + remediation guidance)
```

## Red Team Architecture

### Standard Mode vs. Adaptive Mode

```
Standard Mode (aig redteam)               Adaptive Mode (aig redteam --adaptive)
┌──────────────────┐                   ┌──────────────────┐
│ Template          │                   │ Template          │
│ generation        │                   │ generation        │
│ 9 categories × N │                   │ 9 categories × N │
└────────┬─────────┘                   └────────┬─────────┘
         │                                      │
         ▼                                      ▼
┌──────────────────┐                   ┌──────────────────┐
│ Scan execution    │                   │ Scan execution    │
│ blocked/bypassed │                   │ blocked/bypassed │
└────────┬─────────┘                   └────────┬─────────┘
         │                                      │ blocked?
         ▼                                      ▼
      Result                           ┌──────────────────┐
      aggregation                      │ Apply mutations   │
                                       │ (5 strategies)    │
                                       │ ① char spacing   │
                                       │ ② emoji insertion │
                                       │ ③ case mix       │
                                       │ ④ prefix/suffix  │
                                       │ ⑤ synonym replace │
                                       └────────┬─────────┘
                                                │
                                                ▼
                                       Rescan (up to N times)
                                                │
                                                ▼
                                       Final result aggregation
                                       + Markdown/HTML report
```

## Security Coverage

### 25+ Categories × Pattern Count

| # | Category | Patterns | Languages | OWASP LLM |
|---|---------|:----------:|:----:|-----------|
| 1 | Prompt Injection | 18 | EN/JA/KO/ZH | LLM01 |
| 2 | Jailbreak / Roleplay | 6 | EN | LLM01 |
| 3 | MCP Tool Poisoning | 13 | EN | LLM01 |
| 4 | Indirect Injection (RAG) | 5 | EN | LLM01 |
| 5 | Encoding Bypass | 8 | EN | LLM01 |
| 6 | Memory Poisoning | 9 | EN/JA/KO/ZH | LLM01 |
| 7 | Second-Order Injection | 9 | EN/JA/KO/ZH | LLM01 |
| 8 | System Prompt Leak | 8 | EN/JA | LLM07 |
| 9 | SQL Injection | 8 | EN | — |
| 10 | Command Injection | 2 | EN | — |
| 11 | Data Exfiltration | 4 | EN | LLM06 |
| 12 | PII Detection (Input) | 11+ | JP/Intl/KO/ZH | LLM02 |
| 13 | Confidential Data | 3 | EN/JA | LLM02 |
| 14 | Token Exhaustion | 5 | EN | LLM10 |
| 15 | Hallucination Action | 3 | EN/JA | — |
| 16 | Synthetic Content | 4 | EN/JA | — |
| 17 | Emotional Manipulation | 3 | EN/JA | — |
| 18 | Over-Reliance | 3 | EN/JA | — |
| 19 | Sandbox Escape ★v1.2 | 4 | EN | LLM01 |
| 20 | Self-Privilege Escalation ★v1.2 | 4 | EN | LLM01 |
| 21 | CoT Deception ★v1.2 | 3 | EN | — |
| 22 | Evaluation Gaming ★v1.2 | 3 | EN | — |
| 23 | Audit Tampering ★v1.2 | 4 | EN | LLM09 |
| 24 | Autonomous Exploit ★v1.2 | 5 | EN | LLM01 |
| — | **Output Safety** | **9** | EN/JA | LLM02/LLM05 |
| | **Total** | **165+** | | |

### Framework Coverage

| Framework | Coverage |
|-------------|-----------|
| OWASP LLM Top 10 (2025) | 8/10 risks (LLM03 Supply Chain and LLM09 Misinformation are out of scope) |
| NIST AI RMF 1.0 | 4/4 functions (Govern, Map, Measure, Manage) |
| MITRE ATLAS | 40/67 techniques (remaining 27 are infrastructure/pre-attack stages) |
| CSA STAR for AI | 8/10 domains (AI Model Dev and Fairness are N/A) |
| AI Business Operator Guidelines v1.2 | 37/37 requirements (100%) |

## Log Architecture (3 Tiers)

```
Per-project (accessible by users):
  .aigis/
  ├── logs/
  │   ├── 2026-04-10.jsonl        ← Today's events
  │   ├── 2026-03-31.jsonl.gz     ← Compressed (after 7 days)
  │   └── ...                      ← Auto-deleted after 60 days
  └── mcp_snapshots/               ← ★v1.1: MCP snapshot storage
      └── mcp_<server_hash>.json

Global (CISO/audit, cross-project):
  ~/.aigis/
  ├── global/
  │   └── 2026-04-10.jsonl        ← Aggregated from all projects
  └── alerts/
      └── 2026-04-10.jsonl        ← Block/review only (permanent retention)
```

## AGI-Ready Schema

ActivityEvent includes fields designed for future governance extensions.

| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| `autonomy_level` | int (1-5) | Agent autonomy level scale | Schema defined |
| `delegation_chain` | list[str] | Inter-agent delegation tracking | Schema defined |
| `estimated_cost` | float | API/compute cost governance | Schema defined |
| `memory_scope` | str | Knowledge boundary enforcement | Schema defined |
| `suggested_fix` | str | AI-proposed safe alternative action | Schema defined |
| `fix_applied` | bool | Whether auto-fix was applied | Schema defined |

## Security Design Principles

1. **Zero External Dependencies** — Uses only the Python standard library (eliminates supply chain risk)
2. **Default Allow** — Does not block the agent on hook errors (graceful degradation)
3. **Append-Only Logging** — Append only to JSONL files; no update or delete operations
4. **Policy as Code** — YAML managed in git for version control and auditing
5. **Agent Agnostic** — Supports any agent through the adapter pattern
6. **Detection + Remediation** — Every block includes OWASP references and remediation guidance
7. **Defense in Depth** — 6-layer detection and defense (pattern → similarity → decoding → capability → AEP → safety spec) making evasion extremely difficult
8. **Formal Safety Guarantees** — Declarative specifications and proof certificate verification via Safety Specification provide not just detection but formal safety assurance

## Academic Paper References

The architecture layers introduced in v1.2 and later are based on the following academic research.

| Layer | Paper | Authors | Summary |
|----|------|------|------|
| L4 | **CaMeL: Design and Evaluation of a Capability-Based Agent Security Framework** | Debenedetti et al., 2025 | A framework that separates LLM agent control flow (trusted) from data flow (untrusted), defending against prompt injection through taint tracking and capability tokens |
| L5 | **Atomic Execution Pipeline (AEP)** | — | A pattern that isolates tool execution in 3 atomic phases — Scan → Execute → Vaporize — and securely erases execution traces |
| L5 | **CIV: Confidentiality, Integrity, and Vaporization** | — | An execution model that guarantees secure processing and erasure of sensitive data |
| L6 | **Guaranteed Safe AI** | Dalrymple et al., 2024 | A framework that guarantees AI system safety through declarative specifications (Safety Specification) and formal verification (Proof Certificate). A tripartite architecture of World Model + Safety Spec + Verifier |
