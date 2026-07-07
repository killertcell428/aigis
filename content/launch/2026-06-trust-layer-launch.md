# Aigis Trust Layer Launch Playbook — June 2026

Working document for the maintainer. All copy below is paste-ready.
Do not commit this file publicly until after D-Day.

---

## 1. Launch thesis & success metrics

**Thesis:** Engineers want Claude Code at work. IT/security teams are the bottleneck. Aigis is the first open-source tool that generates a bilingual compliance-ready approval package directly from live config — making the IT approval process tractable, not just the security itself stronger.

The "trust layer" framing is accurate and distinct: not a guardrail-only tool (like the now-acquired promptfoo/Invariant/Lakera), but the full approval workflow artifact + runtime enforcement + tamper-evident audit, independent and staying that way.

**Primary metrics (launch week = D through D+7)**

| Metric | Start | D+7 target | Q3 2026 target |
|--------|-------|-----------|----------------|
| GitHub stars | 46 | 300 | 1,000 |
| PyPI weekly downloads | baseline | +50% | track weekly |
| awesome-claude-code PR | — | merged | merged |

**Secondary metrics**

- Zenn: 500+ views, 30+ likes within 7 days of publish
- dev.to: 200+ reactions, top weekly tag on `#claudecode`
- HN front page: ≥50 points (triggers organic amplification)
- GitHub Discussions: ≥5 inbound threads from new users
- Inbound issues tagged `adoption` or `trust-pack`: ≥3

---

## 2. Pre-launch checklist (D-7 through D-1)

**D-7: Code & docs**
- [ ] Merge this PR to master (per CLAUDE.md: merge first, tag second)
- [ ] Cut release per CLAUDE.md release rules:
  1. Land `release: vX.Y.0` commit on master via PR merge
  2. Run `uv run pytest --tb=no -q 2>&1 | tail -3` — capture actual numbers
  3. Create and push tag `vX.Y.0` against the master commit only
- [ ] Confirm `docs/adoption/README.md` is complete and linked from main README
- [ ] Confirm `docs/trust-pack.md` is linked from README and adoption guide
- [ ] Verify `aigis trust-pack --lang both --format html` runs end-to-end cleanly
- [ ] Verify `aigis audit verify` works on a fresh install
- [ ] Verify `aigis mcp --trust --diff` works with a sample MCP config

**D-5: Repository metadata**

Set GitHub repo description to exactly (140 chars including spaces):
```
Open-source trust layer for Claude Code & AI agents — IT-approval pack, tamper-evident audit logs, PreToolUse hooks, SIEM forwarders.
```

Set repository topics to (≤20, final list):
```
claude-code, claude, aigis, ai-security, ai-governance, llm-security,
audit-log, devsecops, mcp-security, prompt-injection, owasp-llm,
nist-ai-rmf, iso27001, openssf, python, zero-dependencies, siem,
enterprise-ai, agent-security, open-source
```

**D-5: README pin**
- [ ] Add "→ Bring Claude Code to your company: [docs/adoption/](docs/adoption/)" as a pinned entry in the README quick-links section (do not bury it)
- [ ] Add OpenSSF badges if not already present (CI, Best Practices, Scorecard)

**D-4: Demo GIF**

Record `aigis-trust-pack-demo.gif` using this script:

```bash
# Terminal recording script (use asciinema or ttyrec + agg)
# Suggested terminal: 100x30, clear background, 14pt monospace

# 1. Show clean starting state
ls -la aigis-trust-pack/ 2>/dev/null || echo "(no pack yet)"

# 2. Install (pre-record this part or show cached)
pip install 'pyaigis[all]'

# 3. Init with enterprise policy
aigis init --agent claude-code --policy enterprise

# 4. Generate trust pack (the money shot)
aigis trust-pack --lang both --format html

# 5. Show what was generated
ls aigis-trust-pack/
head -20 aigis-trust-pack/executive-summary.ja.md
```

Target: ≤90 seconds, focus on the `trust-pack` generation and the file listing. Upload to `images/aigis-trust-pack-demo.gif` and embed in README.

**D-3: GitHub Discussions**

Enable Discussions on the repo. Create a "Welcome / 使い方を共有する" pinned post:

```markdown
# Welcome to Aigis Discussions 👋

Thanks for being here. This is the place to:
- Share how you're using Aigis to get Claude Code approved at your company
- Ask questions about the `aigis trust-pack` adoption workflow
- Discuss policy configurations, SIEM integrations, and MCP security

**Quick links:**
- [Adoption guide](docs/adoption/) — bringing Claude Code through IT review
- [trust-pack docs](docs/trust-pack.md) — what gets generated and why
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute

If you used Aigis to get AI tooling approved internally, we'd especially love to hear your story — it helps other engineers in the same situation.
```

**D-1: Staging check**
- [ ] Zenn article frontmatter ready (published: false → will flip to true on D-Day morning JST)
- [ ] dev.to draft saved with correct canonical URL pointing to Zenn
- [ ] X threads drafted and saved as notes
- [ ] HN post text finalized (see Section 4)
- [ ] Awesome-list PR ready to submit (see Section 5)

---

## 3. D-Day sequence (recommend a Tuesday)

**Why Tuesday:** HN is most active Tuesday–Thursday. Zenn Japanese audience peaks weekday mornings JST. US audience is reachable Tuesday evening JST = Tuesday morning ET.

**Timed order:**

| Time (JST) | Action |
|------------|--------|
| 08:00 | Flip Zenn article `published: true`, push to GitHub |
| 08:15 | Post X Japanese thread (link to Zenn) |
| 08:30 | Submit awesome-claude-code PR (hesreallyhim/awesome-claude-code) |
| 12:00 | Check Zenn engagement; reply to any early comments |
| 20:00 | Publish dev.to post |
| 20:15 | Post X English thread (link to dev.to) |
| 22:00–23:00 | Submit Show HN (targets US Tue morning ET = 08:00–09:00 ET = 21:00–22:00 JST next day) |

**Note on Show HN timing:** HN front page peaks activity Tuesday–Wednesday ~09:00–11:00 ET. Submit at 21:00–22:00 JST the night before (Mon night JST = Tue morning ET). Watch for the first 30 minutes — be ready to respond to comments immediately.

---

## 4. Show HN post

**Title (78 chars):**
```
Show HN: Aigis – open-source audit layer that gets Claude Code past corporate IT
```

**First comment (post this yourself immediately after submission, ~220 words):**

```
Hi HN — I'm the author.

The problem I kept running into: engineers want Claude Code at work, but 
IT security reviews block it because there's no pre-packaged way to answer 
standard questions — what can it execute, where do the logs go, is there 
tamper evidence, which frameworks does it map to?

Aigis answers that with two things:

1. `aigis trust-pack` — one command generates a bilingual (EN/JA) IT-approval 
   package from your live config: exec summary, control matrix mapped to 
   ISO 27001 / NIST AI RMF / OWASP LLM Top 10 / Japan METI guidelines, 
   policy snapshot, audit-log spec, incident runbook, rollout plan. 
   The [TO FILL] fields are intentional — Aigis generates evidence, not 
   organizational decisions.

2. HMAC + hash-chain signed audit logs via Claude Code PreToolUse hooks. 
   `aigis audit verify` detects any modification. There's a specific gap 
   in Claude Code Team/Enterprise: OTel export is telemetry-grade, not 
   audit-grade. This fills it.

Everything is deterministic — no API calls, zero external dependencies, 
$0 marginal cost, 1731 tests. Apache-2.0.

The independent-OSS point matters: Protect AI, Invariant's mcp-scan, Lakera, 
and promptfoo were all acquired in the last year. Aigis stays independent.

Happy to answer questions about the control model, the hash-chain design, 
or why I structured the trust-pack the way I did.
```

**HN etiquette notes:**
- No "please upvote" or "share if useful" — instant credibility damage
- Reply to every comment within 30 minutes while active, within 2 hours otherwise
- If a commenter raises a legitimate technical objection, engage seriously and update docs if warranted — this is visible and builds credibility
- If the post is flagged or dies, do not resubmit the same day. See Section 9 for retry rules.
- Do not share the HN link anywhere until after it is live — brigading kills posts

---

## 5. Awesome-list & directory submissions

Submit these in order. PRs first, then directories.

### hesreallyhim/awesome-claude-code (primary target, ~46K stars)

Find the "Security & Hooks" or "Enterprise / Governance" section. If neither exists, add under a new "Security & Governance" section.

**PR one-liner:**
```markdown
- [Aigis](https://github.com/killertcell428/aigis) - Open-source trust layer: PreToolUse hooks + tamper-evident audit logs + `trust-pack` IT-approval document generator. ISO 27001 / NIST AI RMF / OWASP LLM Top 10 mapped. Zero dependencies.
```

**PR title:** `Add Aigis - open-source audit/governance layer for Claude Code`

**PR body:**
```markdown
Aigis is an open-source trust layer for Claude Code deployments:

- `aigis init --agent claude-code --policy enterprise` — installs PreToolUse hooks that scan tool calls before execution
- `aigis trust-pack` — generates bilingual (EN/JA) IT-approval document pack from live config, mapped to ISO 27001, NIST AI RMF, OWASP LLM Top 10, and Japan METI AI guidelines
- `aigis audit verify` — tamper-detection on HMAC+hash-chain signed audit logs
- `aigis mcp --trust --diff` — MCP tool-poisoning and rug-pull scanner

Apache-2.0, zero dependencies, deterministic (no API calls). 1731 tests.

Fits best in a Security / Governance / Enterprise section.
```

### rohitg00/awesome-claude-code-toolkit

Same one-liner as above. Check their formatting conventions first (some lists use different bracket styles).

### awesome-mcp-servers (security tools section)

```markdown
- [Aigis MCP Scanner](https://github.com/killertcell428/aigis) - Scans MCP tool definitions for poisoning attacks, rug-pull changes, and trust scoring. Snapshot-based diff detection.
```

### claudemarketplaces.com

Submit via their submission form or PR if they have a repo. Category: "Security & Compliance". Description:

```
Aigis — open-source trust layer for Claude Code. Generates IT-approval document packs (ISO 27001, NIST AI RMF, OWASP LLM Top 10), tamper-evident audit logs with HMAC+hash chains, PreToolUse policy hooks, SIEM forwarders, MCP scanner.
```

### Anthropic examples/settings (if applicable)

Once the awesome-list PR is merged, consider opening a PR to anthropics/claude-code examples or settings repo with a sample enterprise hook configuration from `docs/adoption/`. This is lower priority — do it only after initial launch settles.

---

## 6. X/Twitter threads

### Japanese thread (post 1 = main, reply chain for posts 2–8)

**Post 1 (main):**
```
Claude Codeを会社で使いたいのに、情シス審査で止まってる——同じ状況のエンジニアは多いはず。

「審査を突破する」のではなく、「審査に答えられる状態を作る」OSSを公開しました。

Aigis: github.com/killertcell428/aigis

🧵 詳しく説明します
```

**Post 2:**
```
情シスが聞いてくる質問は正当です：

・何を実行できる？
・ログはどこに？
・改ざん検知は？
・ISO 27001・NIST AI RMF対応は？
・インシデント手順は？

問題はClaude Code公式にこれらをまとめた文書が存在しないこと。
```

**Post 3:**
```
aigis trust-pack は3コマンドで承認パッケージを生成します：

```
pip install 'pyaigis[all]'
aigis init --agent claude-code --policy enterprise
aigis trust-pack --lang both --format html
```

→ エグゼクティブサマリー（日英）
→ コントロールマトリクス
→ 監査ログ仕様
→ インシデントRunbook
[GIF]
```

**Post 4:**
```
二層防御の構造：

第1層: Claude Code managed-settings.json（MDM配布、Anthropic公式）
第2層: Aigis PreToolUseフック + HMAC+ハッシュチェーン署名ログ

OTelエクスポートはテレメトリ相当（改ざん検知なし）
Aigisのログはaudit verify で検証可能

両層が必要で、どちらか一方では不十分です
```

**Post 5:**
```
MCPツールのリスクも対応：

aigis mcp --trust --diff

・ツールポイズニング検出
・ラグプル（定義変更）を差分で検知
・トラストスコア算出

サードパーティMCPを使っているチームは特に重要
[IMG: mcp scan output]
```

**Post 6:**
```
正直な限界：

✅ パターン・ポリシーベースの決定論的検査
✅ HMAC署名ログ、改ざん検知可能
✅ ISO 27001 / NIST AI RMF マッピング文書

❌ Anthropicクラウド内部の制御は対象外
❌ 未知の新規攻撃は検知できない
❌ [TO FILL]の組織判断は代行できない

多層防御の一層です
```

**Post 7:**
```
AI セキュリティOSSの独立性について：

Protect AI → Palo Alto（2025年7月）
Invariant mcp-scan → Snyk（2025年6月）
Lakera → Check Point（2025年）
promptfoo → OpenAI（2026年3月）

Aigisは Apache-2.0 で独立を維持します
```

**Post 8:**
```
記事も書きました（Zenn）：
[Zenn記事URL]

⭐ GitHubスターをいただけると嬉しいです
github.com/killertcell428/aigis

承認プロセスで詰まった経験、ぜひコメントで教えてください 🙏
```

---

### English thread (post 1 = main, reply chain for posts 2–8)

**Post 1 (main):**
```
Your company won't approve Claude Code?

I built an open-source trust layer for that.

Aigis: github.com/killertcell428/aigis

🧵 Thread
```

**Post 2:**
```
The pattern I keep seeing:

1. Engineer discovers Claude Code, productivity jumps
2. "Did IT approve this?"
3. Six-month review process, or quiet shadow AI

Neither is good. The security team isn't wrong to ask. They just have no structured answer to work with.
```

**Post 3:**
```
`aigis trust-pack` generates a bilingual IT-approval document pack from your live config:

- Executive summary (EN + JA)
- Control matrix: ISO 27001, NIST AI RMF, OWASP LLM Top 10, Japan METI guidelines
- Policy snapshot
- Audit log spec
- Incident runbook
- Rollout plan

[GIF]
```

**Post 4:**
```
There's a specific audit gap worth knowing:

Claude Code Enterprise exports OpenTelemetry — useful for ops observability, but it's telemetry-grade, not audit-grade (no tamper evidence, no hash chain).

Aigis fills this: HMAC-SHA256 signatures + SHA-256 hash chain.

`aigis audit verify` detects any modification.
```

**Post 5:**
```
Two-layer architecture:

Layer 1: Claude Code managed-settings.json (MDM-deployed, Anthropic-native)
Layer 2: Aigis PreToolUse hooks + signed audit log

Neither replaces the other.
Layer 1 without layer 2: no audit-grade logging.
Layer 2 without layer 1: weaker source enforcement.
```

**Post 6:**
```
MCP supply chain: `aigis mcp --trust --diff`

- Scans tool definitions for poisoning (hidden instructions)
- Diffs against snapshots to detect rug-pulls
- Trust scoring per server

[IMG: mcp output]
```

**Post 7:**
```
Why independent OSS matters here:

Protect AI → Palo Alto (Jul 2025)
Invariant mcp-scan → Snyk (Jun 2025)  
Lakera → Check Point (2025)
promptfoo → OpenAI (Mar 2026)

Every independent AI security tool got acquired.
Aigis is Apache-2.0 and staying that way.
```

**Post 8:**
```
Zero dependencies. Deterministic. $0 API cost. 1731 tests. Apache-2.0.

Full adoption guide: docs/adoption/
dev.to writeup: [dev.to URL]

⭐ github.com/killertcell428/aigis

What's been the sticking point in your company's AI tool approval process?
```

---

## 7. Reddit posts

### r/ClaudeAI

**Title:** I built an open-source tool to get Claude Code through corporate IT security review

**Body:**
```
Disclosure: I'm the author of this project.

The problem: a lot of engineers want to use Claude Code at work, but the IT/security approval process has no structured starting point. The security team asks legitimate questions (what can it execute, where are the logs, is there tamper evidence, which frameworks does this map to) and there's no pre-packaged answer.

I built Aigis (github.com/killertcell428/aigis) to fix this. The main feature for this use case is `aigis trust-pack`:

```bash
pip install 'pyaigis[all]'
aigis init --agent claude-code --policy enterprise
aigis trust-pack --lang both --format html
```

This generates a bilingual IT-approval document pack from your live config — executive summary, control matrix mapped to ISO 27001/NIST AI RMF/OWASP LLM Top 10/Japan METI guidelines, policy snapshot, audit log spec, incident runbook, rollout plan. The [TO FILL] fields are organizational decisions Aigis can't make for you.

The other piece: Claude Code's OTel export is telemetry-grade. Aigis adds tamper-evident audit logs (HMAC+hash chain) via PreToolUse hooks, verifiable with `aigis audit verify`.

Zero dependencies, deterministic (no API calls), 1731 tests, Apache-2.0.

Happy to answer questions about the control model, how the two-layer architecture works, or what I learned trying to get AI tools through enterprise security reviews.
```

---

### r/devops

**Title:** Open-source audit layer for Claude Code — generates IT-approval docs from live config, tamper-evident logs

**Body:**
```
Disclosure: I'm the author.

We've been seeing Claude Code requests come through IT review without any standard documentation package to anchor the security conversation. Aigis is my attempt to fix that:

**`aigis trust-pack`** — generates a bilingual (EN/JA) document pack from your current config: control matrix mapped to ISO 27001 Annex A, NIST AI RMF, OWASP LLM Top 10 2025, and Japan METI AI guidelines. Policy snapshot, audit spec, incident runbook, rollout plan.

**Tamper-evident audit logs** — HMAC-SHA256 signatures + SHA-256 hash chain via Claude Code PreToolUse hooks. `aigis audit verify` reports chain integrity. The specific gap this fills: Claude Code Enterprise's OTel export is operational telemetry, not audit-grade (no chain, no signatures).

**SIEM forwarders** — Splunk HEC, Datadog, Microsoft Sentinel, Elastic. Config examples in docs/forwarders.md.

**MCP scanner** — `aigis mcp --trust --diff` checks tool definitions for poisoning and diffs against snapshots to catch rug-pulls.

Zero dependencies, deterministic, no API keys required, Apache-2.0.

Repo: github.com/killertcell428/aigis
Adoption guide: docs/adoption/

What's your current approach for AI tool governance in your org? Curious what the actual sticking points are.
```

---

## 8. Milestone & cadence plan (W+1 through W+8)

### Star milestones — post EN-first (Liam ERD lesson)

The Liam ERD case study showed that Zenn-first/Japanese-only caps growth. Once we've covered the Japanese audience at launch, all milestone posts go English-first, with Japanese translation after.

| Stars | EN post platform | JA post | Content |
|-------|-----------------|---------|---------|
| 100 | X EN + dev.to | X JA | Short gratitude + "here's what we've shipped since launch" |
| 300 | X EN + dev.to + Reddit | X JA | Feature highlight: `aigis audit verify` demo |
| 500 | X EN + dev.to | X JA | Feature highlight: SIEM forwarder setup |
| 1,000 | X EN + Product Hunt launch | X JA + Zenn | Full milestone post, user story if available |

### Weekly content cadence (maps to existing repo assets)

Each piece links to a live feature that works today:

| Week | Content idea | Repo asset |
|------|-------------|-----------|
| W+1 | "How `aigis audit verify` works" — deep dive on the hash chain | `aigis/audit/chain.py`, `aigis/audit/verify.py` |
| W+2 | "MCP rug-pull demo" — video showing `--diff` catching a change | `aigis mcp --trust --diff` |
| W+3 | "SIEM setup in 5 minutes" — Splunk HEC walkthrough | `docs/forwarders.md` |
| W+4 | "Weekly manager digest" — `aigis report weekly` output example | `aigis/weekly_report.py` |
| W+5 | "The OWASP LLM Top 10 coverage map" — what Aigis covers | `docs/compliance/OWASP_LLM_TOP10_COVERAGE.md` |
| W+6 | "ISO 27001 Annex A walkthrough" — control-by-control | `docs/compliance/` |
| W+7 | "Real IT security questions answered" — Q&A from Discussion threads | GitHub Discussions |
| W+8 | "What 8 weeks of trust-pack feedback taught us" — retrospective | Issues + Discussions |

### GitHub Trending monitoring

Check https://github.com/trending/python daily during W+1. If Aigis appears:
- Screenshot immediately
- Post to X (EN): "Aigis just hit GitHub Trending Python — [screenshot] — thanks everyone, here's what's next: [link to roadmap]"
- Do not over-celebrate; one post is enough

### awesome-list merge cadence

If hesreallyhim/awesome-claude-code PR is not merged within 5 days, add a gentle nudge comment on the PR (not a new PR). If not merged within 2 weeks, proceed to the other lists — the hesreallyhim list is the highest-value target but not the only one.

---

## 9. Risks & counters

### Risk: HN flop (doesn't get traction in first 30 min)

HN posts live or die in the first 30 minutes based on early engagement velocity. If the post gets ≤5 points in 30 minutes:

- Do NOT resubmit immediately — HN penalizes reposts
- Wait 1–2 weeks minimum
- Rework the title (try different angles: lead with the audit-gap fact, or lead with the acquisition context)
- Retry window: one repost allowed under HN rules after ~1–2 weeks with substantially different title/framing
- Backup: r/devops or r/netsec often gives a second wind to posts that didn't land on HN

### Risk: "Yet another AI guardrail" objection

Counter points to have ready:

1. **Runtime hooks, not just filters:** Most guardrail tools intercept text. Aigis intercepts tool calls before execution — a different and complementary layer.
2. **The approval pack is unique:** No other open-source tool generates an IT-approval document mapped to four compliance frameworks from live config. This isn't a guardrail — it's an adoption enabler.
3. **Japanese compliance mapping:** METI AI事業者ガイドラインv1.2 mapping doesn't exist elsewhere in OSS. This covers a real gap for Japanese enterprise buyers.
4. **Independent OSS:** The acquired tools are now vendor products. Aigis is Apache-2.0 and auditable.

### Risk: FUD accusation (implying Claude Code is insecure)

The framing must be careful here. Correct counter:

- We cite Anthropic's own documentation factually: OTel export is documented as telemetry, not audit-grade. We're not claiming Claude Code is insecure — we're describing what the gap is and why two layers together work better.
- The two-layer framing explicitly praises Claude Code's managed-settings.json as a strong Layer 1. We are an additive tool, not a replacement narrative.
- If Anthropic adds an audit-grade log API in a future release, we will update the positioning accordingly and document the change.

### Risk: low quality inbound (feature requests that distort roadmap)

Keep a `won't-fix` tag in issues for requests that would add external API dependencies, reduce determinism, or scope-creep into areas that belong in a full ISMS platform. Document the scope boundaries clearly in CONTRIBUTING.md.
