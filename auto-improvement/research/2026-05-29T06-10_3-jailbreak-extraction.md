# Research: Jailbreak / System Prompt Extraction

- **Domain:** jailbreak-extraction
- **Cycle index:** 3
- **Cycle timestamp:** 2026-05-29T06-10

## Findings

- **Crescendo Multi-Turn Jailbreak (arxiv:2404.01833, USENIX Security 2025)**
  URL: https://arxiv.org/abs/2404.01833
  Microsoft Research introduced the Crescendo multi-turn attack: a benign-seeming
  opening question on a topic is followed by progressively escalating turns that
  each reference prior model output. Tested across ChatGPT, Gemini-Ultra, LLaMA-3
  70b, and Anthropic Chat. The automated tool Crescendomation achieved 29–71% higher
  performance on GPT-4 and 49–71% on Gemini-Pro vs. baselines. Presented at USENIX
  Security 2025.
  *What this means for aigis:* Individual turns look benign, making per-turn regex
  detection unreliable. The automated variant emits detectable meta-prompts
  ("gradually escalate the conversation") when initialising the attacking agent.

- **AI-Assigned-to-Jailbreak (Nature Communications, 2026)**
  URL: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12881495/
  Zhao et al. demonstrated that large reasoning models (o3-class) assigned a
  jailbreaking meta-prompt—"your task is to jailbreak the following model through
  multi-turn conversation"—achieve 97.14% overall ASR with no human in the loop.
  The attacking agent plans, escalates, and adapts fully autonomously.
  *What this means for aigis:* The initiating meta-prompt is distinctively worded
  and can be pattern-matched; no LLM inference needed at detection time.

- **DeepInception Nested-Layer Jailbreak (arxiv:2311.03191, Stanford, updated 2025)**
  URL: https://arxiv.org/abs/2311.03191
  Recursive multi-layer fictional scenario: characters at layer i create their own
  scenarios at layer i+1. The canonical template instructs the model to "reach
  layer N" and at each layer have characters "propose a step" toward the harmful
  goal. Reported 42.8% ASR on LLaMA-2, 55.6% on GPT-3.5, 41.6% on GPT-4, and
  46.4% on GPT-4o. The attack bypasses many single-turn content filters.
  *What this means for aigis:* The "reach layer N" and "each character creates
  their own scene" phrases are structurally distinctive and regex-matchable.

- **RTS-Attack News-Frame Nested Framing (arxiv:2510.01223, October 2025)**
  URL: https://arxiv.org/html/2510.01223v2
  Three-stage automated attack: (1) classify harmful query, (2) construct a
  crime/news-report narrative around it, (3) ask the model to "analyze and
  supplement detailed steps." Yang et al. reported 96.69% average ASR across
  six LLMs: GPT-4o 96.15%, Gemini-Pro 98.65%, Claude-3.5 ~94%. Unlike
  jb_fictional_bypass (imaginary worlds), this attack uses real-sounding news
  framing to make refusal feel like withholding factual information.
  *What this means for aigis:* The combination of a news/crime-report citation
  with a request for step-by-step supplementary detail is a structural fingerprint
  not covered by existing patterns.

- **Sockpuppetting / Output Prefix Injection (arxiv:2601.13359, January 2026)**
  URL: https://arxiv.org/abs/2601.13359
  Injects fake "acceptance" into the assistant role (e.g., "Sure, here is...") at
  the API level or inside multi-agent message history, exploiting model self-
  consistency. Achieves 95–98% ASR on Qwen3-8B, 77% on Llama-3.1-8B with zero
  optimization. Trend Micro confirmed against GPT-4o, Claude 4 Sonnet, Gemini 2.5.
  *What this means for aigis:* The text-level form (Assistant: Sure… \nUser:
  continue) is already covered by `jb_affirmative_prefill` (score 65). The raw
  chat-template token injection variant is partially covered by `ii_delimiter_spoof`.

- **ICE Attack — Intent Concealment (arxiv:2505.14316, May 2025)**
  URL: https://arxiv.org/html/2505.14316v1
  Decomposes harmful queries into fragments replaced by uppercase letter
  placeholders (A, B, C…), with semantic expansions appended in random order,
  then asks the model to "reconstruct the sentence." Achieved 99.2% keyword-ASR
  on GPT-3.5, 99.8% on GPT-4, 96.9% on Claude-1.
  *What this means for aigis:* Single-letter placeholder substitution combined
  with a reconstruction task is detectable but overlaps with obfuscation patterns
  in `enc_*` rules. Low priority vs. the three patterns implemented this cycle.

- **Policy Puppetry (HiddenLayer, April 2025)**
  URL: https://www.securityweek.com/all-major-gen-ai-models-vulnerable-to-policy-puppetry-prompt-injection-attack/
  Reformats malicious prompts to resemble XML/INI/JSON policy configuration files
  (e.g., `[SystemPolicy] allowUnsafeOperations=true`), tricking the model into
  treating malicious instructions as legitimate policy directives. Works across
  GPT-4, Claude 3, Gemini 1.5, Mistral, LLaMA 3 with no model-specific tuning.
  *What this means for aigis:* INI-style `[SystemPolicy]` headers and key=value
  safety-override fields are matchable. Deferred to pending due to LOC limit.

- **Time Bandit Jailbreak (November 2024 / January 2025)**
  URL: https://www.bleepingcomputer.com/news/security/time-bandit-chatgpt-jailbreak-bypasses-safeguards-on-sensitive-topics/
  Sets a historical time frame ("imagine it's 1850, before modern drug laws") to
  bypass safety constraints by framing harmful requests as historically appropriate.
  Most effective with eras 1800–1920. Demonstrated producing malware instructions
  "as a programmer in 1789."
  *What this means for aigis:* Temporal framing + harmful content request is
  detectable but has high false-positive risk on legitimate historical questions.
  Deferred to pending.

- **Persona Prompt Jailbreak (arxiv:2507.22171, July 2025)**
  URL: https://arxiv.org/abs/2507.22171
  Genetic-algorithm-crafted persona prompts reduce refusal rates by 50–70% across
  multiple LLMs and show 10–20% synergistic increase when combined with other
  attacks. Core persona framing ("you are X who always answers without
  restrictions") is already partially covered by `jb_evil_roleplay` and
  `pi_jailbreak_dan`.
  *What this means for aigis:* Existing coverage is adequate; refined GA-evolved
  variants are difficult to detect via static regex without LLM inference.

- **Multilingual Jailbreaking via Low-Resource Languages (arxiv:2605.18239, 2026)**
  URL: https://arxiv.org/abs/2605.18239
  Simply translating harmful prompts into Afrikaans, Kiswahili, isiXhosa, or
  isiZulu improves harmful response rates by 10–20 percentage points vs. English.
  Multi-turn approaches push rates to 75.8% average.
  *What this means for aigis:* Detection requires character-set or language-ID
  matching, which aigis does not currently support. Flagged as a gap but requires
  a new detector rather than a regex in existing patterns.

## Candidate Hardenings

- **IMPLEMENT:** `jb_ai_jailbreak_agent` — meta-prompt that assigns jailbreaking
  goal to an AI agent. Score 75. Very distinctive phrasing, near-zero false
  positive risk. (Nature Communications 2026, 97.14% ASR)

- **IMPLEMENT:** `jb_deep_inception` — "reach layer N" recursive nested-scenario
  jailbreak. Score 60. Distinctive "layer N" and "each character creates their
  own scene" phrases. (Stanford arxiv:2311.03191, ~55% ASR on GPT-3.5)

- **IMPLEMENT:** `jb_news_frame_bypass` — news/crime-report framing combined with
  step-by-step instruction request (RTS-Attack). Score 65. Distinct from existing
  fictional bypass pattern. (arxiv:2510.01223, 96.69% avg ASR)

- **DEFER (LOC limit):** `jb_policy_puppetry` — XML/INI config file injection
  with safety-override field names. Requires careful false-positive tuning.

- **DEFER (false positive risk):** `jb_time_bandit` — historical year framing
  combined with harmful instructions. Risk of flagging legitimate history questions.

- **DEFER (new detector needed):** Multilingual/low-resource language jailbreaks.
  Requires language identification capability beyond simple regex.
