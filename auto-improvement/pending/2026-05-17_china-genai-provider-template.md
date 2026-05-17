# Pending: China GB/T 45654-2025 Compliance Template

**Date:** 2026-05-17
**Motivated by:** Research cycle 8 (compliance-regulation), 2026-05-17T00-00

---

## Title

`china_genai_provider.yaml` — aigis policy template for GB/T 45654-2025 (China generative AI security standard)

## Motivation

China released GB/T 45654-2025 ("Basic Security Requirements for Generative Artificial Intelligence Services") on 25 April 2025, effective 1 November 2025. The standard mandates:
- Training data security (provenance, labelling, bias mitigation)
- Model security (robustness, resistance to adversarial inputs)
- Content security (blocking prohibited content, labelling AI-generated output)
- Security incident response

Any provider offering generative AI services in China or to Chinese users must comply. This is a certifiable national standard, not merely guidance.

## Research finding

- Source: <https://cset.georgetown.edu/publication/china-gen-ai-safety-standard-draft/>
- Source: <https://iclg.com/practice-areas/cybersecurity-laws-and-regulations/01-generative-ai-and-cyber-risk-in-china>
- Source: <https://www.mondaq.com/china/new-technology/1389098/china-proposes-national-standards-on-generative-ai-security-the-basic-requirements-for-the-security-of-generative-artificial-intelligence-services>

## Proposed change

Create `policy_templates/china_genai_provider.yaml` with custom rules targeting:
- Instructions to bypass content labelling requirements (AI-generated content disclosure)
- Requests to suppress prohibited content filters
- Training data documentation bypass patterns (similar to `gpai_provider.yaml` patterns)

## Why held back

English-language technical analysis of GB/T 45654-2025's specific requirements is still sparse as of May 2026. Most available commentary is at the headline level. Implementing a policy template without a detailed technical breakdown risks inaccuracy and would require future correction. CSET Georgetown's analysis is the most authoritative but lacks the level of detail needed to write accurate aigis custom rules.

## Constraint blocking implementation

Would-be-nice constraint: "any change touching > 100 LOC across non-test files" could be met here, but the primary blocker is accuracy risk from insufficient technical source material, not LOC.

## Suggested next step

Revisit when:
1. CSET or equivalent publishes a detailed English-language breakdown of the technical requirements in GB/T 45654-2025.
2. A major provider publishes a compliance checklist for the standard.
3. Enforcement actions or official guidance clarify priority obligations.

Expected timeline: late 2026 once enforcement experience accumulates.
