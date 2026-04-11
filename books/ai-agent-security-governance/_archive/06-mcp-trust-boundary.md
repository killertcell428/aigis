---
title: "MCPの信頼境界設計とラグプル攻撃"
---

# MCPの信頼境界設計とラグプル攻撃

## なぜAIエージェントはMCPツールを信頼しすぎるのか

前章ではMCPサーバーの脆弱性を概観しました。本章では、より根本的な問題——MCPプロトコルの**信頼モデル**そのものの設計課題と、承認後に豹変する「ラグプル攻撃」について解説します。

### MCPの信頼境界はどこにあるのか

```
ユーザー → Claude Code → MCP Server → 外部サービス
         ↑               ↑            ↑
         信頼される       信頼境界？    外部
```

現在のMCPプロトコルでは、**ツールのdescriptionがLLMのコンテキストに直接注入**されます。これは以下の問題を引き起こします。

1. **ツールdescriptionがシステム指示と同等の権威を持つ**
2. **ツール実行結果が他のツールのコンテキストを汚染する**
3. **信頼レベルの明確な区分がない**

### 信頼レベルの設計

本来、AIエージェントのコンテキスト内のデータには明確な信頼レベルが必要です。

```
SYSTEM（最高信頼）  → システムプロンプト、開発者定義の指示
USER（高信頼）      → ユーザーの直接入力
TOOL_RESULT（中信頼）→ MCPツールの実行結果
EXTERNAL（低信頼）  → 外部から取得したデータ（Web、メール等）
```

しかし現状のLLMは、これらすべてを**同じ「テキスト」**として処理します。外部のWebページに書かれたテキストも、システムプロンプトと同じ重みで解釈される可能性があるのです。

## ラグプル攻撃——承認後に豹変するツール

![ラグプル攻撃のタイムライン](/images/ch06-rugpull-timeline.png)
*図：MCPラグプル攻撃のタイムラインと防御策の有効性比較*

### 攻撃の仕組み

「ラグプル（Rug Pull）」は暗号通貨の世界で知られる詐欺手法ですが、MCPエコシステムでも同様の攻撃が可能です。

```
Day 1:  安全なツールを公開
        → ユーザーがコードレビューし、承認

Day 8:  サーバー側でツール定義を密かに変更
        → tool descriptionに悪意ある指示を追加

Day 9〜: ユーザーは承認済みのつもりで使い続ける
        → 変更されたdescriptionにより、機密データが流出
```

### なぜ既存の防御が効かないのか

| 防御策 | 承認時 | 実行時 | 問題 |
|--------|--------|--------|------|
| **コードレビュー** | ✅ 安全を確認 | ❌ 再レビューなし | 承認時と実行時で内容が異なる |
| **ホワイトリスト** | ✅ ツール名を許可 | ❌ 定義変更を検知しない | 同じツール名、異なる動作 |
| **ネットワーク監視** | - | ⚠️ 正常通信に紛れる | 正当なAPI通信との区別が困難 |
| **OSS限定ポリシー** | ✅ ソース確認 | ⚠️ デプロイ後は未監視 | サーバー側の変更は見えない |

### CyberArkの調査結果

CyberArkの2025年の調査によると、npmで公開されているMCPサーバーの**15%がリリース後にツール定義を変更**していました。すべてが悪意あるものではありませんが、変更を検知する仕組みが不足していることが浮き彫りになっています。

## ETDI：暗号署名による解決策

### ETDIとは

ETDI（Enhanced Tool Definition Interface）は、MCPツール定義に暗号署名を導入する提案です。

```
ツール定義の作成時:
  定義内容 → ハッシュ生成 → 秘密鍵で署名 → 署名付き定義を配布

ツール使用時:
  署名付き定義を受信 → 公開鍵で署名検証 → ハッシュ一致を確認
  → 不一致なら実行拒否
```

### ETDIが保証するもの

1. **完全性**: 定義が改竄されていないことを暗号的に保証
2. **真正性**: 定義の作成者を特定可能
3. **タイムスタンプ**: いつの時点の定義かを記録

### 現在のETDIのステータス

ETDIは現時点では**ドラフト段階**であり、MCPプロトコルの標準仕様には含まれていません。しかし、MCP WGで活発に議論されており、今後の標準化が期待されています。

## ETDIが使えない今、何をすべきか

ETDIの標準化を待つ間にも、以下の対策でラグプル攻撃のリスクを軽減できます。

### 1. OSS限定 + 定期的なソース確認

```bash
# MCPサーバーのソースコードを定期的に確認
# tool descriptionの変更差分をチェック
git -C ./mcp-servers/target-server log --diff-filter=M -- "*.json" "*.yaml"
```

### 2. ツール定義のスナップショット管理

承認時のツール定義を保存し、実行時に比較する。

```python
import hashlib
import json

def verify_tool_definition(tool_name: str, current_def: dict, snapshot_path: str) -> bool:
    """承認時のスナップショットと現在の定義を比較"""
    with open(snapshot_path) as f:
        approved_snapshot = json.load(f)
    
    current_hash = hashlib.sha256(
        json.dumps(current_def, sort_keys=True).encode()
    ).hexdigest()
    
    approved_hash = approved_snapshot.get(tool_name, {}).get("hash")
    
    if current_hash != approved_hash:
        raise SecurityError(
            f"Tool '{tool_name}' definition has changed since approval. "
            f"Expected: {approved_hash[:16]}... Got: {current_hash[:16]}..."
        )
    return True
```

### 3. コンテナ化によるネットワーク制限

MCPサーバーをDockerコンテナ内で実行し、不要な外部通信を遮断する。

```yaml
# docker-compose.yml
services:
  mcp-filesystem:
    image: mcp-filesystem:pinned-v1.2.3
    read_only: true
    volumes:
      - ./project:/workspace:ro  # 読み取り専用マウント
    networks:
      - isolated
    # ~/.ssh, ~/.aws はマウントしない

networks:
  isolated:
    internal: true  # 外部ネットワークアクセスなし
```

### 4. Human-in-the-Loopゲート

機密性の高い操作には人間の承認を必須にする。

```python
# 承認が必要な操作カテゴリ
SENSITIVE_OPERATIONS = {
    "DELETE":     "データの削除操作",
    "NETWORK":    "外部ネットワークへの通信",
    "CREDENTIAL": "認証情報へのアクセス",
    "EXECUTE":    "任意コマンドの実行",
    "EMAIL":      "メールの送信",
}
```

## MCPセキュリティのロードマップ

```
現在（2026年Q1）
├── ホワイトリスト管理 ✅
├── auto_approve無効化 ✅
├── tool descriptionスキャン ✅
└── コンテナ化 ✅

短期（2026年Q2-Q3）
├── ツール定義スナップショット管理
├── 定期的な定義変更監視
└── Cross-toolコンテキスト分離の検討

中期（2026年後半〜）
├── ETDI標準化・導入
├── 暗号署名によるツール検証
└── MCPサーバー認証局の整備
```

MCPは強力な接続性を提供しますが、その信頼モデルはまだ発展途上です。「便利だから」ではなく「安全だから」という基準でMCPサーバーを選定し、多層的な防御を構築することが重要です。
