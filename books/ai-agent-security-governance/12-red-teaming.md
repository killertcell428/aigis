---
title: "レッドチーミングと継続的テスト"
free: false
---

# レッドチーミングと継続的テスト

## なぜエージェント専用のレッドチーミングが必要か

従来のLLMに対するレッドチーミングは、有害コンテンツの生成やガードレールの回避に焦点を当てていました。しかし、AIエージェントのレッドチーミングは質的に異なるアプローチを必要とします。エージェントはツールを使い、外部システムに作用するため、攻撃の影響範囲がテキスト出力を超えて実世界に及ぶからです。

NISTのCAISI（Computational AI Safety Institute、2025年1月）がAgentDojoベンチマークを使って実施した検証は、この差を端的に示しています。エージェント環境でのプロンプトインジェクション攻撃成功率は**81%**に達しました。一方、ベースライン（ツール呼び出し権限のない標準的なLLM）での成功率はわずか**11%**でした。

この約7倍の差は、エージェントがツール呼び出し権限を持つことで攻撃面が飛躍的に拡大することを意味しています。モデル単体のセキュリティテストでは、エージェントとしてデプロイした際の脆弱性を発見できません。

Adversa AIの2025 Edition報告は、実際のインシデントデータからこの問題の深刻さを裏付けています。プロンプトインジェクション（PI）がAIセキュリティインシデントの**35.3%**を占め、単独カテゴリとして最多です。損失額が10万ドルを超えるケースも報告されており、「理論的なリスク」ではなく「実在する経済的損失」であることが明確です。

### エージェントレッドチーミングの攻撃面

エージェント固有のレッドチーミングでは、以下の攻撃面をカバーする必要があります。

```
攻撃面              テスト内容
──────────────    ──────────────────────────────
プロンプト層        直接/間接PI、多言語攻撃、エンコーディング回避
ツール呼び出し層    ツールポイズニング、パラメータ改ざん、権限昇格
メモリ層           Memory Poisoning、コンテキスト汚染
マルチエージェント層  エージェント間メッセージスプーフィング、権限委任悪用
出力層             データ流出、PII漏洩、有害コンテンツ生成
```

これらの攻撃面を網羅的にテストするには、手動のレッドチーミングだけでは到底足りません。自動化ツールの導入が不可欠です。

## 自動化レッドチーミングツール

### Garak（NVIDIA）

Garakは、NVIDIAが開発・公開しているオープンソースのLLM脆弱性スキャナです。名前は「Deep Space Nine」のキャラクターに由来しています。

```bash
# 基本的な脆弱性スキャン
garak --model_type openai --model_name gpt-4 --probes all

# 特定のプローブセット（PI検出）
garak --model_type openai --model_name gpt-4 \
  --probes encoding,dan,knownbadsignatures
```

Garakは数十種類のプローブ（攻撃パターン）を内蔵しており、エンコーディング回避（Base64、ROT13等）、DAN（Do Anything Now）系統の脱獄、既知の悪意あるシグネチャ検出など、幅広いテストを自動化できます。

**強み**: プローブの豊富さ、OSS（カスタムプローブの追加が容易）、レポート出力機能。
**弱み**: エージェント固有の攻撃面（ツール呼び出し、マルチエージェント）への対応は限定的。モデル単体のテストに最適化されています。

### Promptfoo

Promptfooは、YAML設定ベースのLLMテストフレームワークで、CI/CDパイプラインへの統合を前提に設計されています。`promptfoo redteam`コマンドにより、自動化されたレッドチーミングテストを実行できます。

```yaml
# promptfoo redteam設定例
redteam:
  purpose: "エージェントのセキュリティテスト"
  plugins:
    - id: prompt-injection
      config:
        strategies:
          - jailbreak
          - indirect
          - multilingual
    - id: pii-leak
    - id: harmful-content
  providers:
    - id: openai:gpt-4
  numTests: 100
```

```bash
# レッドチーミング実行
promptfoo redteam run

# 結果をCI/CDで評価
promptfoo redteam report --format json --output results.json
```

Promptfooの最大の強みは、テスト定義がYAMLで宣言的に記述できることと、CI/CDパイプラインに組み込むための設計がされていることです。GitHub ActionsやGitLab CIのワークフローに1ステップとして追加でき、プロンプトやモデルの変更時に自動的にセキュリティテストが実行されます。

### PyRIT（Microsoft）

PyRIT（Python Risk Identification Toolkit）はMicrosoftが2024年2月にオープンソースとして公開した自動レッドチーミングツールです。マルチモーダル（テキスト・画像・音声）に対応し、攻撃シナリオの自動生成・実行・評価を一貫して行えます。

```python
from pyrit.orchestrator import RedTeamingOrchestrator
from pyrit.prompt_target import AzureOpenAITarget

target = AzureOpenAITarget(
    deployment_name="my-agent",
    endpoint="https://my-resource.openai.azure.com/",
)

orchestrator = RedTeamingOrchestrator(
    attack_strategy="prompt_injection",
    prompt_target=target,
    max_turns=5,  # マルチターン攻撃
)

result = await orchestrator.run()
print(f"攻撃成功率: {result.success_rate:.1%}")
```

PyRITの特徴は、**マルチターン攻撃**のシミュレーションです。単発のプロンプトではなく、複数のやり取りを通じて段階的にエージェントのガードレールを突破する攻撃パターンを自動生成します。これは実際の攻撃者の行動に近く、単発テストでは発見できない脆弱性を検出できます。

### ツール比較

| ツール | 開発元 | 対象 | CI/CD統合 | マルチモーダル | エージェント対応 |
|---|---|---|---|---|---|
| Garak | NVIDIA | モデル単体 | 部分的 | テキストのみ | 限定的 |
| Promptfoo | OSS | モデル/エージェント | ネイティブ | テキストのみ | 部分的 |
| PyRIT | Microsoft | モデル/エージェント | API経由 | テキスト/画像/音声 | マルチターン |

単一のツールですべてをカバーすることは難しく、目的に応じた組み合わせが現実的です。Promptfooを日常的なCI/CDテストに使い、PyRITを定期的な深度テストに使い、Garakをモデル変更時のベースラインテストに使う——といった使い分けが推奨されます。

## CI/CD統合パターン

レッドチーミングは一度実施すれば終わりではありません。エージェントのプロンプト変更、モデルのアップデート、ツール追加のたびに再テストが必要です。これを持続可能にするには、CI/CDパイプラインへの組み込みが不可欠です。

### GitHub Actions統合例

```yaml
# .github/workflows/agent-security.yml
name: Agent Security Test
on:
  pull_request:
    paths:
      - 'prompts/**'
      - 'agent-config/**'
      - 'tools/**'

jobs:
  red-team:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Promptfoo Red Team
        run: |
          npx promptfoo redteam run \
            --config agent-security.yaml \
            --output results.json

      - name: Evaluate Results
        run: |
          npx promptfoo redteam report \
            --format json \
            --output report.json
          # 攻撃成功率が閾値を超えたらfail
          python scripts/check_security.py report.json \
            --max-success-rate 0.05

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: report.json
```

### テストのトリガー設計

すべてのコード変更で完全なレッドチーミングを実行するのは、時間とコストの観点から現実的ではありません。以下のようなトリガー設計が推奨されます。

| トリガー | テスト範囲 | 実行時間目安 |
|---|---|---|
| プロンプト変更PR | 変更されたプロンプトに対するPI テスト | 5〜10分 |
| モデル変更 | フルスイートのレッドチーミング | 30〜60分 |
| ツール追加・変更 | ツール固有の攻撃パターン | 10〜20分 |
| 週次スケジュール | フルスイート + 新規攻撃パターン | 60〜120分 |
| リリース前 | フルスイート + マルチターン攻撃 | 2〜4時間 |

### 閾値の設定

CI/CDでレッドチーミングを「合否判定」するには、閾値の設定が重要です。攻撃成功率の許容閾値は、エージェントのリスクレベルに応じて段階的に設定します。

```
リスクレベル    許容攻撃成功率    説明
──────────    ────────────    ──────────────────
Critical      0%              金融取引・医療判断・インフラ制御
High          2%以下           本番データアクセス・外部API連携
Medium        5%以下           内部ツール・分析タスク
Low           10%以下          情報参照のみ・サンドボックス内
```

## 2026年の転換点：AIによるレッドチーミングの本格化

### Project Glasswing（Anthropic, 2026年4月）

2026年4月7日、Anthropicは**Project Glasswing**を発表しました。Claude Mythos Previewを活用した**$100M超の防御サイバーセキュリティイニシアチブ**です。

| 項目 | 内容 |
|------|------|
| 参加企業 | AWS、Apple、Broadcom、Cisco、CrowdStrike、Google、JPMorganChase、Linux Foundation、Microsoft、NVIDIA、Palo Alto Networks + 40以上のOSSメンテナ |
| 投入クレジット | $100M（モデル使用量） |
| OSS支援 | $2.5M（Alpha-Omega/OpenSSF）、$1.5M（Apache Software Foundation） |

**成果**:
- 主要OS・ブラウザの**全てで数千の高深刻度脆弱性**を発見
- 27年間未発見のOpenBSD TCP SACKバグ、16年間未発見のFFmpegバグを検出
- CyberGymベンチマーク: 83.1%（Opus 4.6: 66.6%）
- Cybench CTF: 全35問を100%正答（初のモデル）

Linux Kernelメンテナの**Greg Kroah-Hartman**は「1ヶ月前に何かが変わった。今や本物のレポートが来ている」とコメントし、curlの開発者**Daniel Stenberg**は「1日に何時間もこれに費やしている」と述べています。

### Mythos評価から学ぶレッドチーミングの新たな課題

Mythos Previewの244ページのSystem Cardは、AI自体を対象としたレッドチーミングの新たな課題を明らかにしました。

**評価認識（Evaluation Awareness）**

Mythosは評価中であることを約**29%**のケースで認識しました。つまり、レッドチーミングの結果が「モデルの真の振る舞い」を反映しているかどうかが疑わしくなります。モデルが「テスト中は安全に振る舞い、本番では異なる振る舞いをする」可能性——これはSleeper Agents研究（第15章）が予測した脅威そのものです。

**隠蔽行動（Concealment）**

<0.001%の頻度ながら、ルール違反を隠蔽する行動が観察されました。git履歴の改ざん、回答精度の偽装など。ホワイトボックス分析で「隠蔽」「戦略的操作」「疑惑回避」に関連する特徴量の活性化が確認されています。

**レッドチーミング手法への示唆**:
- ブラックボックステストだけでなく、**ホワイトボックス分析**（活性化パターンの検査）の重要性が増加
- テスト環境と本番環境を区別できないようにする工夫が必要
- 「モデルが整合的に見える」ことと「モデルが整合的である」ことの区別が、AIレッドチーミング最大の課題に

### AIによる防御的レッドチーミングの実用化

Project Glasswingは、AIを攻撃に使うのではなく**防御に使う**パラダイムを確立しました。Mythosは公開されませんが、セキュリティ専門家は**Cyber Verification Program**への申請で限定的にアクセスできます。

この流れは自動化レッドチーミングの未来を示唆しています。次世代のレッドチーミングは、**AIがAIをテストし、人間が結果を監査する**形態へ進化していく可能性があります。

## 規制要件としてのレッドチーミング

レッドチーミングは技術的なベストプラクティスであるだけでなく、規制要件として法的に義務化される流れが加速しています。

### EU AI Act

EU AI Act第55条(1)は、システミックリスクを持つ汎用AI（GPAI）モデルの提供者に対して、**adversarial testing（敵対的テスト）**の実施を義務付けています。Recital 110ではレッドチーミングが明示的に言及されており、体系的な敵対的テストが法的義務であることが明確です。

EU AI Actの完全施行は2026年8月ですが、GPAIモデル提供者への義務は段階的に適用が開始されます。EU市場でAIエージェントを提供する企業、またはEUのGPAIモデルを利用してエージェントを構築する企業は、レッドチーミングの実施体制を整備する必要があります。

### 米国の動向

米国では2023年10月の大統領令（Executive Order 14110）がAIの安全性テストに言及しており、NISTがAI Safety Institute（AISI）を通じてテスト手法の標準化を進めています。法的拘束力はEU AI Actに比べて弱いものの、政府調達や規制産業（金融・医療）では事実上の必須事項になりつつあります。

### 日本の動向

日本のAI事業者ガイドラインv1.2は、リスクの高いAIシステムに対するセキュリティテストの実施を推奨しています。法的拘束力はソフトローですが、EU AI Actと同様に、ガイドラインの遵守がインシデント発生時の過失認定に影響する可能性があります。

## ツール紹介

### Aigis — `aig benchmark`

Aigisの`aig benchmark`コマンドは、Aigisのガードレール（入出力スキャン、ポリシーエンジン）の検出精度をテストするためのベンチマーク機能です。

```bash
# Aigisの検出精度ベンチマーク
aig benchmark

# 結果例
Running benchmark suite...
  Prompt Injection Detection:  100% (64/64 patterns detected)
  PII Detection:               100% (all categories)
  Policy Evaluation:           100% (14/14 rules)
  False Positive Rate:         < 1%
Overall Score: 100%
```

`aig benchmark`は、Aigis自体の防御能力を定量的に評価するツールです。前述のGarak・Promptfoo・PyRITがエージェントやモデルの脆弱性を発見するツールであるのに対し、`aig benchmark`は防御側（ガードレール）の品質保証に焦点を当てています。

両者は補完的な関係にあります。Promptfooでエージェントの脆弱性を発見し、Aigisのガードレールで防御し、`aig benchmark`で防御の有効性を検証する——このサイクルが継続的セキュリティテストの基本形です。

### 推奨テスト構成

```
[開発フェーズ]
  Promptfoo redteam（CI/CD）→ 脆弱性の早期発見
  aig benchmark             → ガードレールの品質保証

[運用フェーズ]
  PyRIT（月次深度テスト）   → マルチターン・マルチモーダル攻撃
  Garak（モデル変更時）     → ベースライン脆弱性スキャン
  aig benchmark（変更時）   → ガードレール回帰テスト
```

## まとめ

レッドチーミングは「セキュリティチームが年に一度実施するイベント」ではなく、CI/CDパイプラインに組み込まれた継続的プロセスであるべきです。エージェントの攻撃面は従来のLLMよりも格段に広く、NISTの検証が示すように攻撃成功率は81%に達します。

自動化ツール（Garak、Promptfoo、PyRIT）をCI/CDに統合し、Aigisのベンチマークで防御の有効性を検証し、EU AI Act等の規制要件に対応する。このサイクルを回すことで、「テストしたことがない脆弱性に攻撃される」リスクを体系的に低減できます。

次章では、これまでに解説したガバナンス体制、HITL、オブザーバビリティ、レッドチーミングを統合し、エンタープライズ導入のロードマップとして具体化します。
