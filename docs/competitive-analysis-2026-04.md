# AI Security/Guardrails Competitive Analysis Report

> Research period: October 2025 - April 2026
> Created: 2026-04-06

---

## 1. Industry-Wide Trend Summary

### M&A Storm -- Consolidation of AI Security Startups Accelerates

From late 2025 through 2026, **3 major acquisitions** occurred in the AI security space. The trend of independent startups being absorbed by large cybersecurity companies is prominent.

| Acquirer | Target | Amount | Timing |
|----------|--------|--------|--------|
| **Check Point** | Lakera | $300M | September 2025 |
| **SentinelOne** | Prompt Security | ~$250M | August 2025 |
| **CrowdStrike** | Pangea | $260M | September 2025 (completed 2026) |
| **OpenAI** | Promptfoo | Undisclosed | March 2026 |

### Funding -- Investment in AI Security Hits All-Time High

| Company | Amount Raised | Valuation | Purpose |
|---------|---------------|-----------|---------|
| Tenex.ai | $250M | $1B+ | AI cybersecurity tools |
| Xbow | $120M | $1B+ | AI vulnerability scanning |
| Vega Security | $120M Series B | $700M | Cyber threat detection |

VC investment in Q1 2026 surpassed $300B, hitting an all-time high. AI security is established as a high-growth category.

### Technology Trends

1. **Agentic AI Security** -- Monitoring and controlling autonomous AI agents has become the top priority
2. **MCP (Model Context Protocol) Gateway** -- Security scanning of MCP servers is becoming the new standard
3. **Chain-of-Thought Auditing** -- Guardrails that audit the reasoning process of LLMs
4. **Shadow AI Detection** -- Visibility into unauthorized AI tool usage within enterprises
5. **Code Generation Security** -- Static analysis of LLM-generated code integrated into guardrails

---

## 2. Latest Developments by Competitor (October 2025 - April 2026)

### 2.1 Lakera (Acquired by Check Point)

- **September 2025**: Acquired by Check Point for $300M. Integrated into Check Point Infinity architecture
- **Integration targets**: CloudGuard WAF (AI app protection), GenAI Protect (GenAI traffic protection)
- Became the foundation of the **Check Point Global Center of Excellence for AI Security**
- 100+ language support, 98%+ detection rate, sub-50ms latency
- **New features**: Advanced PII Detection & DLP, custom detectors, violent content detection
- **March 2026**: Open-sourced Canica (interactive text dataset viewer with t-SNE/UMAP support)

### 2.2 HiddenLayer

- **July 2025**: Listed on AWS Intelligence Community Marketplace
- **December 2025**: Won the SHIELD IDIQ contract from the U.S. Missile Defense Agency (ceiling $151B)
- **December 2025**: Expanded integration with AWS GenAI (Bedrock, AgentCore, SageMaker)
- **March 2026**: **Agentic Runtime Security** -- next-gen module for real-time protection of autonomous AI agent decision-making and actions
- Published the **2026 AI Threat Landscape Report**: AI agent-related incidents now account for 1/8 of all AI breaches

### 2.3 Protect AI

- **ModelScan v0.8.7**: Addressed Keras CVE-2025-1550
- **Guardian (Enterprise Edition)**: Automatic model format detection, broader model support
- **LLM Guard (OSS)**: Input scanners (PII anonymization, topic prohibition, toxicity detection) + output scanners (bias detection, malicious URL detection)

### 2.4 Arthur AI

- **Toxicity classifier**: Token limit expanded from 1,200 to 8,000
- **PII detection accuracy improvement**: False positive filtering for "me", "you", "doctor", etc.
- **Prompt injection classifier**: Improved accuracy, precision-focused (reduced false positives)
- **January 2026**: Added agentic capabilities (testing, tracing, deployment)

### 2.5 Guardrails AI

- **February 2025**: Launched Guardrails Index (performance/latency benchmarks for 24 guardrails)
- **NeMo Guardrails integration**: Can add input/output validators to NeMo
- **Planned**: Multimodal support (media verification beyond text), advanced agentic workflows

### 2.6 Prompt Security (Acquired by SentinelOne)

- **August 2025**: Acquired by SentinelOne for ~$250M
- **MCP Gateway**: Monitors 13,000+ MCP servers with dynamic risk scoring
- **Prompt Fuzzer**: OSS tool for GenAI vulnerability assessment
- **Embedding-level prompt injection research**: Contamination detection in RAG pipelines
- **Authorization features**: Enhanced AI data access control

### 2.7 Pangea (Acquired by CrowdStrike)

- **February 2025**: Released AI Guard + Prompt Guard (50+ PII types, 99%+ injection detection)
- **July 2025**: **AI Detection and Response (AIDR)** platform
  - Chrome browser monitoring for Shadow AI detection
  - MCP proxy (agent security)
  - AWS log analysis for AI usage visibility
- **September 2025**: Acquired by CrowdStrike for $260M -> integrated into the Falcon platform
- Achieved the industry's first complete AI Detection and Response (AIDR)

### 2.8 Lasso Security

- **Agentic Purple Teaming**: AI agents autonomously scan for vulnerabilities -> apply governance and security policies
- **MCP Gateway**: Security plugins for context guardrails, prompt monitoring, real-time logging
- **Memory Poisoning Countermeasures**: Session memory isolation, data source verification, forensic snapshots for rollback
- **CBAC (Context-Based Access Control)**: Context-based access control
- **Intent-Aware Controls**: Understand agent intent and detect out-of-bounds behavior

### 2.9 NVIDIA NeMo Guardrails

- **IORails**: Optimized Input/Output rails engine with parallel execution support (content-safety, topic-safety, jailbreak detection)
- **BotThinking**: Apply guardrails to LLM reasoning traces
- **OpenAI-compatible server**: v1/models endpoint + GuardrailsMiddleware for LangChain
- **LangChain 1.x compatibility**: Content blocks API support (reasoning traces + tool calls)
- **Azure OpenAI / Cohere / Google embedding** provider additions
- **LFU cache**: For content-safety, topic-control, jailbreak detection models

### 2.10 Emerging OSS Tools

#### Meta LlamaFirewall (April 2025-)
- **PromptGuard 2**: BERT-based jailbreak/injection detection (86M / 22M parameters)
- **Agent Alignment Checks**: Real-time chain-of-thought auditing (first in OSS)
- **CodeShield**: Online static analysis of LLM-generated code (8 languages, Semgrep + regex)
- Reduced attack success rate by 90% (down to 1.75%)

#### Cisco DefenseClaw (March 2026)
- OSS framework for AI agent security automation
- Integration with NVIDIA NeMo Guardrails
- MCP server scanning, memory poisoning detection, tool abuse detection
- Extends Zero Trust to AI agents

#### OpenAI Promptfoo (Acquired by OpenAI in March 2026)
- Automated red teaming, prompt injection detection, data leak prevention
- Used by more than 25% of Fortune 500
- Planned integration into OpenAI Frontier, OSS to continue

#### Trylon Gateway
- OSS AI gateway (self-hosted proxy)
- Guardrails for OpenAI / Gemini / Claude

#### OpenGuardrails
- Context-aware safety & manipulation detection models (first OSS large-scale safety LLM + production-ready platform)

---

## 3. Feature Gap Comparison Table for aigis

| Feature Category | Feature | aigis | Competitor Implementation | Priority |
|---|---|---|---|---|
| **ML-Based Detection** | LLM/BERT-based injection classifier | None (regex + similarity only) | LlamaFirewall PromptGuard 2, Lakera Guard, Arthur Shield | **Highest** |
| **Agent Monitoring** | Chain-of-thought auditing | None | LlamaFirewall Agent Alignment Checks, HiddenLayer Agentic Runtime | **Highest** |
| **Agent Monitoring** | MCP gateway / MCP server scanning | None | Lasso MCP Gateway, Prompt Security MCP Gateway, Cisco AI Defense | **High** |
| **Code Safety** | Static analysis of LLM-generated code | None | LlamaFirewall CodeShield (8 languages) | **High** |
| **Shadow AI** | Visibility and control of enterprise AI tool usage | None | Pangea AIDR (Chrome monitoring), Prompt Security | Medium |
| **Memory Safety** | Memory poisoning detection & session isolation | None | Lasso Security, Cisco DefenseClaw | **High** |
| **Multimodal** | Image/audio guardrails | None | Guardrails AI (planned), LlamaFirewall (planned) | Medium |
| **Automated Red Teaming** | Autonomous vulnerability scanning | None | Lasso Purple Teaming, Promptfoo, Cisco AI Defense Explorer | **High** |
| **Embedding Attacks** | Embedding-level injection detection | None | Prompt Security research | Medium |
| **Context Awareness** | Context-Based Access Control (CBAC) | None | Lasso Security | Medium |
| **Intent Detection** | Agent intent understanding & deviation detection | None | Lasso Intent-Aware Controls | Medium |
| **Reasoning Traces** | Guardrails applied to LLM reasoning process | None | NeMo BotThinking | Medium |
| **Benchmarks** | Guardrail performance comparison benchmarks | `aig benchmark` available | Guardrails Index (across 24 guardrails) | Low |
| **Advanced PII** | 50+ type PII detection | 8 types | Pangea AI Guard (50+ types) | **High** |
| **DLP** | Data Loss Prevention integration | None | Lakera Advanced DLP, Prompt Security | Medium |
| **Dashboard** | Real-time monitoring Web UI | Cloud Dashboard available (v0.7.0) | Enterprise editions from all competitors | Addressed |
| **Slack Notifications** | High-risk detection alerts | Available (v0.7.0) | HiddenLayer, others | Addressed |
| **LangGraph Integration** | GuardNode | Available (v0.6.2) | NeMo GuardrailsMiddleware | Addressed |
| **Compliance** | Japanese regulatory mapping | 37 requirements 100% (v0.8.0) | Competitors have no Japan coverage | **Strength** |
| **Zero Dependencies** | Runs on stdlib only | Yes | Competitors have many dependencies | **Strength** |
| **Japanese Native** | Japanese attack patterns + PII | Yes | Only Lakera (100+ languages) has coverage | **Strength** |

---

## 4. Recommended Actions (Prioritized)

### Tier 1: Top Priority (Directly differentiating, recommended for Phase 2)

1. **Add ML-based injection classifier**
   - In addition to the current regex + similarity approach, provide a lightweight BERT/DistilBERT-based classifier as an optional dependency
   - Reference LlamaFirewall PromptGuard 2 (22M parameter lightweight version)
   - `pip install aigis[ml]` for optional installation (maintaining zero-dependency principle)

2. **MCP Gateway / MCP Security Scanning**
   - Proxy functionality to inspect MCP server requests/responses
   - Lasso / Prompt Security MCP Gateways are becoming the de facto standard
   - High affinity with Claude Code hooks (aigis strength)

3. **Automated Red Teaming Feature**
   - `aig redteam` command to automatically generate and test attack patterns
   - Reference Promptfoo's OSS components, Lasso Purple Teaming

### Tier 2: High Priority (Phase 2-3)

4. **LLM-Generated Code Safety Checks**
   - CodeShield-like static analysis (leveraging Semgrep rules)
   - Execute via `aig scan --code` or `guard.check_code()`

5. **Memory Poisoning Countermeasures**
   - Multi-turn conversation memory contamination detection
   - Cross-session context isolation verification

6. **Major Expansion of PII Detection**
   - Current 8 types -> 30+ types (passport, bank account, health insurance card, address, etc.)
   - Particularly comprehensive coverage of Japan-specific PII (corporate number, health insurance card number, etc.)

### Tier 3: Medium Priority (Phase 3 onwards)

7. **Chain-of-Thought Auditing**
   - Monitor AI agent reasoning processes and detect deviations

8. **Shadow AI Detection**
   - Visibility into unauthorized AI tool usage within enterprises

9. **Multimodal Guardrails**
   - Prompt injection detection within images, etc.

---

## 5. Strategic Considerations

### aigis's Positioning

The industry M&A rush has resulted in independent AI security startups being rapidly absorbed by large companies. This is also an **opportunity** for aigis.

**Advantages:**
- With Lakera, Prompt Security, and Pangea acquired by large enterprises, **the number of independent OSS options is decreasing**
- Post-acquisition price increases and vendor lock-in are expected, **increasing demand for OSS alternatives**
- Meta LlamaFirewall is strong but leans toward the Meta ecosystem. **There is an open niche for a provider-neutral lightweight OSS**
- **Native Japanese support + Japanese regulatory mapping** is a unique differentiator

**Challenges:**
- Without ML-based detection, it may be perceived as "regex only," lacking technical credibility
- Not supporting MCP gateways risks falling behind in the 2026 agentic era
- To compete against the resources and sales force of large companies, maximizing community and OSS advantages is essential

---

## Sources

- [Lakera Product Updates](https://www.lakera.ai/product-updates)
- [Lakera Q4 2025 Blog](https://www.lakera.ai/blog/the-year-of-the-agent-what-recent-attacks-revealed-in-q4-2025-and-what-it-means-for-2026)
- [HiddenLayer 2026 AI Threat Report](https://www.hiddenlayer.com/news/hiddenlayer-releases-the-2026-ai-threat-landscape-report-spotlighting-the-rise-of-agentic-ai-and-the-expanding-attack-surface-of-autonomous-systems)
- [HiddenLayer Agentic Runtime Security](https://www.morningstar.com/news/pr-newswire/20260323da16125/hiddenlayer-unveils-new-agentic-runtime-security-capabilities-for-securing-autonomous-ai-execution)
- [Arthur AI December 2025 Release](https://docs.arthur.ai/changelog/december-2025-release-notes)
- [Arthur Shield Changelog](https://shield.docs.arthur.ai/changelog)
- [Guardrails AI Docs](https://guardrailsai.com/docs)
- [Guardrails AI + NeMo Integration](https://guardrailsai.com/blog/nemoguardrails-integration)
- [NeMo Guardrails GitHub](https://github.com/NVIDIA-NeMo/Guardrails)
- [NeMo Guardrails Release Notes](https://docs.nvidia.com/nemo/guardrails/latest/release-notes.html)
- [Check Point acquires Lakera ($300M)](https://www.checkpoint.com/press-releases/check-point-acquires-lakera-to-deliver-end-to-end-ai-security-for-enterprises/)
- [SentinelOne acquires Prompt Security (~$250M)](https://investors.sentinelone.com/press-releases/news-details/2025/SentinelOne-to-Acquire-Prompt-Security-to-Advance-GenAI-Security-and-Agent-Security-Strategy/default.aspx)
- [CrowdStrike acquires Pangea ($260M)](https://www.crowdstrike.com/en-us/press-releases/crowdstrike-to-acquire-pangea-to-secure-every-layer-of-enterprise-ai/)
- [OpenAI acquires Promptfoo](https://openai.com/index/openai-to-acquire-promptfoo/)
- [Meta LlamaFirewall](https://ai.meta.com/research/publications/llamafirewall-an-open-source-guardrail-system-for-building-secure-ai-agents/)
- [Cisco DefenseClaw](https://siliconangle.com/2026/03/23/cisco-debuts-new-ai-agent-security-features-open-source-defenseclaw-tool/)
- [Cisco AI Defense RSA 2026](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2026/m03/cisco-reimagines-security-for-the-agentic-workforce.html)
- [Lasso Agentic AI Security](https://www.lasso.security/resources/agentic-ai-security-platform)
- [Pangea AI Detection & Response](https://siliconangle.com/2025/07/29/pangea-launches-ai-detection-response-close-gaps-generative-ai-security/)
- [Protect AI ModelScan](https://github.com/protectai/modelscan)
- [Tenex.ai raises $250M](https://www.bloomberg.com/news/articles/2026-03-31/google-partner-tenex-raises-250-million-for-ai-security-tools)
- [Xbow valued at $1B+](https://www.bloomberg.com/news/articles/2026-03-18/ai-security-startup-xbow-now-valued-at-more-than-1-billion)
- [Q1 2026 VC funding $300B](https://news.crunchbase.com/venture/record-breaking-funding-ai-global-q1-2026/)
- [OpenGuardrails](https://openguardrails.com/)
- [Trylon Gateway](https://github.com/trylonai/gateway)
