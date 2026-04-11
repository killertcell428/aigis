---
title: "litellmに悪意あるコードが混入 — AIエージェント環境を狙ったサプライチェーン攻撃の全貌と防御策"
emoji: "🔓"
type: "tech"
topics: ["セキュリティ", "AI", "Python", "サプライチェーン", "ClaudeCode"]
published: false
---

## この記事を読んでほしい人

- `pip install litellm` したことがある人（**今すぐバージョン確認してください**）
- AIエージェント（Claude Code / LangChain / Cursor等）を業務で使っている開発者
- CI/CDパイプラインでPythonパッケージを自動インストールしている運用者
- AIセキュリティに関心があるエンジニア全般

:::message alert
**緊急確認事項**: litellm v1.82.7 または v1.82.8 をインストールした環境がある場合、**全認証情報が漏洩した前提**で対応してください。パッケージの削除だけでは不十分です。
:::

## 何が起きたのか — 3時間で9,500万DL/月のパッケージが兵器化された

2026年3月24日、Pythonパッケージ**litellm**（月間ダウンロード約340万回/日）に、認証情報を窃取するマルウェアが混入されたバージョンがPyPIに公開されました。

> LiteLLM versions 1.82.7 and 1.82.8 were published on March 24, 2026, likely stemming from the package's use of Trivy in their CI/CD workflow.
> — [Datadog Security Labs](https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/)

**影響を受けたバージョン:**
- `litellm==1.82.7` — `proxy_server.py` にBase64エンコードされたペイロードを注入
- `litellm==1.82.8` — 上記に加え、`litellm_init.pth` ファイルによるPythonインタプリタ起動時の自動実行

PyPIが隔離措置を取るまでの約3時間、これらのバージョンがダウンロード可能な状態でした。

> 出典: [LiteLLM公式 Security Update](https://docs.litellm.ai/blog/security-update-march-2026)

**CVE-2026-33634**（CVSS 9.4）が割り当てられています。

## 攻撃チェーン — セキュリティスキャナーが攻撃の入口になった

この攻撃の最大の特徴は、**セキュリティツール（Trivy）自体が侵害の起点**になったことです。攻撃者グループ「TeamPCP」による5段階の攻撃チェーンを時系列で解説します。

### Phase 1: Trivyの侵害（3月19日）

攻撃はlitellmへの直接攻撃ではなく、**Aqua Security社のセキュリティスキャナーTrivy**の侵害から始まりました。

> An automated bot called "hackerbot-claw" exploited this misconfiguration to steal a privileged Personal Access Token (PAT) from the CI environment.
> — [GitGuardian Blog](https://blog.gitguardian.com/trivys-march-supply-chain-attack-shows-where-secret-exposure-hurts-most/)

具体的には：

1. Trivy リポジトリのGitHub Actionsワークフローに設定ミスがあった
2. 攻撃者は`aqua-bot`サービスアカウントのPAT（Personal Access Token）を窃取
3. このPATを使い、悪意あるTrivy v0.69.4をリリース
4. さらに`aquasecurity/trivy-action`の**75〜76個のGitタグを強制的に書き換え**、ピン留めされたバージョンも悪意あるコードを指すようにした

> 出典: [Snyk — How a Poisoned Security Scanner Became the Key to Backdooring LiteLLM](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)

:::message
**重要な教訓**: 2026年2月末にPATの漏洩が最初に検知された際、Aqua Securityはクレデンシャルのローテーションを実施しました。しかし**ローテーションが不完全**で、一部のアクセスパスが残っていたため、3月19日の攻撃が可能になりました。
> "The rotation was incomplete, leaving residual access paths still open to the attacker."
> — [GitGuardian Blog](https://blog.gitguardian.com/trivys-march-supply-chain-attack-shows-where-secret-exposure-hurts-most/)
:::

### Phase 2: npmワームの展開（3月20-22日）

TeamPCPは並行して、**45以上のnpmパッケージ**（@EmilGroup, @opengov スコープ）に自己増殖型のワームを展開しました。

### Phase 3: Checkmarx KICS等の侵害（3月23日）

Checkmarx KICSおよびOpen VSX拡張機能が侵害されました。

### Phase 4: litellmの侵害（3月24日）— 本記事の焦点

LiteLLMのCI/CDパイプラインは、ビルド時にTrivyを使ってセキュリティスキャンを実行していました。しかし、**Trivyのバージョンをピン留めしていなかった**ため、侵害済みのTrivy v0.69.4が自動的にプルされました。

> LiteLLM's build pipeline invoked the compromised Trivy scanner without version pinning, pulling it via `apt`. The malicious action extracted the `PYPI_PUBLISH` token from the GitHub Actions runner environment.
> — [Snyk](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)

攻撃者はこの`PYPI_PUBLISH`トークンを使って、悪意あるlitellm v1.82.7 / v1.82.8をPyPIに直接公開しました。

### Phase 5: Telnyx侵害（3月27日）

同様の手法で、VoIPライブラリ`telnyx` v4.87.1/4.87.2も侵害されました。

> 出典: [Datadog Security Labs — LiteLLM and Telnyx compromised on PyPI](https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/)

## マルウェアの技術的詳細 — 6段階のペイロード

混入されたマルウェアは単純な情報窃取ではなく、**6段階の高度なペイロード**で構成されていました。

### Stage 1: 認証情報の大量収集

以下を網羅的に収集します：

- 環境変数（全体）
- SSH鍵（`~/.ssh/`）
- クラウド認証情報（AWS / GCP / Azure）
- **AWS Secrets Manager、SSM Parameter Store**の内容
- Kubernetesの`kubeconfig`ファイルとトークン
- Dockerレジストリ認証情報
- `.env`ファイル、API トークン
- シェル履歴（`.bash_history`等）
- データベース認証情報
- **暗号通貨ウォレットファイルとシードフレーズ**

### Stage 2: 暗号化とパッケージング

> A 32-byte AES-256 session key is generated via `openssl rand`, encrypted with AES-256-CBC (PBKDF2 key derivation). The session key itself was encrypted using a hardcoded 4096-bit RSA public key.
> — [Snyk](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)

収集データはAES-256で暗号化された上で、RSA-4096公開鍵でセッションキーをラップ。`tpcp.tar.gz`としてパッケージングされます。

### Stage 3: データ送信

暗号化されたデータは、攻撃者が管理するドメインにHTTP POSTで送信されます：

```
POST https://models.litellm[.]cloud
Header: X-Filename: tpcp.tar.gz
```

:::message alert
`models.litellm.cloud` は公式のlitellmドメインではありません。攻撃者が取得した偽装ドメインです。
:::

### Stage 4: 永続化

バックドアがシステムに永続的にインストールされます：

```
~/.config/sysmon/sysmon.py       ← バックドア本体
~/.config/systemd/user/sysmon.service  ← systemdによる自動起動
```

### Stage 5: C2ビーコニング

5分ごとに`https://checkmarx[.]zone/raw`にポーリングし、追加のペイロードをダウンロード・実行します。

### Stage 6: Kubernetes横展開

Kubernetesクラスタ内で特権付きDaemonSetを展開し、全ノードに感染を拡大：

```
Pod名パターン: node-setup-*, kamikaze, provisioner
イメージ: alpine:latest（特権モードで実行）
→ ホストファイルシステムをマウントしてバックドアをインストール
```

> 出典: [Datadog Security Labs](https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/)

## 2つの異なる注入手法

TeamPCPは、検知を困難にするために2つの異なる手法を使い分けました。

### v1.82.7: ソースコード注入

`litellm/proxy/proxy_server.py`にBase64エンコードされたペイロードを直接埋め込み。`litellm.proxy`モジュールがインポートされたときにのみ実行されます。

> executes when anything imports `litellm.proxy`
> — [Snyk](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)

### v1.82.8: .pthファイル注入（より危険）

`litellm_init.pth`ファイルをsite-packagesに配置。この手法が極めて危険な理由：

> executable lines in `.pth` files run during interpreter startup — executable on every Python interpreter startup with no import required, including when `pip`, `python -c`, or an IDE's language server starts Python
> — [Snyk](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)

つまり、**litellmをインポートしなくても、Pythonを起動するだけで実行される**ということです。IDEの言語サーバーやpipコマンドの実行時にも発火します。

## IOC（侵害の痕跡）— 今すぐ確認してください

### ネットワークIOC

| IOC | 用途 |
|-----|------|
| `models.litellm[.]cloud` | データ送信先 |
| `checkmarx[.]zone/raw` | C2サーバー |
| `83.142.209.203:8080` | Telnyx用ペイロード配信 |
| `aquasecurtiy[.]org` | Trivyのタイポスクワッティング |

### ファイルシステムIOC

```bash
# 以下のファイルが存在しないか確認
ls -la ~/.config/sysmon/sysmon.py
ls -la ~/.config/systemd/user/sysmon.service
find / -name "litellm_init.pth" 2>/dev/null
ls -la /tmp/pglog /tmp/.pg_state 2>/dev/null
```

### Kubernetes IOC

```bash
# 不審なPod名を検索
kubectl get pods -A | grep -E "node-setup-|kamikaze|provisioner"

# 不審なDaemonSetを検索
kubectl get daemonsets -A --field-selector metadata.namespace=kube-system
```

### 検知クエリ（Datadog等）

```
# DNS/ネットワーク
@dns.question.name:(models.litellm.cloud OR checkmarx.zone)

# Kubernetes監査ログ
source:kubernetes.audit @objectRef.name:*node-setup-*

# ファイルシステム
@file.path:(*litellm_init.pth OR *sysmon.py OR /tmp/pglog)
```

> 出典: [Datadog Security Labs](https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/)

## 影響を受けたかの判定フローチャート

```
litellmを使っている？
  │
  ├─ No → 影響なし（ただし依存関係の確認推奨）
  │
  └─ Yes → バージョンは？
       │
       ├─ v1.82.6以下 → 影響なし ✅
       │
       ├─ v1.82.7 or v1.82.8 → ⚠️ 侵害の前提で対応
       │     │
       │     ├─ 1. 全認証情報をローテーション
       │     ├─ 2. IOCの確認
       │     ├─ 3. Kubernetes環境の監査
       │     └─ 4. システムの再構築を検討
       │
       └─ Docker公式イメージ使用 → 影響なし ✅
          (ghcr.io/berriai/litellm)
```

> 出典: [LiteLLM公式 Security Update](https://docs.litellm.ai/blog/security-update-march-2026)

## AIエージェント環境への示唆 — なぜこの攻撃が特に危険なのか

litellmは「100+ LLM APIを統一的に呼び出すためのプロキシ」であり、**AIエージェントのインフラ層**で広く使われています。この攻撃がAIエージェント環境で特に危険な理由：

### 1. AIエージェントは大量の認証情報を持つ

Claude Code、LangChain、AutoGPTなどのAIエージェントは、各種API（OpenAI、Anthropic、AWS等）のキーを環境変数に保持しています。これらは今回のマルウェアの**最優先の窃取対象**です。

### 2. CI/CDパイプラインは信頼の起点

開発者は `pip install litellm` をCI/CDで自動実行しています。セキュリティスキャナー（Trivy）が侵害されたことで、**「セキュリティを確認するツールそのものが攻撃ベクトル」**という、信頼の根幹を揺るがす事態が発生しました。

### 3. .pthファイルは従来のスキャンで検出困難

v1.82.8で使われた`.pth`ファイル注入は、通常のソースコード検査やimportフック監視では検出できません。Pythonインタプリタの起動プロセスに直接介入するため、**既存のセキュリティツールの盲点**を突いています。

## 防御策 — AIエージェント環境を守るために

### 即時対応

```bash
# 1. バージョン確認
pip show litellm | grep Version

# 2. v1.82.6以下にダウングレード（影響を受けている場合）
pip install litellm==1.82.6

# 3. .pthファイルの確認・削除
find $(python -c "import site; print(site.getsitepackages()[0])") -name "litellm_init.pth" -delete

# 4. 永続化の確認
ls -la ~/.config/sysmon/sysmon.py 2>/dev/null && echo "⚠️ バックドア検出！"
```

### 中長期対応

| 対策 | 詳細 |
|------|------|
| **バージョンピン留め** | `litellm==1.82.6` のように必ずバージョンを固定 |
| **ハッシュ検証** | `pip install --require-hashes` でパッケージのSHA-256を検証 |
| **CI/CDの最小権限化** | PyPI公開トークンをGitHub Actionsの環境変数に直接置かない |
| **依存関係の監査** | `pip-audit`や`safety`で定期的に脆弱性をスキャン |
| **ネットワーク監視** | 上記IOCドメインへの通信を監視・ブロック |

### エージェント操作レベルの防御

上記の対策はサプライチェーン攻撃の**予防**に焦点を当てていますが、万が一マルウェアが混入した場合に**被害を最小化**するには、エージェントの操作そのものを監視・制御する必要があります。

[**aigis**](https://github.com/killertcell428/aigis)は、AIエージェントの全ツール呼び出しをインターセプトし、脅威スキャン・ポリシー評価・ログ記録を行うOSSです。

```bash
pip install aigis
aig init
```

aigisが今回の攻撃に対して提供する防御レイヤー：

| 攻撃ステージ | aigisの防御 |
|------------|-----------------|
| Stage 1: 認証情報の収集 | **PII/機密情報検出**: `.env`やAPIキーパターンを含むファイルアクセスをブロック |
| Stage 3: 外部へのデータ送信 | **ネットワークポリシー**: 未承認ドメインへのcurl/wget実行をブロック |
| Stage 4: 永続化 | **ファイルシステムポリシー**: `~/.config/systemd/`への書き込みを検知・ブロック |
| Stage 6: Kubernetes横展開 | **操作ログ**: kubectl操作を全件記録し、異常なDaemonSet作成を検知 |
| 全ステージ共通 | **48パターンの脅威スキャン**: Base64エンコードされたペイロード実行パターンを検知 |

サプライチェーン攻撃を100%防ぐことは困難ですが、**「攻撃が侵入した後の被害を最小化する」** という多層防御の考え方が重要です。aigisはその「最後の砦」として機能します。

## まとめ

litellmサプライチェーン攻撃は、AIエージェント開発者にとって3つの重要な教訓を残しました。

1. **セキュリティツール自体が攻撃ベクトルになりうる** — Trivyという信頼されたスキャナーが起点だった
2. **バージョンピン留めとハッシュ検証は必須** — 「最新版を常にインストール」は危険
3. **多層防御が不可欠** — サプライチェーン攻撃の予防だけでなく、侵入後の被害最小化も考慮すべき

AIエージェントを業務で使うなら、**操作ログの記録・危険操作のブロック・機密情報の保護**は「あるといいね」ではなく「なければ詰む」レベルの必須要件です。

## 参考資料

### 公式情報
- [LiteLLM公式 Security Update: March 2026](https://docs.litellm.ai/blog/security-update-march-2026)
- [CVE-2026-33634](https://nvd.nist.gov/vuln/detail/CVE-2026-33634)（CVSS 9.4）

### 技術分析
- [Datadog Security Labs — LiteLLM and Telnyx compromised on PyPI: Tracing the TeamPCP supply chain campaign](https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-teampcp-supply-chain-campaign/)
- [Snyk — How a Poisoned Security Scanner Became the Key to Backdooring LiteLLM](https://snyk.io/articles/poisoned-security-scanner-backdooring-litellm/)
- [GitGuardian — Trivy's March Supply Chain Attack Shows Where Secret Exposure Hurts Most](https://blog.gitguardian.com/trivys-march-supply-chain-attack-shows-where-secret-exposure-hurts-most/)
- [Wiz — LiteLLM TeamPCP Supply Chain Attack](https://www.wiz.io/blog/threes-a-crowd-teampcp-trojanizes-litellm-in-continuation-of-campaign)
- [Kaspersky — Trojanization of Trivy, Checkmarx, and LiteLLM](https://www.kaspersky.com/blog/critical-supply-chain-attack-trivy-litellm-checkmarx-teampcp/55510/)

### メディア報道
- [The Hacker News — TeamPCP Backdoors LiteLLM Versions 1.82.7–1.82.8](https://thehackernews.com/2026/03/teampcp-backdoors-litellm-versions.html)
- [BleepingComputer — Popular LiteLLM PyPI package backdoored to steal credentials](https://www.bleepingcomputer.com/news/security/popular-litellm-pypi-package-compromised-in-teampcp-supply-chain-attack/)
- [The Register — LiteLLM infected with credential-stealing code via Trivy](https://www.theregister.com/2026/03/24/trivy_compromise_litellm/)
- [ReversingLabs — TeamPCP software supply chain attack spreads to LiteLLM](https://www.reversinglabs.com/blog/teampcp-supply-chain-attack-spreads)

### 関連ツール
- [aigis — AIエージェントの操作監視・制御OSS](https://github.com/killertcell428/aigis)
