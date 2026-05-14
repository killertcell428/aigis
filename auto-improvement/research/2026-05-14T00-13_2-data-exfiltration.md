# Research: data-exfiltration — 2026-05-14T00-13

## Domain: data-exfiltration (index 2, third pass)
## Focus: Invisible-character smuggling, sharded exfiltration, CSS hidden-text injection

Previous cycles (2026-05-07, 2026-05-10) covered markdown image exfil, OAST relay domains,
DNS tunneling instructions, EchoLeak / reference-style markdown bypass, and tunnel relay services.
Pending from cycle 2: Unicode Tag Block detection (false-positive analysis), Mermaid href exfil.
This pass focuses on resolving the Unicode Tag Block pending item and the newly documented
sharded exfiltration technique (arxiv:2602.22450).

---

## Findings

- **Unicode Tag Block ASCII Smuggling — threat confirmed, detection viable** (AWS/Cisco/arXiv, 2025–2026):
  Unicode Tag Block characters U+E0000–U+E007F map 1-to-1 to ASCII but render as zero-width
  (invisible) glyphs. Attackers embed full instruction payloads invisibly in documents, tool
  outputs, RAG content, and chat messages; LLMs read and execute the hidden instructions while
  users see nothing. The arXiv:2603.00164 paper ("Reverse CAPTCHA", 2026) shows high attack
  success rates against GPT-4o and Claude. The false-positive concern from the previous pending
  item — subdivision flag emoji (England 🏴󠁧󠁢󠁥󠁮󠁧󠁿) — is resolved by a threshold of 8+ consecutive tag
  chars: all valid subdivision flags use at most 6 tag characters (5-letter region code + cancel).
  Setting `{8,}` avoids all false positives while catching any real attack instruction.
  - Source: https://aws.amazon.com/blogs/security/defending-llm-applications-against-unicode-character-smuggling/
  - Source: https://blogs.cisco.com/ai/understanding-and-mitigating-unicode-tag-prompt-injection
  - Source: https://arxiv.org/html/2603.00164v1
  - **aigis takeaway**: Implement `unicode_tag_block_smuggling` (input, score 80) and
    `out_unicode_tag_block_smuggling` (output, score 80) using `r"[\U000E0000-\U000E007F]{8,}"`.
    **→ IMPLEMENTED this cycle.**

- **Silent Egress / Sharded Exfiltration** (arXiv:2602.22450, Feb 2026): Research from the
  University of Edinburgh demonstrates that injected instructions can cause an LLM agent to
  split stolen context into small fragments (4-character chunks), transmit each via a separate
  HTTP request, and rely on the attacker to reassemble server-side. In 480 experimental runs,
  P(egress)≈0.89; 95% of successful attacks evade output-based safety checks. The sharding
  defeats single-request DLP inspection and reduces per-request leakage size to resemble benign
  telemetry. The attack works against Qwen2.5 7B-based agents and was tested at scale.
  - Source: https://arxiv.org/abs/2602.22450
  - **aigis takeaway**: Add input pattern `exfil_shard_split_requests` (score 65) detecting
    instructions pairing split/shard/fragment keywords with HTTP request context.
    **→ IMPLEMENTED this cycle.**

- **CSS Hidden-Text Injection in AI Summarization** (Microsoft Defender, Feb 2026): Microsoft's
  Defender team identified 50+ distinct manipulation prompts from 31 companies across 14
  industries embedded via CSS hiding techniques (white-on-white text, `display:none`,
  `opacity:0`, `font-size:0`, zero-width chars). These prompt AI summarization tools to follow
  hidden instructions when processing affected pages, used for AI SEO manipulation and more
  aggressive context hijacking. Comparing raw HTML vs post-render output is a high-signal
  detector but requires an HTML parser, not a regex. Pure regex can catch the most common
  patterns though.
  - Source: https://www.penligent.ai/hackinglabs/ai-agents-hacking-in-2026-defending-the-new-execution-boundary/
  - Source: https://brainbyteslab.org/articles/llm-seo-manipulating-ai-summarization/
  - **aigis takeaway**: Potential future rule for `style="color:white"` / `style="opacity:0"` /
    `style="display:none"` combined with non-trivial text content. Send to pending for this cycle.

- **LogJack: Cloud Log Injection against LLM Debugging Agents** (arXiv:2604.15368, Apr 2026):
  Attack goals include data exfiltration by injecting malicious instructions into cloud logs that
  are then processed by LLM debugging agents (CloudWatch, GCP Logging, Azure Monitor). Attack
  succeeds because debugging agents consume raw log lines as context without sanitization.
  Relevant as a RAG poisoning / indirect injection vector through logs.
  - Source: https://arxiv.org/html/2604.15368
  - **aigis takeaway**: Existing `INDIRECT_INJECTION_PATTERNS` partially cover this; a specific
    pattern for `grep`/`tail`/CloudWatch log commands combined with injection markers would be
    new. Send to pending.

- **Protocol Exploits: 30+ attack techniques in LLM-agent workflows** (arXiv:2506.23260, Jun 2025):
  Unified threat model cataloguing attack techniques including: host-to-tool communication
  exploits, agent-to-agent message injection, multimodal adversarial inputs, and privacy attacks
  that exfiltrate or corrupt sensitive data across agent boundaries.
  - Source: https://arxiv.org/html/2506.23260v1
  - **aigis takeaway**: Useful taxonomy for future cycles; no single new detection rule identified
    this cycle. Cross-reference against existing patterns.

- **EchoLeak paper published on arXiv** (arXiv:2509.10540, Sep 2025): Full academic writeup of
  the CVE-2025-32711 zero-click M365 Copilot vulnerability. Confirms both the reference-style
  markdown bypass (already implemented) and the Unicode tag character injection path as used in
  the same exploit chain. The paper shows the two techniques were combined: tag chars carried the
  instructions, and reference-style Markdown carried the exfiltration link.
  - Source: https://arxiv.org/html/2509.10540
  - **aigis takeaway**: Both components now covered (cycle 2 added ref-style markdown; this cycle
    adds the Unicode tag character path). EchoLeak is now fully mitigated in aigis.

- **Content injection traps — CSS/HTML hidden commands** (Wiz agentic browser review, 2025):
  Content injection traps using hidden HTML/CSS commands successfully hijack browser-using agents
  in up to 86% of scenarios (WASP benchmark). Brave's research identified specific entry points:
  text concealed within images using same-color text, and malicious commands embedded in URL
  parameters that execute when the AI processes them.
  - Source: https://www.wiz.io/blog/agentic-browser-security-2025-year-end-review
  - **aigis takeaway**: Invisible-pixel and same-color-text techniques are hard to detect
    statically; browser agent hardening is out of aigis scope. Send to pending.

---

## Candidate Hardenings

1. **`unicode_tag_block_smuggling`** (input, score 80) — Regex `r"[\U000E0000-\U000E007F]{8,}"`.
   Resolves the pending item from 2026-05-10. Threshold of 8+ avoids all subdivision flag false
   positives. Covers the input-side of ASCII smuggling used in EchoLeak.
   **→ IMPLEMENTED**

2. **`out_unicode_tag_block_smuggling`** (output, score 80) — Same regex, output filter.
   Catches agent-to-agent tag block propagation (one injected agent embeds hidden instructions
   in its output for downstream agents to execute).
   **→ IMPLEMENTED**

3. **`exfil_shard_split_requests`** (input, score 65) — Detects instructions to split/shard
   data across multiple HTTP requests. Covers the Silent Egress sharded exfiltration attack
   (arXiv:2602.22450). Requires "split/shard/fragment" AND network-request context to avoid
   false positives on benign "split document into sections" language.
   **→ IMPLEMENTED**

4. *(pending)* CSS hidden-text injection pattern — `style="color:\s*white"` or
   `style="display:\s*none"` with non-trivial content. Requires parsing HTML; too complex for
   a pure-regex DetectionPattern without risk of catastrophic backtracking on large HTML pages.

5. *(pending)* LogJack / cloud log injection — `grep|tail|awk` combined with injection keywords
   in log processing prompts. Needs more research on the exact prompt patterns used.
