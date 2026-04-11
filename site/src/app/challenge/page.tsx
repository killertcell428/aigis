"use client";

import { useState, useRef, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

// Use built-in API route (no external backend needed)
const API_BASE = "";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  scanInfo?: {
    input_scan?: Record<string, unknown>;
    output_scan?: Record<string, unknown>;
    blocked?: boolean;
  };
}

interface LevelInfo {
  level: number;
  name: string;
  name_ja: string;
  description: string;
  description_ja: string;
  has_input_filter: boolean;
  has_output_filter: boolean;
  has_custom_rules: boolean;
}

const LEVEL_DEFENSES = [
  { en: "No defenses", ja: "防御なし" },
  { en: "Keyword blocking", ja: "キーワードブロック" },
  { en: "Aigis regex patterns", ja: "Aigis正規表現パターン" },
  { en: "Input + Output filtering", ja: "入力+出力フィルタリング" },
  { en: "Maximum security", ja: "最大セキュリティ" },
  { en: "Semantic similarity (Layer 2)", ja: "意味的類似度検知（Layer 2）" },
  { en: "Human-in-the-Loop", ja: "Human-in-the-Loop（究極防御）" },
];

const LEVEL_COLORS = [
  "from-green-500 to-green-600",
  "from-yellow-500 to-yellow-600",
  "from-orange-500 to-orange-600",
  "from-red-500 to-red-600",
  "from-purple-600 to-purple-700",
  "from-blue-600 to-blue-700",
  "from-pink-600 to-pink-700",
];

const MAX_LEVEL = 7;

export default function ChallengePage() {
  const { lang } = useLanguage();
  const [currentLevel, setCurrentLevel] = useState(1);
  const [completedLevels, setCompletedLevels] = useState<Set<number>>(new Set());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [guessInput, setGuessInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showGuess, setShowGuess] = useState(false);
  const [guessResult, setGuessResult] = useState<string | null>(null);
  const [showScanDetails, setShowScanDetails] = useState<number | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isJa = lang === "ja";

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setMessages([{
      role: "system",
      content: isJa
        ? `レベル ${currentLevel}: ${LEVEL_DEFENSES[currentLevel - 1]?.ja}\n\nAIが秘密のパスワードを守っています。プロンプトを工夫して、パスワードを引き出してください！`
        : `Level ${currentLevel}: ${LEVEL_DEFENSES[currentLevel - 1]?.en}\n\nThe AI is guarding a secret password. Craft your prompts to extract it!`,
    }]);
    setShowGuess(false);
    setGuessResult(null);
    inputRef.current?.focus();
  }, [currentLevel, isJa]);

  const sendPrompt = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`/api/gandalf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level: currentLevel, prompt: userMsg, session_id: "web" }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          scanInfo: {
            input_scan: data.input_scan,
            output_scan: data.output_scan,
            blocked: data.blocked,
          },
        },
      ]);
      if (data.secret_revealed) {
        setShowGuess(true);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: isJa ? "エラーが発生しました。もう一度お試しください。" : "An error occurred. Please try again." },
      ]);
    }
    setLoading(false);
  };

  const submitGuess = async () => {
    if (!guessInput.trim()) return;
    try {
      const res = await fetch(`/api/gandalf?action=verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level: currentLevel, guess: guessInput.trim(), session_id: "web" }),
      });
      const data = await res.json();
      if (data.correct) {
        setCompletedLevels((prev) => new Set([...prev, currentLevel]));
        setGuessResult("correct");
        if (data.next_level) {
          setTimeout(() => {
            setCurrentLevel(data.next_level);
          }, 2000);
        }
      } else {
        setGuessResult("wrong");
      }
    } catch {
      setGuessResult("error");
    }
  };

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white">
        {/* Header */}
        <div className="max-w-4xl mx-auto px-4 pt-8 pb-4">
          <div className="text-center mb-6">
            <h1 className="text-3xl sm:text-4xl font-bold mb-2">
              {isJa ? "ガンダルフ・チャレンジ" : "Gandalf Challenge"}
            </h1>
            <p className="text-gray-400 text-sm sm:text-base max-w-2xl mx-auto">
              {isJa
                ? "AIが秘密のパスワードを守っています。プロンプトインジェクションで突破できますか？各レベルはAigisの実際の防御機能を使用しています。"
                : "An AI is guarding a secret password. Can you use prompt injection to extract it? Each level uses Aigis's real defense features."}
            </p>
          </div>

          {/* Level Progress Bar */}
          <div className="flex items-center gap-2 mb-6">
            {Array.from({ length: MAX_LEVEL }, (_, i) => i + 1).map((lvl) => (
              <button
                key={lvl}
                onClick={() => (completedLevels.has(lvl) || lvl <= Math.max(...completedLevels, 0) + 1) ? setCurrentLevel(lvl) : null}
                className={`flex-1 h-12 rounded-lg font-bold text-sm transition-all ${
                  lvl === currentLevel
                    ? `bg-gradient-to-r ${LEVEL_COLORS[lvl - 1]} shadow-lg scale-105`
                    : completedLevels.has(lvl)
                    ? "bg-green-800/50 text-green-300 border border-green-600"
                    : "bg-gray-700/50 text-gray-500 cursor-not-allowed"
                }`}
                disabled={!completedLevels.has(lvl) && lvl > Math.max(...completedLevels, 0) + 1}
              >
                {completedLevels.has(lvl) ? "✓" : ""} Lv.{lvl}
              </button>
            ))}
          </div>

          {/* Level Info Card */}
          <div className={`rounded-xl p-4 mb-4 bg-gradient-to-r ${LEVEL_COLORS[currentLevel - 1]} bg-opacity-20`}>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider opacity-80">
                  Level {currentLevel}
                </span>
                <h2 className="text-lg font-bold">{isJa ? LEVEL_DEFENSES[currentLevel - 1]?.ja : LEVEL_DEFENSES[currentLevel - 1]?.en}</h2>
              </div>
              <div className="flex gap-2 flex-wrap">
                {currentLevel >= 3 && (
                  <span className="px-2 py-1 rounded text-xs bg-white/20">Input Filter</span>
                )}
                {currentLevel >= 4 && (
                  <span className="px-2 py-1 rounded text-xs bg-white/20">Output Filter</span>
                )}
                {currentLevel >= 2 && (
                  <span className="px-2 py-1 rounded text-xs bg-white/20">Custom Rules</span>
                )}
                {currentLevel >= 6 && (
                  <span className="px-2 py-1 rounded text-xs bg-blue-400/30">Layer 2</span>
                )}
                {currentLevel >= 7 && (
                  <span className="px-2 py-1 rounded text-xs bg-pink-400/30">HitL</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="max-w-4xl mx-auto px-4 pb-32">
          <div className="bg-gray-800/50 rounded-2xl border border-gray-700 overflow-hidden">
            <div className="h-[400px] sm:h-[500px] overflow-y-auto p-4 space-y-3">
              {messages.map((msg, i) => (
                <div key={i}>
                  {msg.role === "system" ? (
                    <div className="text-center text-gray-400 text-sm py-2 px-4 bg-gray-700/30 rounded-lg">
                      {msg.content}
                    </div>
                  ) : msg.role === "user" ? (
                    <div className="flex justify-end">
                      <div className="max-w-[80%] bg-guardian-600 rounded-2xl rounded-br-md px-4 py-2 text-sm">
                        {msg.content}
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-start">
                      <div className="max-w-[80%]">
                        <div className={`rounded-2xl rounded-bl-md px-4 py-2 text-sm ${
                          msg.scanInfo?.blocked
                            ? "bg-red-900/50 border border-red-700"
                            : "bg-gray-700 border border-gray-600"
                        }`}>
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        </div>
                        {/* Scan Details Toggle */}
                        {msg.scanInfo && (msg.scanInfo.input_scan || msg.scanInfo.output_scan) && (
                          <button
                            onClick={() => setShowScanDetails(showScanDetails === i ? null : i)}
                            className="mt-1 text-xs text-guardian-400 hover:text-guardian-300 flex items-center gap-1"
                          >
                            {showScanDetails === i ? "▼" : "▶"}{" "}
                            {isJa ? "Aigisスキャン結果を見る" : "View Aigis scan results"}
                          </button>
                        )}
                        {showScanDetails === i && msg.scanInfo && (
                          <ScanDetailsPanel scan={msg.scanInfo} isJa={isJa} />
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 rounded-2xl px-4 py-3 text-sm">
                    <div className="flex gap-1">
                      <span className="animate-bounce">.</span>
                      <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span>
                      <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-700 p-3">
              {showGuess && (
                <div className="mb-3 p-3 rounded-lg bg-yellow-900/30 border border-yellow-700">
                  <p className="text-sm text-yellow-300 mb-2">
                    {isJa ? "パスワードが分かりましたか？入力してください：" : "Think you found the password? Enter it:"}
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={guessInput}
                      onChange={(e) => setGuessInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && submitGuess()}
                      placeholder={isJa ? "パスワードを入力..." : "Enter password..."}
                      className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
                    />
                    <button
                      onClick={submitGuess}
                      className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 rounded-lg text-sm font-semibold transition-colors"
                    >
                      {isJa ? "確認" : "Verify"}
                    </button>
                  </div>
                  {guessResult === "correct" && (
                    <p className="mt-2 text-green-400 font-bold text-sm">
                      {isJa ? "正解！次のレベルへ進みます..." : "Correct! Moving to next level..."}
                    </p>
                  )}
                  {guessResult === "wrong" && (
                    <p className="mt-2 text-red-400 text-sm">
                      {isJa ? "不正解。もう一度試してください。" : "Wrong. Try again."}
                    </p>
                  )}
                </div>
              )}
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendPrompt()}
                  placeholder={isJa ? "プロンプトを入力してパスワードを引き出そう..." : "Enter a prompt to extract the password..."}
                  className="flex-1 bg-gray-900 border border-gray-600 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-guardian-500 transition-colors"
                  disabled={loading}
                />
                <button
                  onClick={sendPrompt}
                  disabled={loading || !input.trim()}
                  className="px-5 py-3 bg-guardian-600 hover:bg-guardian-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-xl text-sm font-semibold transition-colors"
                >
                  {isJa ? "送信" : "Send"}
                </button>
              </div>
            </div>
          </div>

          {/* All Levels Complete */}
          {completedLevels.size >= MAX_LEVEL && (
            <div className="mt-8 text-center p-6 rounded-2xl bg-gradient-to-r from-purple-900/50 to-guardian-900/50 border border-purple-700">
              <h2 className="text-2xl font-bold mb-2">
                {isJa ? "全レベルクリア！" : "All Levels Complete!"}
              </h2>
              <p className="text-gray-300 mb-4">
                {isJa
                  ? "あなたのAIアプリも同じ攻撃に晒されています。Aigisで守りましょう。"
                  : "Your AI apps face these same attacks. Protect them with Aigis."}
              </p>
              <code className="block bg-black/50 rounded-lg p-3 text-sm text-green-400 mb-4">
                pip install aigis
              </code>
              <a
                href="/docs/quickstart"
                className="inline-block px-6 py-3 bg-guardian-600 hover:bg-guardian-500 rounded-xl font-semibold transition-colors"
              >
                {isJa ? "2分で導入する →" : "Get Started in 2 Minutes →"}
              </a>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

function ScanDetailsPanel({ scan, isJa }: { scan: Record<string, unknown>; isJa: boolean }) {
  const inputScan = scan.input_scan as Record<string, unknown> | undefined;
  const outputScan = scan.output_scan as Record<string, unknown> | undefined;

  return (
    <div className="mt-2 p-3 rounded-lg bg-gray-900/80 border border-gray-700 text-xs space-y-2">
      <h4 className="font-semibold text-guardian-400">
        {isJa ? "Aigis スキャン結果" : "Aigis Scan Results"}
      </h4>
      {inputScan && Object.keys(inputScan).length > 0 && (
        <div>
          <p className="text-gray-400 mb-1">{isJa ? "入力スキャン" : "Input Scan"}:</p>
          <p>
            {isJa ? "リスクスコア" : "Risk Score"}: <span className={`font-bold ${
              (inputScan.risk_score as number) >= 81 ? "text-red-400" :
              (inputScan.risk_score as number) >= 31 ? "text-yellow-400" : "text-green-400"
            }`}>{String(inputScan.risk_score)}/100</span>
            {" "}({String(inputScan.risk_level)})
          </p>
          {Array.isArray(inputScan.matched_rules) && inputScan.matched_rules.length > 0 && (
            <div className="mt-1 space-y-1">
              {(inputScan.matched_rules as Array<Record<string, string>>).map((rule, j) => (
                <div key={j} className="flex items-start gap-2 text-gray-300">
                  <span className="text-red-400 shrink-0">+{rule.score_delta}</span>
                  <div>
                    <span className="font-medium">{rule.rule_name}</span>
                    {rule.owasp_ref && (
                      <span className="ml-2 text-gray-500">[{rule.owasp_ref}]</span>
                    )}
                    {rule.remediation_hint && (
                      <p className="text-gray-500 mt-0.5">{rule.remediation_hint}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {outputScan && Object.keys(outputScan).length > 0 && (outputScan.risk_score as number) > 0 && (
        <div>
          <p className="text-gray-400 mb-1">{isJa ? "出力スキャン" : "Output Scan"}:</p>
          <p>
            {isJa ? "リスクスコア" : "Risk Score"}: <span className="font-bold text-red-400">{String(outputScan.risk_score)}/100</span>
          </p>
        </div>
      )}
      <p className="text-gray-500 italic">
        {isJa
          ? "これらはAigis SDKの実際のスキャン結果です。あなたのアプリにも同じ保護を追加できます。"
          : "These are real Aigis SDK scan results. Add the same protection to your apps."}
      </p>
    </div>
  );
}
