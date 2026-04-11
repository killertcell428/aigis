---
title: "エージェントID・認証・認可——Non-Human Identityの管理"
free: false
---

# エージェントID・認証・認可——Non-Human Identityの管理

## NHIの爆発と実際のインシデント

### 人間IDの45倍——見えないIDが組織を蝕む

企業のIT環境において、サービスアカウント、APIキー、OAuthトークン、証明書といった**Non-Human Identity（NHI）**が爆発的に増加しています。CyberArkの2024年調査によれば、NHIと人間IDの比率は**45:1**に達しました。Gartnerは「2026年までにセキュリティ障害の75%がID管理不備に起因する」と予測しています（2023年時点では50%）。

AIエージェントはこの問題をさらに加速させます。エージェントは自律的にAPIを呼び出し、データベースにアクセスし、外部サービスと通信します。1つのエージェントが複数のサービスアカウントやトークンを保持し、それぞれが独立したNHIとして存在します。しかし多くの組織で、これらのNHIはIAMの管理対象外に置かれています。

### NHIが引き起こした重大インシデント

NHI管理の不備がどれほど深刻な結果をもたらすか、実際のインシデントが示しています。

**Cloudflare/Okta侵害（2024年1月）**

2023年10月のOkta侵害で流出したサービストークンとサービスアカウント資格情報が、**ローテーションされないまま**放置されていました。攻撃者はこれらのNHIを使い、CloudflareのAtlassian環境（Confluence、Jira、Bitbucket）に侵入しました。Cloudflareのインシデント対応は迅速でしたが、根本原因は「流出後にNHIを失効させなかった」という管理不備です（Cloudflare Blog, 2024-02-02）。

**Microsoft Midnight Blizzard（2024年1月）**

ロシアの国家支援グループNobellium（Midnight Blizzard）が、Microsoftのレガシー**テスト用OAuthアプリケーション**を悪用しました。このNHIには過剰な権限が付与されており、攻撃者はExchange Online環境を通じて上級幹部のメールにアクセスしました（Microsoft Security Blog, 2024-01-19）。世界最大級のテクノロジー企業ですら、放置されたNHIが攻撃経路となったのです。

**CircleCI侵害（2023年1月）**

エンジニアのセッショントークンが窃取され、そこから**CI/CDパイプラインに保存されたOAuthトークンとサービスアカウントキー**が連鎖的に流出しました。CI/CD環境はNHIの集積地であり、1つの侵害が組織全体のサービスアカウントに波及する典型例です（CircleCI Blog, 2023-01-13）。

これらのインシデントに共通するパターンは明確です。**NHIのライフサイクル管理（発行・ローテーション・失効）が機能していなかった**ことです。

### NHIライフサイクル管理の4フェーズ

NHI管理を体系化するには、以下の4フェーズのライフサイクルを定義・運用する必要があります。

1. **発見（Discovery）**: 組織内に存在するNHIの棚卸し。APIキー、サービスアカウント、OAuthアプリ、証明書を網羅的に可視化する
2. **発行（Provisioning）**: 最小権限の原則に基づく資格情報の発行。有効期限とスコープを明示的に設定する
3. **ローテーション（Rotation）**: 定期的な資格情報の更新。自動化が必須であり、手動ローテーションはスケールしない
4. **失効（Revocation）**: 不要になったNHIの即座の無効化。インシデント発生時の緊急失効手順も含む

CyberArkの2024年報告では、回答企業の93%が過去1年間に2件以上のID関連侵害を経験しています。その多くは、このライフサイクルのいずれかのフェーズの不備に起因しています。

## SPIFFE/SPIREによるワークロードID

### なぜ従来のID管理では不十分なのか

従来のサービスアカウント管理は、静的な資格情報（APIキー、パスワード、長期トークン）に依存しています。これらは以下の問題を抱えています。

- **漏洩リスク**: 環境変数やコード内にハードコードされやすい
- **ローテーション困難**: 依存サービスが多いほど更新が困難
- **ID検証の欠如**: トークンの保持者が正当なワークロードか検証できない

SPIFFE（Secure Production Identity Framework For Everyone）は、この問題に対する構造的な解決策です。

### SPIFFEの仕組み

SPIFFEはCNCFのgraduatedプロジェクト（2022年9月）であり、ワークロードに暗号学的に検証可能なIDを付与する標準仕様です。

**SPIFFE ID**の形式は以下の通りです。

```
spiffe://trust-domain/workload-identifier

例:
spiffe://mycompany.com/agent/product-search
spiffe://mycompany.com/agent/order-processing
spiffe://mycompany.com/mcp-server/database-reader
```

この識別子はSVID（SPIFFE Verifiable Identity Document）として発行されます。SVIDにはX.509証明書形式（SAN内にURI SANとしてSPIFFE IDを格納）とJWT形式（`sub`クレームにSPIFFE IDを格納）の2種類があります。

**SPIRE**はSPIFFEの参照実装です。Serverコンポーネント（CA機能）とAgent（各ノードでのattestation）で構成され、ワークロードの身元を確認した上で短命な証明書を自動発行します。

```
┌─────────────┐
│ SPIRE Server│ ← CA（認証局）として機能
│  (Control)  │    信頼ドメインを管理
└──────┬──────┘
       │  Attestation（ワークロードの身元確認）
       │
┌──────┴──────┐     ┌──────────────┐
│ SPIRE Agent │────→│ AIエージェント │
│  (Node)     │     │   SVID保持    │
└─────────────┘     └──────────────┘
```

エージェントのID管理にSPIFFEを採用する利点は、**静的な資格情報が不要になる**ことです。SVIDは短命（通常1時間以内）で自動ローテーションされるため、漏洩しても被害期間が限定されます。

### エージェント環境へのSPIFFE適用例

マルチエージェント環境では、各エージェントとMCPサーバーにSPIFFE IDを割り当てます。

```
spiffe://mycompany.com/agent/orchestrator       ← オーケストレーター
spiffe://mycompany.com/agent/data-analyst        ← データ分析エージェント
spiffe://mycompany.com/mcp-server/postgres       ← DB接続MCPサーバー
spiffe://mycompany.com/mcp-server/slack          ← Slack MCPサーバー
```

mTLS（相互TLS認証）により、各ワークロード間の通信を暗号化し、通信相手のIDを暗号学的に検証できます。これにより、なりすましエージェントやMCPサーバーによる不正アクセスを防止できます。

## OAuth 2.0のエージェント適用

### Client Credentials Flowの活用

AIエージェントのような非対話型クライアントには、OAuth 2.0のClient Credentials Flow（RFC 6749 Section 4.4）が適しています。エージェントはクライアントIDとシークレットで直接トークンを取得し、ユーザーの介在なしにAPIにアクセスします。

ただし、エージェントが複数のAPIを呼び出す場合、単一のアクセストークンに過剰なスコープが付与されるリスクがあります。ここでRFC 8707 Resource Indicators（2020年2月）が重要になります。

```
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=agent-product-search
&client_secret=...
&scope=read:products
&resource=https://api.example.com/products
```

`resource`パラメータにより、トークンの有効範囲を特定のAPIリソースに限定できます。エージェントが商品検索APIと注文APIの両方にアクセスする場合、**それぞれ別のトークンを取得**させることで、1つのトークン漏洩の影響を限定できます。

### Workload Identity Federation（WIF）

主要クラウドプロバイダは、外部IDプロバイダからのトークンをクラウドIAMロールにマッピングするWIFを提供しています。

| 項目 | GCP | AWS | Azure |
|------|-----|-----|-------|
| 機能名 | Workload Identity Federation | IAM Roles Anywhere | Workload Identity Federation |
| GA時期 | 2021年4月 | 2022年7月 | 2024年 |
| SPIFFE対応 | OIDC経由マッピング | X.509-SVIDで直接利用可 | OIDC経由間接 |

WIFにより、AIエージェントは**長期的なクラウドアクセスキーを保持せず**、SPIFFE/SPIREで取得したSVIDを短命のクラウド資格情報に交換できます。Midnight Blizzard事件のようなレガシーOAuthアプリの放置リスクを構造的に排除する設計です。

## ゼロトラストのエージェント適用

### Zero Standing Privileges（ZSP）

ゼロトラストの原則をNHI管理に適用する上で、**Zero Standing Privileges（ZSP）**は中核的な概念です。常時付与の特権をゼロにし、必要な時に最小権限を一時的に付与する設計です。

**実装パターン1：JIT Access**

Azure PIM（Privileged Identity Management）のように、エージェントがタスク実行時にのみ権限を申請し、承認後に時間制限付きで付与されます。

```
エージェント → 権限申請（タスク: DB読取、時間: 30分）
    → 承認エンジン → 権限付与（30分後に自動失効）
        → タスク実行 → 権限自動回収
```

**実装パターン2：Ephemeral Credentials**

HashiCorp VaultのDynamic Secretsのように、エージェントのリクエスト時にデータベース資格情報を動的に生成し、TTL（生存時間）経過後に自動的に無効化します。

```
エージェント → Vault API → 一時的なDB資格情報（TTL: 1時間）
    → DB操作 → TTL満了 → 資格情報自動失効
```

### Microsoft Zero Trust for AI（ZT4AI）

2026年3月、MicrosoftはRSACにおいてZero Trust for AI（ZT4AI）リファレンスアーキテクチャを発表しました。700以上のコントロールを含み、AIエージェントへのゼロトラスト適用を体系化しています。

ZT4AIの3原則は、ゼロトラストの基本原則をエージェントに読み替えたものです。

- **Verify Explicitly（明示的に検証）**: エージェントのすべてのアクセスをID・場所・デバイス状態で検証
- **Least Privilege（最小権限）**: JIT/JEAによる一時的かつ最小限の権限付与
- **Assume Breach（侵害前提）**: エージェントが侵害された場合のブラストラディウスを最小化

エージェント環境におけるゼロトラストの実践は、従来の人間ユーザー向け設計からの大きな転換を要求します。人間のように多要素認証やパスワード変更を促すことはできません。代わりに、**暗号学的ID（SPIFFE）、短命資格情報（Vault）、継続的検証（行動ベースの信頼度評価）**を組み合わせた自動化されたゼロトラストが必要です。

## ツール紹介

エージェントのNHI管理とゼロトラスト実装を支援するツールを紹介します。

### HashiCorp Vault

シークレット管理のデファクトスタンダードです。Vault 1.17（2024年6月GA）以降、PKI Secrets EngineでX.509-SVIDの発行が可能になり、SPIFFE/SPIREとの統合が強化されています。Dynamic Secretsによるエフェメラル資格情報の生成は、エージェントのZSP実装において中核的な役割を果たします。

### CyberArk / Astrix / Clutch Security

NHI管理に特化したプラットフォームです。CyberArkは従来のPAM（特権アクセス管理）にNHI管理を統合し、NHIの発見・分類・リスク評価・ローテーションを自動化します。AstrixとClutch SecurityはNHIセキュリティの新興ベンダーとして、APIキーやサービスアカウントの可視化と管理に特化しています。

### Aigis

Aigisは、YAMLベースのポリシーエンジンによるアクセス制御を提供します。エージェントのアクションに対してallow/deny/reviewの判定をポリシーファイルで定義できます。

```yaml
# Aigisポリシー定義の例
rules:
  - name: restrict-database-access
    action: deny
    condition:
      tool: database_query
      resource: "production.*"
    message: "本番DBへの直接アクセスは禁止されています"
```

ただし、AigisはSPIFFE/Vaultのような暗号学的ID基盤やシークレット管理の機能は提供しません。NHI管理の全体像においては、ID基盤（SPIFFE/SPIRE）、シークレット管理（Vault）、ポリシー制御（Aigis/OPA）をそれぞれの強みに応じて組み合わせる設計が推奨されます。
