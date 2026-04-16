# Aigis — Roadmap from OSS to Monetization

> Last updated: 2026-04-10
> Strategy: Build trust with OSS -> Monetize with SaaS -> Scale with Enterprise

---

## Vision

**"A world where every AI agent has a security layer as a matter of course."**

Gartner predicts that "Guardian Agent" technology will account for 10-15% of the Agentic AI market by 2030.
Aigis serves as the OSS version, providing a governance foundation that developers and enterprises can control themselves.

---

## Revenue Model (Projected)

```
OSS Core (free, forever)
  -> Community trust, stars, downloads, awareness
      -> Cloud Pro ($49/mo+)
          -> Enterprise (custom quotes, $500/mo+)
```

| Tier | Target | Price | Key Features |
|------|--------|-------|-------------|
| **OSS Free** | Individuals & startups | Free | Guard class, 165+ patterns, CLI, MCP Scanner, Red Team, Capabilities, AEP, Safety Verification |
| **Cloud Pro** | Small teams (2-20) | $49/mo | Web dashboard, Slack notifications, monthly reports |
| **Business** | Mid-size companies (20-200) | $299/mo | Multi-tenant, SSO, SLA, custom policies |
| **Enterprise** | Large enterprises, finance, healthcare | Custom | On-premises, LDAP, audit compliance, dedicated support |

---

## Phase 0: Seeding (through 2026-04-12) -- Phase 1 started early

**Goal**: First 50 stars, 100 PyPI DL/day, early community growth

### Marketing
- [x] HN: replied to existing threads (switched from Show HN -> replies due to new account posting limits)
- [x] Zenn article published (MCP trust model article was too shallow and withdrawn -> replaced with a different article)
- [x] Reddit r/Python, r/netsec, r/MachineLearning posts
- [x] DEV.to English article published
- [ ] Submit PRs to awesome lists (3 lists)

### Product
- [x] PyPI v0.7.0 release (v0.4.0 -> v0.5.0 -> v0.6.0 -> v0.6.1 -> v0.7.0)
- [x] GitHub Discussions enabled
- [x] Created 3 good-first-issues
- [x] Gandalf Challenge verified & debugged (levels.py syntax fix, all 7 levels working)

### KPI Targets
| Metric | Current | 2-Week Target |
|--------|---------|---------------|
| GitHub Stars | 4 | 50 |
| PyPI DL/month | Unknown | 500 |
| Zenn/Qiita total likes | Tracking | 100 |

---

## Phase 1: Ignition (2026-04-12 through 2026-05-31)

**Goal**: 300 stars, 1,000 PyPI DL/month, first external contributor

### Marketing
- [ ] Maintain weekly article pace on Qiita/Zenn
- [ ] Maintain 3-5 posts/week pace on Twitter/X
- [ ] **Product Hunt Launch (planned for Wednesday 5/13)** <- Details in `content/product_hunt_strategy.md`
  - Note: Coming Soon pages were discontinued (August 2025). Using Maker trust building + external channels instead
  - [x] Phase A: Create PH account & Product Draft, daily commenting activity (through 4/20) <- Account & Draft done (4/7), commenting ongoing
  - [ ] Phase B: External channel seeding & acquire 50-100 supporters (4/14-4/28)
  - [x] Gallery images x5 EN/JA (10 PNGs) + CLI demo GIFs EN/JA + new icon (4/16 done)
  - [ ] OG image PNG (derive from gallery_1_hero)
  - [ ] Final launch copy review & supporter pre-notification (by 4/28)
  - [ ] LP improvements & upload all assets to PH (by 5/5)
  - [ ] Go/NoGo decision (5/5) -> if criteria not met, postpone to 5/20 or 5/27
  - [ ] Launch execution 12:01 AM PT & phased SNS rollout (5/13)
- [ ] 5-minute lightning talk at AI meetup
- [ ] Share in LangChain/LlamaIndex Discord
- [x] ~~All Japan AI Hackathon 2026 (4/25)~~ -> Not participating (cancelled)

### Product
- [x] Anthropic SDK integration (Issue #3) <- v0.5.0 complete
- [x] Policy Template Hub published (industry-specific YAML policies) <- v0.5.0 complete
- [x] "Secured by Aigis" badge created (for adopters to put in their README) <- Done
- [x] VS Code extension prototype (run aig scan from the editor) <- v0.6.0 complete
- [x] **LangGraph GuardNode** integration <- v0.6.2 added (Phase 1 early implementation)
- [x] **Benchmark 100% accuracy achieved** (53/53 attacks, 0% false positive) <- v0.6.1
- [x] **Korean & Chinese patterns added** (Issue #7) <- v0.8.1
- [x] **Indirect injection detection** (Issue #6: RAG/web scraping) <- v0.8.1
- [x] **Compliance documentation created** (OWASP/NIST/MITRE/CSA) <- v0.8.1
- [x] **Full compliance with Japan AI Business Operator Guidelines v1.2** (37/37 requirements) <- v0.8.2
- [x] **MCP Security Scanner enhanced** (`aig mcp --trust --diff`) -- rug pull detection, permission analysis, server trust score, snapshot management <- v1.1.0
- [x] **Latency benchmarks published** -- Markdown report generation, shields.io badges, competitor comparison table <- v1.1.0
- [x] **Base64/Unicode/Emoji obfuscation detection enhanced** -- actual decoding + re-scanning, Cyrillic/Greek confusable normalization, emoji removal <- v1.1.0
- [x] **Capability-based access control** -- CapabilityStore, CapabilityEnforcer, TaintTracking, principle of least privilege <- v1.3.0
- [x] **Atomic Execution Pipeline (AEP)** -- sandbox execution, side effect rollback (Vaporizer), timeout control <- v1.3.0
- [x] **Formal safety verification** -- SafetyVerifier, SafetySpec (YAML definition), invariant verification, ProofCertificate <- v1.3.0
- [x] **`Guard.authorize_tool()`** -- unified entry point for capabilities + safety verification + AEP <- v1.3.0
- [x] **165+ patterns reached** -- detection patterns expanded from 137 to 165+ <- v1.3.1

### KPI Targets
| Metric | Target |
|--------|--------|
| GitHub Stars | 300 |
| PyPI DL/month | 1,000 |
| External PRs | 3+ |
| Discussions posts | 10+ |

---

## Phase 2: Growth (2026-06-01 through 2026-08-31)

**Goal**: 1,000 stars, 5,000 PyPI DL/month, SaaS beta release, first revenue

### Marketing
- [x] ~~Product Hunt Launch~~ -> Moved up to Phase 1 (5/13 launch planned)
- [ ] Lablab.ai x Anthropic Hackathon (5/26-6/2) participation
- [ ] DevNetwork Hackathon (5/11-28) participation
- [ ] Create 1 enterprise adoption case study (own company or acquaintance's company)
- [ ] AI Security Conference talk ("How I built an OSS as a solo developer")

### Product (SaaS Beta)
- [x] **Cloud Dashboard beta**: Log visualization, billing page, usage meter, PlanGate
- [x] **Stripe payment integration**: Free/Pro/Business/Enterprise plans, 6 webhooks implemented, plan control middleware
- [x] **Team management**: Member list, invitations, role settings, plan limit controls
- [x] **Slack notifications**: High-risk detection webhook notifications (Block Kit messages, Settings UI, notification settings API)
- [ ] Email list -> beta invitation flow setup
- [x] **Automated red teaming enhanced** (`aig redteam --adaptive`) -- adaptive mutations, multi-step attack chains, Markdown/HTML report generation, HTTP endpoint testing <- v1.1.0 (Phase 1 early implementation)
- [x] **Memory poisoning detection enhanced** -- 9 patterns (cross-session, gradual drift, tool permission override, EN/JA/KO/ZH) <- v1.1.0 (Phase 1 early implementation)
- [x] **Second-order injection detection enhanced** -- 9 patterns (tool chain, response craft, shared context, EN/JA/KO/ZH) <- v1.1.0 (Phase 1 early implementation)

### KPI Targets
| Metric | Target |
|--------|--------|
| GitHub Stars | 1,000 |
| PyPI DL/month | 5,000 |
| SaaS beta signups | 100 |
| MRR | First revenue ($1-$500) |

---

## Phase 3: Monetization (2026-09-01 through 2026-12-31)

**Goal**: MRR $1,000+, 3 enterprise adoptions, sustainable development structure

### Marketing
- [ ] Launch "Powered by Aigis" logo program
- [ ] PR to Nikkei xTECH / IT Leaders (targeting IT department media)
- [ ] ISACA conference exhibition & talk
- [ ] Host enterprise webinars

### Product (Enterprise Features)
- [ ] **On-premises installer** (Docker Compose one-command deploy)
- [ ] **LDAP/SSO integration** (Okta, Azure AD)
- [ ] **Automated compliance report generation** (Japan AI Business Operator GL, ISO27001)
- [ ] **Multi-tenant enhancements**: Per-tenant policies and usage management
- [ ] **SLA-backed support** (Pro: 24h, Enterprise: 4h)
- [ ] **Lightweight ML classifier (optional)** -- BERT-based injection detection as optional dependency. Zero-dependency core maintained
- [ ] **SIEM integration** (Splunk/Datadog/Azure Sentinel) -- integration into existing enterprise infrastructure

### KPI Targets
| Metric | Target |
|--------|--------|
| MRR | $1,000 |
| Paying customers | 20 |
| GitHub Stars | 3,000 |
| PyPI DL/month | 10,000 |
| Enterprise adoptions | 3 |

---

## Phase 4: Scale (2027-01 onwards)

**Goal**: MRR $10,000+, consider fundraising, team expansion

- [ ] Consider Series A / angel funding
- [ ] Hire full-time developer (from OSS contributors)
- [ ] AWS/GCP/Azure Marketplace listing
- [ ] Apply to GENIAC-PRIZE
- [ ] International expansion (US, EU)

---

## Competitive Differentiation

| Axis | Aigis | Guardrails AI | NeMo Guardrails | llm-guard | Cisco AI Defense |
|----|-------------|---------------|-----------------|-----------|-----------------|
| Installation | `pip install aigis` (one line) | Complex | Complex | Somewhat complex (ML) | SDK dependency |
| Dependencies | **Zero** (stdlib only) | Many | NVIDIA required | Many (ML) | Cisco required |
| Price | **Free OSS** | OSS (partially paid) | Free | OSS | Paid |
| Japanese support | **Native** (JA/KO/ZH) | None | None | None | None |
| MCP security | **Supported (only one)** | None | None | None | None |
| Japan AI Guidelines v1.2 | **37/37 full compliance** | None | None | None | None |
| Compliance | OWASP/NIST/MITRE/CSA | None | None | Partial | SOC 2 |
| Remediation | **Yes** (explains how to fix) | None | None | None | None |

### Market Trends (April 2026)
- **Most independent competitors acquired by large companies**: Lakera->Check Point($300M), Prompt Security->SentinelOne(~$250M), Pangea->CrowdStrike($260M), CalypsoAI->F5($180M), Promptfoo->OpenAI
- **Emerging OSS threats**: Meta LlamaFirewall (3-layer defense), Cisco DefenseClaw (Zero Trust)
- **Market size**: AI security tools market estimated at $8.2B in 2026
- **Aigis's opportunity**: Drastic decrease in independent OSS options -> growing demand for OSS to avoid vendor lock-in

### vs. Runtime/Governance Competitors

| Feature | aigis (Current) | aigis (Planned) | MS Agent Governance | Lasso Security |
|---------|----------------------|----------------------|---------------------|----------------|
| Pattern detection | 165+ | 165+ | ✅ | ✅ |
| Capability control | ✅ CaMeL | ✅ | ✅ | — |
| Atomic execution | ✅ AEP | ✅ | — | — |
| Safety spec + verifier | ✅ | ✅ | — | — |
| Runtime behavior monitoring | — | Phase 1 | ✅ | ✅ |
| Intent drift detection | — | Phase 1 | — | ✅ |
| Memory poisoning defense | — | Phase 2 | — | — |
| Multi-agent monitoring | — | Phase 2 | ✅ | — |
| Policy DSL | — | Phase 3 | — | — |
| Cryptographic audit | — | Phase 3 | — | — |
| Zero dependencies | ✅ | ✅ | ❌ | ❌ |

---

## Technical Implementation Roadmap

> Business phases (Phase 0-4 above) と並行して進める技術ロードマップ。
> 現在の aigis は「門番」（入口でチェック）だが、企業が本当に必要としているのは「監視カメラ」（ずっと見張る）。

### Tech Phase 1: Runtime Monitoring (A + E) — Highest enterprise value

```
aigis/
└── monitor/
    ├── tracker.py         # エージェント行動の軌跡記録           [✅ 実装済]
    ├── drift.py           # インテントドリフト検知（ゴール乖離度スコア）  [ ] TODO
    ├── baseline.py        # 行動ベースライン構築（正常パターン学習）   [✅ 実装済]
    ├── anomaly.py         # 異常検知（ベースラインからの逸脱）       [ ] TODO
    └── containment.py     # 段階的封じ込め（warn→throttle→restrict→isolate→stop） [ ] TODO
```

**検知対象:**
- [ ] ツール呼び出し頻度の急変（通常は1分に2回 → 突然20回）
- [ ] アクセスパターンの変化（通常は docs/ のみ → 突然 .ssh/ にアクセス）
- [ ] エスカレーションパターン（file:read → file:write → shell:exec と権限が段階的に上昇）
- [ ] 外部通信の異常（通常は内部APIのみ → 突然外部URLにPOST）

### Tech Phase 2: Memory Defense + Multi-Agent (B + C)

```
aigis/
├── memory/
│   ├── scanner.py         # メモリストアのスキャン（読み出し時検証）   [✅ 実装済]
│   ├── rotation.py        # メモリローテーション（TTL付き記憶管理）   [ ] TODO
│   └── integrity.py       # メモリ整合性チェック（ポイズニング検知）   [✅ 実装済]
└── multi_agent/
    ├── message_scanner.py # エージェント間メッセージのスキャン       [ ] TODO
    ├── topology.py        # エージェント通信トポロジー監視          [ ] TODO
    └── consensus.py       # 協調行動の異常検知                    [ ] TODO
```

### Tech Phase 3: Policy DSL + Cryptographic Audit (D + F)

```
aigis/
├── spec_lang/
│   ├── parser.py          # AgentSpec風DSLパーサー               [ ] TODO
│   ├── evaluator.py       # ランタイム評価エンジン                [ ] TODO
│   └── stdlib.py          # 組み込み述語（file_exists, is_sensitive等） [ ] TODO
└── audit/
    ├── signed_log.py      # HMAC署名付きログエントリ              [ ] TODO
    ├── chain.py           # ハッシュチェーン（前のエントリのハッシュを含む） [ ] TODO
    └── verify.py          # ログ完全性検証                       [ ] TODO
```

### Tech Phase 4: Supply Chain + Cross-Session (G + H)

```
aigis/
├── supply_chain/
│   ├── hash_pin.py        # MCPツール定義のハッシュ固定            [ ] TODO
│   ├── sbom.py            # AI依存のSBOM生成                     [ ] TODO
│   └── verify.py          # 依存パッケージ署名検証                [ ] TODO
└── cross_session/
    ├── store.py           # セッション横断イベントストア           [ ] TODO
    ├── correlator.py      # クロスセッション相関分析              [ ] TODO
    └── sleeper.py         # スリーパー攻撃検知（時限発動パターン）  [ ] TODO
```

---

## Revenue Simulation (Conservative)

| Period | Pro ($49/mo) | Business ($299/mo) | MRR | ARR |
|--------|-------------|-------------------|-----|-----|
| 2026-08 (beta) | 5 customers | 0 customers | $245 | $2,940 |
| 2026-12 | 15 customers | 3 customers | $1,632 | $19,584 |
| 2027-06 | 50 customers | 15 customers | $6,935 | $83,220 |
| 2027-12 | 100 customers | 40 customers | $16,860 | $202,320 |

> The Japanese market has many SMBs, and $49/mo is about "one lunch per month." Decision-making is fast.
> A single enterprise customer equals the revenue of 20 Pro customers. Prioritize IT department acquisition channels.

---

## Immediate Action Items (Prioritized)

> Last updated: 2026-04-16

### Completed (Phase 0)
1. ~~HN reply post~~ Done (switched Show HN -> replies)
2. ~~Zenn article published~~ Done (replaced with alternative article)
3. ~~Reddit 3 posts~~ Posted
4. ~~DEV.to English article published~~ Posted
5. ~~Gandalf Challenge verification~~ Fixed
6. ~~v0.7.0 release~~ 2026-03-31
7. ~~**PH account creation & Product Draft registration** (by 4/8)~~ Done (4/7)
8. ~~**Gallery images x10 (EN/JA) + CLI demo GIFs x2 (EN/JA) + new icon**~~ Done (4/16)
9. ~~**README branding overhaul** — icon, GIF, architecture/compliance/integrations/dashboard images embedded~~ Done (4/16)

### Now (This Week 4/16 onwards)
10. **OG image PNG** — derive from gallery_1_hero_en for PH & SNS sharing
11. **Daily 2-3 PH comments** (ongoing, target: 20+ by 4/20)
12. **Awesome list PR submissions** (3 lists) — drafts in `content/awesome_list_pr_drafts.md`

### This Month (4/16 - 4/30)
13. **External channel seeding & acquire 50-100 supporters** (4/14-4/28)
14. **Final launch copy review & supporter pre-notification** (by 4/28)
15. Qiita/Zenn weekly article pace (aim for 3 articles before PH launch) — 4 drafts ready in `content/articles/`

### Next Month (5/1 - 5/13 Launch)
16. **LP improvements & upload all assets to PH** (by 5/5)
17. **Go/NoGo decision** (5/5) -> if criteria not met, postpone to 5/20 or 5/27
18. **Product Hunt Launch 12:01 AM PT** (5/13 Wed)

### Backlog
19. AI meetup LT talk application
20. Share in LangChain/LlamaIndex Discord
21. Email list -> beta invitation flow setup

---

---

## Automated Development Loop (Research -> Dev -> Content)

Starting 2026-04-03, Aigis is continuously strengthened through the following semi-automated loop.

```
Monday 09:00 JST — Research Scout    -> content/research_backlog/
Wednesday 09:00 JST — Feature Dev    -> pattern addition, tests, CHANGELOG
Friday 09:00 JST — Content Writer    -> content/articles/ drafts + content/ph_comments/ PH comments
Human Review      — review articles, publish, post PH comments, SNS outreach
```

| Trigger Name | Trigger ID | Schedule | Output |
|-------------|-----------|----------|--------|
| `aig-research-scout` | `trig_017oPfYD5zp4hy25sYM1gPvw` | Every Monday 00:00 UTC | content/research_backlog/ |
| `aig-feature-dev` | `trig_01DhcJ8X6TLdJrGD8V4bX6M2` | Every Wednesday 00:00 UTC | Pattern additions, tests |
| `aig-content-writer` | `trig_01Tqos8yAwkigrH4DiXaxsz4` | Every Friday 00:00 UTC | content/articles/ + content/ph_comments/ |

Details: [docs/DEV_LOOP.md](docs/DEV_LOOP.md)

### KPIs
| Metric | Target |
|--------|--------|
| Weekly research execution rate | 90%+ |
| Monthly new patterns added | 4-8 |
| Monthly articles published | 2-4 |
| Benchmark accuracy maintenance | 100% |

---

*This roadmap is reviewed monthly. Phases may be moved up or pushed back based on KPI performance.*
