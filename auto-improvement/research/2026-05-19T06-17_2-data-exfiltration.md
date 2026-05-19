# Research: data-exfiltration — 2026-05-19T06-17

## Domain: data-exfiltration (index 2, fourth pass)
## Cycle timestamp: 2026-05-19T06-17
## Focus: CI/CD credential exfiltration via AI coding agents — "Comment and Control" attack class

Previous passes covered:
- Pass 1 (2026-05-07): markdown image URL exfil, OAST relay domains (`out_markdown_img_exfil`, `out_known_exfil_relay`)
- Pass 2 (2026-05-10): DNS encode instruct, reference-style Markdown exfil (EchoLeak), tunnel relay URLs
- Pass 3 (2026-05-13/14): Mermaid/PlantUML href exfil, web-search encode, HTML img exfil, Unicode tag block, sharded exfiltration
  Pending from pass 3: CSS hidden-text injection (needs HTML parser), LogJack cloud log injection

This pass targets a fresh April 2026 attack class affecting AI coding agents in CI/CD pipelines.

---

## Findings

- **"Comment and Control" — AI coding agent credential exfiltration via GitHub inputs** (Aonan Guan,
  Zhengyu Liu, Gavin Zhong / Johns Hopkins, April 2026): Researchers disclosed a class of indirect
  prompt-injection attacks that hijack AI coding agents by embedding malicious instructions in GitHub
  PR titles, issue bodies, and HTML comments (`<!-- ... -->`). When agents such as Claude Code Security
  Review, Google Gemini CLI Action, and GitHub Copilot Agent process these inputs, they treat the
  injected text as trusted instructions and execute shell commands including `env`, `printenv`, and
  `ps auxeww`, returning the full environment variable dump — including ANTHROPIC_API_KEY, GITHUB_TOKEN,
  and GEMINI_API_KEY — as a JSON "security finding" posted to the PR comment. HTML comments make the
  payload invisible to human reviewers in GitHub's rendered Markdown view but visible to the AI agent.
  All three vendors paid quiet bug bounties (Anthropic $100, GitHub $500, Google undisclosed) without
  publishing CVEs or public advisories.
  - Source: https://oddguan.com/blog/comment-and-control-prompt-injection-credential-theft-claude-code-gemini-cli-github-copilot/
  - Source: https://venturebeat.com/security/ai-agent-runtime-security-system-card-audit-comment-and-control-2026
  - Source: https://www.theregister.com/2026/04/15/claude_gemini_copilot_agents_hijacked/
  - **aigis takeaway**: Add input pattern `exfil_env_var_dump` (score 75) detecting instructions to
    run `env`, `printenv`, `ps auxeww`, or `/proc/self/environ`, and instructions to echo/output
    specific CI/CD credential names. **→ IMPLEMENTED this cycle.**

- **Credential Leakage in LLM Agent Skills** (arxiv:2604.03070, Apr 2026): Large-scale empirical
  study of 519 publicly available LLM agent skills found that 75.8% (394 skills) leak credentials
  through stdout capture — LLM frameworks capture stdout/stderr from tool calls and inject the output
  into the agent context, making any printed API keys directly retrievable via natural language queries.
  Skills that emit runtime diagnostics (env vars, service endpoints) inadvertently expose credentials.
  - Source: https://arxiv.org/abs/2604.03070
  - **aigis takeaway**: The output-filter (`filter_output`) should flag raw credential strings in
    agent tool output that gets surfaced to the LLM context. Existing `exfil_api_keys` partially
    covers but does not cover stdout-captured tool output specifically. Consider an output-side
    pattern for raw credential value patterns (sk-ant-..., ghp_..., ghs_...) — send to pending
    as this requires careful false-positive analysis.

- **CrewAI SSRF in RAG Search Tools — CVE-2026-2286** (CERT/CC VU#221883, March 2026):
  CrewAI's RAG search tools do not validate URLs provided at runtime, enabling an attacker to
  supply internal/cloud service URLs (e.g., AWS IMDS http://169.254.169.254/latest/meta-data/)
  via a prompt injection. The agent fetches the internal URL and returns cloud IAM credentials.
  CVSS score not yet public; associated local file read (CVE-2026-2285) and Docker sandbox bypass
  (CVE-2026-2287) compound the risk. Prompt injection achieves 65% data exfiltration success rate
  against GPT-4o-backed CrewAI agents in lab testing.
  - Source: https://kb.cert.org/vuls/id/221883
  - Source: https://www.securityweek.com/crewai-vulnerabilities-expose-devices-to-hacking/
  - **aigis takeaway**: Existing `mcp_aws_imds_url` pattern already covers AWS IMDS URL detection.
    The JSON loader path traversal (CVE-2026-2285) is a framework-level bug not detectable by
    aigis input filter. No new pattern needed this cycle.

- **Grafana AI Component Prompt Injection → External Image Exfil** (Noma Security / OWASP Q1 2026
  GenAI Exploit Report, April 2026): A flaw in Grafana's AI component let attackers supply a URL
  to external content containing hidden instructions. When processed, the AI rendered an external
  image whose URL encoded and transmitted enterprise telemetry, infrastructure, and financial data.
  Because Grafana often holds high-value observability data, a rendered `<img>` tag with encoded
  query parameters was sufficient to exfiltrate sensitive data to an attacker.
  - Source: https://genai.owasp.org/2026/04/14/owasp-genai-exploit-round-up-report-q1-2026/
  - **aigis takeaway**: Covered by existing `out_html_img_exfil` and `ii_exfil_via_markdown`
    patterns. The Grafana attack is a known exfil-via-img variant.

- **Indirect Injection Vulnerabilities in Agentic LLMs** (arxiv:2604.03870, Apr 2026): Systematic
  study across multiple LLM agent frameworks found that 73% of production deployments are vulnerable
  to indirect prompt injection leading to credential exfiltration, RCE, or data corruption. Attack
  success rates against state-of-the-art defenses exceed 85% with adaptive strategies. The dominant
  exfiltration channels remain (1) URL-embedded data, (2) tool call parameter stuffing, and (3) env
  var capture via shell command execution.
  - Source: https://arxiv.org/abs/2604.03870
  - **aigis takeaway**: Reinforces coverage gaps in CI/CD context. Env var capture via shell is the
    dominant channel not yet covered by aigis — addressed by `exfil_env_var_dump` this cycle.

- **"Prompt Injection Attacks on Agentic Coding Assistants"** (arxiv:2601.17548, Jan 2026):
  Analysis of vulnerabilities in AI coding assistant skills and tool ecosystems. Data exfiltration
  includes stealing source code, credentials, environment variables, API keys, and sensitive files.
  Attack success rates against defenses exceed 85% with adaptive payloads. Key vector: agent reads
  malicious file/URL, which contains injection instruction including env dump + post-back.
  - Source: https://arxiv.org/abs/2601.17548
  - **aigis takeaway**: Confirms env var dump + post-back as the dominant credential exfil vector
    for coding agents. Supports implementing `exfil_env_var_dump`.

---

## Candidate hardenings

1. **[IMPLEMENTED] `exfil_env_var_dump`** (input filter, score 75): Detect instructions to run
   `env`, `printenv`, `ps auxeww`, read `/proc/self/environ`, or to echo/output specific CI/CD
   credential variable names (ANTHROPIC_API_KEY, GITHUB_TOKEN, GEMINI_API_KEY, etc.).
   Source: "Comment and Control" (Guan et al., April 2026), arxiv:2604.03070.

2. **[PENDING] Raw credential string output filter**: Add output-side patterns for raw credential
   token formats (sk-ant-api03-..., ghp_..., ghs_..., AKIA...) to catch stdout-leaked credentials
   surfaced in LLM context. Requires careful false-positive analysis across token formats.
   Send to pending/.

3. **[PENDING] `exfil_css_hidden_text`** (from pass 3): Full implementation requires stdlib
   html.parser for DOM-level inspection of hidden elements. Kept in pending/.

4. **[PENDING] LogJack cloud log injection**: Detect injection markers in log-format strings passed
   to agent context. Kept in pending/.
