# Aigis — Roadmap

> Last updated: 2026-08-13
> Strategy: be the tool that gets AI agents through a **Japanese company's internal
> security review** — and stay small enough for one person to maintain.

---

## What changed in this revision (2026-08-13)

The previous roadmap (2026-04-10) planned *OSS trust → SaaS revenue → Enterprise
scale*, with targets of 1,000 stars, $1,000 MRR, and 3 enterprise adoptions.
**That plan is withdrawn.** Every number below is measured, not estimated.

| | Apr 2026 plan | Measured 2026-08-13 |
|---|---|---|
| GitHub stars | 1,000 by 08-31 | **54** (46 in June → 54 in August: ~4/month) |
| Article likes | 100 | **300** (Qiita 161 + 139) — target met, but it did not convert to stars |
| PyPI downloads | 5,000/month | **~15,000** as of June (August figure not retrieved — pypistats rate-limited) |
| MRR | first $1–500 | **0** |
| Official site | aigis.dev | **A broken 301 to an unrelated project.** `site/` has been removed |
| Market read | "acquisitions thinned out independent OSS → our opening" | **Inverted.** Large vendors filled the gap with free OSS |

Three findings drove the rewrite.

**1. The winning channel does not produce stars.** Two Qiita articles earned 161 and
139 likes, and downloads grew, but stars moved ~4/month. The readers who respond to
"how do I get Claude Code approved at work" are IT/DX staff, not people who star
GitHub repos. Stars were the wrong KPI, not a missing effort.

**2. The site never existed.** `aigis.dev` returned a 301 to `archive.aigis.dev`
(a different project), and every path except `/` redirected to a malformed host
(`archive.aigis.devdocs`) because the rule concatenated without a slash. The
Next.js app under `site/` was never reachable at the domain it declared. Crawlers
hitting any documentation URL dead-ended. Removed in `adfd9cd`.

**3. Pattern count is an unwinnable race.** Measured competitors as of 2026-08:

- **agent-threat-rules** — 768 machine-readable rules across 10 categories, versioned
- **Cisco MCP Scanner** — open source, vendor-backed
- **Meta LlamaFirewall** — PromptGuard 2 + Agent Alignment Checks + CodeShield
- **LLM Guard** — ~2.5M downloads (Aigis is at ~15k)

Aigis has 260+ patterns. Adding 4–8 per month does not close a 3x rule gap against
teams with staff. This is a headcount race, and Aigis has one part-time maintainer.

---

## Vision (revised)

**Japanese companies can adopt AI agents with their security team's approval.**

The previous vision — "every AI agent has a security layer as a matter of course" —
addressed the whole market. Aigis cannot win the whole market. It can plausibly be
the best tool for one specific job, in one specific market.

### Why this job, and why Japan

Searching for how to get an AI agent approved at work returns **vendor blog posts
only** — getmaxim, TrueFoundry, MintMCP, Airia's "CISO's Guide to Approving Claude",
PlatformSecurity. Many articles explaining the process; **no tool that produces the
artifact**. `aigis trust-pack` generates the approval pack itself. That gap is real
and currently unoccupied.

Japanese-language searches surface LLM Guard, promptmap, and Open-Prompt-Injection —
**none of which map to 経産省 AI 事業者ガイドライン or emit a bilingual approval pack.**
Cisco and Meta will not build a control matrix for a Japanese ministry's guidelines.
This is the one area where the large vendors are structurally absent, not merely
behind.

---

## What Aigis is getting out of

Stated explicitly, because leaving these implicit is what let the last roadmap drift.

- **Pattern-count competition.** 260+ patterns is where it stops being the headline.
  Rules still get *fixed* when wrong (false negatives, language gaps), but "N new
  detectors per cycle" is no longer a goal or a KPI.
- **The general-purpose guardrail shelf.** LLM Guard's job (chatbot input/output
  filtering) is theirs. Aigis is not positioned against it.
- **Broad English-market awareness.** Not competing with Cisco/Meta for attention.
  Current awareness there is zero, so nothing is being given up.
- **SaaS revenue, and the roadmap that served it.** Cloud Pro / Business / Enterprise
  tiers, LDAP/SSO, SLA support, multi-tenancy: dropped. `backend/` and `frontend/`
  stay in the tree but are dormant, not roadmap items.
- **Chasing a single enterprise adoption as proof.** Without a channel into a company
  whose review process is independent and heavyweight, this is waiting, not working.

### The tradeoff, stated plainly

This narrows the addressable market. Downloads may grow more slowly than a
general-purpose library's would, and "Japan-only" is a weak story for acquisition.
That is accepted: the goal is to be genuinely first at something small enough for one
maintainer, not fifth at something large.

---

## What Aigis is doing

Ordered by cost, cheapest first.

1. **Fix where Aigis is discoverable.** The README already leads with the right
   positioning ("trust layer for bringing Claude Code to work"), but the GitHub
   description still says "firewall for AI agents … 44 compliance templates" — the
   generic shelf. Topics are missing `tool-poisoning`, `claude-code`, and `audit-log`,
   even though `github.com/topics/tool-poisoning` ranks for the exact search Aigis
   should win.
2. **Get listed where people actually look.** `awesome-ai-security-tools` and
   `awesome-ai-agent-incidents` both rank on the core query and neither lists Aigis.
   (Open since April as "Awesome list PRs (3 lists)".) Note: a 2026 submission to an
   *academic literature* list was rejected as "not original work" — tool directories
   are a different thing and are the right target.
3. **Make `trust-pack` good enough to survive a real review.** It is the only
   differentiator with no competing tool, and nobody with audit experience has read
   its output yet. Development effort moves here from pattern work.
4. **Keep publishing.** The two winning articles share a shape: a felt threat, a
   simple fix, a cited basis. One per month is enough to show the project is alive.

---

## KPI

Only things that can actually be measured. The previous roadmap's KPIs included
figures nobody was reading.

| Metric | Why | Current |
|---|---|---|
| PyPI downloads/month | The only real signal that Aigis is used | ~15,000 (June; re-measure) |
| Externally-originated issues/PRs | Someone read the code well enough to touch it | 1 external PR (#180), 6 open issues |
| Articles published + response | Leading indicator; the channel that demonstrably works | 2 winners (161, 139 likes) |
| Awesome-list placements | Discovery path that does not depend on search rank | 0 |

**Not KPIs:** stars (uncorrelated with the working channel), MRR (no longer pursued),
pattern count (race abandoned).

**Deliberately unmeasurable:** `trust-pack` runs and actual approvals granted. Aigis
is zero-dependency and never phones home, so local runs cannot be counted. This will
not be turned into a KPI by adding telemetry.

---

## Automation — actual state

The previous roadmap described a research → dev → content loop as if it were running.
Measured on 2026-08-13:

| Mechanism | Claimed | Actual |
|---|---|---|
| `auto-improvement/` rotation (10 domains, 6-hourly) | continuous | **Stopped.** `LAST_RUN_UTC: 2026-06-02` |
| `.github/workflows/paper-review.yml` (daily) | 10 papers/day → candidates | **Failing daily.** `ANTHROPIC_API_KEY` not configured; runs exit in ~20s |
| 3 scheduled triggers (Mon/Wed/Fri) | research / feature-dev / content | **Unverified** — cannot be inspected from the repo |

So the pattern-addition machinery had already stopped on its own. Stopping it is not
work; the work is not restarting it, and reshaping the rotation's domain definitions
(8 of 10 pointed at attack research feeding new rules — see
[auto-improvement/ROTATION.md](auto-improvement/ROTATION.md)).

Recent pattern commits (`e66d07a`, `d67473d`, August) came from neither loop — they
were done by hand.

---

## Competitive position (measured 2026-08)

| | Aigis | agent-threat-rules | Cisco MCP Scanner | Meta LlamaFirewall | LLM Guard |
|---|---|---|---|---|---|
| Rules / patterns | 260+ | **768** | signature-based | 3-layer | many |
| Backing | 1 part-time maintainer | community | **Cisco** | **Meta** | Palo Alto (acq.) |
| MCP re-scan at invocation | **Yes** | — | at scan time | — | — |
| Tamper-evident audit log | **Yes** (HMAC + hash chain) | — | — | — | — |
| Generates an approval pack | **Yes** (`trust-pack`) | — | — | — | — |
| 経産省 AI 事業者ガイドライン | **Yes** (10 templates) | — | — | — | — |
| Japanese / Korean / Chinese patterns | **Yes** | — | — | — | — |
| Zero runtime dependencies | **Yes** | n/a | — | — | — |

Read the first two rows as the reason to stop competing there, and the last five as
where Aigis is actually alone.

---

## Out of scope (unchanged)

Model-artifact scanning (use ModelScan) · training/fine-tuning safety · content
moderation · LLM-based detection. See [Limits](README.md#limits).

---

*Revised when measurement contradicts the plan — not on a fixed schedule. The April
version went four months without an update while its targets drifted 20x from
reality.*
