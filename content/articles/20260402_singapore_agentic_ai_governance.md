---
title: "世界初のエージェンティックAIガバナンスフレームワーク — シンガポールIMDAが示した「行動するAI」時代の5つのリスク管理原則"
emoji: "🏛️"
type: "tech"
topics: ["AIガバナンス", "AIエージェント", "セキュリティ", "コンプライアンス", "エンタープライズ"]
published: false
---

## はじめに

2026年1月22日、シンガポールの情報通信メディア開発庁（IMDA）がダボス会議（WEF）の場で世界初の「エージェンティックAIガバナンスフレームワーク」を発表しました。

これは単なるガイドラインではありません。**AIエージェントが自律的に「行動」する時代における責任・統制・技術設計の三位一体の枠組み**を初めて体系化したものです。日本でAIエージェントの企業導入を検討しているエンジニア・CTOにとって、このフレームワークを知ることは今後の設計の基準点になります。

---

## なぜ今「エージェンティックAI専用」ガバナンスが必要なのか

従来のAIガバナンスは「AIが推薦→人間が判断→人間が実行」という前提で設計されていました。しかしAIエージェントの登場により、この前提が崩れています。

| 従来のAI | AIエージェント |
|---------|-------------|
| 推薦・予測のみ | ツール呼び出し・外部API実行 |
| 人間が承認 | 自律的に連続行動 |
| 単一タスク完結 | マルチステップ・長期タスク |
| 影響範囲が限定的 | ファイル削除・メール送信・DB書き込み等 |
| エラーの巻き戻しが容易 | 取り消し不可能な副作用が発生しうる |

Gartnerの予測では、2026年末までにエージェンティックAIは企業アプリケーションの40%以上に組み込まれるとされています（2025年時点では5%未満）。しかしCiscoの調査（State of AI Security 2026）では、**稼働中のAIエージェントのうちセキュリティ・IT部門の正式承認を得ているのはわずか14.4%** というのが現実です。

このギャップを埋めるための最初の国際的な参照フレームワークが、シンガポールのものです。

---

## シンガポールAIガバナンスフレームワーク 2.0 — エージェンティック版の概要

### フレームワークの位置づけ

IMDAが2020年に初版を公開した「Model AI Governance Framework」の大幅改訂版です。今回の改訂の最大の焦点は**エージェンティックAIへの対応**であり、「AIが人間の監督なしに連続的な行動を取る」シナリオを正面から扱った最初の政府公式ドキュメントとなりました。

策定には100以上の企業・研究機関が参画し、NST（米国国立標準技術研究所）と欧州委員会による査読を経ています。

### 定義するエージェンティックAIとは

フレームワークでは、エージェンティックAIを以下のように定義しています：

> 人間の継続的な監督なしに、目標達成に向けて複数ステップの行動を計画・実行し、外部システムと相互作用できるAIシステム

この定義により、単純なチャットボットやRAGシステムはスコープ外となり、**ツールを持ち・自律判断し・副作用を伴う行動を取れるシステム**が対象となります。Claude CodeやCopilot Studio、AutoGenベースのシステムはこれに該当します。

---

## 5つのリスクカテゴリーと管理要件

フレームワークの核心は、エージェンティックAI固有のリスクを5つに分類し、それぞれに技術・プロセス・組織の三層で対応策を定めていることです。

### リスク1: 誤った行動（Erroneous Action）

**定義**: エージェントが誤った判断・入力・推論に基づいて有害な行動を取るリスク

**主な懸念シナリオ**:
- ファイル削除の対象を誤認識して本番DBのデータを削除
- 誤った顧客情報を参照してメールを誤送信

**フレームワークが求める対応**:
```yaml
技術的管理:
  - 取り消し可能な操作を優先する設計（"reversibility by default"）
  - 取り消し不可能な操作前の確認フロー実装
  - アクション実行前のドライラン機能

プロセス的管理:
  - エラー境界（error boundary）の文書化
  - インシデント対応手順のエージェント特化版作成
```

### リスク2: 許可されていない行動（Unauthorized Action）

**定義**: エージェントが付与された権限の範囲を超えた行動を取るリスク

**主な懸念シナリオ**:
- カレンダー参照のみを許可されたエージェントがメール送信を実行
- 財務データ読み取り権限のエージェントが外部APIに情報を転送

**フレームワークが求める対応**:
```python
# 推奨されるアーキテクチャ：明示的な権限リスト（allowlist）
agent_permissions = {
    "allowed_tools": ["read_calendar", "create_calendar_event"],
    "denied_tools": ["send_email", "read_email", "file_write"],
    "scope_limits": {
        "data_access": ["own_calendar"],
        "external_apis": []  # 外部API呼び出しは原則禁止
    }
}
```

特に重要なのが **最小権限原則（Principle of Least Privilege）のエージェント適用**です。フレームワークは「タスク完了に必要な最小限の権限のみを付与し、タスク完了後は即時失効させる」ことを推奨しています。

### リスク3: 偏った・不公平な行動（Biased/Unfair Action）

**定義**: エージェントが差別的・偏った判断に基づいて行動し、影響を与えるリスク

採用・融資・医療などの高リスク領域での自動意思決定を中心に扱っており、技術的なセキュリティよりも倫理・公平性に焦点を当てています。

**フレームワークが求める対応**:
- 高リスク領域での意思決定ログの全記録
- 定期的なバイアス監査（少なくとも四半期ごと）
- 影響を受けた個人への説明可能性の確保

### リスク4: データ漏洩（Data Breach）

**定義**: エージェントが処理・保存するデータが不正アクセス・漏洩するリスク

エージェントは複数のツール・API・データソースと接続するため、従来のシステムよりも攻撃対象面（attack surface）が広くなります。

**フレームワークが求める対応**:

```bash
# 推奨されるログ設計
# すべてのツール呼び出しを記録（入出力含む）
{
  "timestamp": "2026-04-02T10:15:30Z",
  "agent_id": "agent_001",
  "tool": "read_file",
  "input": {"path": "/data/reports/Q1.csv"},
  "output_hash": "sha256:abc123...",  # 出力そのものではなくハッシュ
  "user_id": "user_42",
  "session_id": "sess_xyz"
}
```

特筆すべきは「**エージェントのメモリ（コンテキスト）もデータとして扱え**」という要件です。長期記憶ストアに保存されたユーザー情報は個人データとして管理し、保持期間・削除要件を定めることが求められます。

### リスク5: 悪意ある操作（Adversarial Manipulation）

**定義**: 攻撃者がエージェントを操作して意図しない行動を取らせるリスク

これがエンジニアにとって最も技術的に深いカテゴリです。フレームワークが明示的に言及している攻撃手法：

| 攻撃手法 | 概要 | 対策 |
|---------|------|------|
| プロンプトインジェクション | 悪意あるコンテンツでエージェントの指示を書き換え | 入力サニタイズ、コンテキスト分離 |
| ツールポイズニング | 悪意あるMCPサーバーが偽の情報を返す | ツール出力の検証、信頼できるソースの明示 |
| マルチエージェント信頼攻撃 | 悪意あるエージェントが他のエージェントを操作 | エージェント間通信の認証・検証 |
| 間接的プロンプトインジェクション | Webページ・ファイル内の悪意ある指示を実行 | ツール出力のサンドボックス化 |

---

## 日本企業が特に注目すべき「人間の監督」要件

フレームワークの中で日本企業にとって最も実務的な含意を持つのが「**Human Oversight（人間の監督）**」の要件化です。

### 監督レベルの分類

```
レベル1: Human-in-the-loop（人間が各行動を承認）
レベル2: Human-on-the-loop（人間が監視し必要時に介入）  ← 推奨最低ライン
レベル3: Human-out-of-the-loop（完全自律、高リスク領域では禁止）
```

フレームワークは「**リスクの大きさに応じて最低限のHuman Oversightレベルを定めよ**」と要求しています。取り消し不可能な外部アクション（メール送信・支払い・ファイル削除等）はレベル1または2が必須とされます。

### 実装例：Claude Codeでの対応

Claude Codeの`--dangerously-skip-permissions`フラグを使った完全自動化は、この観点ではレベル3（Human-out-of-the-loop）に該当します。エンタープライズ環境での使用には、少なくとも事後監査ログの完全記録と定期的なアクションレビューが必要です。

```yaml
# claude_code_governance.yaml 設定例
oversight:
  level: "human_on_loop"
  review_triggers:
    - file_deletion
    - external_api_call
    - database_write
  audit_log:
    enabled: true
    retention_days: 90
    include_full_context: true
```

---

## 日本への影響：EU AI ActとのアライメントとISO/IEC 42001

シンガポールのフレームワークはEU AI Act（2025年8月完全施行）との整合性を意識して設計されています。

| 項目 | EU AI Act | Singapore フレームワーク |
|------|-----------|----------------------|
| 高リスクAIの定義 | 用途ベース（採用・医療・法執行等） | リスクカテゴリ×自律度のマトリクス |
| ログ保持要件 | 最低6ヶ月 | タスクリスクレベルに応じて定義 |
| 人間監督要件 | 高リスク用途で義務 | エージェント全体に段階的要件 |
| インシデント報告 | 重大インシデントは当局報告 | 内部記録 + 推奨報告 |

ISO/IEC 42001（AIマネジメントシステム）の認証取得を目指す日本企業にとって、このフレームワークは実務的な実装ガイドとして活用できます。

---

## まとめ

- シンガポールIMDAが2026年1月に発表したエージェンティックAIガバナンスフレームワークは、自律的に行動するAIを扱う**世界初の包括的ガバナンス文書**
- 5つのリスクカテゴリ（誤行動・不正行動・偏り・データ漏洩・悪意ある操作）に対し、技術・プロセス・組織の三層で対応策を定義
- **最小権限原則・取り消し可能設計・完全な監査ログ**がエンジニアリング要件のコアとなる
- EU AI ActやISO/IEC 42001との整合性を持ち、グローバル展開する日本企業の設計基準として機能する
- 完全自律エージェント（Human-out-of-the-loop）は高リスク領域では原則禁止とされており、Claude Code等の本番自動化には監督設計が必須

:::message
Aigisは「AIエージェントが何をしたか」を記録・可視化するガバナンス基盤として開発中のサービスです。このフレームワークが求める監査ログ・権限管理・Human Oversightの実装を支援することを目指しています。
:::

## 参考リンク

- [Singapore Model AI Governance Framework for Agentic AI (IMDA, January 2026)](https://www.imda.gov.sg/how-we-can-help/model-ai-governance-framework)
- [K&L Gates: Singapore's New Model AI Governance Framework for Agentic AI](https://www.klgates.com/Singapores-New-Model-AI-Governance-Framework-for-Agentic-AI-2026-Client-Alert-2-9-2026)
- [Baker McKenzie: Singapore Launches First Global Agentic AI Governance Framework](https://www.bakermckenzie.com/en/insight/publications/2026/01/singapore-governance-framework-for-agentic-ai-launched)
- [Cisco State of AI Security 2026 Report](https://blogs.cisco.com/ai/cisco-state-of-ai-security-2026-report)
- [Microsoft Security Blog: Addressing OWASP Top 10 in Agentic AI with Copilot Studio](https://www.microsoft.com/en-us/security/blog/2026/03/30/addressing-the-owasp-top-10-risks-in-agentic-ai-with-microsoft-copilot-studio/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [Hogan Lovells: Singapore Launches First Global Agentic AI Governance Framework](https://www.hoganlovells.com/en/publications/singapore-launches-first-global-agentic-ai-governance-framework)
