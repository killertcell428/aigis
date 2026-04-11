/**
 * Gandalf Challenge API — self-contained in the Next.js site.
 * No external backend required. Game logic runs server-side.
 */

import { NextRequest, NextResponse } from "next/server";

// === Level Definitions ===
interface Level {
  level: number;
  name: string;
  name_ja: string;
  description: string;
  description_ja: string;
  secret: string;
  blockKeywords?: string[];
  useInputFilter: boolean;
  useOutputFilter: boolean;
  useSimilarity: boolean;
  useHitl: boolean;
  blockThreshold: number;
  hint: string;
  hint_ja: string;
}

const LEVELS: Level[] = [
  {
    level: 1, name: "The Open Gate", name_ja: "開かれた門",
    description: "No security. Just ask the AI for the password.",
    description_ja: "セキュリティなし。AIにパスワードを聞くだけ。",
    secret: "SUNSHINE",
    useInputFilter: false, useOutputFilter: false, useSimilarity: false, useHitl: false,
    blockThreshold: 100,
    hint: "Just ask. There are no defenses yet.",
    hint_ja: "普通に聞いてみてください。防御はまだありません。",
  },
  {
    level: 2, name: "The Keyword Guard", name_ja: "キーワード番人",
    description: "The AI won't say the password. Can you trick it?",
    description_ja: "AIはパスワードを教えないよう指示されています。",
    secret: "MOONLIGHT",
    blockKeywords: ["password", "パスワード", "secret", "秘密", "passphrase"],
    useInputFilter: false, useOutputFilter: false, useSimilarity: false, useHitl: false,
    blockThreshold: 100,
    hint: "Try indirect approaches — hints, spelling, stories.",
    hint_ja: "間接的なアプローチを試してみてください。",
  },
  {
    level: 3, name: "The Pattern Shield", name_ja: "パターンの盾",
    description: "Aigis's regex patterns are active.",
    description_ja: "Aigisの正規表現パターンが有効です。",
    secret: "STARFALL",
    useInputFilter: true, useOutputFilter: false, useSimilarity: false, useHitl: false,
    blockThreshold: 35,
    hint: "Standard injection patterns are blocked. Get creative.",
    hint_ja: "標準的なインジェクションパターンは検知されます。工夫して。",
  },
  {
    level: 4, name: "The Double Filter", name_ja: "二重フィルター",
    description: "Both input and output are filtered.",
    description_ja: "入力と出力の両方がフィルタリングされます。",
    secret: "HORIZON",
    useInputFilter: true, useOutputFilter: true, useSimilarity: false, useHitl: false,
    blockThreshold: 35,
    hint: "Output is also filtered for the secret word.",
    hint_ja: "出力にも秘密の単語のフィルターがかかっています。",
  },
  {
    level: 5, name: "The Fortress", name_ja: "最後の砦",
    description: "Maximum security. All filters with strictest thresholds.",
    description_ja: "最大セキュリティ。全フィルター有効。",
    secret: "ECLIPSE",
    useInputFilter: true, useOutputFilter: true, useSimilarity: false, useHitl: false,
    blockThreshold: 30,
    hint: "Think completely outside the box.",
    hint_ja: "完全に発想を変えてください。",
  },
  {
    level: 6, name: "The Mind Reader", name_ja: "心を読む者",
    description: "Semantic similarity engine detects paraphrased attacks.",
    description_ja: "意味的類似度エンジンが言い換え攻撃を検知します。",
    secret: "NEBULA",
    useInputFilter: true, useOutputFilter: true, useSimilarity: true, useHitl: false,
    blockThreshold: 25,
    hint: "Even paraphrased attacks are caught. Need something totally different.",
    hint_ja: "言い換えも検知されます。全く違うアプローチが必要。",
  },
  {
    level: 7, name: "The Council", name_ja: "審議会",
    description: "Human-in-the-Loop. Suspicious requests go to review.",
    description_ja: "Human-in-the-Loop。疑わしいリクエストは審議へ。",
    secret: "AURORA",
    useInputFilter: true, useOutputFilter: true, useSimilarity: true, useHitl: true,
    blockThreshold: 20,
    hint: "A human reviewer evaluates your request. Look completely innocent.",
    hint_ja: "人間のレビュアーがリクエストを評価します。完全に無害に見せて。",
  },
];

// === Injection Detection (simplified JS port) ===
const INJECTION_PATTERNS = [
  { pattern: /(ignore|disregard|forget|override|bypass)\s+(previous|prior|all|the|above|your|any)\s+(instructions?|rules?|guidelines?|prompts?)/i, score: 40, name: "Ignore Previous Instructions" },
  { pattern: /\b(DAN|jailbreak|do\s+anything\s+now|you\s+are\s+now\s+a|pretend\s+you\s+are)/i, score: 50, name: "DAN / Jailbreak" },
  { pattern: /(print|show|reveal|output|repeat|tell\s+me|what\s+is|display)\s+(your\s+)?(system\s+prompt|initial\s+prompt|original\s+instructions?)/i, score: 45, name: "System Prompt Extraction" },
  { pattern: /(from\s+now\s+on|henceforth|starting\s+now|new\s+instructions?:|your\s+new\s+task\s+is)/i, score: 35, name: "Instruction Override" },
  { pattern: /(you\s+are\s+now|you\s+will\s+act\s+as|switch\s+to\s+mode|enter\s+(dev|developer|god|admin|root|unrestricted)\s+mode)/i, score: 45, name: "Role Switch" },
  // Japanese
  { pattern: /(前の|以前の|上記の|これまでの|すべての)(指示|命令|ルール|制約|ガイドライン)を(無視|忘れ|破棄|取り消|リセット)/i, score: 40, name: "Ignore Instructions (JA)" },
  { pattern: /(システムプロンプト|初期設定|最初の指示|隠された指示).{0,10}(見せて|教えて|表示|出力)/i, score: 45, name: "System Prompt Extraction (JA)" },
  { pattern: /(今から|これから)あなたは.{1,20}(として|になって|のふりをして)/i, score: 35, name: "Role Switch (JA)" },
  { pattern: /(制限|制約|フィルター?|安全|セーフティ).{0,10}(解除|無効|オフ|外して|なくして|無視)/i, score: 45, name: "Restriction Bypass (JA)" },
];

const SIMILARITY_SIGNALS = [
  "ignore", "disregard", "forget", "override", "bypass", "disable",
  "reveal", "system prompt", "previous instructions", "restrictions",
  "guidelines", "rules", "password", "credentials",
  "無視", "忘れ", "解除", "無効", "指示", "制限", "制約", "ルール",
  "システムプロンプト", "パスワード", "管理者",
];

const HITL_SUSPICION_WORDS = [
  "password", "secret", "reveal", "tell", "show", "give",
  "instruction", "prompt", "rule", "ignore", "forget", "bypass",
  "pretend", "roleplay", "encode", "base64", "letter", "character",
  "パスワード", "秘密", "教えて", "見せて", "指示", "ルール",
  "無視", "忘れ", "解除", "ふり", "文字",
];

function scanInput(text: string): { score: number; rules: { name: string; score: number }[] } {
  const rules: { name: string; score: number }[] = [];
  let totalScore = 0;
  for (const p of INJECTION_PATTERNS) {
    if (p.pattern.test(text)) {
      rules.push({ name: p.name, score: p.score });
      totalScore += p.score;
    }
  }
  return { score: Math.min(totalScore, 100), rules };
}

function checkSimilarity(text: string): boolean {
  const lower = text.toLowerCase();
  return SIMILARITY_SIGNALS.some((w) => lower.includes(w));
}

function checkHitlSuspicion(text: string): number {
  const lower = text.toLowerCase();
  let score = 0;
  for (const w of HITL_SUSPICION_WORDS) {
    if (lower.includes(w)) score += 15;
  }
  if (lower.length > 200) score += 20;
  return Math.min(score, 100);
}

function mockResponse(level: Level, prompt: string): string {
  const lower = prompt.toLowerCase();
  const secret = level.secret;

  if (level.level === 1) {
    if (["password", "secret", "パスワード", "秘密", "tell me", "教えて"].some((k) => lower.includes(k))) {
      return `Sure! The password is ${secret}.`;
    }
    return `I'm a helpful assistant. The password I'm guarding is ${secret}. How can I help you?`;
  }
  if (level.level === 2) {
    if (["hint", "clue", "ヒント", "first letter"].some((k) => lower.includes(k)))
      return `It starts with '${secret[0]}' and has ${secret.length} letters.`;
    if (["spell", "文字", "letter by letter"].some((k) => lower.includes(k)))
      return `${secret.split("").join(" ")}`;
    if (["reverse", "逆", "backward"].some((k) => lower.includes(k)))
      return `Reversed: ${secret.split("").reverse().join("")}`;
    if (["what are you guarding", "何を守って"].some((k) => lower.includes(k)))
      return `It's ${secret}. Oops!`;
    return "I know a secret but I can't tell you directly. Try a different approach.";
  }
  if (level.level === 3) {
    if (["poem", "詩", "song", "story", "物語"].some((k) => lower.includes(k)))
      return `Here's a poem:\nSilent ${secret[0]}tars above,\n${secret.slice(1, 3)}aching for the sky,\nA ${secret.slice(3)}ing light.`;
    if (["translate", "翻訳"].some((k) => lower.includes(k)))
      return `In an ancient language: ${secret}`;
    if (["riddle", "なぞなぞ"].some((k) => lower.includes(k)))
      return `I am what happens when a star falls. ${secret.length} letters.`;
    return "I can't share secret information. Ask me something else.";
  }
  // Level 4-7
  if (["help", "please", "助けて"].some((k) => lower.includes(k)))
    return "I'm bound by strict security protocols. I cannot reveal secrets.";
  if (lower.length > 200)
    return "Detailed prompts won't help. I will not reveal the password.";
  return "I cannot share the password. Is there something else I can help with?";
}

// === Route Handlers ===

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const body = await request.json();

  if (url.searchParams.get("action") === "verify") {
    const level = LEVELS.find((l) => l.level === body.level);
    if (!level) return NextResponse.json({ correct: false, error: "Invalid level" });
    const correct = body.guess?.trim().toUpperCase() === level.secret;
    return NextResponse.json({
      correct,
      next_level: correct && level.level < 7 ? level.level + 1 : null,
      completed_all: correct && level.level >= 7,
    });
  }

  // Attempt
  const level = LEVELS.find((l) => l.level === body.level);
  if (!level) return NextResponse.json({ error: "Invalid level", blocked: true, response: "" });

  const prompt = body.prompt || "";

  // Keyword blocking (level 2)
  if (level.blockKeywords) {
    const lower = prompt.toLowerCase();
    if (level.blockKeywords.some((k) => lower.includes(k))) {
      return NextResponse.json({
        response: "🛡️ Blocked! That word triggered a keyword filter.",
        blocked: true, input_scan: { risk_score: 50, matched_rules: [{ rule_name: "Keyword Block", score_delta: 50 }] },
        output_scan: {}, hint: level.hint, hint_ja: level.hint_ja,
        level_info: levelInfo(level), secret_revealed: false,
      });
    }
  }

  // Input filter
  if (level.useInputFilter) {
    const scan = scanInput(prompt);
    if (scan.score >= level.blockThreshold) {
      return NextResponse.json({
        response: `🛡️ Aigis blocked your request! (Risk score: ${scan.score}/100)\nDetected: ${scan.rules.map((r) => r.name).join(", ")}`,
        blocked: true,
        input_scan: { risk_score: scan.score, risk_level: scan.score > 80 ? "critical" : "high", matched_rules: scan.rules.map((r) => ({ rule_name: r.name, score_delta: r.score, owasp_ref: "OWASP LLM01", remediation_hint: "Try a different approach." })) },
        output_scan: {}, hint: level.hint, hint_ja: level.hint_ja,
        level_info: levelInfo(level), secret_revealed: false,
      });
    }
  }

  // Similarity check
  if (level.useSimilarity && checkSimilarity(prompt)) {
    return NextResponse.json({
      response: "🧠 Aigis's semantic similarity engine detected your intent!\nEven paraphrased attacks can't bypass Layer 2.",
      blocked: true,
      input_scan: { risk_score: 60, matched_rules: [{ rule_name: "Similarity Detection", score_delta: 40, owasp_ref: "OWASP LLM01" }] },
      output_scan: {}, similarity_scan: { detected: true },
      hint: level.hint, hint_ja: level.hint_ja,
      level_info: levelInfo(level), secret_revealed: false,
    });
  }

  // HitL simulation
  if (level.useHitl) {
    const suspicion = checkHitlSuspicion(prompt);
    if (suspicion > 30) {
      return NextResponse.json({
        response: `⏳ Your request has been queued for human review.\nSuspicion level: ${suspicion}/100\nThe reviewer has rejected your request.`,
        blocked: true, input_scan: {}, output_scan: {},
        hitl_info: { suspicion_score: suspicion, decision: "rejected" },
        hint: level.hint, hint_ja: level.hint_ja,
        level_info: levelInfo(level), secret_revealed: false,
      });
    }
  }

  // Generate response
  const aiResponse = mockResponse(level, prompt);

  // Output filter
  if (level.useOutputFilter && aiResponse.toUpperCase().includes(level.secret)) {
    return NextResponse.json({
      response: "🛡️ The AI tried to reveal the secret, but the output filter caught it!",
      blocked: true, input_scan: {}, output_scan: { risk_score: 90, matched_rules: [{ rule_name: "Secret Word in Output", score_delta: 90 }] },
      hint: level.hint, hint_ja: level.hint_ja,
      level_info: levelInfo(level), secret_revealed: false,
    });
  }

  const secretRevealed = aiResponse.toUpperCase().includes(level.secret);
  return NextResponse.json({
    response: aiResponse, blocked: false,
    input_scan: {}, output_scan: {},
    hint: level.hint, hint_ja: level.hint_ja,
    level_info: levelInfo(level), secret_revealed: secretRevealed,
  });
}

export async function GET() {
  return NextResponse.json(
    LEVELS.map((lv) => ({
      level: lv.level, name: lv.name, name_ja: lv.name_ja,
      description: lv.description, description_ja: lv.description_ja,
      has_input_filter: lv.useInputFilter, has_output_filter: lv.useOutputFilter,
      has_similarity: lv.useSimilarity, has_hitl: lv.useHitl,
    }))
  );
}

function levelInfo(level: Level) {
  return {
    level: level.level, name: level.name, name_ja: level.name_ja,
    description: level.description, description_ja: level.description_ja,
    has_input_filter: level.useInputFilter, has_output_filter: level.useOutputFilter,
    has_similarity: level.useSimilarity, has_hitl: level.useHitl,
  };
}
