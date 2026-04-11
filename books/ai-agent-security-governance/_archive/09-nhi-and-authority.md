---
title: "NHI管理と権限設計——エージェントを「非人間ID」として管理する"
---

# NHI管理と権限設計——エージェントを「非人間ID」として管理する

## AIエージェントの暴走は「権限の問題」である

AIエージェントが意図しない行動を取ると「モデルが悪い」と考えがちです。しかし実際のインシデントの大部分は**権限設計の不備**に起因しています。

> "Most agentic failures are not model failures but authority failures."
> — Bessemer Venture Partners

Ciscoの調査でも**50%以上の企業がセキュリティレビューなしにエージェントをデプロイ**しています。モデルの性能以前に、与えられた権限が不適切であれば安全は担保できません。

---

## Part 1：NHI（Non-Human Identity）管理

### AIエージェントは「サービスアカウント」である

Claude Codeのセッションは技術的に以下の特性を持ちます。

- 固有のAPIコンテキスト（セッションID）
- ファイルシステム・ターミナル・ネットワークへのアクセス
- 長時間の自律実行
- 複数のAPIキーへのアクセス

これは**サービスアカウントの定義そのもの**です。しかし多くの組織で、AIエージェントはIAMの管理対象外に置かれています。

![NHIライフサイクル管理](/images/ch11-nhi-lifecycle.png)
*図：NHIライフサイクル管理 — 人間アカウントとAIエージェントの比較*

### 統計が示す危機

| 指標 | 数値 | 出典 |
|------|------|------|
| NHI関連の侵害率 | **68%** | Verizon DBIR 2025 |
| NHI対人間アカウント比率 | **45:1** | CyberArk Survey |
| NHI侵害が人間侵害を上回る | **初めて** | Verizon DBIR 2025 |

### 現状のギャップ

| 観点 | 人間の開発者 | AIセッション（現状） |
|------|-------------|---------------------|
| アイデンティティ | SSO/IdPで管理 | 共有APIキー（ID無し） |
| 権限スコープ | ロールベース（明示的） | 無制限（ツール範囲内） |
| 監査ログ | 組織全体に統合 | ローカルのみ |
| ライフサイクル | HR起点（入社/退社） | 管理なし |
| インシデント対応 | アカウント無効化 | 対応手段なし |

### 4つのNHI管理原則

**原則1：最小権限（Least Privilege）**

```yaml
# claude_code_policy.yaml
permissions:
  file_access:
    read_write: ["./src/", "./tests/"]
    read_only: ["./docs/"]
    deny: ["~/.ssh/", "~/.aws/", ".env*", "**/*.pem"]
  commands:
    allow: ["npm test", "git status", "git diff", "python -m pytest"]
    deny: ["rm -rf", "curl *", "wget *", "ssh *", "sudo *"]
  network:
    allow: ["api.anthropic.com", "registry.npmjs.org"]
    deny_all_others: true
```

**原則2：Just-in-Timeアクセス**

常時アクセス権を保持するのではなく、セッション開始時に最小スコープの一時認証を発行し、終了とともに自動失効させます。AWS STSやGCP Workload Identity Federationが有効です。

**原則3：監査可能性（Auditability）**

```python
# Claude Codeフックを利用したログ送信
log_entry = {
    "timestamp": "2026-04-01T10:30:00Z",
    "session_id": session_id,
    "developer_id": developer_id,
    "tool": "Bash",
    "action": "command_execution",
    "target": "npm test",
    "risk_score": 0.1,
}
send_to_logging_platform(log_entry)  # CloudWatch, Datadog, Splunk等
```

**原則4：アイデンティティ分離**

```
❌ チーム全員が同じAPIキーを共有 → 追跡不能
✅ 開発者ごと・用途ごとにAPIキーを分離
   開発者A: ANTHROPIC_API_KEY_DEV_A
   CI/CD:   ANTHROPIC_API_KEY_CI（最小権限）
   本番:    ANTHROPIC_API_KEY_PROD（厳格制限）
```

### NHIライフサイクル管理

| フェーズ | 従来のIAM | AIエージェントNHI |
|----------|-----------|-------------------|
| プロビジョニング | HR入社→アカウント作成 | タスク開始→スコープ付きセッション認証発行 |
| 権限管理 | ロール+グループ | ポリシーファイル+ツール制限 |
| 監査 | ログイン/操作ログ | ツール呼び出し+コマンド+ファイルアクセスログ |
| ローテーション | 90日パスワード変更 | セッション終了で自動失効+定期キーローテーション |
| デプロビジョニング | 退社→無効化 | セッション終了→即時無効化 |

---

## Part 2：権限設計の原則

### Confused Deputy Problem

エージェントがユーザーの権限を超えたアクセスを許可する問題です。

```
ユーザーA（一般社員）: 自部門のファイルのみアクセス権限
AIエージェント: 全社共有ドライブへのアクセス権限

→ ユーザーAがAI経由で他部門の機密ファイルを取得
```

### 権限の交差モデル

![権限の交差モデル](/images/ch12-permission-intersection.png)
*図：エージェント権限の交差モデルとリスクレベル別の承認フロー*

エージェントの実効権限は、**ユーザー権限とエージェント権限の交差（AND）**であるべきです。

```
実効権限 = ユーザー権限 ∩ エージェント権限

例:
  ユーザー権限:     {読み取り: 部門A, 書き込み: 部門A}
  エージェント権限: {読み取り: 全社, 書き込み: なし}
  実効権限:         {読み取り: 部門A, 書き込み: なし}
```

### 段階的承認モデル

操作のリスクレベルに応じて承認要件を変えます。

| レベル | 承認 | 操作例 |
|--------|------|--------|
| **Lv.1** | 自動承認 | 許可パス内の読み取り、git status、テスト実行 |
| **Lv.2** | ログ記録+自動承認 | ファイル書き込み、パッケージインストール |
| **Lv.3** | 人間の承認必須 | ファイル削除、外部通信、新APIキー使用 |
| **Lv.4** | 禁止 | `rm -rf` / `sudo` / `cat ~/.ssh/` |

### ポリシーベースのアクセス制御

```yaml
# agent_policy.yaml
version: "1.0"
default_action: deny  # デフォルトは拒否

rules:
  - name: "ソースコードの読み書き"
    action: allow
    resources:
      - type: file
        paths: ["./src/**", "./tests/**"]
        operations: [read, write, create]
  
  - name: "機密ファイルの保護"
    action: deny
    priority: high
    resources:
      - type: file
        paths: [".env*", "**/*.key", "~/.ssh/**", "~/.aws/**"]
  
  - name: "安全なコマンドのみ許可"
    action: allow
    resources:
      - type: command
        patterns: ["npm test*", "git status", "git diff*"]
  
  - name: "外部通信の制限"
    action: deny
    resources:
      - type: network
        destinations: ["*"]
    exceptions: ["api.anthropic.com", "registry.npmjs.org"]
```

### ゼロトラストアプローチ

```
従来:「一度認証したエージェントは信頼する」
     → セッション中のすべての操作を無条件に許可

ゼロトラスト:「毎回の操作で権限を検証する」
     → 各ツール呼び出しで権限チェック
     → 機密操作は追加承認を要求
     → 異常パターン検出で自動停止
```

---

## アンチパターン：避けるべき権限設計

| アンチパターン | リスク |
|---------------|--------|
| 「とりあえず全権限」 | インシデント時の被害が最大化 |
| 「一度設定したら放置」 | 不要な権限が残り続ける |
| 「共有APIキーで全員同じ」 | 責任追跡不能、漏洩時の影響が全員に波及 |
| 「セキュリティはモデル任せ」 | ガードレールは回避可能。権限はモデル非依存であるべき |
| 「社内利用だから安全」 | 内部脅威・意図しない操作のリスクは変わらない |

---

## 今日からできる4つのクイックウィン

| # | アクション | 所要時間 |
|---|-----------|---------|
| 1 | **インベントリ作成**: 全AIセッション・APIキーの洗い出し | 1時間 |
| 2 | **キー分離**: 個人別・用途別にAPIキーを発行 | 30分 |
| 3 | **CLAUDE.mdポリシー**: 禁止・許可の明記 | 30分 |
| 4 | **ログ集約**: フックで操作ログを組織ログ基盤に送信 | 2時間 |

NHI管理と権限設計は、AIエージェントガバナンスの**核心**です。「AIエージェントは非人間アイデンティティとして管理する」——この認識を組織全体で共有することが、安全なAI活用の第一歩です。
