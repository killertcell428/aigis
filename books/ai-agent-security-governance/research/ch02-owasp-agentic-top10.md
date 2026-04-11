# 第2章 ファクトシート：脅威の全体像 — OWASP Agentic Top 10 を読み解く

## 1. OWASP Top 10 for Agentic Applications

**出典**: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications/
**発表**: 2025年初頭（OWASP GenAI プロジェクト配下）

### ASI01: Agentic Goal Hijacking（エージェント目的の乗っ取り）
- **リスク**: 攻撃者がPI等を通じてエージェントの本来の目的を別の目的にすり替える
- **攻撃例**: 文書要約依頼 → 文書内の悪意ある指示で機密データ外部送信に目的変更
- **対策**: system prompt hardening、ゴール検証、出力サニタイズ、HITL承認

### ASI02: Tool and Function Misuse（ツール・関数の悪用）
- **リスク**: エージェントのツールを意図しない方法で使用・操作される
- **攻撃例**: DBクエリツールへのSQLインジェクションで権限外データ取得
- **対策**: 最小権限、ツール呼び出しバリデーション、サンドボックス実行、ホワイトリスト

### ASI03: Excessive Permissions（過剰な権限）
- **リスク**: 必要以上の権限付与で攻撃・誤動作時の影響範囲が拡大
- **攻撃例**: CSエージェントに管理者権限 → 目的乗っ取り後に全ユーザーデータ削除可能
- **対策**: RBAC、動的スコーピング、タスクごとの権限分離

### ASI04: Insufficient Sandboxing（不十分なサンドボックス化）
- **リスク**: コード実行・システム操作が隔離されずホスト環境に不正アクセス可能
- **攻撃例**: 生成コードをサンドボックスなしで実行 → ホストOSファイルシステムにアクセス
- **対策**: コンテナ化、gVisor、ネットワーク分離、読み取り専用マウント

### ASI05: Insecure Output Handling（安全でない出力処理）
- **リスク**: 出力がサニタイズされずXSS・コマンドインジェクションに繋がる
- **攻撃例**: エージェント生成HTMLにスクリプト埋込 → ブラウザで実行
- **対策**: 出力エスケーピング、CSP、出力フォーマット検証

### ASI06: Improper Multi-Agent Orchestration（不適切なマルチエージェント連携）
- **リスク**: マルチエージェント環境で信頼境界・認証・通信の安全性が不十分
- **攻撃例**: 1エージェント侵害 → 踏み台にして他エージェントに悪意ある指示伝播
- **対策**: ゼロトラスト認証、メッセージ署名・検証、暗号化通信、集中監視

### ASI07: Uncontrolled Autonomous Actions（制御されない自律的行動）
- **リスク**: 人間の監視なしに重大影響のある行動を自律実行
- **攻撃例**: 投資エージェントが異常データで大量誤取引を人間確認なしに実行
- **対策**: HITL、影響度ベース承認フロー、レートリミット、金額上限

### ASI08: Cascading Hallucination and Failures（連鎖するハルシネーションと障害）
- **リスク**: 1エージェントのハルシネーション・障害が連鎖的に波及・増幅
- **攻撃例**: リサーチ誤情報 → 意思決定が採用 → 実行エージェントが誤判断で行動
- **対策**: ファクトチェック機構、サーキットブレーカー、信頼度メタデータ伝播、異常検知

### ASI09: Insufficient Logging and Monitoring（不十分なログ記録と監視）
- **リスク**: 行動・判断・ツール使用のログ不足でインシデント検知・監査が困難
- **攻撃例**: 徐々に権限昇格する攻撃を行動ログ未記録で検知できない
- **対策**: 全ツール呼び出し監査ログ、reasoning trace記録、リアルタイム異常検知、改ざん防止

### ASI10: Trust Boundary Violations（信頼境界の侵害）
- **リスク**: 異なる信頼レベルのデータ・ツール・ユーザーを区別せず信頼境界を越える
- **攻撃例**: 外部Web未検証データを内部DB書込権限エージェントがそのまま処理
- **対策**: データ来歴（provenance）追跡、信頼レベルタグ、境界ごとバリデーション、Taint Analysis

---

## 2. OWASP Securing Agentic Applications Guide

### 主要推奨事項
1. Defense in Depth（多層防御）
2. Least Privilege（最小権限）
3. Human Oversight（人間の監視）
4. Input/Output Validation
5. Audit Trail（監査証跡）

### 実装パターン
- **Guardian Agent パターン**: メインエージェント出力を監視・検証する別エージェント
- **Tool Use Proxy パターン**: ツール呼び出しをプロキシ経由にしポリシー違反検知
- **Staged Execution パターン**: 計画→承認→実行のステージ分離

---

## 3. 各リスクの連鎖パターン

### パターン1: Goal Hijack → Tool Misuse → Cascading Failures
ASI01 → ASI02 → ASI08
例: メール処理エージェントが悪意あるメールでゴール乗っ取り → カレンダーAPI悪用 → 他のワークフローに波及

### パターン2: Excessive Permissions → Uncontrolled Actions → Trust Boundary Violations
ASI03 → ASI07 → ASI10
例: 過剰権限 → 制御されない行動 → 信頼境界を越えたデータアクセス

### パターン3: Improper Orchestration → Insufficient Logging → 検知不能
ASI06 → ASI09
例: エージェント間認証不十分 → 行動記録なし → インシデント検知の大幅遅延

---

## 4. 実際のインシデントとの対応

| ASI項目 | インシデント | 出典 |
|---|---|---|
| ASI01 | Bing Chat/Bard への間接PI | Greshake et al., 2023 (arXiv:2302.12173) |
| ASI01 | ChatGPTプラグイン経由の情報漏洩 | セキュリティ研究者による実証（2023年） |
| ASI02 | AIコーディングアシスタントの悪意あるコード生成 | 複数報告（2023-2024年） |
| ASI05 | LLM出力のXSS脆弱性 | OWASP LLM Top 10 LLM02 |
| ASI07 | AutoGPT/AgentGPTの暴走（APIコスト大量消費） | 複数報告（2023-2024年） |

⚠️ エージェントAI固有のCVE体系は2025年時点で未成熟

---

## 5. OWASP LLM Top 10 との対応関係

| 観点 | LLM Top 10 | Agentic Top 10 |
|------|------------|-----------------|
| 対象 | LLMアプリケーション全般 | 自律型AIエージェント |
| スコープ | 単一のLLM呼び出し中心 | マルチステップ・マルチツール・マルチエージェント |
| 主要関心事 | PI、データ漏洩 | 自律行動制御、ツール悪用、連鎖障害 |

進化のポイント:
- LLM01 Prompt Injection → ASI01 Goal Hijacking（上位概念に発展）
- LLM02 Insecure Output → ASI05（エージェント間通信の文脈追加）
- ASI06/07/08 はエージェント固有の**新規項目**

### MITRE ATLAS との対応

| ASI項目 | ATLAS技法 |
|---|---|
| ASI01 | AML.T0051 LLM Prompt Injection |
| ASI02 | AML.T0054 LLM Plugin Compromise（類似） |
| ASI04 | AML.T0048 C&C via AI Model（関連） |
| ASI05 | AML.T0043 Craft Adversarial Data |
| ASI09 | AML.T0052 Evade ML Model（検知回避関連） |

---

## 要検証事項

- [ ] 2026年版 OWASP Agentic Top 10 の変更点確認（公式サイト）
- [ ] Securing Agentic Applications Guide 1.0 正式版の全文確認
- [ ] カバレッジマトリクスの公開状況
- [ ] MITRE ATLAS 最新版のID確認
- [ ] AI Incident Database (https://incidentdatabase.ai/) での最新インシデント補完
