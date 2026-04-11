# Aigis — Automated Development Loop Design

> Last updated: 2026-04-03
> Overview: A semi-automated loop of Security Research -> Feature Development -> Article Publishing to continuously strengthen Aigis

---

## Loop Overview

```
+----------------------------------------------------------+
|                  Weekly Dev Loop                          |
|                                                          |
|  (1) Research Scout (Monday)                             |
|     -> content/research_backlog/YYYYMMDD_findings.md     |
|                                                          |
|  (2) Feature Dev (Wednesday)                             |
|     -> gap_analysis -> pattern addition -> test -> ver up|
|                                                          |
|  (3) Article Writer (Friday)                             |
|     -> content/articles/YYYYMMDD_*.md (draft)            |
|                                                          |
|  Human Review: review article -> publish -> SNS outreach |
+----------------------------------------------------------+
```

---

## Phase 1: Research Scout (Every Monday 09:00 JST)

### Purpose
Research the latest AI agent security threats and governance trends, and compile them into structured findings.

### Research Scope
1. **Threats & Vulnerabilities**: New attack techniques, CVEs, incident reports
2. **Governance & Regulation**: AI regulatory developments across countries, guideline updates
3. **Tools & Frameworks**: Competitor product updates, new tools
4. **Academic & Industry Reports**: New reports from OWASP, NIST, Gartner, etc.

### Output Location
```
content/research_backlog/
├── YYYYMMDD_findings.md      # Weekly research report
├── YYYYMMDD_findings.md
└── ...
```

### Output Format
```markdown
---
date: YYYY-MM-DD
type: weekly_research
status: new  # new -> analyzed -> developed -> published
---

# Weekly Security Research (YYYY-MM-DD)

## Findings Summary
- High severity: N items
- Medium severity: N items
- Low severity: N items

## Findings

### [HIGH] Title
- **Summary**: ...
- **Source**: URL
- **Aigis Relevance**: High/Medium/Low
- **Mitigation Direction**: What aigis can address
- **Recommended Action**: add pattern / update policy / write article / continue monitoring

### [MED] Title
...
```

---

## Phase 2: Feature Dev (Every Wednesday 09:00 JST)

### Purpose
Read findings from the Research Scout, identify gaps with aigis's current state, and implement necessary features.

### Process
1. **Gap Analysis**: Read entries with `status: new` from `content/research_backlog/`
2. **Prioritization**: Prioritize by Aigis relevance x implementation cost
3. **Implementation**: Execute one of the following:
   - Add new detection patterns to `aigis/patterns.py`
   - Add Guard class patterns to `aigis/filters/patterns.py`
   - Add new attack phrases to `aigis/similarity.py`
   - Add new policy templates to `policy_templates/`
   - Add new regulatory mappings to `aigis/compliance.py`
4. **Testing**: Add test cases to `tests/`, run benchmarks
5. **Status Update**: Update findings status from `new` -> `analyzed` -> `developed`

### Implementation Rules
- Implement a maximum of 3 patterns per loop iteration (quality first)
- Do not merge changes that lower benchmark accuracy (maintain 100%)
- Verify all existing tests pass
- Add entry to CHANGELOG.md

### Output
- Code changes for new patterns/features
- Test code
- CHANGELOG.md update
- Findings status update

---

## Phase 3: Article Writer (Every Friday 09:00 JST)

### Purpose
Combine research results and new features to generate technical article drafts for Zenn/Qiita.

### Article Structure Template
```markdown
---
title: "..."
emoji: "..."
type: "tech"
topics: ["AI Security", "AI Agents", ...]
published: false
---

## Introduction
[Hook with latest threats/trends]

## Background
[Technical explanation, why it matters]

## Specific Risks
[Real examples, attack technique explanations]

## Mitigation Approaches
[General countermeasures + how Aigis addresses them]

## Implementation with Aigis
[Code examples, usage instructions]

## Conclusion
[Key takeaways]

## References
```

### Article Guidelines
- **Value first**: 80% of the article should be pure technical content. Aigis promotion should be naturally woven in and limited to 20% or less
- **Practical**: Always include code examples and configuration samples
- **Current**: Base articles on news and research from the past 1-2 weeks
- **Platform differentiation**:
  - Zenn: Deep technical explanations, article series
  - Qiita: How-tos, implementation guides
  - DEV.to: English version (approximately once per month)

### Output Location
```
content/articles/YYYYMMDD_[topic]_[platform].md
```

---

## Operational Rules

### Human Involvement Points (the "semi" in semi-automated)
1. **Research Review**: Review Monday's findings and adjust direction
2. **Implementation Review**: Review and merge Wednesday's PRs
3. **Article Review**: Review, edit, and publish Friday's drafts
4. **Monthly Retrospective**: Measure loop effectiveness and adjust

### KPIs
| Metric | Target |
|--------|--------|
| Weekly research execution rate | 90%+ |
| Monthly new patterns added | 4-8 |
| Monthly articles published | 2-4 |
| Benchmark accuracy maintenance | 100% |
| PyPI download growth rate | +20%/month |

### Directory Structure (additions)
```
content/
├── articles/              # Existing: articles for publishing
├── research_backlog/      # New: research findings
│   └── YYYYMMDD_findings.md
└── ...
```

---

## Remote Trigger Configuration

| Trigger Name | Schedule | Description |
|-------------|----------|-------------|
| `aig-research-scout` | Every Monday 09:00 JST | Security research |
| `aig-feature-dev` | Every Wednesday 09:00 JST | Gap analysis & feature development |
| `aig-article-writer` | Every Friday 09:00 JST | Article draft generation |

---

*This document is reviewed monthly.*
