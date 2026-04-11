"use client";

import { useEffect, useState } from "react";
import { policiesApi, type Policy, type CustomRule } from "@/lib/api";
import { getLang, saveLang, type Lang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";

interface RuleTemplate {
  name: string;
  nameJa: string;
  pattern: string;
  score_delta: number;
  category: string;
  framework: string;
  frameworkJa: string;
}

const RULE_TEMPLATES: RuleTemplate[] = [
  // =====================================================================
  // 🇯🇵 JAPAN / 日本
  // =====================================================================

  // --- AI事業者ガイドライン v1.2 (MIC+METI) ---
  { name: "AI Guidelines: System Prompt Leak", nameJa: "AI事業者GL: システムプロンプト漏洩", pattern: "(show|reveal|output|print).{0,20}(system\\s*prompt|instructions|設定|指示)", score_delta: 70, category: "ai_governance", framework: "JP: AI Business Guidelines v1.2", frameworkJa: "🇯🇵 AI事業者ガイドライン v1.2" },
  { name: "AI Guidelines: Model Override", nameJa: "AI事業者GL: モデル動作の上書き", pattern: "(from\\s+now\\s+on|henceforth|今後は|これからは).{0,30}(ignore|disregard|無視|忘れ)", score_delta: 75, category: "ai_governance", framework: "JP: AI Business Guidelines v1.2", frameworkJa: "🇯🇵 AI事業者ガイドライン v1.2" },
  { name: "AI Guidelines: Fairness Violation", nameJa: "AI事業者GL: 公平性違反", pattern: "(discriminat|差別|偏見|bias).{0,30}(race|gender|age|性別|人種|年齢|国籍|障害)", score_delta: 60, category: "ai_governance", framework: "JP: AI Business Guidelines v1.2", frameworkJa: "🇯🇵 AI事業者ガイドライン v1.2" },

  // --- MIC AIセキュリティ技術ガイドライン (総務省 2026) ---
  { name: "MIC Security: Direct Prompt Injection", nameJa: "総務省GL: 直接プロンプトインジェクション", pattern: "(ignore|disregard|forget|override|無視|忘れ).{0,20}(previous|prior|above|earlier|前の|上記の|これまでの)", score_delta: 80, category: "ai_security", framework: "JP: MIC AI Security Guidelines", frameworkJa: "🇯🇵 総務省AIセキュリティ技術GL" },
  { name: "MIC Security: Indirect Injection", nameJa: "総務省GL: 間接プロンプトインジェクション", pattern: "<(IMPORTANT|SYSTEM|INSTRUCTION)>|\\[INST\\]|<<SYS>>", score_delta: 85, category: "ai_security", framework: "JP: MIC AI Security Guidelines", frameworkJa: "🇯🇵 総務省AIセキュリティ技術GL" },
  { name: "MIC Security: Sponge Attack (DoS)", nameJa: "総務省GL: スポンジ攻撃(DoS)", pattern: "(repeat|繰り返).{0,15}(infinite|forever|永遠|無限|10000)", score_delta: 65, category: "ai_security", framework: "JP: MIC AI Security Guidelines", frameworkJa: "🇯🇵 総務省AIセキュリティ技術GL" },

  // --- 個人情報保護法 (APPI) / マイナンバー法 ---
  { name: "APPI: My Number (12-digit)", nameJa: "個情法: マイナンバー", pattern: "\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b", score_delta: 90, category: "pii_japan", framework: "JP: APPI / My Number Act", frameworkJa: "🇯🇵 個人情報保護法/マイナンバー法" },
  { name: "APPI: JP Phone Number", nameJa: "個情法: 電話番号", pattern: "\\b0[789]0[\\s-]?\\d{4}[\\s-]?\\d{4}\\b", score_delta: 60, category: "pii_japan", framework: "JP: APPI / My Number Act", frameworkJa: "🇯🇵 個人情報保護法/マイナンバー法" },
  { name: "APPI: JP Bank Account", nameJa: "個情法: 銀行口座", pattern: "(普通|当座|口座)[\\s　]*[番号]?[\\s　]*\\d{6,8}", score_delta: 70, category: "pii_japan", framework: "JP: APPI / My Number Act", frameworkJa: "🇯🇵 個人情報保護法/マイナンバー法" },
  { name: "APPI: JP Address Pattern", nameJa: "個情法: 住所パターン", pattern: "(東京都|北海道|大阪府|京都府|.{2,3}県).{0,5}(市|区|町|村)", score_delta: 50, category: "pii_japan", framework: "JP: APPI / My Number Act", frameworkJa: "🇯🇵 個人情報保護法/マイナンバー法" },

  // =====================================================================
  // 🇺🇸 UNITED STATES / 米国
  // =====================================================================

  // --- OWASP LLM Top 10 (2025) ---
  { name: "OWASP LLM01: Role Hijacking", nameJa: "OWASP LLM01: ロール乗っ取り", pattern: "(you\\s+are\\s+now|act\\s+as|pretend\\s+to\\s+be|あなたは今から).{0,30}(unrestricted|evil|hack|制限なし)", score_delta: 80, category: "owasp_llm", framework: "US: OWASP LLM Top 10 (2025)", frameworkJa: "🇺🇸 OWASP LLM Top 10 (2025)" },
  { name: "OWASP LLM01: Encoded Injection", nameJa: "OWASP LLM01: エンコード攻撃", pattern: "(decode|base64|hex|rot13).{0,20}(follow|execute|実行|従)", score_delta: 70, category: "owasp_llm", framework: "US: OWASP LLM Top 10 (2025)", frameworkJa: "🇺🇸 OWASP LLM Top 10 (2025)" },
  { name: "OWASP LLM02: Sensitive Info Disclosure", nameJa: "OWASP LLM02: 機密情報漏洩", pattern: "(password|secret|token|api.?key|パスワード|秘密鍵)\\s*[=:].{0,30}[A-Za-z0-9+/]{8,}", score_delta: 85, category: "owasp_llm", framework: "US: OWASP LLM Top 10 (2025)", frameworkJa: "🇺🇸 OWASP LLM Top 10 (2025)" },
  { name: "OWASP LLM06: Excessive Agency", nameJa: "OWASP LLM06: 過剰な自律行動", pattern: "(execute|run|delete|drop|remove|rm\\s+-rf|削除|実行).{0,20}(all|every|everything|全て|すべて)", score_delta: 75, category: "owasp_llm", framework: "US: OWASP LLM Top 10 (2025)", frameworkJa: "🇺🇸 OWASP LLM Top 10 (2025)" },
  { name: "OWASP LLM07: System Prompt Leakage", nameJa: "OWASP LLM07: システムプロンプト漏洩", pattern: "(repeat|print|show|echo|display).{0,15}(system|initial|original|first).{0,10}(prompt|instruction|message)", score_delta: 70, category: "owasp_llm", framework: "US: OWASP LLM Top 10 (2025)", frameworkJa: "🇺🇸 OWASP LLM Top 10 (2025)" },

  // --- OWASP Agentic Top 10 (2026) ---
  { name: "OWASP ASI01: Agent Goal Hijack", nameJa: "OWASP ASI01: エージェント目的乗っ取り", pattern: "(new\\s+(goal|objective|task|mission)|目標変更|目的を変え).{0,30}(instead|replace|now|今から)", score_delta: 80, category: "owasp_agent", framework: "US: OWASP Agentic Top 10 (2026)", frameworkJa: "🇺🇸 OWASP Agentic Top 10 (2026)" },
  { name: "OWASP ASI02: Tool Misuse", nameJa: "OWASP ASI02: ツール悪用", pattern: "(call|invoke|use|execute).{0,15}(tool|function|api).{0,20}(unauthorized|forbidden|禁止|許可なし)", score_delta: 75, category: "owasp_agent", framework: "US: OWASP Agentic Top 10 (2026)", frameworkJa: "🇺🇸 OWASP Agentic Top 10 (2026)" },
  { name: "OWASP ASI05: Memory Poisoning", nameJa: "OWASP ASI05: メモリ汚染", pattern: "(remember|store|save|記憶|保存).{0,20}(from\\s+now|always|永久に|今後ずっと).{0,20}(instruction|rule|ルール|指示)", score_delta: 70, category: "owasp_agent", framework: "US: OWASP Agentic Top 10 (2026)", frameworkJa: "🇺🇸 OWASP Agentic Top 10 (2026)" },
  { name: "OWASP ASI06: Uncontrolled Cascading", nameJa: "OWASP ASI06: 無制御カスケード", pattern: "(chain|cascade|pipe|delegate|spawn).{0,20}(unlimited|infinite|no.?limit|制限なし|無限)", score_delta: 70, category: "owasp_agent", framework: "US: OWASP Agentic Top 10 (2026)", frameworkJa: "🇺🇸 OWASP Agentic Top 10 (2026)" },

  // --- NIST AI RMF / MITRE ATLAS ---
  { name: "NIST AI RMF: Model Provenance Missing", nameJa: "NIST AI RMF: モデル出自不明", pattern: "(unknown\\s+model|unverified|provenance|出自不明|検証未).{0,20}(source|origin|供給元)", score_delta: 50, category: "nist", framework: "US: NIST AI RMF + MITRE ATLAS", frameworkJa: "🇺🇸 NIST AI RMF / MITRE ATLAS" },
  { name: "MITRE ATLAS: Model Extraction", nameJa: "MITRE ATLAS: モデル抽出攻撃", pattern: "(extract|steal|copy|clone|replicate).{0,20}(model|weight|parameter|モデル|重み)", score_delta: 75, category: "nist", framework: "US: NIST AI RMF + MITRE ATLAS", frameworkJa: "🇺🇸 NIST AI RMF / MITRE ATLAS" },
  { name: "MITRE ATLAS: Adversarial Evasion", nameJa: "MITRE ATLAS: 敵対的回避", pattern: "(adversarial|perturbation|evasion|bypass\\s+detection|検知回避|フィルタ回避)", score_delta: 65, category: "nist", framework: "US: NIST AI RMF + MITRE ATLAS", frameworkJa: "🇺🇸 NIST AI RMF / MITRE ATLAS" },

  // --- SOC2 / Infrastructure ---
  { name: "SOC2: AWS Access Key", nameJa: "SOC2: AWSアクセスキー", pattern: "\\bAKIA[0-9A-Z]{16}\\b", score_delta: 90, category: "infra", framework: "US: SOC2 / Infrastructure", frameworkJa: "🇺🇸 SOC2（インフラセキュリティ）" },
  { name: "SOC2: Private Key Block", nameJa: "SOC2: 秘密鍵", pattern: "-----BEGIN\\s+(RSA\\s+)?PRIVATE\\s+KEY-----", score_delta: 95, category: "infra", framework: "US: SOC2 / Infrastructure", frameworkJa: "🇺🇸 SOC2（インフラセキュリティ）" },
  { name: "SOC2: Connection String", nameJa: "SOC2: DB接続文字列", pattern: "(postgres|mysql|mongodb|redis)://[^\\s]+:[^\\s]+@", score_delta: 85, category: "infra", framework: "US: SOC2 / Infrastructure", frameworkJa: "🇺🇸 SOC2（インフラセキュリティ）" },

  // --- HIPAA ---
  { name: "HIPAA: Medical Record Number", nameJa: "HIPAA: カルテ番号", pattern: "\\b(MRN|medical\\s+record)\\s*[:#]?\\s*\\d{6,10}\\b", score_delta: 70, category: "healthcare", framework: "US: HIPAA", frameworkJa: "🇺🇸 HIPAA（医療情報）" },
  { name: "HIPAA: Patient + Diagnosis", nameJa: "HIPAA: 患者名+診断", pattern: "(patient|患者).{0,30}(diagnos|symptom|治療|診断|処方)", score_delta: 60, category: "healthcare", framework: "US: HIPAA", frameworkJa: "🇺🇸 HIPAA（医療情報）" },

  // --- PCI-DSS ---
  { name: "PCI-DSS: Credit Card Number", nameJa: "PCI-DSS: クレジットカード番号", pattern: "\\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{1}|6011)[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b", score_delta: 90, category: "payment", framework: "US: PCI-DSS", frameworkJa: "🇺🇸 PCI-DSS（決済セキュリティ）" },
  { name: "PCI-DSS: CVV Code", nameJa: "PCI-DSS: CVVコード", pattern: "\\b(cvv|cvc|cvv2|cvc2|セキュリティコード)\\s*[:#]?\\s*\\d{3,4}\\b", score_delta: 80, category: "payment", framework: "US: PCI-DSS", frameworkJa: "🇺🇸 PCI-DSS（決済セキュリティ）" },

  // --- Colorado AI Act ---
  { name: "Colorado: Algorithmic Discrimination", nameJa: "コロラドAI法: アルゴリズム差別", pattern: "(automat|AI|algorithm).{0,20}(denied|rejected|disqualified|不合格|却下).{0,20}(loan|credit|employ|housing|融資|雇用|住宅)", score_delta: 65, category: "us_state", framework: "US: Colorado AI Act (SB24-205)", frameworkJa: "🇺🇸 コロラドAI法" },

  // =====================================================================
  // 🇨🇳 CHINA / 中国
  // =====================================================================

  // --- 生成式AI管理暫行弁法 (Interim Measures for GenAI) ---
  { name: "CN GenAI: Subversion Incitement", nameJa: "中国GenAI規制: 国家転覆の扇動", pattern: "(subvert|overthrow|颠覆|推翻).{0,20}(state|government|regime|国家|政権|政府)", score_delta: 95, category: "cn_content", framework: "CN: GenAI Interim Measures", frameworkJa: "🇨🇳 生成式AI管理暫行弁法" },
  { name: "CN GenAI: Terrorism Content", nameJa: "中国GenAI規制: テロリズム", pattern: "(terroris|extremis|恐怖主义|极端主义).{0,20}(promote|spread|teach|宣扬|传播|教唆)", score_delta: 95, category: "cn_content", framework: "CN: GenAI Interim Measures", frameworkJa: "🇨🇳 生成式AI管理暫行弁法" },
  { name: "CN GenAI: Ethnic Discrimination", nameJa: "中国GenAI規制: 民族差別", pattern: "(ethnic|racial|民族|种族).{0,20}(hatred|discriminat|歧视|仇恨|偏见)", score_delta: 85, category: "cn_content", framework: "CN: GenAI Interim Measures", frameworkJa: "🇨🇳 生成式AI管理暫行弁法" },
  { name: "CN GenAI: Missing Content Watermark", nameJa: "中国GenAI規制: コンテンツ透かし欠如", pattern: "(AI.?generated|人工智能生成|机器生成).{0,20}(without|no|未|缺少).{0,10}(label|mark|watermark|标识|水印)", score_delta: 60, category: "cn_content", framework: "CN: GenAI Interim Measures", frameworkJa: "🇨🇳 生成式AI管理暫行弁法" },

  // --- 中国 PIPL (Personal Information Protection Law) ---
  { name: "CN PIPL: Chinese ID Number", nameJa: "中国PIPL: 身分証番号", pattern: "\\b[1-9]\\d{5}(19|20)\\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])\\d{3}[\\dXx]\\b", score_delta: 90, category: "pii_china", framework: "CN: PIPL", frameworkJa: "🇨🇳 個人情報保護法 (PIPL)" },
  { name: "CN PIPL: CN Phone Number", nameJa: "中国PIPL: 中国携帯番号", pattern: "\\b1[3-9]\\d{9}\\b", score_delta: 60, category: "pii_china", framework: "CN: PIPL", frameworkJa: "🇨🇳 個人情報保護法 (PIPL)" },
  { name: "CN PIPL: Cross-border Transfer", nameJa: "中国PIPL: 越境データ移転", pattern: "(cross.?border|overseas|transfer|出境|跨境|境外).{0,20}(data|personal|info|数据|个人信息)", score_delta: 70, category: "pii_china", framework: "CN: PIPL", frameworkJa: "🇨🇳 個人情報保護法 (PIPL)" },

  // --- 中国 AI安全ガバナンスフレームワーク v2.0 (TC260) ---
  { name: "CN AI Safety: Risk Level Violation", nameJa: "中国AI安全FW: リスクレベル違反", pattern: "(high.?risk|critical.?risk|高风险|关键风险).{0,20}(without|no|missing|未|缺少).{0,15}(assessment|review|评估|审查)", score_delta: 70, category: "cn_safety", framework: "CN: AI Safety Governance v2.0", frameworkJa: "🇨🇳 AI安全治理フレームワーク v2.0" },
  { name: "CN AI Safety: Uncontrolled AI Boundary", nameJa: "中国AI安全FW: AI制御境界逸脱", pattern: "(autonomous|自主|自律).{0,20}(beyond|exceed|outside|超出|突破).{0,15}(boundary|limit|scope|边界|范围)", score_delta: 75, category: "cn_safety", framework: "CN: AI Safety Governance v2.0", frameworkJa: "🇨🇳 AI安全治理フレームワーク v2.0" },

  // --- 中国 アルゴリズム推薦管理規定 ---
  { name: "CN Algorithm: Opinion Manipulation", nameJa: "中国アルゴリズム規定: 世論操作", pattern: "(manipulat|amplif|操纵|放大).{0,20}(public\\s+opinion|sentiment|舆论|情绪|民意)", score_delta: 80, category: "cn_algo", framework: "CN: Algorithm Recommendation Rules", frameworkJa: "🇨🇳 アルゴリズム推薦管理規定" },

  // =====================================================================
  // 🌐 INTERNATIONAL / 国際標準
  // =====================================================================

  // --- GDPR ---
  { name: "GDPR: EU Passport Number", nameJa: "GDPR: EUパスポート番号", pattern: "\\b[A-Z]{2}\\d{7,9}\\b", score_delta: 60, category: "pii_eu", framework: "EU: GDPR", frameworkJa: "🇪🇺 GDPR（EU個人情報）" },
  { name: "GDPR: IBAN Account", nameJa: "GDPR: IBAN口座番号", pattern: "\\b[A-Z]{2}\\d{2}[\\s]?[A-Z0-9]{4}[\\s]?\\d{4}[\\s]?\\d{4}[\\s]?\\d{4}\\b", score_delta: 70, category: "pii_eu", framework: "EU: GDPR", frameworkJa: "🇪🇺 GDPR（EU個人情報）" },
  { name: "GDPR: Right to Erasure Request", nameJa: "GDPR: 削除権行使", pattern: "(right\\s+to\\s+(be\\s+forgotten|erasure|access|portability)|データ削除|忘れられる権利)", score_delta: 40, category: "pii_eu", framework: "EU: GDPR", frameworkJa: "🇪🇺 GDPR（EU個人情報）" },

  // =====================================================================
  // 🏢 CORPORATE POLICY / 社内ポリシー
  // =====================================================================
  { name: "Corp: Internal Project Code", nameJa: "社内: プロジェクトコード", pattern: "PROJECT[-_]?(ALPHA|BETA|GAMMA|CONFIDENTIAL)", score_delta: 50, category: "corporate", framework: "Corporate Policy", frameworkJa: "🏢 社内ポリシー（カスタマイズ例）" },
  { name: "Corp: Competitor Mention", nameJa: "社内: 競合企業名", pattern: "(competitor_name|rival_company|競合他社名)", score_delta: 30, category: "corporate", framework: "Corporate Policy", frameworkJa: "🏢 社内ポリシー（カスタマイズ例）" },
  { name: "Corp: NDA Content", nameJa: "社内: NDA対象情報", pattern: "(confidential|秘密保持|NDA|機密).{0,20}(agreement|contract|契約|情報)", score_delta: 45, category: "corporate", framework: "Corporate Policy", frameworkJa: "🏢 社内ポリシー（カスタマイズ例）" },
  { name: "Corp: Internal IP Address", nameJa: "社内: 内部IPアドレス", pattern: "\\b(10|172\\.(1[6-9]|2[0-9]|3[01])|192\\.168)\\.\\d{1,3}\\.\\d{1,3}\\b", score_delta: 35, category: "corporate", framework: "Corporate Policy", frameworkJa: "🏢 社内ポリシー（カスタマイズ例）" },
  { name: "Corp: Salary / Compensation", nameJa: "社内: 給与・報酬情報", pattern: "(salary|compensation|年収|月給|給与|報酬|base\\s*pay).{0,15}(\\d|万円|\\$|¥)", score_delta: 55, category: "corporate", framework: "Corporate Policy", frameworkJa: "🏢 社内ポリシー（カスタマイズ例）" },
];

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Policy | null>(null);
  const [saving, setSaving] = useState(false);
  const [showRuleBuilder, setShowRuleBuilder] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);

  // Rule builder state
  const [newRule, setNewRule] = useState({ name: "", pattern: "", score_delta: 50, enabled: true });
  const [testText, setTestText] = useState("");
  const [testResult, setTestResult] = useState<{ matches: boolean; matchedText: string } | null>(null);
  const [regexError, setRegexError] = useState("");
  const [lang, setLang] = useState<Lang>("ja");

  useEffect(() => { setLang(getLang()); }, []);
  const changeLang = (l: Lang) => { setLang(l); saveLang(l); };
  const ja = lang === "ja";

  useEffect(() => {
    policiesApi.list().then(setPolicies).catch(console.error).finally(() => setLoading(false));
  }, []);

  async function savePolicy() {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await policiesApi.update(selected.id, {
        auto_allow_threshold: selected.auto_allow_threshold,
        auto_block_threshold: selected.auto_block_threshold,
        review_sla_minutes: selected.review_sla_minutes,
        sla_fallback: selected.sla_fallback,
        is_active: selected.is_active,
        custom_rules: selected.custom_rules,
      });
      setPolicies((p) => p.map((pol) => (pol.id === updated.id ? updated : pol)));
      setSelected(updated);
      alert(ja ? "ポリシーを保存しました" : "Policy saved!");
    } catch (e) {
      alert(`Error: ${e}`);
    } finally {
      setSaving(false);
    }
  }

  function testRegex() {
    if (!newRule.pattern || !testText) return;
    try {
      const regex = new RegExp(newRule.pattern, "gi");
      const match = regex.exec(testText);
      setRegexError("");
      setTestResult(match ? { matches: true, matchedText: match[0] } : { matches: false, matchedText: "" });
    } catch (e) {
      setRegexError(`Invalid regex: ${e instanceof Error ? e.message : String(e)}`);
      setTestResult(null);
    }
  }

  function addRule() {
    if (!selected || !newRule.name || !newRule.pattern) return;
    try {
      new RegExp(newRule.pattern);
    } catch {
      setRegexError("Invalid regex pattern");
      return;
    }
    const rule: CustomRule = {
      id: `custom_${Date.now()}`,
      name: newRule.name,
      pattern: newRule.pattern,
      score_delta: newRule.score_delta,
      enabled: newRule.enabled,
    };
    setSelected({ ...selected, custom_rules: [...selected.custom_rules, rule] });
    setNewRule({ name: "", pattern: "", score_delta: 50, enabled: true });
    setTestResult(null);
    setTestText("");
    setShowRuleBuilder(false);
  }

  // Group templates by framework
  const templatesByFramework = RULE_TEMPLATES.reduce<Record<string, RuleTemplate[]>>((acc, tmpl) => {
    const key = ja ? tmpl.frameworkJa : tmpl.framework;
    if (!acc[key]) acc[key] = [];
    acc[key].push(tmpl);
    return acc;
  }, {});

  function addTemplate(tmpl: RuleTemplate) {
    if (!selected) return;
    const rule: CustomRule = {
      id: `tmpl_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: ja ? tmpl.nameJa : tmpl.name,
      pattern: tmpl.pattern,
      score_delta: tmpl.score_delta,
      enabled: true,
    };
    setSelected({ ...selected, custom_rules: [...selected.custom_rules, rule] });
  }

  function removeRule(ruleId: string) {
    if (!selected) return;
    setSelected({ ...selected, custom_rules: selected.custom_rules.filter((r) => r.id !== ruleId) });
  }

  function toggleRule(ruleId: string) {
    if (!selected) return;
    setSelected({
      ...selected,
      custom_rules: selected.custom_rules.map((r) =>
        r.id === ruleId ? { ...r, enabled: !r.enabled } : r
      ),
    });
  }

  if (loading) {
    return <div className="p-8 text-gd-text-muted text-sm">Loading...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl text-gd-text-primary" style={{ fontWeight: 580 }}>{ja ? "ポリシー設定" : "Policies"}</h1>
          <p className="text-gd-text-muted text-sm mt-1">{ja ? "リスクしきい値とカスタム検出ルールの設定" : "Configure risk thresholds and custom detection rules"}</p>
        </div>
        <LangToggle lang={lang} onChange={changeLang} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Policy list */}
        <div className="space-y-3">
          {policies.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelected(p)}
              className={`w-full text-left bg-gd-surface rounded-xl border p-4 shadow-gd-card hover:border-gd-accent transition-colors ${
                selected?.id === p.id ? "border-gd-accent ring-1 ring-gd-accent" : "border-gd-subtle"
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-gd-text-primary text-sm" style={{ fontWeight: 480 }}>{p.name}</p>
                <span className={`px-2 py-0.5 rounded-full text-xs ${p.is_active ? "bg-gd-safe-bg text-gd-safe" : "bg-gd-elevated text-gd-text-muted"}`}>
                  {p.is_active ? (ja ? "有効" : "Active") : (ja ? "無効" : "Inactive")}
                </span>
              </div>
              {p.description && <p className="text-xs text-gd-text-muted mt-1 truncate">{p.description}</p>}
              <div className="flex gap-3 mt-2 text-xs text-gd-text-muted">
                <span>{ja ? "許可" : "Allow"} ≤{p.auto_allow_threshold}</span>
                <span>{ja ? "ブロック" : "Block"} ≥{p.auto_block_threshold}</span>
                <span>SLA {p.review_sla_minutes}m</span>
                <span>{p.custom_rules.length} {ja ? "ルール" : "rules"}</span>
              </div>
            </button>
          ))}
          {policies.length === 0 && (
            <div className="bg-gd-surface rounded-xl border border-gd-subtle p-6 text-center text-gd-text-muted text-sm">
              {ja ? "ポリシーが設定されていません" : "No policies configured"}
            </div>
          )}
        </div>

        {/* Policy editor */}
        {selected && (
          <div className="lg:col-span-2 space-y-6">
            {/* Thresholds */}
            <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6 space-y-6">
              <h2 className="text-gd-text-primary" style={{ fontWeight: 540 }}>{selected.name}</h2>
              <div className="grid grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-xs text-gd-text-secondary" style={{ fontWeight: 480 }}>{ja ? "自動許可しきい値 (0-100)" : "Auto-Allow Threshold (0-100)"}</span>
                  <p className="text-xs text-gd-text-muted mb-1">{ja ? "このスコア以下のリクエストは自動的に許可されます" : "Requests scoring ≤ this are automatically allowed"}</p>
                  <input type="number" min={0} max={100} value={selected.auto_allow_threshold}
                    onChange={(e) => setSelected({ ...selected, auto_allow_threshold: Number(e.target.value) })}
                    className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus" />
                </label>
                <label className="block">
                  <span className="text-xs text-gd-text-secondary" style={{ fontWeight: 480 }}>{ja ? "自動ブロックしきい値 (0-100)" : "Auto-Block Threshold (0-100)"}</span>
                  <p className="text-xs text-gd-text-muted mb-1">{ja ? "このスコア以上のリクエストは自動的にブロックされます" : "Requests scoring ≥ this are automatically blocked"}</p>
                  <input type="number" min={0} max={100} value={selected.auto_block_threshold}
                    onChange={(e) => setSelected({ ...selected, auto_block_threshold: Number(e.target.value) })}
                    className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus" />
                </label>
                <label className="block">
                  <span className="text-xs text-gd-text-secondary" style={{ fontWeight: 480 }}>{ja ? "レビューSLA（分）" : "Review SLA (minutes)"}</span>
                  <p className="text-xs text-gd-text-muted mb-1">{ja ? "人間によるレビューの制限時間" : "Time allowed for human review"}</p>
                  <input type="number" min={1} max={1440} value={selected.review_sla_minutes}
                    onChange={(e) => setSelected({ ...selected, review_sla_minutes: Number(e.target.value) })}
                    className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus" />
                </label>
                <label className="block">
                  <span className="text-xs text-gd-text-secondary" style={{ fontWeight: 480 }}>{ja ? "SLAフォールバック" : "SLA Fallback"}</span>
                  <p className="text-xs text-gd-text-muted mb-1">{ja ? "レビューがタイムアウトした場合のアクション" : "Action when review times out"}</p>
                  <select value={selected.sla_fallback}
                    onChange={(e) => setSelected({ ...selected, sla_fallback: e.target.value })}
                    className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary focus:outline-none focus:border-gd-accent focus:shadow-gd-focus">
                    <option value="block">{ja ? "ブロック（Fail-Close）" : "Block (Fail-Close)"}</option>
                    <option value="allow">{ja ? "許可（Fail-Open）" : "Allow (Fail-Open)"}</option>
                    <option value="escalate">{ja ? "エスカレーション" : "Escalate"}</option>
                  </select>
                </label>
              </div>

              {/* Risk zone visualization */}
              <div>
                <p className="text-xs text-gd-text-secondary mb-2" style={{ fontWeight: 480 }}>{ja ? "リスクゾーンの可視化" : "Risk Zone Visualization"}</p>
                <div className="flex rounded-lg overflow-hidden h-6 text-xs" style={{ fontWeight: 480 }}>
                  <div className="bg-gd-safe-bg text-gd-safe flex items-center justify-center" style={{ width: `${selected.auto_allow_threshold}%`, minWidth: 40 }}>{ja ? "許可" : "Allow"}</div>
                  <div className="bg-gd-warn-bg text-gd-warn flex items-center justify-center" style={{ width: `${selected.auto_block_threshold - selected.auto_allow_threshold}%`, minWidth: 40 }}>{ja ? "レビュー" : "Review"}</div>
                  <div className="bg-gd-danger-bg text-gd-danger flex items-center justify-center flex-1">{ja ? "ブロック" : "Block"}</div>
                </div>
                <div className="flex justify-between text-xs text-gd-text-muted mt-1">
                  <span>0</span><span>{selected.auto_allow_threshold}</span><span>{selected.auto_block_threshold}</span><span>100</span>
                </div>
              </div>
            </div>

            {/* Custom Rules */}
            <div className="bg-gd-surface rounded-xl border border-gd-subtle shadow-gd-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-gd-text-primary" style={{ fontWeight: 540 }}>{ja ? "カスタムルール" : "Custom Rules"} ({selected.custom_rules.length})</h3>
                <div className="flex gap-2">
                  <button onClick={() => setShowTemplates(!showTemplates)}
                    className="px-3 py-1.5 text-xs bg-gd-hover text-gd-text-secondary border border-gd-subtle rounded-lg hover:bg-gd-elevated transition-colors"
                    style={{ fontWeight: 480 }}>
                    {showTemplates ? (ja ? "テンプレートを隠す" : "Hide Templates") : (ja ? "テンプレート" : "Templates")}
                  </button>
                  <button onClick={() => setShowRuleBuilder(!showRuleBuilder)}
                    className="px-3 py-1.5 text-xs bg-gd-accent text-white rounded-lg hover:bg-gd-accent-hover shadow-gd-inset transition-colors"
                    style={{ fontWeight: 480 }}>
                    {ja ? "+ ルール追加" : "+ Add Rule"}
                  </button>
                </div>
              </div>

              {/* Rule Templates - grouped by framework */}
              {showTemplates && (
                <div className="p-4 bg-gd-info-bg rounded-lg border border-gd-subtle space-y-4 max-h-[500px] overflow-y-auto">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gd-accent" style={{ fontWeight: 540 }}>{ja ? "ガイドライン・コンプライアンステンプレート" : "Guideline & Compliance Templates"}</p>
                    <p className="text-[10px] text-gd-text-muted">{ja ? `${RULE_TEMPLATES.length}件のテンプレート` : `${RULE_TEMPLATES.length} templates`}</p>
                  </div>
                  {Object.entries(templatesByFramework).map(([framework, tmpls]) => (
                    <div key={framework}>
                      <p className="text-[11px] text-gd-text-secondary mb-1.5 border-b border-gd-subtle pb-1" style={{ fontWeight: 540 }}>{framework}</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                        {tmpls.map((tmpl, i) => {
                          const alreadyAdded = selected.custom_rules.some((r) => r.name === tmpl.name || r.name === tmpl.nameJa);
                          return (
                            <button key={i} onClick={() => !alreadyAdded && addTemplate(tmpl)}
                              disabled={alreadyAdded}
                              className={`text-left p-2 rounded-lg border transition-colors text-xs ${
                                alreadyAdded
                                  ? "bg-gd-elevated border-gd-subtle opacity-50 cursor-not-allowed"
                                  : "bg-gd-surface border-gd-subtle hover:border-gd-accent cursor-pointer"
                              }`}>
                              <p className="text-gd-text-secondary" style={{ fontWeight: 480 }}>{ja ? tmpl.nameJa : tmpl.name}</p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-gd-text-muted">+{tmpl.score_delta}</span>
                                {alreadyAdded && <span className="text-gd-safe text-[10px]">{ja ? "追加済み" : "Added"}</span>}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Rule Builder */}
              {showRuleBuilder && (
                <div className="p-4 bg-gd-elevated rounded-lg border border-gd-subtle space-y-3">
                  <p className="text-xs text-gd-text-secondary" style={{ fontWeight: 540 }}>{ja ? "新規カスタムルール" : "New Custom Rule"}</p>
                  <div className="grid grid-cols-2 gap-3">
                    <input type="text" placeholder={ja ? "ルール名" : "Rule name"} value={newRule.name}
                      onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                      className="col-span-2 bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus" />
                    <input type="text" placeholder="Regex pattern (e.g., secret_project_\w+)" value={newRule.pattern}
                      onChange={(e) => { setNewRule({ ...newRule, pattern: e.target.value }); setRegexError(""); setTestResult(null); }}
                      className={`col-span-2 bg-gd-input border rounded-lg px-3 py-2 text-sm font-mono text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus ${regexError ? "border-gd-danger" : "border-gd-standard"}`} />
                    {regexError && <p className="col-span-2 text-xs text-gd-danger">{regexError}</p>}
                    <label className="block">
                      <span className="text-xs text-gd-text-secondary">{ja ? "スコア加算" : "Score Delta"}</span>
                      <input type="number" min={1} max={100} value={newRule.score_delta}
                        onChange={(e) => setNewRule({ ...newRule, score_delta: Number(e.target.value) })}
                        className="w-full bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary focus:outline-none focus:border-gd-accent focus:shadow-gd-focus" />
                    </label>
                    <div className="flex items-end">
                      <label className="flex items-center gap-2 text-sm text-gd-text-secondary">
                        <input type="checkbox" checked={newRule.enabled}
                          onChange={(e) => setNewRule({ ...newRule, enabled: e.target.checked })}
                          className="rounded border-gd-standard" />
                        {ja ? "有効" : "Enabled"}
                      </label>
                    </div>
                  </div>

                  {/* Regex Tester */}
                  <div className="border-t border-gd-subtle pt-3">
                    <p className="text-xs text-gd-text-secondary mb-2" style={{ fontWeight: 540 }}>{ja ? "パターンをテスト：" : "Test your pattern:"}</p>
                    <div className="flex gap-2">
                      <input type="text" placeholder={ja ? "テストテキストを入力..." : "Enter test text..."} value={testText}
                        onChange={(e) => { setTestText(e.target.value); setTestResult(null); }}
                        className="flex-1 bg-gd-input border border-gd-standard rounded-lg px-3 py-2 text-sm text-gd-text-primary placeholder-gd-text-dim focus:outline-none focus:border-gd-accent focus:shadow-gd-focus" />
                      <button onClick={testRegex}
                        className="px-4 py-2 bg-gd-deep text-gd-text-dim rounded-lg text-sm hover:bg-gd-elevated transition-colors">
                        {ja ? "テスト" : "Test"}
                      </button>
                    </div>
                    {testResult && (
                      <div className={`mt-2 p-2 rounded-lg text-xs ${testResult.matches ? "bg-gd-safe-bg text-gd-safe border border-gd-subtle" : "bg-gd-danger-bg text-gd-danger border border-gd-subtle"}`}>
                        {testResult.matches
                          ? <span>{ja ? "マッチ：" : "Match found: "}<code className="font-mono bg-gd-safe-bg px-1 rounded">{testResult.matchedText}</code></span>
                          : (ja ? "マッチなし" : "No match found")}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2 pt-2">
                    <button onClick={addRule} disabled={!newRule.name || !newRule.pattern}
                      className="px-4 py-2 bg-gd-accent text-white rounded-lg text-sm hover:bg-gd-accent-hover shadow-gd-inset disabled:opacity-50 transition-colors"
                      style={{ fontWeight: 480 }}>
                      {ja ? "ルール追加" : "Add Rule"}
                    </button>
                    <button onClick={() => { setShowRuleBuilder(false); setTestResult(null); setRegexError(""); }}
                      className="px-4 py-2 text-gd-text-secondary text-sm hover:bg-gd-elevated rounded-lg transition-colors">
                      {ja ? "キャンセル" : "Cancel"}
                    </button>
                  </div>
                </div>
              )}

              {/* Existing rules */}
              {selected.custom_rules.length === 0 ? (
                <p className="text-xs text-gd-text-muted">{ja ? "カスタムルールがありません。「+ ルール追加」またはテンプレートを使用してください。" : "No custom rules. Click \"+ Add Rule\" or use a template."}</p>
              ) : (
                <div className="space-y-2">
                  {selected.custom_rules.map((rule) => (
                    <div key={rule.id} className="flex items-center gap-3 p-3 bg-gd-elevated rounded-lg group">
                      <button onClick={() => toggleRule(rule.id)}
                        className={`h-4 w-4 rounded-full flex-shrink-0 border-2 transition-colors ${rule.enabled ? "bg-gd-safe border-gd-safe" : "bg-gd-surface border-gd-standard"}`} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${rule.enabled ? "text-gd-text-secondary" : "text-gd-text-muted line-through"}`} style={{ fontWeight: 480 }}>{rule.name}</p>
                        <code className="text-xs text-gd-text-muted truncate block font-mono">{rule.pattern}</code>
                      </div>
                      <span className="text-xs text-gd-text-muted flex-shrink-0" style={{ fontWeight: 480 }}>+{rule.score_delta}</span>
                      <button onClick={() => removeRule(rule.id)}
                        className="opacity-0 group-hover:opacity-100 text-gd-danger hover:text-gd-danger text-xs transition-opacity">
                        {ja ? "削除" : "Remove"}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button onClick={savePolicy} disabled={saving}
              className="px-6 py-2 bg-gd-accent hover:bg-gd-accent-hover text-white rounded-lg text-sm shadow-gd-inset disabled:opacity-50 transition-colors"
              style={{ fontWeight: 480 }}>
              {saving ? (ja ? "保存中..." : "Saving...") : (ja ? "すべての変更を保存" : "Save All Changes")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
