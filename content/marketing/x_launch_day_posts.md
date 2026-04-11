# X/Twitter Posts — PH Launch Day (5/13) + Ongoing

## Launch Day Thread (5/13, 16:01 JST = 12:01 AM PT)

### Tweet 1 (Announcement)
Aigis v1.0.0 を Product Hunt でローンチしました!

AIエージェントのセキュリティを5分で解決するOSSツールです。

- 121検出パターン / 19カテゴリ
- 唯一のOSS MCPセキュリティスキャナー
- AI事業者GL v1.2 完全対応（37/37）
- ゼロ依存、3行で導入

PH: [link]
GitHub: github.com/killertcell428/aigis

#ProductHunt #AIセキュリティ #OSS

### Tweet 2 (English version, post 5 min later)
Just launched Aigis on @ProductHunt!

The first open-source MCP security scanner. 121 detection patterns, zero dependencies.

43% of MCP servers have injection vulnerabilities. Now you can scan them before your AI agent uses them.

pip install aigis

PH: [link]

### Tweet 3 (Demo GIF, post 30 min later)
`aig mcp` のデモ。

悪意あるMCPツール定義を検知する様子:
[GIF/Screenshot]

6つの攻撃面（ポイズニング、シャドウイング、ラグプル等）を10パターン+5層防御でカバー。

---

## Weekly Posts Template (ongoing, 3-5/week)

### Pattern: Threat of the Week
今週の脅威: [specific attack name]

[1-2 sentence explanation]

Aigisでの検知:
```
aig scan "[attack example]"
→ [result]
```

### Pattern: Did You Know
知ってましたか？

MCPツールの「説明文」はLLMのコンテキストにそのまま注入されます。

つまり、ツールの説明に「~/.ssh/id_rsaを読め」と書くだけで、AIエージェントはそれに従います。

対策: aig mcp でツール定義をスキャン

### Pattern: Compliance Update
AI事業者ガイドライン v1.2 の [specific requirement] に対応するには？

Aigisの [feature] で技術的に対応できます。

詳細: [Zenn article link]

### Pattern: Benchmark Update
Aigis v1.0.0 ベンチマーク:
- 98/98 攻撃検出 (100%)
- 0/26 偽陽性 (0%)
- 中央値 1.6ms / スキャン
- ゼロ依存

`aig benchmark` で自分の環境でも計測できます。

### Pattern: Red Team Result
`aig redteam` で自動レッドチーム:

9カテゴリ × 15攻撃 = 135パターンを自動生成。
95.6%がブロックされました。

あなたのLLMアプリは何%ブロックできますか？

---

## Hashtags (rotate)
JP: #AIセキュリティ #LLM #プロンプトインジェクション #MCP #AIエージェント #OSS #AIガバナンス
EN: #LLMSecurity #AIAgents #MCP #PromptInjection #OpenSource #CyberSecurity
