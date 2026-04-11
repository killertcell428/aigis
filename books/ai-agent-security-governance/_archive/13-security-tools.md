---
title: "セキュリティツールの導入——Aigisとエコシステム"
---

# セキュリティツールの導入——Aigisとエコシステム

## AIエージェントセキュリティツールの全体像

AIエージェントのセキュリティを手動で管理し続けることは、スケールしません。本章では、セキュリティを自動化・強化するためのツール群を紹介し、実際の導入方法を解説します。

### ツールのカテゴリ

```
1. 入出力フィルタリング
   → プロンプトインジェクションの検出・ブロック
   
2. アクセス制御
   → 権限管理、ポリシー適用
   
3. 監査・ログ
   → 操作ログの記録・分析
   
4. 脆弱性スキャン
   → 依存関係・MCPサーバーの脆弱性検出
   
5. コンプライアンス
   → 規制要件への準拠状況の管理
```

## Aigis

Aigisは、AIアプリケーション向けのセキュリティライブラリです。プロンプトインジェクションの検出、機密情報の漏洩防止、コンプライアンス対応を統合的に提供します。

### 主な機能

| 機能 | 説明 |
|------|------|
| **入力フィルタリング** | 64種類の検出パターンによるプロンプトインジェクション検知 |
| **出力フィルタリング** | 機密情報（APIキー、PII等）の漏洩検出 |
| **リスクスコアリング** | 入出力のリスクを0.0〜1.0で定量評価 |
| **フレームワーク統合** | FastAPI、LangChain、LangGraph等との統合ミドルウェア |
| **コンプライアンス** | 総務省ガイドライン等への準拠チェック |
| **監査ログ** | 全検出イベントの構造化ログ出力 |

### インストールと基本利用

```bash
pip install aigis
```

```python
from aigis import Guard

# 基本的な使用方法
guard = Guard()

# 入力のスキャン
result = guard.scan_input("ユーザーからの入力テキスト")
if result.is_safe:
    # 安全な入力 → LLMに渡す
    response = llm.generate(result.sanitized_text)
else:
    # リスク検出 → ブロックまたは警告
    print(f"Risk detected: {result.findings}")

# 出力のスキャン
output_result = guard.scan_output(response)
if not output_result.is_safe:
    # 機密情報の漏洩を検出
    print(f"Sensitive data detected: {output_result.findings}")
```

### 検出パターンの例

Aigisは64種類の検出パターンを内蔵しています。

```python
# プロンプトインジェクション検出パターン（一部）
PATTERNS = {
    "instruction_override": r'ignore\s+(previous|prior|above)',
    "role_hijack":          r'you\s+are\s+now\s+a',
    "system_prompt_fake":   r'system\s*:\s*',
    "hidden_html":          r'<!--.*?-->',
    "command_injection":    r'(curl|wget|nc)\s+http',
    "credential_access":    r'cat\s+~/?\.(ssh|aws|env)',
    "data_encoding":        r'base64\s+(encode|decode)',
    "file_exfiltration":    r'cat\s+/etc/(passwd|shadow)',
}

# 機密情報検出パターン（一部）
SENSITIVE_PATTERNS = {
    "aws_key":        r'AKIA[0-9A-Z]{16}',
    "openai_key":     r'sk-[a-zA-Z0-9]{48}',
    "anthropic_key":  r'sk-ant-[a-zA-Z0-9\-]{80,}',
    "github_token":   r'ghp_[a-zA-Z0-9]{36}',
    "private_key":    r'-----BEGIN.*PRIVATE KEY-----',
    "email":          r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "phone_jp":       r'\d{2,4}-\d{2,4}-\d{4}',
}
```

### FastAPI統合

```python
from fastapi import FastAPI
from aigis.middleware.fastapi import AIGuardianMiddleware

app = FastAPI()
app.add_middleware(AIGuardianMiddleware, risk_threshold=0.7)

@app.post("/chat")
async def chat(message: str):
    # ミドルウェアが自動的に入出力をスキャン
    response = await llm.generate(message)
    return {"response": response}
```

### LangChain統合

```python
from langchain.chat_models import ChatAnthropic
from aigis.middleware.langchain import AIGuardianCallback

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    callbacks=[AIGuardianCallback(risk_threshold=0.7)]
)

# コールバックが自動的に入出力をスキャン
response = llm.invoke("ユーザーの質問")
```

## その他のセキュリティツール

### 入出力フィルタリング

| ツール | 特徴 | 用途 |
|--------|------|------|
| **Aigis** | 64パターン、日本語対応、軽量 | 汎用的なAIセキュリティ |
| **Rebuff** | プロンプトインジェクション特化 | PI検出 |
| **NeMo Guardrails** | NVIDIA製、対話型ガードレール | チャットボット |
| **Guardrails AI** | 構造化出力の検証 | 出力品質管理 |

### 認証情報検出

| ツール | 特徴 |
|--------|------|
| **detect-secrets** | Yelp製、pre-commit対応 |
| **truffleHog** | Git履歴のスキャン |
| **gitleaks** | CI/CD統合に強い |

### 依存関係の脆弱性スキャン

| ツール | 言語 |
|--------|------|
| **npm audit** | Node.js |
| **pip-audit** | Python |
| **Snyk** | マルチ言語 |
| **Dependabot** | GitHub統合 |

### ログ・監視

| ツール | 特徴 |
|--------|------|
| **Datadog** | APM + ログ + メトリクス統合 |
| **Splunk** | エンタープライズSIEM |
| **CloudWatch** | AWS統合 |
| **Grafana + Loki** | OSS、ダッシュボード |

## ツール導入のロードマップ

```
Phase 1: 即時導入（1週間）
├── detect-secrets （pre-commit フック）
├── .claudeignore / .gitignore の整備
├── CLAUDE.md のセキュリティポリシー記載
└── npm audit / pip-audit の手動実行

Phase 2: 自動化（1ヶ月）
├── Aigis の統合（入出力フィルタリング）
├── CI/CD での脆弱性スキャン自動化
├── Claude Code フックの導入
└── ログ集約の開始

Phase 3: 高度化（3ヶ月）
├── SIEM統合（Datadog/Splunk）
├── 異常検知ルールの設定
├── コンプライアンスダッシュボード
└── 定期的なセキュリティ評価の自動化
```

## ツール選定の基準

```
✅ 選定基準:
  - 既存のワークフローへの統合のしやすさ
  - メンテナンスの継続性（最終更新日、コミュニティ）
  - ドキュメントの充実度
  - ライセンスの互換性
  - パフォーマンスへの影響

❌ 避けるべき:
  - メンテナンスが停止しているツール
  - 過度に複雑な設定が必要なツール
  - ワークフローを大幅に変更する必要があるツール
  - ベンダーロックインが強いツール
```

セキュリティツールは「導入して終わり」ではなく、継続的な運用と改善が必要です。まずは最小限のツールから始め、組織の成熟度に応じて段階的に拡充していくアプローチを推奨します。
