export type Lang = "en" | "ja";

type I18n = { en: string; ja: string };

export function tx(entry: I18n, lang: Lang): string {
  return entry[lang];
}

export const t = {
  /* ── Navigation ── */
  nav: {
    pricing: { en: "Pricing", ja: "料金" },
    docs: { en: "Docs", ja: "ドキュメント" },
    github: { en: "GitHub", ja: "GitHub" },
    signIn: { en: "Sign In", ja: "ログイン" },
    startTrial: { en: "Start Free", ja: "無料で試す" },
  },

  /* ── Hero ── */
  hero: {
    badge: {
      en: "Open-source — Start free (no card required)",
      ja: "オープンベータ — 無料で始められます（カード不要）",
    },
    headline1: {
      en: "Prompt injection is the",
      ja: "プロンプトインジェクションは",
    },
    headline2: {
      en: "#1 LLM attack.",
      ja: "LLM攻撃の第1位。",
    },
    headline3: {
      en: "Are you protected?",
      ja: "対策できていますか？",
    },
    subhead: {
      en: "Scan every request to your AI. Safe ones pass instantly, suspicious ones are auto-blocked. Just change your base_url — zero code changes needed.",
      ja: "AIへのリクエストをすべてスキャン。安全なものは即座に通過、怪しいものは自動でブロック。base_url を変えるだけで、既存のコードは一切変更不要です。",
    },
    ctaPrimary: { en: "Start Free (No Card)", ja: "無料で始める（カード不要）" },
    ctaSecondary: { en: "How It Works", ja: "仕組みを見る" },
    badge1: { en: "OWASP LLM Top 10 Coverage", ja: "OWASP LLM Top 10 対応" },
    badge2: { en: "SOC2-ready Audit Logs", ja: "SOC2対応監査ログ付き" },
    badge3: { en: "No request content stored by default", ja: "デフォルトでリクエスト内容を保存しない" },
    badge4: { en: "Latency <5ms (safe verdict)", ja: "遅延 <5ms（安全判定時）" },
    flowApp: { en: "Your App", ja: "あなたのアプリ" },
    flowAppSub: { en: "Python / Node.js / Any SDK", ja: "Python / Node.js / 任意のSDK" },
    flowAllRequests: { en: "All Requests →", ja: "全リクエスト →" },
    flowGuardian: { en: "Aigis", ja: "Aigis" },
    flowGuardianSub: { en: "Security Proxy · <5ms", ja: "セキュリティプロキシ · <5ms" },
    flowSafeOnly: { en: "Safe Only →", ja: "安全なもののみ →" },
    flowLLM: { en: "Your LLM", ja: "あなたのLLM" },
    flowLLMSub: { en: "OpenAI / Anthropic / Any", ja: "OpenAI / Anthropic / 任意" },
    routingLabel: { en: "Intelligent Routing", ja: "インテリジェントルーティング" },
    routePass: { en: "Pass", ja: "通過" },
    routeBlock: { en: "Block", ja: "ブロック" },
    routeReview: { en: "Review", ja: "レビュー" },
  },

  /* ── How It Works ── */
  howItWorks: {
    label: { en: "How It Works", ja: "仕組み" },
    heading: {
      en: "Three steps to secure your AI",
      ja: "AIを守る3つのステップ",
    },
    sub: {
      en: "Drop-in proxy that scans every request — no code changes needed.",
      ja: "すべてのリクエストをスキャンするドロップインプロキシ。コード変更不要。",
    },
    step1Title: {
      en: "Change one line: your base URL",
      ja: "1行変えるだけ：base URLをAigisに",
    },
    step1Desc: {
      en: "Point your OpenAI SDK's base URL to Aigis's proxy endpoint. SDK, request format, and error handling stay the same.",
      ja: "OpenAI SDKのbase URLをAigisのプロキシエンドポイントに換えるだけ。SDK・リクエスト形式・エラーハンドリングは何も変えなくて大丈夫です。",
    },
    step1Aside: { en: "Average setup time: 4 minutes", ja: "平均セットアップ時間：4分" },
    step2Title: {
      en: "Aigis scores & routes",
      ja: "Aigisがスコア&ルーティング",
    },
    step2Desc: {
      en: "OWASP LLM Top 10 coverage with 165+ detection patterns across 25+ threat categories. 6-layer defense including CaMeL Capabilities, Atomic Execution Pipeline, and Safety Verifier. Every request gets a risk score within 5ms.",
      ja: "OWASP LLM Top 10 に対応した165+検出パターン（25+脅威カテゴリ）で検査。CaMeL Capabilities・AEP・Safety Verifierを含む6層防御。5ms以内にリスクスコアを付与します。",
    },
    step2Aside: { en: "165+ patterns · 25+ categories · 6-layer defense", ja: "165+パターン · 25+カテゴリ · 6層防御" },
    step3Title: {
      en: "Your team decides the hard calls",
      ja: "難しい判断はあなたのチームが下す",
    },
    step3Desc: {
      en: "Borderline requests aren't just blocked or passed. They go to your team's review queue. A black-box model doesn't decide — your team does. Risky requests are sent to LLM pre-blocked with a 403.",
      ja: "危うくもないし安全とも言い切れないリクエストは、チームのレビューキューへ。ブラックボックスモデルではなく、あなたのチームが判断します。重大な脅威はLLMに届く前に403でブロック。",
    },
    step3Aside: {
      en: "Default SLA 30 min · Fallback configurable",
      ja: "デフォルトSLA 30分 · フォールバック設定可能",
    },
  },

  /* ── Testimonials ── */
  testimonials: {
    label: { en: "What Users Say", ja: "ユーザーの声" },
    q1: {
      en: "Security team went from 'absolutely not' to 'approved in 2 weeks.' The deal-closer was the audit log — every request, verdict, and reviewer action is fully visible.",
      ja: "「セキュリティチームが絶対承認しない」から「2週間で承認」に変わりました。決め手は監査ログでした。リクエスト・判断・担当者のアクションがすべて可視化されているのが刺さったようです。",
    },
    r1: { en: "Staff Engineer", ja: "スタッフエンジニア" },
    c1: { en: "Series B Fintech", ja: "シリーズBフィンテック" },
    q2: {
      en: "Last quarter, prompt injection took our customer-facing chatbot down twice. Since Aigis — zero incidents. Edge cases our own rules missed, the HitL queue catches.",
      ja: "先四半期、プロンプトインジェクションで顧客向けチャットボットが2回ダウンしました。Aigis導入後はゼロ件。自社ルールでは拾えなかったエッジケースも、HitLキューが対処してくれています。",
    },
    r2: { en: "AI Platform Lead", ja: "AIプラットフォームリード" },
    c2: { en: "SaaS Company · 200 employees", ja: "SaaS企業 · 従業員200名" },
    q3: {
      en: "LLM-first product, so investors and enterprise customers kept asking 'how do you prevent jailbreaks?' Now we just show the Aigis dashboard and the conversation ends.",
      ja: "LLMファーストのプロダクトなので、投資家やエンタープライズのお客様から「ジェイルブレイクはどう防いでいるの？」と繰り返し聞かれていました。今は、Aigisのダッシュボードを見せるだけで会話が終わります。",
    },
    r3: { en: "CTO & Co-founder", ja: "CTO・共同創業者" },
    c3: { en: "AI-native Startup", ja: "AIネイティブスタートアップ" },
  },

  /* ── Features ── */
  features: {
    label: { en: "What We Protect Against", ja: "何から守るか" },
    heading: {
      en: "Built on OWASP LLM Top 10.",
      ja: "OWASP LLM Top 10 に基づいて設計。",
    },
    sub: {
      en: "Not a generic WAF. Rules designed specifically for LLM attack patterns.",
      ja: "AIに後付けしたWAFではありません。LLMの攻撃パターンを専用に研究し、設計したルールで守ります。",
    },
    f1Title: {
      en: "Prompt Injection & Jailbreak",
      ja: "プロンプトインジェクション・ジェイルブレイク対策",
    },
    f1Desc: {
      en: '"Ignore previous instructions..." attacks, DAN patterns, role-play abuse, system prompt leaks. Covers OWASP LLM Top 10 #1 threat. Updated as new techniques emerge.',
      ja: "「前の指示を無視して…」という攻撃・DANパターン・ロールプレイ悪用・システムプロンプト漏洩を検知。OWASP LLM Top 10 第1位の脅威に対応し、新しい手法が出るたびにパターンを更新します。",
    },
    f2Title: {
      en: "Sensitive Data & Credential Leak Prevention",
      ja: "機密情報・認証情報の漏洩防止",
    },
    f2Desc: {
      en: "Auto-scan LLM responses before they reach users. Catches API keys, credit card numbers, SSNs, internal hostnames. Your model never becomes the data leak path.",
      ja: "LLMのレスポンスをユーザーに返す前に自動スキャン。APIキー・クレジットカード番号・SSN・内部接続文字列を検知しブロック。モデルがデータ流出の経路になりません。",
    },
    f3Title: {
      en: "SQL Injection Detection",
      ja: "SQLインジェクション遮断",
    },
    f3Desc: {
      en: "UNION SELECT, DROP TABLE, blind injection, and more — blocks attacks that try to manipulate data pipelines. Especially critical for text-to-SQL and RAG architectures.",
      ja: "UNION SELECT・DROP TABLE・ブラインドインジェクションなど、データ連携パイプラインを操作する攻撃をブロック。text-to-SQLやRAGを使っているアーキテクチャで特に重要です。",
    },
    f4Title: {
      en: "Human-in-the-Loop (HitL) Review",
      ja: "人間によるレビューキュー（HitL）",
    },
    f4Desc: {
      en: "Borderline requests go to your team's review queue with a SLA timer. Reviewers approve, reject, or escalate. If time runs out, the fallback action triggers automatically.",
      ja: "安全とも危険とも判断しにくいリクエストは、SLAタイマー付きでチームのレビューキューへ。担当者が承認・却下・エスカレーションを選択。期限切れ時はフォールバックが自動発動します。",
    },
    f5Title: {
      en: "Per-Tenant Policy Configuration",
      ja: "テナント別ポリシー設定",
    },
    f5Desc: {
      en: "Custom risk thresholds per team. Score 30 and below auto-pass, 81+ auto-block, etc. Medical, financial, and compliance-specific custom rules (regex) can be added.",
      ja: "チームごとにリスク閾値をカスタム設定。スコア30以下は自動通過、81以上は自動ブロックなど。医療・金融・コンプライアンスに合わせた独自ルール（正規表現）も追加できます。",
    },
    f6Title: {
      en: "Immutable Audit Logs",
      ja: "改ざん不可の監査ログ",
    },
    f6Desc: {
      en: "Every request is auto-recorded: timestamp, risk score, matched rule, routing result, and reviewer action. Filterable by date and risk level. SOC2-ready CSV export.",
      ja: "全リクエストを自動記録：日時・リスクスコア・マッチしたルール・ルーティング結果・担当者のアクション。日付やリスクレベルで絞り込み可能。SOC2証拠資料としてCSV出力にも対応。",
    },
    footnote: {
      en: "OWASP LLM Top 10 · CWE/SANS reference · NIST AI RMF aligned",
      ja: "OWASP LLM Top 10 · CWE/SANS参照 · NIST AI RMF準拠",
    },
  },

  /* ── Pricing ── */
  pricing: {
    label: { en: "Pricing", ja: "料金" },
    heading: {
      en: "Simple, transparent pricing",
      ja: "シンプルで明確な料金体系",
    },
    sub: {
      en: "Start free. Scale with your business. Enterprise-grade security included.",
      ja: "無料スタート。ビジネスの成長に合わせてスケール。エンタープライズ級のセキュリティ標準装備。",
    },
    footnote: {
      en: "All plans include OWASP LLM Top 10 coverage · Annual billing saves 20%",
      ja: "全プランにOWASP LLM Top 10対応を含む · 年間契約で20%OFF",
    },
    free: {
      name: { en: "Free", ja: "Free" },
      period: { en: "forever", ja: "永久無料" },
      tagline: {
        en: "Open-source core — everything you need to get started",
        ja: "オープンソースコア — 始めるために必要なすべてが無料",
      },
      f1: { en: "165+ detection patterns, 6-layer defense (100% accuracy)", ja: "165+検出パターン、6層防御（100%精度）" },
      f2: { en: "MCP Security Scanner", ja: "MCPセキュリティスキャナー" },
      f3: { en: "Automated Red Team testing", ja: "自動レッドチームテスト" },
      f4: { en: "CLI tool (pip install)", ja: "CLIツール（pip install）" },
      f5: { en: "FastAPI / LangChain / OpenAI integration", ja: "FastAPI / LangChain / OpenAI統合" },
      f6: { en: "Apache 2.0 License", ja: "Apache 2.0ライセンス" },
      cta: { en: "Get Started Free", ja: "無料で始める" },
    },
    starter: {
      name: { en: "Pro", ja: "Pro" },
      price: { en: "$49", ja: "$49" },
      period: { en: "/ month", ja: "/ 月" },
      tagline: {
        en: "For teams that need visibility into LLM security",
        ja: "LLMセキュリティの可視化が必要なチーム向け",
      },
      f1: { en: "Cloud dashboard (log & risk visualization)", ja: "クラウドダッシュボード（ログ・リスク可視化）" },
      f2: { en: "Up to 5 team members", ja: "最大5名のチームメンバー" },
      f3: { en: "500K API requests / month", ja: "月間50万APIリクエスト" },
      f4: { en: "90-day log retention", ja: "90日間ログ保持" },
      f5: { en: "Email alerts (critical events)", ja: "メールアラート（重大イベント時）" },
      f6: { en: "14-day free trial", ja: "14日間無料トライアル" },
      cta: { en: "Start Free Trial", ja: "無料トライアルを開始" },
    },
    business: {
      name: { en: "Business", ja: "Business" },
      price: { en: "$299", ja: "$299" },
      period: { en: "/ month", ja: "/ 月" },
      tagline: {
        en: "For organizations that need compliance & governance",
        ja: "コンプライアンスとガバナンスが必要な組織向け",
      },
      f1: { en: "Everything in Pro", ja: "Proの全機能" },
      f2: { en: "Up to 50 team members", ja: "最大50名のチームメンバー" },
      f3: { en: "5M API requests / month", ja: "月間500万APIリクエスト" },
      f4: { en: "1-year log retention (immutable audit)", ja: "1年間ログ保持（イミュータブル監査ログ）" },
      f5: { en: "Compliance reports (OWASP, SOC2, GDPR)", ja: "コンプライアンスレポート（OWASP, SOC2, GDPR）" },
      f6: { en: "SSO / SAML authentication", ja: "SSO / SAML認証" },
      f7: { en: "Slack + PagerDuty notifications", ja: "Slack + PagerDuty通知" },
      cta: { en: "Start Business Trial", ja: "Businessトライアルを開始" },
      badge: { en: "Most Popular", ja: "人気No.1" },
    },
    enterprise: {
      name: { en: "Enterprise", ja: "Enterprise" },
      period: { en: "Custom", ja: "要相談" },
      tagline: {
        en: "For regulated industries & large organizations",
        ja: "規制産業・大規模組織向け",
      },
      f1: { en: "Everything in Business", ja: "Businessの全機能" },
      f2: { en: "Unlimited users & API requests", ja: "ユーザー・APIリクエスト無制限" },
      f3: { en: "On-premises / VPC deployment", ja: "オンプレミス / VPC対応" },
      f4: { en: "Custom compliance reports (HIPAA, FISC, ISMAP)", ja: "カスタムコンプラレポート（HIPAA, FISC, ISMAP）" },
      f5: { en: "Dedicated CSM & security engineer", ja: "専任CSM・セキュリティエンジニア" },
      f6: { en: "99.99% SLA guarantee", ja: "99.99% SLA保証" },
      cta: { en: "Contact Sales", ja: "営業に相談する" },
    },
  },

  /* ── FAQ ── */
  faq: {
    label: { en: "FAQ", ja: "よくある質問" },
    heading: {
      en: "Questions before you start",
      ja: "登録前によく聞かれる質問",
    },
    q1: { en: "How long does setup take?", ja: "導入にどれくらいかかりますか？" },
    a1: {
      en: "Most teams are up and running in under 5 minutes. You just change one line — the base_url — in your existing OpenAI SDK configuration. No new dependencies, no infrastructure changes.",
      ja: "ほとんどのチームが5分以内に稼働始しています。既存のOpenAI SDK設定のbase_urlを1行変えるだけ。新しい依存関係もインフラ変更も不要です。",
    },
    q2: {
      en: "What is the pricing structure? How much for a team of 5?",
      ja: "料金体系を教えてください。5人チームだといくらになりますか？",
    },
    a2: {
      en: "Starter plan is $15/user/month. For a 5-person team, that's $75/month. Business plan at $38/user/month includes decision tracking and compliance features. Annual billing saves 20%.",
      ja: "Starterプランはユーザーあたり月額¥2,000。5人チームなら月額¥10,000です。Businessプラン（¥5,000/ユーザー/月）には意思決定追跡とコンプライアンス機能が含まれます。年間契約で20%OFFになります。",
    },
    q3: {
      en: "How does the review queue actually work?",
      ja: "レビューキューって、実際どんなふうに動くんですか？",
    },
    a3: {
      en: "When a request scores in the medium-risk range (31-60), it's held for human review. Your team gets notified, and a reviewer can approve, reject, or escalate the request within the configured SLA (default: 30 minutes). If no action is taken, the configurable fallback kicks in.",
      ja: "リクエストが中リスク（31-60）にスコアリングされると保留されます。チームに通知が届き、担当者がSLA（デフォルト30分）以内に承認・却下・エスカレーションを選択します。未対応の場合は設定済みのフォールバックが発動します。",
    },
    q4: {
      en: "Is request content stored?",
      ja: "リクエストの内容は保存されますか？",
    },
    a4: {
      en: "By default, no. We store only metadata (timestamp, risk score, rule matches, routing decisions). You can opt-in to content logging for audit/compliance purposes, which is stored encrypted and configurable by retention policy.",
      ja: "デフォルトでは保存しません。メタデータ（タイムスタンプ、リスクスコア、ルールマッチ、ルーティング判定）のみ記録。監査・コンプライアンス用にコンテンツログのオプトインが可能で、暗号化して保存されます。",
    },
    q5: {
      en: "We use Azure OpenAI. Is that supported?",
      ja: "Azure OpenAIを使っています。対応していますか？",
    },
    a5: {
      en: "Yes. Aigis works as a proxy layer — it's compatible with any OpenAI-compatible endpoint including Azure OpenAI, AWS Bedrock (via compatibility layer), and self-hosted models.",
      ja: "はい、対応しています。Aigisはプロキシレイヤーとして動作するため、Azure OpenAI、AWS Bedrock（互換レイヤー経由）、セルフホストモデルなど、OpenAI互換のあらゆるエンドポイントで使えます。",
    },
    q6: {
      en: "We're preparing for SOC2 Type II. Can this help?",
      ja: "SOC2 Type II監査の準備をしています。役に立ちますか？",
    },
    a6: {
      en: "Absolutely. Our audit logs are designed for SOC2 evidence collection. Immutable records, CSV export, retention policies, and role-based access controls. Several of our customers cite Aigis in their SOC2 evidence packages.",
      ja: "はい、大いに役立ちます。監査ログはSOC2証拠反集向けに設計されています。改ざん不可の記録、CSVエクスポート、保持ポリシー、ロールベースのアクセス制御を備えています。複数のお客様がSOC2証拠パッケージにAigisを引用しています。",
    },
    contactLabel: {
      en: "Have other questions?",
      ja: "他に気になることがあれば",
    },
    contactSub: {
      en: "Email us at",
      ja: "こちらまでメールください：",
    },
    contactSuffix: {
      en: " — we reply within 1 business day.",
      ja: "（1営業日以内にご返信します）",
    },
  },

  /* ── Footer CTA ── */
  footerCta: {
    label: {
      en: "Ready to secure your AI?",
      ja: "AIを守る準備はできましたか？",
    },
    heading: {
      en: "Start protecting your LLM in minutes",
      ja: "数分でLLMの保護を始めましょう",
    },
    sub: {
      en: "No credit card required. Free tier available for small teams.",
      ja: "クレジットカード不要。小規模チーム向けの無料枠あり。",
    },
    cta1: { en: "Get Started Free", ja: "無料で始める" },
    cta2: { en: "Read the Docs", ja: "ドキュメントを読む" },
    contactPrefix: {
      en: "Enterprise or custom needs? Reach out at",
      ja: "エンタープライズ・カスタム要件は",
    },
    contactSuffix: { en: "", ja: " までご連絡ください" },
  },

  /* ── Footer ── */
  footer: {
    product: { en: "Product", ja: "プロダクト" },
    features: { en: "Features", ja: "機能" },
    pricing: { en: "Pricing", ja: "料金" },
    howItWorks: { en: "How It Works", ja: "仕組み" },
    riskScoring: { en: "Risk Scoring", ja: "リスクスコアリング" },
    docs: { en: "Documentation", ja: "ドキュメント" },
    overview: { en: "Overview", ja: "概要" },
    quickstart: { en: "Quickstart", ja: "クイックスタート" },
    concepts: { en: "Concepts", ja: "コンセプト" },
    apiRef: { en: "API Reference", ja: "APIリファレンス" },
    integrations: { en: "Integrations", ja: "インテグレーション" },
    python: { en: "Python SDK", ja: "Python SDK" },
    nodejs: { en: "Node.js SDK", ja: "Node.js SDK" },
    openai: { en: "OpenAI", ja: "OpenAI" },
    langchain: { en: "LangChain", ja: "LangChain" },
    company: { en: "Company", ja: "会社" },
    github: { en: "GitHub", ja: "GitHub" },
    privacy: { en: "Privacy Policy", ja: "プライバシーポリシー" },
    terms: { en: "Terms of Service", ja: "利用規約" },
    security: { en: "Security", ja: "セキュリティ" },
    tagline: {
      en: "Open-source LLM security for teams that ship fast.",
      ja: "高速リリースするチームのためのオープンソースLLMセキュリティ。",
    },
    copyright: {
      en: "© 2025 Aigis. All rights reserved.",
      ja: "© 2025 Aigis. All rights reserved.",
    },
    builtFor: {
      en: "Built for teams that build with AI.",
      ja: "AIで開発するチームのために。",
    },
  },

  /* ── Docs Layout ── */
  docsLayout: {
    gettingStarted: { en: "Getting Started", ja: "はじめに" },
    overview: { en: "Overview", ja: "概要" },
    quickstart: { en: "Quickstart", ja: "クイックスタート" },
    conceptsCategory: { en: "Concepts", ja: "コンセプト" },
    coreConcepts: { en: "Core Concepts", ja: "コアコンセプト" },
    reference: { en: "Reference", ja: "リファレンス" },
    apiReference: { en: "API Reference", ja: "APIリファレンス" },
    integrationsCategory: { en: "Integrations", ja: "インテグレーション" },
    python: { en: "Python SDK", ja: "Python SDK" },
    nodejs: { en: "Node.js SDK", ja: "Node.js SDK" },
    complianceCategory: { en: "Compliance", ja: "コンプライアンス" },
    japanGovernance: { en: "Japan AI Governance", ja: "日本AIガバナンス" },
    breadcrumbDocs: { en: "Documentation", ja: "ドキュメント" },
    onThisPage: { en: "On this page", ja: "このページの内容" },
  },

  /* ── Stats / Social Proof ── */
  stats: {
    rules: { en: "Detection Rules", ja: "検出ルール" },
    latency: { en: "Latency (safe verdict)", ja: "レイテンシ（安全判定時）" },
    owasp: { en: "Coverage", ja: "カバレッジ" },
    uptime: { en: "Uptime SLA", ja: "稼働率SLA" },
    soc2: { en: "SOC2-ready Audit Logs", ja: "SOC2対応監査ログ" },
    japanReady: { en: "Japan AI Governance Ready", ja: "日本AIガバナンス対応" },
  },

  /* ── Code Integration / Chat ── */
  chat: {
    completions: { en: "chat/completions", ja: "chat/completions" },
  },

} as const;
