# Research Rotation

aigis 自動強化ループのリサーチ領域。6 時間ごとに 1 領域ずつ進む。
10 領域 × 6h = 60h で 1 周。数週間で複数周し、各領域の変化を時系列で捉える。

## 現在のカウンタ

```
NEXT_INDEX: 7
LAST_RUN_UTC: 2026-05-11T06-12
```

> 保守エージェントは実行開始時に `NEXT_INDEX` を読み、終了時に `(NEXT_INDEX + 1) % 10` に更新し、`LAST_RUN_UTC` を当回の開始 UTC に書き換える。

## 領域定義

| # | キー | 主たる調査対象 |
|---|------|--------------|
| 0 | `prompt-injection` | プロンプトインジェクション最新手法（直接/間接/multi-modal）。論文・PoC・実例 |
| 1 | `agent-tool-abuse` | エージェントの tool / MCP 濫用。tool poisoning、関数偽装、confused deputy |
| 2 | `data-exfiltration` | データ漏洩・PII 流出パターン。出力チャンネル悪用、URL exfil、log leak |
| 3 | `jailbreak-extraction` | jailbreak / system prompt 抽出技術。レッドチーム手法、universal adversarial |
| 4 | `memory-context` | メモリ汚染／コンテキスト操作／long-context attack／RAG poisoning |
| 5 | `supply-chain-llm` | LLM サプライチェーン（model/dataset/dep）攻撃。typosquatting、weight tampering |
| 6 | `multi-agent` | マルチエージェント間攻撃。agent-to-agent prompt smuggling、coordination abuse |
| 7 | `evasion-obfuscation` | 検知回避・敵対的難読化。encoding、homoglyph、policy bypass |
| 8 | `compliance-regulation` | 各国規制・ガイドライン更新（NIST AI RMF、EU AI Act、ISO/IEC、各国 AI 安全機関） |
| 9 | `incident-postmortems` | 実インシデント・CVE・ベンダーアドバイザリ・公表されたポストモーテム |

## 各領域からの引き出し方針

リサーチで見つけた事象は、以下のいずれかの形で aigis に落とし込む：

- 新規検出ルール（`aigis/policies/` 等の YAML / コード）
- 既存検出器の improvement（誤検知/取りこぼしの是正）
- 新規 compliance template（`policy_templates/` 配下）
- 監査ログ可視化／レポート上の表示項目追加
- ドキュメントベースの hardening guide（`docs/` 配下）

実装可能な落とし込みが見つからない回は CHANGELOG への追記なしで終わってよい
（`research/` と `INDEX.md` には必ず痕跡を残す）。
