# Aigis インシデントレスポンス戦略設計書

> 競合調査 + Aigisの差別化方針（2026-04-16）

---

## 1. 競合・類似ツールの「検出後」ワークフロー比較

### カテゴリ分類

AI セキュリティツールは大きく3層に分かれる：

| レイヤー | ツール例 | 得意領域 | 検出後の対応 |
|----------|---------|----------|-------------|
| **A. LLMファイアウォール** | Lakera Guard, CalypsoAI(F5), Robust Intelligence(Cisco) | リアルタイム遮断 | ブロック→SIEM転送。自前の対応UIは薄い |
| **B. LLM Observability** | Datadog LLM Obs, Langfuse, WhyLabs | トレース・評価・ダッシュボード | 検出→評価→人間レビューキュー。ブロック機能は弱い |
| **C. Guardrails SDK** | NeMo Guardrails, Guardrails.ai, LLM Guard | 開発者向けルール定義 | フロー停止→例外処理。運用UIなし |

### 各社の「検出後」設計の具体パターン

#### Lakera Guard（エンタープライズSaaS）
```
検出 → flagging response返却（JSONに脅威詳細）
     → アプリ側で判断（ブロック/警告/アラート）
     → SIEMに転送（Splunk/Sentinel等へのイベント送信）
     → ダッシュボードで集計表示
```
- **ポイント**: 対応判断はアプリ側に委ねる設計。Lakera自体にレビューUIやインシデント管理はない
- **SIEM連携**: イベントをSIEM/SOARに転送し、既存のセキュリティ運用フローに乗せる思想
- **価格**: 非公開（企業見積もり）

#### CalypsoAI → F5 AI Guardrails
```
検出 → リアルタイムブロック（cognitive layerで介入）
     → 全インタラクションの監査ログ
     → SIEM/SOAR/監査ワークフローへの統合
     → 「なぜブロックしたか」の説明性（Explainability）
```
- **ポイント**: 「なぜブロックされたか」の理由説明を重視。監査・コンプライアンス向け
- **F5買収額**: $180M — エンタープライズ市場の大きさを示す
- **価格**: 非公開

#### Datadog AI Guard（内部ツール → 製品化）
```
検出 → 同期ブロック（downstream到達前）
     → LLM Observabilityでトレース可視化
     → 評価メトリクス（Accuracy/Precision/Recall/F1）
     → PR毎の自動実験 → エンジニアがレビュー
     → 異常検出 → トレーニングデータへフィードバック
```
- **ポイント**: 「ガードレールの品質をCI/CDで計測する」開発者中心の設計。運用者向けUIではない
- **差別化**: ガードレール自体の精度をMLメトリクスで継続改善するループ

#### Langfuse（OSS Observability）
```
検出 → トレースにスコア付与
     → Annotation Queue（人間レビューキュー）
       - バルク選択 or 個別追加
       - レビュアーがスコア+コメント付与
       - 「Complete + next」で順次処理
     → LLM-as-a-Judge と人間評価を比較
     → ガードレール改善に反映
```
- **ポイント**: 人間レビューキューが最も充実。ただしブロック機能はない（観察専門）
- **通知**: なし（キューを見に行く必要がある）

#### NeMo Guardrails（NVIDIA OSS）
```
検出 → 会話フロー停止（intervention flow発動）
     → 定型の拒否メッセージ返却
     → ログ出力（Elastic等の外部Observabilityに転送可能）
```
- **ポイント**: 開発者が自分でフロー定義。運用者向けの管理UIは存在しない
- **Elastic連携**: AWS Bedrockとの組み合わせでElastic Observabilityに接続し、ダッシュボード+アラート

---

## 2. 業界全体の「未解決課題」（= Aigisの差別化チャンス）

調査から見えた、どのツールも十分に解決していない領域：

### Gap 1: 「ブロック」と「観察」が分離している
- **ファイアウォール系**（Lakera, CalypsoAI）→ ブロックはできるが対応管理UIがない
- **Observability系**（Langfuse, Datadog）→ 可視化は強いがブロックできない
- **誰も「ブロック + レビュー + 対応完了」を一気通貫で持っていない**

### Gap 2: SIEM依存の限界
- エンタープライズは「SIEMに投げればOK」という設計が主流
- しかし中小企業・スタートアップにはSplunk/Sentinelはオーバースペック
- **SIEMなしでもインシデント管理ができるビルトインUI**がない

### Gap 3: レビュー承認後のリクエスト再実行
- どのツールにも「レビュー承認 → 元のリクエストをLLMに再送」の仕組みがない
- Langfuseのキューは事後評価（品質改善目的）で、リアルタイム承認フローではない

### Gap 4: インシデントのライフサイクル管理
- 「検出 → 調査 → 対応 → クローズ → 再発防止」の一連の流れを管理するツールがない
- セキュリティインシデントのSTATUS管理はJira/ServiceNow任せ

### Gap 5: 管理者への段階的通知
- 検出時のSlack通知はあっても、SLA切れ警告、エスカレ通知、日次/週次レポート送信を一体で持つツールがない

---

## 3. Aigis差別化戦略：「Detection-to-Resolution」一気通貫

### ポジショニング

```
            ブロック力
               ↑
  Lakera ●    |     ● Aigis（ここを狙う）
  CalypsoAI ● |     |
               |     |
  NeMo ●      |     |
               |-----+----------→ 対応管理力
  LLM Guard ● |
               |   ● Langfuse
               |   ● Datadog LLM Obs
```

**Aigisの狙い**: ブロック力（既に6層検出あり）×対応管理力（ここを構築）の両方を持つ唯一のOSSツール

### 設計方針：3段階モデル

#### Phase 1: Immediate Response（即時対応）— 検出から5分以内

```
脅威検出
  ├─ score > 80 (CRITICAL) → 自動ブロック + 即時通知
  │    ├─ Slack通知（チャンネル + DM）
  │    ├─ メール通知（管理者宛）
  │    └─ Webhook（外部SIEM/PagerDuty等に転送可能）
  │
  ├─ score 50-80 (HIGH/MEDIUM) → レビューキューに投入
  │    ├─ レビュアーにSlack通知
  │    ├─ SLA開始（デフォルト30分）
  │    ├─ SLA残5分で警告通知
  │    └─ SLAタイムアウト → fallback policy適用 + 管理者通知
  │
  └─ score < 50 (LOW) → 自動許可 + ログ記録のみ
```

#### Phase 2: Daily Operations（日常運用）— レビューと対応

```
レビューキュー
  ├─ レビュアーのアクション
  │    ├─ 承認 → リクエスト再実行（元のLLMリクエストを再送）
  │    ├─ 却下 → ユーザーに却下理由通知
  │    ├─ エスカレート → セキュリティチームに転送 + 理由入力必須
  │    └─ 一括操作（同一パターンをまとめて処理）
  │
  ├─ インシデントカード（NEW）
  │    ├─ ステータス: Open → Investigating → Mitigated → Closed
  │    ├─ 担当者アサイン
  │    ├─ タイムライン（検出→レビュー→対応の全履歴）
  │    ├─ 関連イベントの自動紐づけ（同一IP/ユーザー/パターン）
  │    └─ 対応メモ（根本原因、対策内容）
  │
  └─ ダッシュボード
       ├─ リアルタイム監視（既存）
       ├─ SLA遵守率
       ├─ 平均レビュー時間
       └─ オープンインシデント数
```

#### Phase 3: Periodic Reporting（定期報告）— 週次/月次

```
自動レポート生成・配信
  ├─ 日次サマリー（Slack/メール）
  │    └─ 昨日のスキャン数、ブロック数、新規インシデント、SLA違反数
  │
  ├─ 週次レポート（PDF/Excel）
  │    ├─ 脅威トレンド（前週比）
  │    ├─ カテゴリ別検出数推移
  │    ├─ レビュー対応メトリクス
  │    └─ 自動修正（auto-fix）で追加されたルール
  │
  └─ 月次コンプライアンスレポート（PDF）
       ├─ OWASP LLM Top 10スコアカード
       ├─ SOC2/GDPR/日本法準拠状況
       ├─ インシデント一覧（Open/Closed）
       ├─ SLA遵守率
       └─ 推奨アクション（auto-fix提案含む）
```

---

## 4. 通知チャネル設計

| イベント | Slack | メール | Webhook | ダッシュボード |
|---------|-------|--------|---------|--------------|
| CRITICAL検出 | 即時 | 即時 | 即時 | リアルタイム |
| レビュー投入 | 即時 | - | オプション | リアルタイム |
| SLA残5分警告 | 即時 | - | - | バッジ表示 |
| SLAタイムアウト | 即時 | 即時 | 即時 | アラート |
| レビュー完了 | - | - | オプション | ステータス更新 |
| エスカレーション | 即時(チーム) | 即時(チーム) | 即時 | 専用キュー |
| 日次サマリー | 定時 | 定時 | - | - |
| 週次レポート | リンク通知 | 添付 | - | ダウンロード |
| 月次レポート | リンク通知 | 添付 | - | ダウンロード |

---

## 5. インシデントカード設計（Aigis独自機能）

**競合にない機能**: 検出イベントを「インシデント」として追跡し、対応完了まで管理する

```
┌─────────────────────────────────────────────┐
│ Incident #2026-0416-001                      │
│ Status: 🔴 Open → 🟡 Investigating          │
│ Severity: CRITICAL (score=95)                │
│ Assigned: admin@demo.com                     │
│ Created: 2026-04-16 16:30                    │
│ SLA: 30min (⚠ 5min remaining)              │
├─────────────────────────────────────────────┤
│ Timeline:                                    │
│  16:30  Detected: DAN Jailbreak attempt      │
│  16:30  Auto-blocked                         │
│  16:30  Slack notification sent              │
│  16:31  Assigned to admin@demo.com           │
│  16:35  Investigation started                │
│  16:40  Root cause: Testing by dev team      │
│  16:41  Status → Mitigated                   │
│  16:41  Note: "Dev team testing, not attack" │
├─────────────────────────────────────────────┤
│ Related Events (3):                          │
│  - Same IP: 2 other blocked requests         │
│  - Same pattern: 1 similar in last 24h       │
├─────────────────────────────────────────────┤
│ Actions:                                     │
│  [Add to allowlist] [Close] [Escalate]       │
└─────────────────────────────────────────────┘
```

---

## 6. 実装優先度

### Tier 1（最優先 — Aigisの差別化コア）
1. **インシデントカードUI** — Open→Investigating→Mitigated→Closedのライフサイクル
2. **通知ハブ** — Slack/メール/Webhookの統合送信（SLA警告含む）
3. **レビュー承認→リクエスト再実行** — review queueから承認したらLLMに再送

### Tier 2（重要 — 運用に必要）
4. **定期レポート自動配信** — 日次Slackサマリー、週次PDF
5. **エスカレーション先定義** — チーム/チャネル/外部Webhookの設定UI
6. **SLA fallback設定の実装** — block/allow/escalateの使い分け

### Tier 3（差別化強化）
7. **関連イベント自動紐づけ** — 同一IP/パターン/時間帯の相関分析
8. **SIEM連携** — Webhook汎用エクスポート（Splunk HEC/Elastic/Sentinel対応）
9. **レビュー品質メトリクス** — 平均対応時間、SLA遵守率、レビュアー別統計

---

## 7. 競合比較での売り文句

```
"ブロックするだけでは、セキュリティは完結しない。"

Lakera Guard = 検出+ブロック。対応は自分で。
Datadog LLM Obs = 可視化+評価。ブロックはできない。
Langfuse = トレース+レビュー。リアルタイム防御なし。

Aigis = 検出→ブロック→レビュー→対応→クローズ→レポート。
        Detection-to-Resolution、全部入り。
        しかもOSS。SIEMなしでも動く。
```

---

## Sources
- [Datadog LLM Guardrails Best Practices](https://www.datadoghq.com/blog/llm-guardrails-best-practices/)
- [Datadog AI Guard](https://www.datadoghq.com/blog/llm-observability-at-datadog-security/)
- [Lakera Guard Overview](https://www.lakera.ai/lakera-guard)
- [Lakera Guard API](https://docs.lakera.ai/guard)
- [F5 AI Guardrails (CalypsoAI)](https://www.f5.com/company/blog/what-are-ai-guardrails)
- [Langfuse Annotation Queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)
- [Langfuse Security Monitoring](https://langfuse.com/guides/cookbook/example_llm_security_monitoring)
- [NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/latest/about/overview.html)
- [Elastic + Bedrock Guardrails Observability](https://www.elastic.co/observability-labs/blog/llm-observability-amazon-bedrock-guardrails)
- [Top AI Security Tools 2026](https://www.reco.ai/compare/ai-security-tools-for-enterprises)
- [AI Agent Security Tools](https://aimultiple.com/agentic-ai-cybersecurity)
- [Lakera Alternatives Comparison](https://www.eesel.ai/blog/lakera-alternatives)
- [Wiz LLM Guardrails Guide](https://www.wiz.io/academy/ai-security/llm-guardrails)
- [Arthur AI Agent Guardrails](https://www.arthur.ai/blog/best-practices-for-building-agents-guardrails)
