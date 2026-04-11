# AI/LLM Security Products: Pricing & Monetization Analysis

> Date: 2026-03-30
> Purpose: Competitive intelligence for Aigis monetization strategy

---

## 1. AI/LLM Security Products Comparison

### 1A. Detailed Product Profiles

#### Guardrails AI (guardrailsai.com)
- **OSS Core**: Apache 2.0 license. Python framework with 100+ community validators on Guardrails Hub. Full local execution, no account required.
- **Guardrails Pro (SaaS)**: Hosted validation, observability dashboards, enterprise support. Usage-based pricing (per validation op), custom quotes. Flexible deployment: fully hosted or deploy in your VPC. Available on AWS Marketplace.
- **Upgrade Trigger**: Production scale (need hosted infra, SLAs), observability/dashboards, team collaboration, VPC deployment.
- **Key Insight**: Textbook open-core. Hub ecosystem creates lock-in via community validators. Pro adds operational layer, not new detection capabilities.

#### LLM Guard (Protect AI)
- **OSS Core**: MIT license. 15 input scanners + 20 output scanners. Standalone API server or Python library. CPU-optimized (5x cheaper than GPU inference).
- **Paid**: Commercial version with expanded features "coming soon" within Protect AI platform. No public pricing yet.
- **Upgrade Trigger**: Not yet defined (product still maturing commercially).
- **Key Insight**: Fully OSS today. Strong technical foundation but no commercial moat yet. Being part of Protect AI ecosystem (Guardian, ModelScan) may bundle into platform pricing.

#### Lakera Guard
- **OSS**: None. Proprietary SaaS only.
- **Free Tier (Community)**: 10,000 API requests/month, up to 8,000 tokens per prompt. Not recommended for production.
- **Paid (Enterprise)**: Custom pricing. Configurable prompt sizes, custom policies, on-prem deployment, enterprise support.
- **Upgrade Trigger**: Exceeding 10K req/month, need for production SLAs, custom policies, on-prem.
- **Key Insight**: Acquired by Check Point (2025). Pure API-as-a-service model. Low free tier designed as developer trial, not for sustained use. Now folded into Check Point's security portfolio.

#### Prompt Security
- **OSS**: None. Fully proprietary SaaS.
- **Pricing (Published)**:
  - Prompt for Employees: $120/employee seat/year
  - Prompt for Developers (AI Code Assistants): $300/developer seat/year
  - Prompt for Homegrown GenAI Apps: $120 per 1,000 requests/year (overage: $0.01/unit)
- **Enterprise**: Custom pricing, multi-year contracts available.
- **Upgrade Trigger**: Seat count growth, adding use cases (employee vs developer vs app), volume beyond base.
- **Key Insight**: Most transparent pricing in the category. Seat-based + usage hybrid. Three distinct products targeting different buyer personas.

#### Arthur AI (ArthurShield)
- **OSS**: None. Proprietary platform.
- **Free Tier**: Startup program for venture-backed companies. No public free tier.
- **Paid**: Custom enterprise pricing. Available on AWS Marketplace. Focus on GenAI observability + security.
- **Upgrade Trigger**: Enterprise compliance, model monitoring at scale.
- **Key Insight**: Sales-led, enterprise-first. No self-serve or public pricing. Pivoted from ML monitoring to GenAI security. Startup program is a land-and-expand play.

#### Robust Intelligence / Cisco AI Defense
- **OSS**: None (acquired product). But launched **AI Defense: Explorer Edition** (March 2026) -- free self-serve tool for algorithmic red teaming.
- **Free (Explorer)**: Red-team models in ~20 minutes. 200+ risk subcategories. CI/CD integrations (GitHub Actions, GitLab, Jenkins). No cost.
- **Paid (Enterprise)**: AI Defense full platform. Custom Cisco enterprise pricing. Includes AI BOM, MCP Catalog, real-time guardrails for agents, advanced red teaming.
- **Upgrade Trigger**: Move from testing to runtime protection, need for agentic guardrails, enterprise procurement via Cisco.
- **Key Insight**: Cisco acquisition ($B-class) turned a startup into an enterprise platform. Explorer Edition is the free "top of funnel." Enterprise is bundled with broader Cisco security. This is the "big company plays" pattern.

#### Pangea (pangea.cloud) - AI Guard
- **OSS**: None. API-as-a-service.
- **Free Tier**: Free monthly API credits on signup. Startup program: up to $5,000 USD free in first year.
- **Paid**: Pay-as-you-go API usage. Enterprise pricing custom.
- **Products**: AI Guard (data leakage prevention), Prompt Guard (injection), AI Access Control, AI Visibility.
- **Upgrade Trigger**: API volume growth, adding security services beyond basic guard.
- **Key Insight**: Acquired by CrowdStrike for $260M (2025). Sub-30ms response times. Now part of CrowdStrike Falcon as "AI Detection and Response (AIDR)." API-first approach is developer-friendly. 99% bad prompt detection rate claimed.

#### CalypsoAI
- **OSS**: None. Fully proprietary.
- **Free**: Free trial only. No free tier.
- **Paid**: Custom enterprise pricing. Estimated $500K-$2M+ base platform. Subscription by usage tiers (inference requests, data volume, features).
- **Upgrade Trigger**: Enterprise procurement, compliance requirements.
- **Key Insight**: High-end enterprise play. $3.8M revenue with 64 employees (2024). Government/defense focus. Not competing for developer adoption -- competing for procurement budgets.

#### WhyLabs / LangKit
- **OSS**: LangKit (open-source LLM monitoring toolkit). whylogs (open-source data logging). Both on GitHub.
- **Free Tier**: Starter plan was free (full platform, no credit card).
- **Paid (was)**: Expert at $125/month (3 projects, 5 users, 100M predictions/month). Enterprise custom.
- **CRITICAL NOTE**: WhyLabs is discontinuing operations. LangKit remains open-source on GitHub but unmaintained.
- **Key Insight**: Cautionary tale. Strong OSS + reasonable pricing but could not sustain business. Open-source monitoring toolkit without sticky SaaS layer was not enough to build a business around.

---

### 1B. AI Security Products Summary Table

| Product | OSS Component | Free Tier | Paid Model | Price Range | Upgrade Trigger | Status/Note |
|---------|--------------|-----------|------------|-------------|-----------------|-------------|
| **Guardrails AI** | Core framework (Apache 2.0) + Hub validators | Full OSS self-hosted | Usage-based SaaS (per validation) | Custom quotes | Production scale, dashboards, SLAs | Independent. Textbook open-core. |
| **LLM Guard** | Full product (MIT) | Everything is free | Commercial version TBD | TBD | N/A yet | Part of Protect AI ecosystem |
| **Lakera Guard** | None | 10K req/month | Custom enterprise | Enterprise quotes | >10K req, production, custom policies | Acquired by Check Point (2025) |
| **Prompt Security** | None | None (demo only) | Seat + usage hybrid | $120-$300/seat/yr | Seats, use cases, volume | Independent. Most transparent pricing. |
| **Arthur AI** | None | Startup program only | Custom enterprise | Enterprise quotes | Compliance, scale | Sales-led, no self-serve |
| **Cisco AI Defense** | None (Explorer free) | Explorer: free red-teaming | Custom Cisco enterprise | Enterprise quotes | Runtime protection, agents | Acquired by Cisco. Explorer is funnel. |
| **Pangea AI Guard** | None | Free API credits + $5K startup | Pay-per-API-call | Usage-based | Volume, more services | Acquired by CrowdStrike ($260M) |
| **CalypsoAI** | None | Trial only | Custom enterprise | ~$500K-$2M+ | Enterprise procurement | Gov/defense focus |
| **WhyLabs/LangKit** | LangKit + whylogs (OSS) | Was free Starter | Was $125/mo+ | Was $125-custom | Was features/scale | Shutting down. Cautionary tale. |

---

## 2. Developer Tool OSS-to-SaaS Models (Benchmarks)

| Product | OSS Offering | What Triggers Paid | Pricing Model | Key Insight |
|---------|-------------|-------------------|---------------|-------------|
| **Sentry** | Self-hosted (BSL license) | >5K errors/month, >1 user, team features | Event-based: Free -> $26/mo (Team) -> $80/mo (Business) -> Enterprise | Generous OSS for non-profits. Spike protection prevents bill shock. Transparent volume pricing. |
| **PostHog** | Full platform (MIT, Docker) | >1M events/month, >5K recordings | Pay-per-use with free tiers per product: ~$0.00005/event | 98% of users are free. Self-hosted capped at ~100K events. Cloud is the real product. |
| **GitGuardian** | ggshield CLI (OSS) | >25 developers, >10K API calls/month | Free (<25 devs) -> Team -> Business -> Enterprise | "Super-generous free tier" creates viral adoption. Scales by developer count. |
| **Snyk** | CLI scanner (limited) | >100 scans, team CI/CD, private repos | Per-contributing-developer: Free -> $25/dev/mo (Team) -> Enterprise | Charges per "contributing developer" (committed in last 90 days). Smart metric. |

---

## 3. Strategic Insights for Aigis Monetization

### Pattern Analysis: What Works

**Pattern 1: Open-Core with Hub/Marketplace (Guardrails AI model)**
- OSS core is the detection engine
- Hub/marketplace for community rules/validators creates ecosystem lock-in
- SaaS adds operational layer (dashboards, hosting, team management)
- Best for: Developer-first adoption, community building

**Pattern 2: Free Tier as Developer Trial (Lakera, Pangea model)**
- Limited free API calls (10K-50K/month)
- Enough to prototype, not enough to run production
- Enterprise sales kicks in at scale
- Best for: API-as-a-service, quick time-to-value

**Pattern 3: Free Tool -> Paid Platform (Cisco AI Defense, Sentry model)**
- Give away a valuable standalone tool (red-teaming, error tracking)
- Paid platform adds runtime protection, team features, compliance
- Best for: When the "testing" tool is different from the "production" tool

**Pattern 4: Per-Seat + Usage Hybrid (Prompt Security, Snyk model)**
- Seat-based provides predictable revenue
- Usage component captures value from high-volume users
- Multiple product lines for different personas
- Best for: When different buyer personas exist (dev vs security vs compliance)

### Key Pricing Metrics in LLM Security

| Metric | Used By | Pros | Cons |
|--------|---------|------|------|
| API calls / requests | Lakera, Pangea | Simple, usage-correlated | Penalizes high-volume, low-risk use |
| Validation operations | Guardrails AI | Directly tied to value delivered | Complex to predict costs |
| Per employee seat | Prompt Security | Predictable, easy to budget | Doesn't scale with actual usage |
| Per developer seat | Snyk, GitGuardian | Scales with team, not with volume | May miss non-developer users |
| Events / errors | Sentry, PostHog | Fair pay-for-what-you-use | Risk of bill shock |

### Acquisition Trends (Critical Signal)

Three major acquisitions in 2025-2026 validate the market:
1. **Lakera -> Check Point** (2025): Prompt injection detection acquired by network security giant
2. **Pangea -> CrowdStrike** ($260M, 2025): AI guardrails acquired by endpoint security leader
3. **Robust Intelligence -> Cisco** (2024): AI security acquired by networking/security giant

**Implication**: Large security vendors are buying, not building. An OSS project with traction is an acquisition target worth $100M-$500M+.

### WhyLabs Failure Analysis (What to Avoid)

- Had strong OSS (LangKit, whylogs) and reasonable SaaS pricing
- Failed despite good technology
- Likely causes: monitoring alone is not sticky enough, LLM-specific monitoring is a feature not a product, no clear "must-have" trigger for paid conversion
- **Lesson**: The OSS component must solve a pain point that naturally leads to paid features. Monitoring alone is not enough -- security/compliance/blocking is the monetizable layer.

### Recommendations for Aigis

Based on competitive analysis, Aigis's current ROADMAP.md pricing ($49/mo Cloud Pro, $299/mo Business) is **well-positioned** but should consider:

1. **Keep OSS core generous**: Full detection engine, all rule types, CLI. This is table stakes -- Guardrails AI and LLM Guard both do this. Competing on OSS completeness is necessary but not sufficient.

2. **Build the "Hub" early**: A community rule/policy marketplace (like Guardrails Hub) creates ecosystem lock-in that pure OSS does not. This is the most defensible moat.

3. **Free cloud tier**: Add a free cloud tier (e.g., 10K-25K validations/month) for trial/prototype use. Lakera does 10K. This is critical for self-serve conversion.

4. **Usage-based pricing component**: Consider adding per-validation pricing alongside the flat monthly fee. Prompt Security's hybrid model ($120/seat/yr + $0.01/request overage) is instructive.

5. **Multiple buyer personas**: Security teams, developers, and compliance officers have different budgets and triggers. Consider Prompt Security's approach of separate products for each.

6. **Enterprise = custom quotes**: Every competitor does this at the enterprise tier. The $500+/mo in the roadmap should be "contact sales" with much higher actual pricing ($1K-$5K/mo+).

7. **Build for acquisition optionality**: With Check Point, CrowdStrike, and Cisco all acquiring in this space, having strong OSS traction (GitHub stars, downloads, integrations) + modest SaaS revenue is the profile acquirers seek. $260M (Pangea) is the floor for a product with real traction.

---

## 4. Competitive Positioning Matrix

```
                    OSS/Free ────────────────────── Proprietary/Paid Only
                    |                                          |
  Developer-First   |  Aigis (target)                    |
                    |  Guardrails AI                           |
                    |  LLM Guard                               |
                    |                  Cisco Explorer           |
                    |                      Lakera              |  Prompt Security
                    |                      Pangea              |
  Enterprise-First  |                                          |  Arthur AI
                    |                                          |  CalypsoAI
                    |                                          |
```

Aigis's sweet spot: **Developer-first + OSS core**, competing directly with Guardrails AI and LLM Guard, while offering a smoother upgrade path to SaaS than either.

---

## Sources

- [Guardrails AI](https://guardrailsai.com/) | [Guardrails Hub](https://guardrailsai.com/hub) | [Guardrails Pro](https://guardrailsai.com/pro)
- [LLM Guard - GitHub](https://github.com/protectai/llm-guard) | [Protect AI](https://protectai.com/llm-guard)
- [Lakera Guard Pricing](https://platform.lakera.ai/pricing) | [Lakera Pricing Guide](https://www.eesel.ai/blog/lakera-pricing)
- [Prompt Security](https://prompt.security/) | [Prompt Security Pricing](https://aichief.com/ai-productivity-tools/prompt-security/)
- [Arthur AI Pricing](https://www.arthur.ai/pricing) | [Arthur Shield](https://www.arthur.ai/product/shield)
- [Cisco AI Defense Explorer](https://blogs.cisco.com/ai/introducing-cisco-ai-defense-explorer) | [Cisco AI Defense](https://www.cisco.com/site/us/en/products/security/ai-defense/robust-intelligence-is-part-of-cisco/index.html)
- [Pangea Cloud](https://pangea.cloud/) | [CrowdStrike acquires Pangea](https://www.crowdstrike.com/en-us/blog/crowdstrike-to-acquire-pangea/)
- [CalypsoAI](https://calypsoai.com/news/calypsoai-now-offering-first-class-saas/)
- [WhyLabs LangKit](https://github.com/whylabs/langkit) | [WhyLabs Pricing (archived)](https://whylabs.ai/pricing)
- [Sentry Pricing](https://sentry.io/pricing/)
- [PostHog Pricing](https://posthog.com/pricing)
- [GitGuardian Pricing](https://www.gitguardian.com/pricing)
- [Snyk Pricing](https://snyk.io/plans/)
- [OSS-to-SaaS Monetization Strategies](https://www.getmonetizely.com/articles/monetizing-open-source-software-pricing-strategies-for-open-core-saas)
